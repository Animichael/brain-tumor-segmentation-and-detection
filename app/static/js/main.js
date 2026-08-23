/**
 * Landing page interactivity: navbar scroll state + mobile drawer, hero slider,
 * how-it-works carousel, and the testimonials scroll-slider.
 */
document.addEventListener('DOMContentLoaded', () => {
  initNavbar();
  initHeroSlider();
  initStepsCarousel();
  initTestimonialsSlider();
});

/* ---- Navbar: transparent over hero, solid on scroll + mobile drawer ---- */
function initNavbar() {
  const navbar = document.getElementById('site-navbar');
  if (navbar) {
    const onScroll = () => {
      navbar.classList.toggle('is-scrolled', window.scrollY > 24);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
  }

  const burger = document.getElementById('navbar-burger');
  const mobileMenu = document.getElementById('navbar-mobile');
  const closeBtn = document.getElementById('navbar-mobile-close');
  const backdrop = document.getElementById('navbar-mobile-backdrop');
  if (!burger || !mobileMenu) return;

  const openMenu = () => {
    mobileMenu.classList.add('is-open');
    backdrop.classList.add('is-open');
    burger.setAttribute('aria-expanded', 'true');
  };
  const closeMenu = () => {
    mobileMenu.classList.remove('is-open');
    backdrop.classList.remove('is-open');
    burger.setAttribute('aria-expanded', 'false');
  };

  burger.addEventListener('click', openMenu);
  closeBtn?.addEventListener('click', closeMenu);
  backdrop?.addEventListener('click', closeMenu);
  mobileMenu.querySelectorAll('a').forEach((link) => link.addEventListener('click', closeMenu));
}

/* ---- Hero slider: autoplay fade every 5s, arrows, dots ---- */
function initHeroSlider() {
  const slides = document.querySelectorAll('#hero-slider .hero-slide');
  if (slides.length < 2) return;

  const dots = document.querySelectorAll('#hero-dots .hero-dot');
  const prevBtn = document.getElementById('hero-prev');
  const nextBtn = document.getElementById('hero-next');
  const AUTOPLAY_MS = 5000;

  let current = 0;
  let timer = null;

  function goTo(index) {
    slides[current].classList.remove('is-active');
    dots[current]?.classList.remove('is-active');
    current = (index + slides.length) % slides.length;
    slides[current].classList.add('is-active');
    dots[current]?.classList.add('is-active');
  }

  function next() {
    goTo(current + 1);
  }

  function restartAutoplay() {
    if (timer) clearInterval(timer);
    timer = setInterval(next, AUTOPLAY_MS);
  }

  prevBtn?.addEventListener('click', () => {
    goTo(current - 1);
    restartAutoplay();
  });
  nextBtn?.addEventListener('click', () => {
    goTo(current + 1);
    restartAutoplay();
  });
  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      goTo(index);
      restartAutoplay();
    });
  });

  restartAutoplay();
}

/* ---- How-it-works carousel: rotates which card is centered/emphasized ---- */
function initStepsCarousel() {
  const track = document.getElementById('steps-track');
  if (!track) return;

  const cards = Array.from(track.children);
  if (cards.length < 2) return;

  const prevBtn = document.getElementById('steps-prev');
  const nextBtn = document.getElementById('steps-next');

  function setCenter(offset) {
    if (offset > 0) {
      track.appendChild(track.firstElementChild);
    } else if (offset < 0) {
      track.insertBefore(track.lastElementChild, track.firstElementChild);
    }
    const current = Array.from(track.children);
    current.forEach((card, index) => {
      card.classList.toggle('is-center', index === 1);
    });
  }

  prevBtn?.addEventListener('click', () => setCenter(-1));
  nextBtn?.addEventListener('click', () => setCenter(1));
}

/* ---- Testimonials: horizontal scroll-snap track driven by dot controls ---- */
function initTestimonialsSlider() {
  const track = document.getElementById('testimonials-track');
  const dotsWrap = document.getElementById('testimonials-dots');
  if (!track || !dotsWrap) return;

  const cards = Array.from(track.children);
  const dots = Array.from(dotsWrap.children);

  dots.forEach((dot, index) => {
    dot.addEventListener('click', () => {
      cards[index]?.scrollIntoView({ behavior: 'smooth', inline: 'start', block: 'nearest' });
    });
  });

  if (!('IntersectionObserver' in window)) return;

  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          const index = cards.indexOf(entry.target);
          dots.forEach((dot) => dot.classList.remove('is-active'));
          dots[index]?.classList.add('is-active');
        }
      });
    },
    { root: track, threshold: 0.6 }
  );

  cards.forEach((card) => observer.observe(card));
}
