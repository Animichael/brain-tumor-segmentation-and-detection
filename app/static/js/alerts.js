/**
 * Bridges Flask flash() messages to SweetAlert2 toasts, and exposes a themed
 * `appAlert` helper (a Swal mixin) for confirm dialogs used elsewhere (e.g.
 * delete confirmations in the dashboard).
 */
(function () {
  if (typeof Swal === 'undefined') return;

  const CATEGORY_TO_ICON = {
    success: 'success',
    error: 'error',
    danger: 'error',
    warning: 'warning',
    info: 'info',
    message: 'info',
  };

  window.appAlert = Swal.mixin({
    confirmButtonColor: '#2F7D5B',
    cancelButtonColor: '#6B7280',
    background: 'var(--color-surface)',
    color: 'var(--color-text)',
  });

  const toast = Swal.mixin({
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 4000,
    timerProgressBar: true,
    background: 'var(--color-surface)',
    color: 'var(--color-text)',
    didOpen: (el) => {
      el.addEventListener('mouseenter', Swal.stopTimer);
      el.addEventListener('mouseleave', Swal.resumeTimer);
    },
  });

  document.addEventListener('DOMContentLoaded', () => {
    const dataEl = document.getElementById('flashed-messages-data');
    if (!dataEl) return;

    let messages = [];
    try {
      messages = JSON.parse(dataEl.textContent);
    } catch (err) {
      return;
    }

    messages.forEach(([category, message]) => {
      toast.fire({ icon: CATEGORY_TO_ICON[category] || 'info', title: message });
    });
  });
})();
