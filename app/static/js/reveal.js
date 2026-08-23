/**
 * Scroll-reveal animation for elements marked with the `.reveal` class.
 * Elements sharing a `[data-reveal-group]` ancestor are staggered in order
 * (capped so long lists don't produce an unreasonably long delay chain).
 */
(function () {
  const STAGGER_STEP_MS = 80;
  const STAGGER_MAX_STEPS = 8;

  function initReveal() {
    const items = document.querySelectorAll('.reveal');
    if (!items.length) return;

    if (!('IntersectionObserver' in window)) {
      items.forEach((el) => el.classList.add('is-visible'));
      return;
    }

    items.forEach((el, index) => {
      const group = el.closest('[data-reveal-group]');
      const staggerIndex = group
        ? Array.from(group.querySelectorAll('.reveal')).indexOf(el)
        : index;
      const delay = Math.min(staggerIndex, STAGGER_MAX_STEPS) * STAGGER_STEP_MS;
      el.style.setProperty('--reveal-delay', `${delay}ms`);
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('is-visible');
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.15, rootMargin: '0px 0px -40px 0px' }
    );

    items.forEach((el) => observer.observe(el));
  }

  document.addEventListener('DOMContentLoaded', initReveal);
})();
