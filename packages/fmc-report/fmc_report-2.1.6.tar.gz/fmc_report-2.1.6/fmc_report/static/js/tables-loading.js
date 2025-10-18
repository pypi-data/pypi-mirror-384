function initTablesLoadingSpinner() {
  function onReady(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  onReady(function () {
    const overlay = document.getElementById('page-loading-overlay');
    if (!overlay) return;

    const accessForm = document.getElementById('access-form');
    const prefilterForm = document.getElementById('prefilter-form');
    const listsForm = document.getElementById('lists-form');

    function showOverlay() {
      // Overlay einblenden
      overlay.classList.remove('d-none');
      overlay.setAttribute('aria-hidden', 'false');

      // Optional: Scrollen deaktivieren
      // document.body.style.overflow = 'hidden';
    }

    [accessForm, prefilterForm, listsForm].forEach(function (form) {
      if (form) {
        form.addEventListener('submit', showOverlay);
      }
    });
  });
}
