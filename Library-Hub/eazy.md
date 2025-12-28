# DLCF e-Library

## Overview
Enterprise-grade e-Library platform for managing PDFs, eBooks, audio, and video content with role-based access control (RBAC) for Students, Teachers, and Admins.

## Tech Stack
- **Backend**: Python Flask
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Database**: PostgreSQL
- **Authentication**: Flask-Login with bcrypt password hashing

## Project Structure
```
/
├── app.py              # Main Flask application
├── models.py           # SQLAlchemy database models
├── routes/
│   ├── auth.py         # Authentication routes (login, register, profile)
│   ├── main.py         # Main routes (dashboard, browse, notifications)
│   ├── content.py      # Content management routes (upload, view, download)
│   ├── admin.py        # Admin dashboard routes
│   └── api.py          # RESTful API endpoints
├── templates/          # Jinja2 HTML templates
│   ├── base.html       # Base template with navigation
│   ├── auth/           # Authentication templates
│   ├── content/        # Content templates
│   └── admin/          # Admin templates
├── static/
│   ├── css/style.css   # Main stylesheet
│   └── js/main.js      # Main JavaScript file
└── uploads/            # Uploaded content storage
    ├── pdfs/
    ├── ebooks/
    ├── audio/
    ├── videos/
    └── profiles/
```

## Database Models
- **User**: id, name, email, password_hash, role, bio, profile_photo, created_at, is_active
- **Category**: id, name, description, created_at
- **Tag**: id, name
- **Content**: id, title, author, description, content_type, file_path, file_size, category_id, uploaded_by, is_public, view_count, download_count, created_at
- **ActivityLog**: id, user_id, content_id, action, details, ip_address, timestamp
- **Notification**: id, title, message, recipient_id, is_global, is_read, created_at, sent_at

## User Roles
- **Admin**: Full access, user management, content management, analytics
- **Teacher**: Upload, edit, delete content, view all content
- **Student**: Browse, view, download public content

## Default Admin Account
- Email: admin@dlcf.org
- Password: admin123

## Key Features
1. User authentication with role-based access
2. Content upload (PDF, eBook, audio, video)
3. Content categorization and tagging
4. Search and filtering
5. Online content viewing (PDF viewer, audio/video players)
6. Download tracking
7. Activity logging
8. Admin dashboard with analytics
9. Notification system
10. Responsive design
11. Live Streaming & Message Archiving: Stream messages live within the library, automatically save recordings, categorize and tag them, and make them available for on-demand listening or download.

## Running the Application
```bash
python app.py
```
Server runs on http://0.0.0.0:5000

## Environment Variables
- DATABASE_URL: PostgreSQL connection string
- SESSION_SECRET: Secret key for session management
