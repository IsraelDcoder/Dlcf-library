from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from models import db, Content, Category, Notification, ActivityLog
from sqlalchemy import desc
import os
import time
import json
import urllib.request
import urllib.error

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return render_template('dashboard.html')
    return render_template('index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    recent_content = Content.query.filter_by(is_public=True).order_by(desc(Content.created_at)).limit(8).all()
    popular_content = Content.query.filter_by(is_public=True).order_by(desc(Content.view_count)).limit(8).all()
    categories = Category.query.all()
    
    notifications = Notification.query.filter(
        (Notification.recipient_id == current_user.id) | (Notification.is_global == True)
    ).filter_by(is_read=False).order_by(desc(Notification.created_at)).limit(5).all()
    
    stats = {
        'total_content': Content.query.count(),
        'total_pdfs': Content.query.filter_by(content_type='pdf').count(),
        'total_videos': Content.query.filter_by(content_type='video').count(),
        'total_audio': Content.query.filter_by(content_type='audio').count(),
    }
    
    return render_template('dashboard.html', 
                         recent_content=recent_content,
                         popular_content=popular_content,
                         categories=categories,
                         notifications=notifications,
                         stats=stats)

@main_bp.route('/browse')
@login_required
def browse():
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    content_type = request.args.get('type', '')
    category_id = request.args.get('category', '', type=str)
    sort_by = request.args.get('sort', 'recent')
    search_query = request.args.get('q', '').strip()
    
    query = Content.query.filter_by(is_public=True)
    
    if content_type:
        query = query.filter_by(content_type=content_type)
    
    if category_id and category_id.isdigit():
        query = query.filter_by(category_id=int(category_id))
    
    if search_query:
        search = f"%{search_query}%"
        query = query.filter(
            (Content.title.ilike(search)) |
            (Content.author.ilike(search)) |
            (Content.description.ilike(search))
        )
    
    if sort_by == 'popular':
        query = query.order_by(desc(Content.view_count))
    elif sort_by == 'downloads':
        query = query.order_by(desc(Content.download_count))
    else:
        query = query.order_by(desc(Content.created_at))
    
    contents = query.paginate(page=page, per_page=per_page, error_out=False)
    categories = Category.query.all()
    
    return render_template('browse.html', 
                         contents=contents,
                         categories=categories,
                         current_type=content_type,
                         current_category=category_id,
                         current_sort=sort_by,
                         search_query=search_query)

@main_bp.route('/notifications')
@login_required
def notifications():
    notifications = Notification.query.filter(
        (Notification.recipient_id == current_user.id) | (Notification.is_global == True)
    ).order_by(desc(Notification.created_at)).all()
    
    for notif in notifications:
        if notif.recipient_id == current_user.id:
            notif.is_read = True
    db.session.commit()
    
    return render_template('notifications.html', notifications=notifications)

@main_bp.route('/history')
@login_required
def history():
    page = request.args.get('page', 1, type=int)
    activities = ActivityLog.query.filter_by(user_id=current_user.id).order_by(
        desc(ActivityLog.timestamp)
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('history.html', activities=activities)


@main_bp.route('/categories')
@login_required
def categories():
    """Public-facing categories list. Users can click a category to browse items in it."""
    categories = Category.query.all()
    return render_template('categories.html', categories=categories)


@main_bp.route('/settings')
@login_required
def settings():
    """Redirect main/settings to the user profile settings for now."""
    from flask import redirect, url_for
    return redirect(url_for('auth.profile'))


@main_bp.route('/chat')
@login_required
def chat():
    """Simple chat UI placeholder for the site's AI assistant."""
    return render_template('chat.html')


# Simple in-memory rate limiter for chat (per-user sliding window)
# NOTE: This is suitable for single-process deployments; for multi-process/production use Redis or an external store.
_chat_rate_limits = {}

from flask import current_app

def _check_chat_rate_limit(user_id):
    """Return (allowed: bool, retry_after_seconds: int).

    Uses Redis-backed fixed-window counter when available (default window = 1 hour).
    Limits are defined by CHAT_RATE_LIMIT_PER_HOUR env var (default 20 requests/hour).
    """
    limit = int(os.environ.get('CHAT_RATE_LIMIT_PER_HOUR', '20'))
    window = 60 * 60

    # Prefer Redis when available for multi-process safety
    r = getattr(current_app, 'redis', None)
    if r:
        key = f"chat:count:{user_id}"
        try:
            count = r.incr(key)
            if count == 1:
                r.expire(key, window)
            if count > limit:
                retry = r.ttl(key) or window
                return False, retry
            return True, 0
        except Exception:
            # fallback to in-memory if Redis operation fails
            pass

    # Fallback single-process sliding window
    now = int(time.time())
    entries = _chat_rate_limits.get(user_id, [])
    entries = [t for t in entries if t > now - window]
    if len(entries) >= limit:
        retry_after = window - (now - entries[0]) if entries else window
        _chat_rate_limits[user_id] = entries
        return False, retry_after
    entries.append(now)
    _chat_rate_limits[user_id] = entries
    return True, 0


def _call_openai_chat(user_message):
    """Call OpenAI Chat Completions API (v1) using stdlib urllib.

    Requires OPENAI_API_KEY set in environment.
    Returns assistant text on success or raises Exception.
    """
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        raise RuntimeError('AI provider not configured (OPENAI_API_KEY missing)')

    url = 'https://api.openai.com/v1/chat/completions'
    payload = {
        'model': os.environ.get('OPENAI_MODEL', 'gpt-3.5-turbo'),
        'messages': [
            {'role': 'system', 'content': 'You are a helpful library assistant for DLCF e-Library. Answer concisely and help users find and use resources.'},
            {'role': 'user', 'content': user_message}
        ],
        'max_tokens': 512,
        'temperature': 0.2
    }
    data = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            resp_data = resp.read()
            decoded = json.loads(resp_data.decode('utf-8'))
            # typical response: choices[0].message.content
            choices = decoded.get('choices') or []
            if not choices:
                raise RuntimeError('Empty response from AI provider')
            return choices[0].get('message', {}).get('content', '').strip()
    except urllib.error.HTTPError as e:
        body = e.read().decode('utf-8')
        raise RuntimeError(f'AI provider HTTP error: {e.code} {body}')


@main_bp.route('/chat/message', methods=['POST'])
@login_required
def chat_message():
    """Receive a user message and respond via AI provider with rate limiting and simple safety checks."""
    payload = request.get_json() or {}
    message = (payload.get('message') or '').strip()
    if not message:
        return {'success': False, 'error': 'Message is required'}, 400
    if len(message) > 2000:
        return {'success': False, 'error': 'Message too long (max 2000 characters)'}, 400

    allowed, retry = _check_chat_rate_limit(current_user.id)
    if not allowed:
        return {'success': False, 'error': 'Rate limit exceeded', 'retry_after': retry}, 429

    try:
        reply = _call_openai_chat(message)
    except Exception as e:
        # record failure in activity log for debugging
        log = ActivityLog(user_id=current_user.id, action='chat_error', details=str(e))
        db.session.add(log)
        db.session.commit()
        return {'success': False, 'error': 'AI provider error: ' + str(e)}, 502

    # record successful chat in activity log
    log = ActivityLog(user_id=current_user.id, action='chat', details=message)
    db.session.add(log)
    db.session.commit()

    return {'success': True, 'reply': reply}
