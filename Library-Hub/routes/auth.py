from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
import os
from models import db, User, ActivityLog, Community, Membership
from email_validator import validate_email, EmailNotValidError

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember = request.form.get('remember', False)
        
        if not email or not password:
            flash('Please fill in all fields.', 'error')
            return render_template('auth/login.html')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                flash('Your account has been deactivated. Contact admin.', 'error')
                return render_template('auth/login.html')
            
            login_user(user, remember=remember)
            
            log = ActivityLog(
                user_id=user.id,
                action='login',
                details='User logged in',
                ip_address=request.remote_addr
            )
            db.session.add(log)
            db.session.commit()
            
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'error')
    
    return render_template('auth/login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if not name or not email or not password:
            flash('Please fill in all required fields.', 'error')
            return render_template('auth/register.html')
        
        if len(password) < 6:
            flash('Password must be at least 6 characters.', 'error')
            return render_template('auth/register.html')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return render_template('auth/register.html')
        
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Please enter a valid email address.', 'error')
            return render_template('auth/register.html')
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('An account with this email already exists.', 'error')
            return render_template('auth/register.html')
        
        user = User(
            name=name,
            email=email,
            role='student'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Assign user to default community (create if missing)
        default_slug = os.environ.get('DEFAULT_COMMUNITY_SLUG')
        community = None
        if default_slug:
            community = Community.query.filter_by(slug=default_slug).first()
        if not community:
            community = Community.query.first()
        if not community:
            community = Community(name='DLCF Community', slug='dlcf', description='Default community')
            db.session.add(community)
            db.session.commit()
        membership = Membership(user_id=user.id, community_id=community.id, role='student')
        db.session.add(membership)
        db.session.commit()

        log = ActivityLog(
            user_id=user.id,
            action='register',
            details=f'New user registration and joined community {community.name}',
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
        
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    log = ActivityLog(
        user_id=current_user.id,
        action='logout',
        details='User logged out',
        ip_address=request.remote_addr
    )
    db.session.add(log)
    db.session.commit()
    
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        bio = request.form.get('bio', '').strip()
        
        if not name:
            flash('Name is required.', 'error')
            return render_template('auth/profile.html')
        
        current_user.name = name
        current_user.bio = bio
        
        if 'profile_photo' in request.files:
            file = request.files['profile_photo']
            if file.filename:
                import os
                from flask import current_app
                from werkzeug.utils import secure_filename
                
                filename = secure_filename(f"{current_user.id}_{file.filename}")
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles', filename)
                file.save(filepath)
                current_user.profile_photo = filename
        
        db.session.commit()
        flash('Profile updated successfully!', 'success')
    
    activities = ActivityLog.query.filter_by(user_id=current_user.id).order_by(ActivityLog.timestamp.desc()).limit(20).all()
    return render_template('auth/profile.html', activities=activities)
