from datetime import datetime
from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
import bcrypt

db = SQLAlchemy()

content_tags = db.Table('content_tags',
    db.Column('content_id', db.Integer, db.ForeignKey('content.id'), primary_key=True),
    db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='student')
    bio = db.Column(db.Text)
    profile_photo = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    contents = db.relationship('Content', backref='uploader', lazy='dynamic')
    activities = db.relationship('ActivityLog', backref='user', lazy='dynamic')
    notifications = db.relationship('Notification', backref='recipient', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password_hash.encode('utf-8'))
    
    def is_admin(self):
        return self.role == 'admin'
    
    def is_teacher(self):
        return self.role == 'teacher'
    
    def can_upload(self):
        return self.role in ['admin', 'teacher']
    
    def can_download(self, content):
        if content.is_public:
            return True
        if self.role == 'admin':
            return True
        if self.role == 'teacher':
            return True
        return self.role == 'student'

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    contents = db.relationship('Content', backref='category', lazy='dynamic')

class Tag(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)

class Content(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    content_type = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'))
    uploaded_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    is_public = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    download_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    tags = db.relationship('Tag', secondary=content_tags, lazy='subquery',
                          backref=db.backref('contents', lazy='dynamic'))
    activities = db.relationship('ActivityLog', backref='content', lazy='dynamic')
    
    def get_type_icon(self):
        icons = {
            'pdf': 'fa-file-pdf',
            'ebook': 'fa-book',
            'audio': 'fa-headphones',
            'video': 'fa-video'
        }
        return icons.get(self.content_type, 'fa-file')
    
    def get_file_size_formatted(self):
        if not self.file_size:
            return 'Unknown'
        if self.file_size < 1024:
            return f'{self.file_size} B'
        elif self.file_size < 1024 * 1024:
            return f'{self.file_size / 1024:.1f} KB'
        else:
            return f'{self.file_size / (1024 * 1024):.1f} MB'

class ActivityLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content_id = db.Column(db.Integer, db.ForeignKey('content.id'))
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.Text)
    ip_address = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_global = db.Column(db.Boolean, default=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    sent_at = db.Column(db.DateTime)


# Community system models
class Community(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text)
    photo = db.Column(db.String(255))
    photo_thumbnail = db.Column(db.String(255))
    photo_thumbnail_2x = db.Column(db.String(255))
    is_private = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    memberships = db.relationship('Membership', backref='community', lazy='dynamic')
    posts = db.relationship('Post', backref='community', lazy='dynamic')

class Membership(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    role = db.Column(db.String(20), default='student')  # admin, teacher, student
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)

    # relationship to the user who is a member
    user = db.relationship('User', backref='memberships')

    __table_args__ = (db.UniqueConstraint('user_id', 'community_id', name='_user_community_uc'),)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(300))
    body = db.Column(db.Text, nullable=False)
    is_pinned = db.Column(db.Boolean, default=False)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = db.relationship('User', backref='posts')
    comments = db.relationship('Comment', backref='post', lazy='dynamic')

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('post.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', backref='comments')

class ChatMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_moderated = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship('User', backref='chat_messages')

class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_messages')


class LiveSession(db.Model):
    """Represents an in-progress or completed live session.

    Live sessions are first-class library content: after a session ends
    the recording can be saved and published as a `Content` record.
    """
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(300), nullable=False)
    host_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    community_id = db.Column(db.Integer, db.ForeignKey('community.id'))
    is_live = db.Column(db.Boolean, default=True)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    recording_path = db.Column(db.String(500))
    recording_size = db.Column(db.Integer)
    description = db.Column(db.Text)
    stream_key = db.Column(db.String(255))
    thumbnail = db.Column(db.String(255))
    is_saved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    host = db.relationship('User', backref='live_sessions')
    community = db.relationship('Community', backref='live_sessions')

    # Tags for sessions are kept in a dedicated association table so they
    # don't conflict with Content tags which use `content_tags`.
    live_session_tags = db.Table('live_session_tags',
        db.Column('live_session_id', db.Integer, db.ForeignKey('live_session.id'), primary_key=True),
        db.Column('tag_id', db.Integer, db.ForeignKey('tag.id'), primary_key=True)
    )

    tags = db.relationship('Tag', secondary=live_session_tags, lazy='subquery',
                          backref=db.backref('live_sessions', lazy='dynamic'))

    def save_as_content(self, uploader_id=None, make_public=True):
        """Create a `Content` record from this session recording.

        If `recording_path` is empty this returns None.
        """
        if not self.recording_path:
            return None
        uploader = uploader_id or self.host_id
        # ensure file_path stores only the filename within the uploads/live folder
        filename = self.recording_path.split('/')[-1].split('\\')[-1]
        content = Content(
            title=self.title,
            author=self.host.name if self.host else None,
                    description=f"Recorded live session: {self.title}",
            content_type='live',
            file_path=filename,
            file_size=self.recording_size,
            category_id=None,
            uploaded_by=uploader,
            is_public=make_public,
        )
        # copy tags
        content.tags = list(self.tags)
        db.session.add(content)
        self.is_saved = True
        db.session.add(self)
        db.session.commit()
        return content

