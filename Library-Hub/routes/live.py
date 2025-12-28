from flask import Blueprint, request, jsonify, current_app, abort
from flask_login import login_required, current_user
from models import db, LiveSession, User, Content
from datetime import datetime
import os
from werkzeug.utils import secure_filename
# import socketio lazily inside functions to avoid circular import with app

live_bp = Blueprint('live', __name__)


def _require_teacher():
    if not (current_user.is_authenticated and (current_user.is_teacher() or current_user.is_admin())):
        abort(403)


@live_bp.route('/now', methods=['GET'])
def now_list():
    """List active or recent live sessions."""
    sessions = LiveSession.query.order_by(LiveSession.started_at.desc()).limit(20).all()
    data = []
    for s in sessions:
        data.append({
            'id': s.id,
            'title': s.title,
            'host': s.host.name if s.host else None,
            'is_live': s.is_live,
            'started_at': s.started_at.isoformat() if s.started_at else None,
            'ended_at': s.ended_at.isoformat() if s.ended_at else None,
        })
    return jsonify(data)


@live_bp.route('/start', methods=['POST'])
@login_required
def start_session():
    _require_teacher()
    payload = request.json or {}
    title = payload.get('title') or 'Live Session'
    community_id = payload.get('community_id')
    session = LiveSession(title=title, host_id=current_user.id, community_id=community_id, is_live=True)
    db.session.add(session)
    db.session.commit()
    # broadcast live creation
    try:
        from app import socketio
        socketio.emit('live:started', {'id': session.id, 'title': session.title}, broadcast=True)
    except Exception:
        pass
    return jsonify({'id': session.id, 'started_at': session.started_at.isoformat()})


@live_bp.route('/end/<int:session_id>', methods=['POST'])
@login_required
def end_session(session_id):
    _require_teacher()
    session = LiveSession.query.get_or_404(session_id)
    if not session.is_live:
        return jsonify({'status': 'already-ended'}), 400
    session.is_live = False
    session.ended_at = datetime.utcnow()
    # Expect client or streaming backend to POST recording metadata after upload
    recording_path = request.json.get('recording_path') if request.is_json else None
    recording_size = request.json.get('recording_size') if request.is_json else None
    if recording_path:
        session.recording_path = recording_path
        session.recording_size = recording_size
    db.session.add(session)
    db.session.commit()
    # broadcast end
    try:
        from app import socketio
        socketio.emit('live:ended', {'id': session.id, 'ended_at': session.ended_at.isoformat()}, broadcast=True)
    except Exception:
        pass
    # auto-save if recording uploaded and client requested auto_publish
    auto_publish = (request.json.get('auto_publish') if request.is_json else False)
    if auto_publish and session.recording_path:
        session.save_as_content(uploader_id=current_user.id)
    return jsonify({'id': session.id, 'ended_at': session.ended_at.isoformat()})



@live_bp.route('/upload/<int:session_id>', methods=['POST'])
@login_required
def upload_recording(session_id):
    _require_teacher()
    session = LiveSession.query.get_or_404(session_id)
    if 'recording' not in request.files:
        return jsonify({'error': 'no-file'}), 400
    f = request.files['recording']
    filename = secure_filename(f.filename)
    live_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'live')
    dest_name = f"{session_id}_{int(datetime.utcnow().timestamp())}_{filename}"
    dest = os.path.join(live_dir, dest_name)
    f.save(dest)
    # store filename only (content routes expect file_path to be filename in the live folder)
    session.recording_path = dest_name
    session.recording_size = os.path.getsize(dest) if os.path.exists(dest) else None
    db.session.add(session)
    db.session.commit()
    try:
        from app import socketio
        socketio.emit('live:recording_uploaded', {'id': session.id, 'path': session.recording_path}, broadcast=True)
    except Exception:
        pass
    return jsonify({'status': 'ok', 'path': session.recording_path})


@live_bp.route('/save/<int:session_id>', methods=['POST'])
@login_required
def save_recording(session_id):
    _require_teacher()
    session = LiveSession.query.get_or_404(session_id)
    if not session.recording_path:
        return jsonify({'error': 'no-recording'}), 400
    content = session.save_as_content(uploader_id=current_user.id)
    if not content:
        return jsonify({'error': 'failed'}), 500
    return jsonify({'content_id': content.id})
