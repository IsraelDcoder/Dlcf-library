from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Content, Category, ActivityLog, Notification, LiveSession
from functools import wraps
from sqlalchemy import desc, func
from datetime import datetime, timedelta

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_content = Content.query.count()
    total_downloads = db.session.query(func.sum(Content.download_count)).scalar() or 0
    total_views = db.session.query(func.sum(Content.view_count)).scalar() or 0
    
    users_by_role = db.session.query(User.role, func.count(User.id)).group_by(User.role).all()
    content_by_type = db.session.query(Content.content_type, func.count(Content.id)).group_by(Content.content_type).all()
    
    recent_activities = ActivityLog.query.order_by(desc(ActivityLog.timestamp)).limit(20).all()
    recent_users = User.query.order_by(desc(User.created_at)).limit(10).all()
    
    top_content = Content.query.order_by(desc(Content.view_count)).limit(10).all()
    top_downloaders = db.session.query(
        User, func.count(ActivityLog.id).label('download_count')
    ).join(ActivityLog).filter(
        ActivityLog.action == 'download'
    ).group_by(User.id).order_by(desc('download_count')).limit(10).all()
    
    week_ago = datetime.utcnow() - timedelta(days=7)
    weekly_activity = ActivityLog.query.filter(ActivityLog.timestamp >= week_ago).count()
    
    stats = {
        'total_users': total_users,
        'total_content': total_content,
        'total_downloads': total_downloads,
        'total_views': total_views,
        'users_by_role': dict(users_by_role),
        'content_by_type': dict(content_by_type),
        'weekly_activity': weekly_activity
    }
    
    return render_template('admin/dashboard.html', 
                         stats=stats,
                         recent_activities=recent_activities,
                         recent_users=recent_users,
                         top_content=top_content,
                         top_downloaders=top_downloaders)

@admin_bp.route('/users')
@login_required
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    if role_filter:
        query = query.filter_by(role=role_filter)
    
    if search:
        query = query.filter(
            (User.name.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%'))
        )
    
    users = query.order_by(desc(User.created_at)).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/users.html', users=users, role_filter=role_filter, search=search)

@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        user.name = request.form.get('name', '').strip()
        user.role = request.form.get('role', 'student')
        user.is_active = request.form.get('is_active') == 'on'
        
        new_password = request.form.get('new_password', '').strip()
        if new_password:
            user.set_password(new_password)
        
        db.session.commit()
        flash('User updated successfully!', 'success')
        return redirect(url_for('admin.users'))
    
    activities = ActivityLog.query.filter_by(user_id=user.id).order_by(desc(ActivityLog.timestamp)).limit(20).all()
    return render_template('admin/edit_user.html', user=user, activities=activities)

@admin_bp.route('/content')
@login_required
@admin_required
def content():
    page = request.args.get('page', 1, type=int)
    type_filter = request.args.get('type', '')
    search = request.args.get('search', '').strip()
    
    query = Content.query
    
    if type_filter:
        query = query.filter_by(content_type=type_filter)
    
    if search:
        query = query.filter(
            (Content.title.ilike(f'%{search}%')) |
            (Content.author.ilike(f'%{search}%'))
        )
    
    contents = query.order_by(desc(Content.created_at)).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('admin/content.html', contents=contents, type_filter=type_filter, search=search)


@admin_bp.route('/live')
@login_required
@admin_required
def live():
    # Show recent sessions and their saved content (if any)
    sessions = LiveSession.query.order_by(LiveSession.started_at.desc()).all()
    sessions_data = []
    for s in sessions:
        content = None
        if s.is_saved and s.recording_path:
            content = Content.query.filter_by(file_path=s.recording_path, content_type='live').first()
        sessions_data.append({'session': s, 'content': content})
    return render_template('admin/live.html', sessions=sessions_data)


@admin_bp.route('/live/new', methods=['GET', 'POST'])
@login_required
@admin_required
def live_new():
    from flask import current_app
    from werkzeug.utils import secure_filename
    import os
    import secrets

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        is_public = request.form.get('is_public') == 'on'
        # handle thumbnail upload
        thumbnail_file = request.files.get('thumbnail')
        thumbnail_name = None
        if thumbnail_file and thumbnail_file.filename:
            filename = secure_filename(thumbnail_file.filename)
            thumbs_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'live', 'thumbs')
            os.makedirs(thumbs_dir, exist_ok=True)
            thumbnail_name = f"{int(os.urandom(4).hex(), 16)}_{filename}"
            thumbnail_file.save(os.path.join(thumbs_dir, thumbnail_name))
        # generate a stream key for the session
        stream_key = secrets.token_urlsafe(16)
        session = LiveSession(title=title or 'Live Session', host_id=current_user.id, description=description, stream_key=stream_key, thumbnail=thumbnail_name, is_live=True)
        db.session.add(session)
        db.session.commit()
        flash('Live session created. You are now live.', 'success')
        return redirect(url_for('admin.live'))

    # GET: render form, accept optional title in querystring
    pre_title = request.args.get('title', '')
    return render_template('admin/live_setup.html', pre_title=pre_title)


@admin_bp.route('/content/<int:content_id>/toggle_publish', methods=['POST'])
@login_required
@admin_required
def toggle_publish(content_id):
    content = Content.query.get_or_404(content_id)
    content.is_public = not content.is_public
    db.session.commit()
    flash('Content visibility updated.', 'success')
    return redirect(url_for('admin.content'))


@admin_bp.route('/uploads')
@login_required
@admin_required
def uploads():
    """Alias for admin content management - legacy route compatibility."""
    return redirect(url_for('admin.content'))

@admin_bp.route('/categories', methods=['GET', 'POST'])
@login_required
@admin_required
def categories():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'add':
            name = request.form.get('name', '').strip()
            description = request.form.get('description', '').strip()
            
            if name:
                existing = Category.query.filter_by(name=name).first()
                if existing:
                    flash('Category already exists.', 'error')
                else:
                    category = Category(name=name, description=description)
                    db.session.add(category)
                    db.session.commit()
                    flash('Category added successfully!', 'success')
        
        elif action == 'delete':
            category_id = request.form.get('category_id', type=int)
            category = Category.query.get(category_id)
            if category:
                Content.query.filter_by(category_id=category.id).update({'category_id': None})
                db.session.delete(category)
                db.session.commit()
                flash('Category deleted successfully!', 'success')
    
    categories = Category.query.all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/notifications', methods=['GET', 'POST'])
@login_required
@admin_required
def notifications():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        message = request.form.get('message', '').strip()
        is_global = request.form.get('is_global') == 'on'
        recipient_id = request.form.get('recipient_id', type=int)
        
        if title and message:
            notification = Notification(
                title=title,
                message=message,
                is_global=is_global,
                recipient_id=recipient_id if not is_global else None,
                sent_at=datetime.utcnow()
            )
            db.session.add(notification)
            db.session.commit()
            flash('Notification sent successfully!', 'success')
    
    notifications = Notification.query.order_by(desc(Notification.created_at)).limit(50).all()
    users = User.query.filter_by(is_active=True).all()
    return render_template('admin/notifications.html', notifications=notifications, users=users)

@admin_bp.route('/activity')
@login_required
@admin_required
def activity():
    page = request.args.get('page', 1, type=int)
    action_filter = request.args.get('action', '')
    
    query = ActivityLog.query
    
    if action_filter:
        query = query.filter_by(action=action_filter)
    
    activities = query.order_by(desc(ActivityLog.timestamp)).paginate(page=page, per_page=50, error_out=False)
    
    actions = db.session.query(ActivityLog.action).distinct().all()
    action_types = [a[0] for a in actions]
    
    return render_template('admin/activity.html', activities=activities, action_filter=action_filter, action_types=action_types)

@admin_bp.route('/analytics')
@login_required
@admin_required
def analytics():
    days_30 = datetime.utcnow() - timedelta(days=30)
    
    daily_views = db.session.query(
        func.date(ActivityLog.timestamp),
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.action == 'view',
        ActivityLog.timestamp >= days_30
    ).group_by(func.date(ActivityLog.timestamp)).all()
    
    daily_downloads = db.session.query(
        func.date(ActivityLog.timestamp),
        func.count(ActivityLog.id)
    ).filter(
        ActivityLog.action == 'download',
        ActivityLog.timestamp >= days_30
    ).group_by(func.date(ActivityLog.timestamp)).all()
    
    top_content = Content.query.order_by(desc(Content.view_count)).limit(10).all()
    top_downloaded = Content.query.order_by(desc(Content.download_count)).limit(10).all()
    
    active_users = db.session.query(
        User, func.count(ActivityLog.id).label('activity_count')
    ).join(ActivityLog).filter(
        ActivityLog.timestamp >= days_30
    ).group_by(User.id).order_by(desc('activity_count')).limit(10).all()
    
    content_by_category = db.session.query(
        Category.name, func.count(Content.id)
    ).outerjoin(Content).group_by(Category.id).all()
    
    return render_template('admin/analytics.html',
                         daily_views=daily_views,
                         daily_downloads=daily_downloads,
                         top_content=top_content,
                         top_downloaded=top_downloaded,
                         active_users=active_users,
                         content_by_category=content_by_category)
