/* Dashboard JS - vanilla interactions for dashboard
   - Sidebar toggle and responsive behavior
   - Dropdowns for notifications and user menu
   - Ripple effect for buttons
   - Horizontal scroll drag for popular cards
   - Minimal modal for quick actions
*/

document.addEventListener('DOMContentLoaded', function() {
  // Fade in
  const app = document.querySelector('.app-layout');
  if (app) setTimeout(() => app.classList.add('in'), 8);

  // Sidebar logic
  const sidebar = document.querySelector('.sidebar');
  const toggleBtn = document.querySelector('.sidebar-toggle');
  const body = document.querySelector('body');

  const SIDEBAR_KEY = 'dlcf_sidebar_collapsed';
  let collapsed = JSON.parse(localStorage.getItem(SIDEBAR_KEY)) || false;

  function applySidebarState() {
    if (!sidebar) return;
    if (collapsed) sidebar.classList.add('collapsed'); else sidebar.classList.remove('collapsed');
  }

  applySidebarState();

  if (toggleBtn) {
    toggleBtn.addEventListener('click', function() {
      if (window.innerWidth <= 680) {
        // For mobile, open / close overlay
        if (sidebar) sidebar.classList.toggle('open');
        return;
      }
      collapsed = !collapsed;
      localStorage.setItem(SIDEBAR_KEY, JSON.stringify(collapsed));
      applySidebarState();
    });
  }

  // Mobile open/close logic (if sidebar becomes overlay on small screens)
  const mobileOverlayClose = function(e) {
    if (window.innerWidth <= 680) {
      if (sidebar && sidebar.classList.contains('open')) sidebar.classList.remove('open');
    }
  };

  document.querySelectorAll('.sidebar .nav-link-mobile, .sidebar .nav-link').forEach(el => el && el.addEventListener('click', mobileOverlayClose));

  // Mobile menu button
  const mobileMenuBtn = document.getElementById('mobileMenuBtn');
  if (mobileMenuBtn && sidebar) {
    mobileMenuBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      sidebar.classList.toggle('open');
    });
  }

  // Sidebar hover glow: small harmless hover effect by CSS, handled there

  // Notifications dropdown
  const notifBtn = document.getElementById('topNotifBtn');
  const notifPanel = document.getElementById('notifPanel');
  if (notifBtn && notifPanel) {
    notifBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      notifPanel.classList.toggle('open');
    });
  }

  // User dropdown
  const userBtn = document.getElementById('userAvatar');
  const userMenu = document.querySelector('.user-dropdown');
  if (userBtn && userMenu) {
    userBtn.addEventListener('click', function(e) {
      e.stopPropagation();
      userMenu.classList.toggle('open');
    });
  }

  // Close menus when clicking outside
  document.addEventListener('click', function(event) {
    if (notifPanel) notifPanel.classList.remove('open');
    if (userMenu) userMenu.classList.remove('open');
    if (sidebar && sidebar.classList.contains('open')) {
      // close mobile overlay when clicked outside
      if (!sidebar.contains(event.target) && toggleBtn && !toggleBtn.contains(event.target)) {
        sidebar.classList.remove('open');
      }
    }
  });

  // Ripple effect for buttons (btn-quick, .btn )
  function fastRipple(e) {
    const btn = e.currentTarget;
    const rect = btn.getBoundingClientRect();
    const r = document.createElement('span');
    r.className = 'ripple';
    r.style.left = (e.clientX - rect.left) + 'px';
    r.style.top = (e.clientY - rect.top) + 'px';
    r.style.width = r.style.height = Math.max(rect.width, rect.height) + 'px';
    btn.appendChild(r);
    setTimeout(() => r.remove(), 700);
  }

  document.querySelectorAll('.btn-quick, .btn').forEach(btn => {
    btn.classList.add('btn-ripple');
    btn.addEventListener('click', fastRipple);
  });

  // Horizontal scroll drag for popular cards
  const scrollers = document.querySelectorAll('.popular-scroll');
  scrollers.forEach(scroller => {
    let isDown = false; let startX; let scrollLeft;
    scroller.addEventListener('mousedown', (e) => {
      isDown = true; scroller.classList.add('active'); startX = e.pageX - scroller.offsetLeft; scrollLeft = scroller.scrollLeft; e.preventDefault();
    });
    scroller.addEventListener('mouseleave', () => { isDown = false; scroller.classList.remove('active'); });
    scroller.addEventListener('mouseup', () => { isDown = false; scroller.classList.remove('active'); });
    scroller.addEventListener('mousemove', (e) => {
      if (!isDown) return; e.preventDefault(); const x = e.pageX - scroller.offsetLeft; const walk = (x - startX) * 1.2; scroller.scrollLeft = scrollLeft - walk;
    });
  });

  // Quick Action sample: Upload new material (open file input modal)
  document.querySelectorAll('[data-action]').forEach(btn => {
    btn.addEventListener('click', function(e) {
      const action = btn.getAttribute('data-action');
      if (action === 'upload') {
        const input = document.createElement('input'); input.type = 'file'; input.accept = '*/*'; input.multiple = true;
        input.addEventListener('change', function() { alert('Files selected: ' + (this.files ? this.files.length : 0)); });
        input.click();
      }
      if (action === 'add-category') {
        const name = prompt('Enter category name');
        if (name) alert('Category to add: ' + name);
      }
      if (action === 'manage-users') {
        window.location.href = '/admin/users';
      }
    });
  });

});
