(function () {
  const banner = document.getElementById('library-update-banner');
  if (!banner) return;

  const sinceId = Number(banner.dataset.sinceId || 0);
  const message = document.getElementById('library-update-message');
  const refresh = document.getElementById('library-update-refresh');
  refresh?.addEventListener('click', () => window.location.reload());

  const checkForUpdates = async () => {
    try {
      const response = await fetch(`/api/content/updates?since_id=${sinceId}`, { headers: { Accept: 'application/json' } });
      if (!response.ok) return;
      const result = await response.json();
      if (!result.items?.length) return;
      const count = result.items.length;
      message.textContent = `${count}${result.has_more ? '+' : ''} new ${count === 1 ? 'resource is' : 'resources are'} available.`;
      banner.hidden = false;
      window.clearInterval(poll);
    } catch (_) {
      // A transient polling failure should not interrupt library browsing.
    }
  };

  const poll = window.setInterval(checkForUpdates, 15000);
  window.setTimeout(checkForUpdates, 15000);
})();