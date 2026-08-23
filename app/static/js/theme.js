/**
 * Light/dark theme toggle, persisted in localStorage.
 * The <html> element's data-theme attribute is set as early as possible by an
 * inline snippet in base.html (before CSS paints) to avoid a flash of the
 * wrong theme; this file keeps any [data-theme-toggle] buttons in sync and
 * wires up their click handlers once the DOM is ready.
 */
(function () {
  const STORAGE_KEY = 'theme';
  const root = document.documentElement;

  function getPreferredTheme() {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored === 'light' || stored === 'dark') return stored;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  }

  function syncToggleButtons(theme) {
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      btn.setAttribute('aria-pressed', String(theme === 'dark'));
    });
  }

  function applyTheme(theme) {
    root.setAttribute('data-theme', theme);
    localStorage.setItem(STORAGE_KEY, theme);
    syncToggleButtons(theme);
  }

  function toggleTheme() {
    const current = root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    applyTheme(current === 'dark' ? 'light' : 'dark');
  }

  document.addEventListener('DOMContentLoaded', () => {
    applyTheme(root.getAttribute('data-theme') || getPreferredTheme());
    document.querySelectorAll('[data-theme-toggle]').forEach((btn) => {
      btn.addEventListener('click', toggleTheme);
    });
  });

  window.appTheme = { applyTheme, toggleTheme, getPreferredTheme };
})();
