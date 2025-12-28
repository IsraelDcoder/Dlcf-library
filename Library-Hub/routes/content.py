import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from models import db, Content, Category, Tag, ActivityLog
from functools import wraps

content_bp = Blueprint('content', __name__)

ALLOWED_EXTENSIONS = {
    'pdf': ['pdf'],
    'ebook': ['epub', 'mobi', 'pdf'],
    'audio': ['mp3', 'wav', 'ogg', 'm4a'],
    'video': ['mp4', 'webm', 'avi', 'mkv', 'mov'],
    'live': ['mp3', 'wav', 'm4a', 'ogg']
}

def upload_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.can_upload():
            flash('You do not have permission to upload content.', 'error')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename, content_type):
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in ALLOWED_EXTENSIONS.get(content_type, [])

@content_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@upload_required
def upload():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        author = request.form.get('author', '').strip()
        description = request.form.get('description', '').strip()
        content_type = request.form.get('content_type', '')
        category_id = request.form.get('category_id', type=int)
        is_public = request.form.get('is_public') == 'on'
        tags_str = request.form.get('tags', '').strip()
        
        if not title or not content_type:
            flash('Title and content type are required.', 'error')
            return render_template('content/upload.html', categories=Category.query.all())
        
        if 'file' not in request.files:
            flash('No file selected.', 'error')
            return render_template('content/upload.html', categories=Category.query.all())
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected.', 'error')
            return render_template('content/upload.html', categories=Category.query.all())
        
        if not allowed_file(file.filename, content_type):
            flash(f'Invalid file type for {content_type}.', 'error')
            return render_template('content/upload.html', categories=Category.query.all())
        
        filename = secure_filename(file.filename)
        unique_filename = f"{current_user.id}_{int(os.urandom(4).hex(), 16)}_{filename}"
        
        type_folder = {
            'pdf': 'pdfs',
            'ebook': 'ebooks',
            'audio': 'audio',
            'video': 'videos',
            'live': 'live'
        }.get(content_type, 'pdfs')
        
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], type_folder, unique_filename)
        file.save(filepath)
        
        file_size = os.path.getsize(filepath)
        
        content = Content(
            title=title,
            author=author,
            description=description,
            content_type=content_type,
            file_path=unique_filename,
            file_size=file_size,
            category_id=category_id if category_id else None,
            uploaded_by=current_user.id,
            is_public=is_public
        )
        
        if tags_str:
            tag_names = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                content.tags.append(tag)
        
        db.session.add(content)
        db.session.flush()
        
        log = ActivityLog(
            user_id=current_user.id,
            content_id=content.id,
            action='upload',
            details=f'Uploaded: {title}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Content uploaded successfully!', 'success')
        return redirect(url_for('content.view', content_id=content.id))
    
    categories = Category.query.all()
    return render_template('content/upload.html', categories=categories)

@content_bp.route('/view/<int:content_id>')
@login_required
def view(content_id):
    content = Content.query.get_or_404(content_id)
    
    if not content.is_public and not current_user.can_upload():
        flash('You do not have permission to view this content.', 'error')
        return redirect(url_for('main.browse'))
    
    content.view_count += 1
    
    log = ActivityLog(
        user_id=current_user.id,
        content_id=content.id,
        action='view',
        details=f'Viewed: {content.title}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    related = Content.query.filter(
        Content.id != content.id,
        Content.is_public == True,
        Content.category_id == content.category_id
    ).limit(4).all() if content.category_id else []
    
    return render_template('content/view.html', content=content, related=related)

@content_bp.route('/download/<int:content_id>')
@login_required
def download(content_id):
    content = Content.query.get_or_404(content_id)
    
    if not current_user.can_download(content):
        flash('You do not have permission to download this content.', 'error')
        return redirect(url_for('content.view', content_id=content_id))
    
    type_folder = {
        'pdf': 'pdfs',
        'ebook': 'ebooks',
        'audio': 'audio',
        'video': 'videos',
        'live': 'live'
    }.get(content.content_type, 'pdfs')
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], type_folder, content.file_path)
    
    if not os.path.exists(filepath):
        flash('File not found.', 'error')
        return redirect(url_for('content.view', content_id=content_id))
    
    content.download_count += 1
    
    log = ActivityLog(
        user_id=current_user.id,
        content_id=content.id,
        action='download',
        details=f'Downloaded: {content.title}',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    return send_file(filepath, as_attachment=True, download_name=content.file_path.split('_', 2)[-1])

@content_bp.route('/edit/<int:content_id>', methods=['GET', 'POST'])
@login_required
@upload_required
def edit(content_id):
    content = Content.query.get_or_404(content_id)
    
    if content.uploaded_by != current_user.id and not current_user.is_admin():
        flash('You do not have permission to edit this content.', 'error')
        return redirect(url_for('content.view', content_id=content_id))
    
    if request.method == 'POST':
        content.title = request.form.get('title', '').strip()
        content.author = request.form.get('author', '').strip()
        content.description = request.form.get('description', '').strip()
        content.category_id = request.form.get('category_id', type=int) or None
        content.is_public = request.form.get('is_public') == 'on'
        
        content.tags.clear()
        tags_str = request.form.get('tags', '').strip()
        if tags_str:
            tag_names = [t.strip().lower() for t in tags_str.split(',') if t.strip()]
            for tag_name in tag_names:
                tag = Tag.query.filter_by(name=tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    db.session.add(tag)
                content.tags.append(tag)
        
        db.session.commit()
        flash('Content updated successfully!', 'success')
        return redirect(url_for('content.view', content_id=content_id))
    
    categories = Category.query.all()
    current_tags = ', '.join([tag.name for tag in content.tags])
    return render_template('content/edit.html', content=content, categories=categories, current_tags=current_tags)

@content_bp.route('/delete/<int:content_id>', methods=['POST'])
@login_required
@upload_required
def delete(content_id):
    content = Content.query.get_or_404(content_id)
    
    if content.uploaded_by != current_user.id and not current_user.is_admin():
        flash('You do not have permission to delete this content.', 'error')
        return redirect(url_for('content.view', content_id=content_id))
    
    type_folder = {
        'pdf': 'pdfs',
        'ebook': 'ebooks',
        'audio': 'audio',
        'video': 'videos',
        'live': 'live'
    }.get(content.content_type, 'pdfs')
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], type_folder, content.file_path)
    if os.path.exists(filepath):
        os.remove(filepath)
    
    ActivityLog.query.filter_by(content_id=content.id).delete()
    
    db.session.delete(content)
    db.session.commit()
    
    flash('Content deleted successfully!', 'success')
    return redirect(url_for('main.browse'))

@content_bp.route('/file/<int:content_id>')
@login_required
def serve_file(content_id):
    content = Content.query.get_or_404(content_id)
    
    if not content.is_public and not current_user.can_upload():
        abort(403)
    
    type_folder = {
        'pdf': 'pdfs',
        'ebook': 'ebooks',
        'audio': 'audio',
        'video': 'videos',
        'live': 'live'
    }.get(content.content_type, 'pdfs')
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], type_folder, content.file_path)
    
    if not os.path.exists(filepath):
        abort(404)
    
    return send_file(filepath)
