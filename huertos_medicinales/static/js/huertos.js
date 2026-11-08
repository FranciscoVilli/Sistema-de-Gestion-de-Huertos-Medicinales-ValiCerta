(() => {
  'use strict';
  const toggle = document.querySelector('.menu-toggle');
  const nav = document.getElementById('main-nav');
  if (toggle && nav) {
    const close = () => { toggle.setAttribute('aria-expanded', 'false'); nav.classList.remove('open'); };
    toggle.addEventListener('click', () => { const open = toggle.getAttribute('aria-expanded') !== 'true'; toggle.setAttribute('aria-expanded', String(open)); nav.classList.toggle('open', open); });
    nav.addEventListener('click', event => { if (event.target.closest('a')) close(); });
    document.addEventListener('keydown', event => { if (event.key === 'Escape' && nav.classList.contains('open')) { close(); toggle.focus(); } });
  }
})();
