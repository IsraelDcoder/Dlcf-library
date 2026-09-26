# DLCF e-Library UI/UX Audit

Date: 2026-09-07
Scope: `Library-Hub/`

## Product Map

DLCF e-Library is a Flask application with SQLAlchemy models, Flask-Login authentication, Socket.IO community chat, file uploads, live-session records, and role-based administration.

### Routes

- Public/app: `/`, `/healthz`, `/uploads/<filename>`
- Member: `/dashboard`, `/browse`, `/notifications`, `/history`, `/categories`, `/settings`, `/chat`, `/chat/message`
- Auth: `/login`, `/register`, `/logout`, `/profile`
- Content: `/content/upload`, `/content/view/<id>`, `/content/download/<id>`, `/content/edit/<id>`, `/content/delete/<id>`, `/content/file/<id>`
- Admin: `/admin/`, `/admin/users`, `/admin/users/<id>/edit`, `/admin/content`, `/admin/content/<id>/toggle_publish`, `/admin/uploads`, `/admin/categories`, `/admin/notifications`, `/admin/activity`, `/admin/analytics`, `/admin/live`, `/admin/live/new`
- Community: `/community/`, `/community/new`, `/community/<id>`, `/community/<id>/post`, `/community/post/<id>/comment`, `/community/post/<id>/pin`, `/community/post/<id>/delete`, `/community/<id>/chat`, `/community/<id>/member/<user_id>`, membership management routes
- API: `/api/content`, `/api/content/<id>`, `/api/categories`, `/api/search`, `/api/stats`, `/api/user/history`
- Live: `/live/now`, `/live/start`, `/live/end/<id>`, `/live/upload/<id>`, `/live/save/<id>`
- Socket.IO: `join`, `leave`, `message`, `mute`

### Pages and Templates

- Shared: `base.html`
- Public/member: `index.html`, `dashboard.html`, `browse.html`, `categories.html`, `history.html`, `notifications.html`, `chat.html`
- Auth: `auth/login.html`, `auth/register.html`, `auth/profile.html`
- Content: `content/upload.html`, `content/edit.html`, `content/view.html`
- Admin: `admin/dashboard.html`, `admin/users.html`, `admin/edit_user.html`, `admin/content.html`, `admin/categories.html`, `admin/notifications.html`, `admin/activity.html`, `admin/analytics.html`, `admin/live.html`, `admin/live_setup.html`
- Community: `community/admin_index.html`, `community/new.html`, `community/feed.html`, `community/chat.html`, `community/member.html`, `community/manage_members.html`

### Static Architecture

- Global legacy system: `static/css/style.css`
- Landing: `landing.css`
- Dashboard: `dashboard.css`
- Browse: `browse.css`
- Community: `community.css`, `community_create.css`
- Legacy/unused-looking landing styles: `lp-glass.css`
- Global behavior: `main.js`
- Dashboard behavior: `dashboard.js`
- Community behavior: `community.js`, `community_feed.js`, `community_create.js`, `manage_members.js`
- Live/admin behavior: `admin_live.js`, `admin_live_manage.js`

### Assets

Checked-in static imagery:

- `static/img/hero-screenshot.png`
- `static/img/thumb-sermon.png`
- `static/img/thumb-ebook.png`
- `static/img/thumb-devotional.png`

Uploaded media directories:

- `uploads/audio/`, `ebooks/`, `live/`, `pdfs/`, `videos/` are currently empty in the repository
- `uploads/communities/` contains community source/thumbnail imagery
- `uploads/profiles/` contains profile imagery

### Resource Types

`Content.content_type` supports `pdf`, `ebook`, `audio`, `video`, and `live` upload logic. `LiveSession` separately represents active, ended, recording, and saved live sessions.

### Roles

Site roles: `student`, `teacher`, `admin`.

- Students: browse, view/download public resources, use community features
- Teachers: upload and manage own content, moderate community activity, create live sessions
- Admins: user management, publishing, analytics, categories, notifications, community management, live administration

Community memberships also have `student`, `teacher`, and `admin` roles, creating a separate permission layer.

### Forms, Tables, Modals, and Menus

Forms cover authentication, profile, upload/edit, browse filters, admin users/content/categories/notifications/live, community creation/posts/comments/members, and chat.

Tables are used for admin users, content, activity, and live sessions. History and analytics use list/card presentations.

Dropdowns include shared account navigation, dashboard notifications/profile, browse filters, admin selects, and community controls.

Modals are mostly ad hoc: a demo modal in `main.js`, a member preview modal in `manage_members.js`, and native `confirm()` dialogs for destructive actions. There is no shared modal, drawer, toast, skeleton, or empty-state component system.

### Responsive Behavior

The codebase uses many overlapping breakpoints (`1100`, `1024`, `960`, `900`, `768`, `680`, `620`, `560`, `480`). Dashboard and landing have dedicated responsive rules. Community hides navigation below `900px` but its JavaScript toggle has no matching visible state. Admin tables do not have a dedicated mobile strategy. Browse filters move above results but remain full reload selects.

## Twenty Highest-Impact Problems

1. Resource thumbnails reference `content.thumbnail`, but `Content` has no thumbnail field, so resource cards fall back to icons.
2. Profile images use the static URL root instead of the `/uploads/` serving route and can render broken.
3. Landing category links use unsupported `book` and `sermon` types.
4. Admin live JavaScript calls `io()` without loading the Socket.IO client on the admin shell.
5. Community mobile navigation is hidden without a working `.visible` state.
6. Live UI presents controls without a browser capture, ingest, viewer, or playback experience.
7. Audio/video MIME types are hardcoded despite multiple allowed file extensions.
8. Community feed contains dead anchors and navigation targets.
9. Global, dashboard, community, and landing pages use competing visual systems.
10. Shared class names such as `.btn`, `.card`, `.page-header`, and `.muted` collide across stylesheets.
11. The shared account dropdown is hover-only and unreliable for keyboard/touch users.
12. Theme state is split between `html[data-theme]` and `body.dark`, while page styles do not consistently honor it.
13. Admin tables have no mobile presentation strategy.
14. The PDF reader uses a fixed inline `600px` height.
15. Browse filters are fixed and reload automatically without mobile disclosure or applied-filter feedback.
16. Empty states are duplicated, inconsistent, and lack a shared action pattern.
17. Upload flow advertises drag/drop but lacks accurate `accept`, size validation, preview, and progress feedback.
18. The landing page promises library exploration while `/browse` is authentication-protected.
19. The demo modal posts to a nonexistent `/contact` route.
20. Live status has no coherent user-facing distinction between live, ended, recording-ready, and on-demand sessions.

## Unified Design System Baseline

The product should use one semantic token layer, loaded before page-specific styles. Page styles may compose these tokens but should not redefine the brand palette.

### Colors

- `--color-ink-950`: `#070B12`
- `--color-navy-900`: `#081A33`
- `--color-navy-800`: `#0D2547`
- `--color-blue-700`: `#174EA6`
- `--color-blue-600`: `#2457D6`
- `--color-blue-500`: `#3B73F1`
- `--color-blue-050`: `#EAF1FF`
- `--color-cream-050`: `#F7F3EA`
- `--color-surface`: `#FFFFFF`
- `--color-page`: `#F5F7FB`
- `--color-text`: `#12233F`
- `--color-text-muted`: `#5B6B82`
- `--color-text-subtle`: `#7B8794`
- `--color-gold-600`: `#C9A24A`
- `--color-gold-400`: `#E3BD69`
- `--color-border`: `rgba(18, 35, 63, 0.10)`
- `--color-success`: `#2D9B73`
- `--color-warning`: `#B57916`
- `--color-danger`: `#C45656`

Gold is reserved for accents, active indicators, special labels, and live/featured states.

### Typography

Primary family: Manrope, with a local/system fallback.

- Display: `48-64px`, weight `700-800`, tight tracking
- Page heading: `32-44px`, weight `700`
- Section heading: `20-28px`, weight `700`
- Body: `15-17px`, weight `400-500`, line-height `1.6-1.75`
- Metadata: `12-14px`, weight `600`
- Eyebrow: `11-12px`, weight `800`, uppercase, letter spacing `0.12em`

### Layout and Components

- 8px spacing scale: `8, 12, 16, 24, 32, 40, 48, 64, 80`
- Radii: `8px`, `10px`, `12px`, `16px`, `20px` for feature surfaces only
- Shadow: `0 4px 20px rgba(15, 42, 67, 0.06)`; stronger shadow only for elevated menus and featured surfaces
- Desktop shell: sidebar `240-260px`, sticky topbar, constrained content `1200-1380px`
- Responsive breakpoints: `560px`, `760px`, `1024px`, `1280px`; page components must collapse intentionally
- One resource-card contract: artwork, type, title, author/speaker, metadata, one primary action
- One empty-state contract: icon, concise explanation, one relevant action
- One form contract: label, field, help/error text, visible focus state, grouped sections
- One modal contract: title, description, content, cancel/action order, escape/outside-click behavior

### Product Information Architecture

Member navigation: Home, Library, Categories, Books, Audio, Video, Community, History, Profile, Settings.

Admin navigation: Dashboard, Resources, Uploads, Categories, Users, Activity, Live, Settings.

The same shell, typography, token layer, resource-card contract, and interaction language should be shared across both role experiences; only information density and navigation scope should differ.

## Recommended Implementation Order

1. Consolidate semantic tokens and typography in the global layer.
2. Establish one authenticated AppShell with sidebar, topbar, search, profile, notification, and mobile drawer behavior.
3. Create shared resource-card, category-card, empty-state, form, table, badge, and modal contracts.
4. Migrate dashboard and browse to those contracts.
5. Migrate categories, history, notifications, profile, settings, content detail, and media views.
6. Migrate community pages without changing community behavior.
7. Migrate admin pages with an explicit admin shell and responsive tables.
8. Repair the identified broken UI contracts and route mismatches.
9. Run route, accessibility, responsive, and visual QA across `375`, `390`, `414`, `768`, `1024`, `1280`, `1440`, and `1920px`.
