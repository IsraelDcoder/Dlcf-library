from flask import Blueprint, current_app, send_from_directory, abort
import os
main_uploads = Blueprint('uploads', __name__)

@main_uploads.route('/uploads/<path:filename>')
def uploads(filename):
    base = current_app.config.get('UPLOAD_FOLDER')
    if not base:
        abort(404)
    path = os.path.join(base, filename)
    if not os.path.isfile(path):
        abort(404)
    # send from the uploads directory root
    return send_from_directory(base, filename)
