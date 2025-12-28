from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from models import db, Content, Category, User, ActivityLog
from sqlalchemy import desc

api_bp = Blueprint('api', __name__)

@api_bp.route('/content')
@login_required
def get_content():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    content_type = request.args.get('type', '')
    category_id = request.args.get('category', type=int)
    search = request.args.get('q', '').strip()
    
    query = Content.query.filter_by(is_public=True)
    
    if content_type:
        query = query.filter_by(content_type=content_type)
    
    if category_id:
        query = query.filter_by(category_id=category_id)
    
    if search:
        query = query.filter(
            (Content.title.ilike(f'%{search}%')) |
            (Content.author.ilike(f'%{search}%'))
        )
    
    contents = query.order_by(desc(Content.created_at)).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [{
            'id': c.id,
            'title': c.title,
            'author': c.author,
            'type': c.content_type,
            'category': c.category.name if c.category else None,
            'views': c.view_count,
            'downloads': c.download_count,
            'created_at': c.created_at.isoformat()
        } for c in contents.items],
        'pagination': {
            'page': contents.page,
            'pages': contents.pages,
            'total': contents.total,
            'has_next': contents.has_next,
            'has_prev': contents.has_prev
        }
    })

@api_bp.route('/content/<int:content_id>')
@login_required
def get_content_detail(content_id):
    content = Content.query.get_or_404(content_id)
    
    if not content.is_public and not current_user.can_upload():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    return jsonify({
        'success': True,
        'data': {
            'id': content.id,
            'title': content.title,
            'author': content.author,
            'description': content.description,
            'type': content.content_type,
            'category': content.category.name if content.category else None,
            'tags': [tag.name for tag in content.tags],
            'views': content.view_count,
            'downloads': content.download_count,
            'file_size': content.get_file_size_formatted(),
            'is_public': content.is_public,
            'created_at': content.created_at.isoformat(),
            'uploader': content.uploader.name
        }
    })

@api_bp.route('/categories')
@login_required
def get_categories():
    categories = Category.query.all()
    return jsonify({
        'success': True,
        'data': [{
            'id': c.id,
            'name': c.name,
            'description': c.description,
            'content_count': c.contents.count()
        } for c in categories]
    })

@api_bp.route('/search')
@login_required
def search():
    query = request.args.get('q', '').strip()
    
    if len(query) < 2:
        return jsonify({'success': True, 'data': []})
    
    search = f'%{query}%'
    contents = Content.query.filter(
        Content.is_public == True,
        (Content.title.ilike(search)) |
        (Content.author.ilike(search)) |
        (Content.description.ilike(search))
    ).limit(10).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': c.id,
            'title': c.title,
            'author': c.author,
            'type': c.content_type
        } for c in contents]
    })

@api_bp.route('/stats')
@login_required
def get_stats():
    if not current_user.is_admin():
        return jsonify({'success': False, 'error': 'Access denied'}), 403
    
    from sqlalchemy import func
    
    total_users = User.query.count()
    total_content = Content.query.count()
    total_views = db.session.query(func.sum(Content.view_count)).scalar() or 0
    total_downloads = db.session.query(func.sum(Content.download_count)).scalar() or 0
    
    return jsonify({
        'success': True,
        'data': {
            'users': total_users,
            'content': total_content,
            'views': total_views,
            'downloads': total_downloads
        }
    })

@api_bp.route('/user/history')
@login_required
def get_user_history():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    activities = ActivityLog.query.filter_by(user_id=current_user.id).order_by(
        desc(ActivityLog.timestamp)
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
        'success': True,
        'data': [{
            'id': a.id,
            'action': a.action,
            'details': a.details,
            'content_id': a.content_id,
            'timestamp': a.timestamp.isoformat()
        } for a in activities.items],
        'pagination': {
            'page': activities.page,
            'pages': activities.pages,
            'total': activities.total
        }
    })
