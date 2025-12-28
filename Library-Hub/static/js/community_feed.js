// Minimal interactivity for community feed
document.addEventListener('DOMContentLoaded', function () {
  // Toggle nav on small screens
  const navToggle = document.querySelector('.community-info');
  if (navToggle) {
    navToggle.addEventListener('click', function (e) {
      if (window.innerWidth < 900) {
        const navList = document.querySelector('.nav-list');
        if (navList) navList.classList.toggle('visible');
      }
    });
  }

  // Confirm delete handlers (enhance forms with data-confirm)
  document.querySelectorAll('form[onsubmit]').forEach(function (form) {
    // already has confirm via onsubmit in templates
  });

  // Improve keyboard accessibility for card actions
  document.querySelectorAll('.btn-icon').forEach(function (btn) {
    btn.setAttribute('tabindex', '0');
    btn.addEventListener('keydown', function (e) {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        btn.click();
      }
    });
  });
});