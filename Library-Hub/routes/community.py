from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from models import db, Community, Membership, Post, Comment, ChatMessage, User, ActivityLog
from functools import wraps
from datetime import datetime, timedelta
import time
from flask_socketio import join_room, leave_room, emit


def _emit_room(event, data, room=None):
    """Emit a socket.io event via the app's SocketIO instance (if configured)."""
    s = current_app.extensions.get('socketio')
    if s:
        try:
            s.emit(event, data, room=room)
        except Exception:
            pass

community_bp = Blueprint('community', __name__)

# In-memory mute map: { community_id: { user_id: until_timestamp } }
_muted_users = {}


def _is_user_muted(community_id, user_id):
    """Check whether a user is muted in a community. Returns (muted: bool, until: datetime|None)."""
    r = getattr(current_app, 'redis', None)
    if r:
        key = f"mute:{community_id}:{user_id}"
        try:
            ttl = r.ttl(key)
            if ttl and ttl > 0:
                return True, datetime.utcnow() + timedelta(seconds=ttl)
            return False, None
        except Exception:
            # fall back to in-memory
            pass
    mutes = _muted_users.get(community_id, {})
    mute_until = mutes.get(user_id)
    if mute_until and mute_until > datetime.utcnow():
        return True, mute_until
    return False, None


def _set_user_mute(community_id, user_id, seconds):
    """Mute or unmute a user for a number of seconds. If seconds<=0 unmute."""
    r = getattr(current_app, 'redis', None)
    key = f"mute:{community_id}:{user_id}"
    if r:
        try:
            if seconds > 0:
                r.set(key, '1', ex=int(seconds))
            else:
                r.delete(key)
            return
        except Exception:
            # fall back
            pass
    # fallback to in-memory
    if seconds > 0:
        _muted_users.setdefault(community_id, {})[user_id] = datetime.utcnow() + timedelta(seconds=seconds)
    else:
        m = _muted_users.get(community_id, {})
        if user_id in m:
            del m[user_id]


def get_membership(user, community_id):
    return Membership.query.filter_by(user_id=user.id, community_id=community_id).first()


def community_member_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        community_id = kwargs.get('community_id') or request.view_args.get('community_id')
        if not community_id:
            flash('Community not specified.', 'error')
            return redirect(url_for('main.dashboard'))
        membership = get_membership(current_user, community_id)
        if not membership:
            flash('You are not a member of this community.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated


def role_required(min_role):
    """min_role is one of: 'student' < 'teacher' < 'admin'"""
    order = {'student': 0, 'teacher': 1, 'admin': 2}

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            community_id = kwargs.get('community_id') or request.view_args.get('community_id')
            membership = get_membership(current_user, community_id)
            if not membership or order.get(membership.role, 0) < order.get(min_role, 0):
                flash('Permission denied.', 'error')
                return redirect(url_for('community.feed', community_id=community_id))
            return f(*args, **kwargs)
        return decorated
    return decorator


@community_bp.route('/')
@login_required
def index():
    # Admins get an admin community management index; members are redirected to their community feed.
    if current_user.is_admin():
        communities = Community.query.order_by(Community.created_at.desc()).all()
        return render_template('community/admin_index.html', communities=communities)

    membership = Membership.query.filter_by(user_id=current_user.id).first()
    if not membership:
        flash('You are not currently part of any community.', 'info')
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('community.feed', community_id=membership.community_id))


@community_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_community():

    # Only site admins can create new communities
    if not current_user.is_admin():
        flash('Permission denied.', 'error')
        return redirect(url_for('community.index'))

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        # visibility: private (default) or invite
        visibility = request.form.get('visibility', 'private')
        is_private = True if visibility in ('private', 'invite') else False
        photo = None
        photo_thumb = None
        photo_thumb2 = None
        if not name:
            flash('Community name is required.', 'error')
            return render_template('community/new.html')

        slug = name.lower().replace(' ', '-')
        # ensure unique
        existing = Community.query.filter_by(slug=slug).first()
        if existing:
            slug = f"{slug}-{int(time.time())}"

        # handle photo upload with validation and thumbnail generation
        if 'photo' in request.files:
            f = request.files['photo']
            if f and f.filename:
                from werkzeug.utils import secure_filename
                filename = secure_filename(f"{int(time.time())}_{f.filename}")
                import os
                dest_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'communities')
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                path = os.path.join(dest_dir, filename)

                # read file into memory to check size and type safely
                data = f.read()
                if len(data) > current_app.config.get('MAX_COMMUNITY_PHOTO_SIZE', 2 * 1024 * 1024):
                    flash('Photo is too large (max 2 MB).', 'error')
                    return render_template('community/new.html')

                # Basic mime/extension check
                allowed_ext = ('png', 'jpg', 'jpeg', 'gif')
                if not filename.lower().endswith(allowed_ext):
                    flash('Unsupported image format. Allowed: png, jpg, jpeg, gif', 'error')
                    return render_template('community/new.html')

                # write to disk
                with open(path, 'wb') as out:
                    out.write(data)
                photo = filename

                # try to generate thumbnails (1x and 2x) and optimize if Pillow available
                try:
                    from PIL import Image
                    base_thumb_name = f"thumb_{filename}"
                    thumb_path = os.path.join(dest_dir, base_thumb_name)
                    img = Image.open(path)
                    # generate 1x
                    img1 = img.copy()
                    img1.thumbnail(current_app.config.get('COMMUNITY_PHOTO_THUMB_SIZE', (300, 300)))
                    img1.save(thumb_path, optimize=True, quality=85)
                    # generate 2x
                    img2 = img.copy()
                    w, h = current_app.config.get('COMMUNITY_PHOTO_THUMB_SIZE', (300, 300))
                    img2.thumbnail((w*2, h*2))
                    base_thumb_name_2x = f"thumb2x_{filename}"
                    thumb2x_path = os.path.join(dest_dir, base_thumb_name_2x)
                    img2.save(thumb2x_path, optimize=True, quality=80)
                    photo_thumb = base_thumb_name
                    photo_thumb2 = base_thumb_name_2x
                except Exception:
                    # thumbnail generation failed; proceed without it
                    photo_thumb = None
                    photo_thumb2 = None

        community = Community(name=name, slug=slug, description=description, photo=photo, photo_thumbnail=photo_thumb, photo_thumbnail_2x=photo_thumb2, is_private=is_private)
        db.session.add(community)
        db.session.commit()

        # Ensure the creator is a member with admin privileges so they can access the feed
        try:
            existing = Membership.query.filter_by(user_id=current_user.id, community_id=community.id).first()
            if not existing:
                member = Membership(user_id=current_user.id, community_id=community.id, role='admin')
                db.session.add(member)
                db.session.commit()
        except Exception:
            # If membership cannot be created for any reason, continue and rely on admin to add themselves
            pass

        flash('Community created. Opening community feed...', 'success')
        # Admins should be taken directly to the community feed after creating it
        return redirect(url_for('community.feed', community_id=community.id))

    return render_template('community/new.html')

@community_bp.route('/<int:community_id>/delete', methods=['POST'])
@login_required
def delete_community(community_id):
    # Only site admins may delete communities
    if not current_user.is_admin():
        flash('Permission denied.', 'error')
        return redirect(url_for('community.index'))

    community = Community.query.get_or_404(community_id)

    # Collect post ids for comment cleanup
    post_ids = [p.id for p in Post.query.filter_by(community_id=community.id).all()]

    try:
        # Remove comments for posts in this community
        if post_ids:
            Comment.query.filter(Comment.post_id.in_(post_ids)).delete(synchronize_session=False)
        # Remove posts, chat messages, memberships
        Post.query.filter_by(community_id=community.id).delete(synchronize_session=False)
        ChatMessage.query.filter_by(community_id=community.id).delete(synchronize_session=False)
        Membership.query.filter_by(community_id=community.id).delete(synchronize_session=False)

        # Remove uploaded files if present
        import os
        upload_base = current_app.config.get('UPLOAD_FOLDER')
        comm_dir = os.path.join(upload_base, 'communities') if upload_base else None
        for fn in (community.photo, community.photo_thumbnail, community.photo_thumbnail_2x):
            if fn and comm_dir:
                try:
                    fp = os.path.join(comm_dir, fn)
                    if os.path.exists(fp):
                        os.remove(fp)
                except Exception:
                    # ignore file removal errors
                    pass

        # Finally remove the community record
        db.session.delete(community)
        db.session.commit()
        flash('Community deleted successfully.', 'success')
    except Exception:
        db.session.rollback()
        flash('Failed to delete community. Please check the server logs.', 'error')

    return redirect(url_for('community.index'))

@community_bp.route('/<int:community_id>')
@login_required
@community_member_required
def feed(community_id):
    community = Community.query.get_or_404(community_id)
    # Recent posts, pinned first
    posts = Post.query.filter_by(community_id=community.id, is_deleted=False).order_by(Post.is_pinned.desc(), Post.created_at.desc()).limit(50).all()
    # preload comments and prepare simple member list (do not show private info)
    for p in posts:
        p.comments_list = p.comments.order_by(Comment.created_at.asc()).all()
    members_q = Membership.query.filter_by(community_id=community.id).all()
    members = []
    for m in members_q:
        muted, until = _is_user_muted(community.id, m.user_id)
        members.append({'user_id': m.user_id, 'name': m.user.name, 'role': m.role, 'muted_until': until.isoformat() if until else None})
    current_membership = get_membership(current_user, community.id)
    current_role = current_membership.role if current_membership else 'student'
    return render_template('community/feed.html', community=community, posts=posts, members=members, current_role=current_role)


@community_bp.route('/<int:community_id>/post', methods=['POST'])
@login_required
@community_member_required
def create_post(community_id):
    title = request.form.get('title', '').strip()
    body = request.form.get('body', '').strip()
    if not body:
        flash('Post body is required.', 'error')
        return redirect(url_for('community.feed', community_id=community_id))
    post = Post(community_id=community_id, author_id=current_user.id, title=title, body=body)
    db.session.add(post)
    db.session.commit()
    flash('Post created.', 'success')
    # notify via socket
    _emit_room('post_created', {'post_id': post.id, 'title': post.title, 'body': post.body}, room=f'community_{community_id}')
    return redirect(url_for('community.feed', community_id=community_id))


@community_bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def add_comment(post_id):
    post = Post.query.get_or_404(post_id)
    membership = get_membership(current_user, post.community_id)
    if not membership:
        flash('You are not a member of this community.', 'error')
        return redirect(url_for('main.dashboard'))
    body = request.form.get('body', '').strip()
    if not body:
        flash('Comment body is required.', 'error')
        return redirect(url_for('community.feed', community_id=post.community_id))
    c = Comment(post_id=post.id, author_id=current_user.id, body=body)
    db.session.add(c)
    db.session.commit()
    _emit_room('comment_added', {'post_id': post.id, 'comment_id': c.id, 'body': c.body, 'author': current_user.name}, room=f'community_{post.community_id}')
    flash('Comment added.', 'success')
    return redirect(url_for('community.feed', community_id=post.community_id))


@community_bp.route('/post/<int:post_id>/pin', methods=['POST'])
@login_required
@role_required('teacher')
def pin_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_pinned = not post.is_pinned
    db.session.commit()
    _emit_room('post_pinned', {'post_id': post.id, 'is_pinned': post.is_pinned}, room=f'community_{post.community_id}')
    flash('Post updated.', 'success')
    return redirect(url_for('community.feed', community_id=post.community_id))


@community_bp.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
@role_required('teacher')
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    post.is_deleted = True
    db.session.commit()
    _emit_room('post_deleted', {'post_id': post.id}, room=f'community_{post.community_id}')
    flash('Post removed.', 'success')
    return redirect(url_for('community.feed', community_id=post.community_id))


@community_bp.route('/<int:community_id>/chat')
@login_required
@community_member_required
def chat(community_id):
    community = Community.query.get_or_404(community_id)
    recent = ChatMessage.query.filter_by(community_id=community.id).order_by(ChatMessage.created_at.desc()).limit(100).all()[::-1]
    return render_template('community/chat.html', community=community, messages=recent)


@community_bp.route('/<int:community_id>/member/<int:user_id>')
@login_required
@community_member_required
def member_profile(community_id, user_id):
    # show a member's profile limited to community members
    user = User.query.get_or_404(user_id)
    membership = Membership.query.filter_by(user_id=user.id, community_id=community_id).first()
    if not membership:
        flash('Member not found in this community.', 'error')
        return redirect(url_for('community.feed', community_id=community_id))
    posts = Post.query.filter_by(author_id=user.id, community_id=community_id).order_by(Post.created_at.desc()).limit(20).all()
    comments = Comment.query.filter_by(author_id=user.id).order_by(Comment.created_at.desc()).limit(20).all()
    return render_template('community/member.html', member=user, membership=membership, posts=posts, comments=comments, community_id=community_id)


# --- Socket events (registered at runtime via init_socketio) ---

def _handle_join(data):
    community_id = data.get('community_id')
    if not community_id:
        return
    membership = get_membership(current_user, community_id)
    if not membership:
        emit('error', {'message': 'Not a member of this community'})
        return
    room = f'community_{community_id}'
    join_room(room)
    emit('user_joined', {'user': current_user.name}, room=room)


def _handle_leave(data):
    community_id = data.get('community_id')
    room = f'community_{community_id}'
    leave_room(room)
    emit('user_left', {'user': current_user.name}, room=room)


def _handle_message(data):
    community_id = data.get('community_id')
    text = (data.get('message') or '').strip()
    if not community_id or not text:
        return
    membership = get_membership(current_user, community_id)
    if not membership:
        emit('error', {'message': 'Not a member'}, room=request.sid)
        return
    # check muted
    muted, until = _is_user_muted(community_id, current_user.id)
    if muted:
        emit('muted', {'until': until.isoformat() if until else None}, room=request.sid)
        return
    # persist
    msg = ChatMessage(community_id=community_id, author_id=current_user.id, message=text)
    db.session.add(msg)
    db.session.commit()
    room = f'community_{community_id}'
    emit('message', {'id': msg.id, 'author': current_user.name, 'message': text, 'created_at': msg.created_at.isoformat()}, room=room)


def _handle_mute(data):
    # data: {community_id, target_user_id, seconds}
    community_id = data.get('community_id')
    target = data.get('target_user_id')
    seconds = int(data.get('seconds') or 0)
    membership = get_membership(current_user, community_id)
    if not membership or membership.role not in ['teacher', 'admin']:
        emit('error', {'message': 'Permission denied'})
        return
    until = datetime.utcnow() + timedelta(seconds=seconds) if seconds > 0 else None
    # use Redis if available
    _set_user_mute(community_id, target, seconds)
    if seconds > 0:
        emit('user_muted', {'target': target, 'until': until.isoformat() if until else None}, room=f'community_{community_id}')
    else:
        emit('user_unmuted', {'target': target}, room=f'community_{community_id}')


def init_socketio(sio):
    """Register Socket.IO handlers on the provided SocketIO server instance."""
    sio.on_event('join', _handle_join)
    sio.on_event('leave', _handle_leave)
    sio.on_event('message', _handle_message)
    sio.on_event('mute', _handle_mute)


@community_bp.route('/<int:community_id>/member/<int:user_id>/set_role', methods=['POST'])
@login_required
@role_required('admin')
def set_role(community_id, user_id):
    role = request.form.get('role')
    if role not in ['student', 'teacher', 'admin']:
        flash('Invalid role', 'error')
        return redirect(url_for('community.member_profile', community_id=community_id, user_id=user_id))
    membership = Membership.query.filter_by(user_id=user_id, community_id=community_id).first()
    if not membership:
        flash('Member not found', 'error')
        return redirect(url_for('community.feed', community_id=community_id))
    membership.role = role
    db.session.commit()
    flash('Role updated.', 'success')
    return redirect(url_for('community.member_profile', community_id=community_id, user_id=user_id))


@community_bp.route('/<int:community_id>/member/<int:user_id>/mute', methods=['POST'])
@login_required
@role_required('teacher')
def mute_member(community_id, user_id):
    """Mute or unmute a member. Teachers and admins can perform this action."""
    seconds = int(request.form.get('seconds') or 0)
    membership = Membership.query.filter_by(user_id=current_user.id, community_id=community_id).first()
    if not membership or membership.role not in ['teacher', 'admin']:
        flash('Permission denied.', 'error')
        return redirect(url_for('community.member_profile', community_id=community_id, user_id=user_id))

    target_membership = Membership.query.filter_by(user_id=user_id, community_id=community_id).first()
    if not target_membership:
        flash('Member not found in this community.', 'error')
        return redirect(url_for('community.feed', community_id=community_id))

    _set_user_mute(community_id, user_id, seconds)

    if seconds > 0:
        until = (datetime.utcnow() + timedelta(seconds=seconds)).isoformat()
        _emit_room('user_muted', {'target': user_id, 'until': until}, room=f'community_{community_id}')
        details = f'Muted user {user_id} for {seconds} seconds in community {community_id}'
        flash('Member muted.', 'success')
    else:
        _emit_room('user_unmuted', {'target': user_id}, room=f'community_{community_id}')
        details = f'Unmuted user {user_id} in community {community_id}'
        flash('Member unmuted.', 'success')

    # activity log
    log = ActivityLog(user_id=current_user.id, action='mute' if seconds > 0 else 'unmute', details=details)
    db.session.add(log)
    db.session.commit()

    return redirect(url_for('community.member_profile', community_id=community_id, user_id=user_id))


@community_bp.route('/<int:community_id>/members/manage', methods=['GET', 'POST'])
@login_required
def manage_members(community_id):
    # Only site admins can mass-assign members
    if not current_user.is_admin():
        flash('Permission denied.', 'error')
        return redirect(url_for('community.feed', community_id=community_id))

    community = Community.query.get_or_404(community_id)
    users = User.query.order_by(User.name.asc()).all()
    if request.method == 'POST':
        selected = set([int(x) for x in request.form.getlist('user_ids')])
        # current members
        existing = {m.user_id: m for m in Membership.query.filter_by(community_id=community_id).all()}

        # add or update memberships with selected roles
        for u in users:
            desired_role = request.form.get(f'role_{u.id}', 'student')
            if u.id in selected:
                if u.id in existing:
                    # update role if changed
                    mem = existing[u.id]
                    # prevent non-site-admins from assigning 'admin'
                    if desired_role == 'admin' and not current_user.is_admin():
                        flash(f'Only site admins can assign admin role (skipped {u.name}).', 'error')
                        continue
                    if mem.role != desired_role:
                        mem.role = desired_role
                else:
                    if desired_role == 'admin' and not current_user.is_admin():
                        flash(f'Only site admins can assign admin role (skipped {u.name}).', 'error')
                        continue
                    m = Membership(user_id=u.id, community_id=community_id, role=desired_role)
                    db.session.add(m)
            else:
                if u.id in existing:
                    db.session.delete(existing[u.id])

        db.session.commit()
        flash('Memberships updated.', 'success')
        return redirect(url_for('community.feed', community_id=community_id))

    # prepare selected flags and roles
    member_q = Membership.query.filter_by(community_id=community_id).all()
    member_ids = {m.user_id for m in member_q}
    member_roles = {m.user_id: m.role for m in member_q}
    return render_template('community/manage_members.html', community=community, users=users, member_ids=member_ids, member_roles=member_roles)


@community_bp.route('/<int:community_id>/member/<int:user_id>/remove', methods=['POST'])
@login_required
@role_required('admin')
def remove_member(community_id, user_id):
    membership = Membership.query.filter_by(user_id=user_id, community_id=community_id).first()
    if not membership:
        flash('Member not found', 'error')
        return redirect(url_for('community.feed', community_id=community_id))
    db.session.delete(membership)
    db.session.commit()
    flash('Member removed from community.', 'success')
    _emit_room('member_removed', {'user_id': user_id}, room=f'community_{community_id}')
    return redirect(url_for('community.feed', community_id=community_id))