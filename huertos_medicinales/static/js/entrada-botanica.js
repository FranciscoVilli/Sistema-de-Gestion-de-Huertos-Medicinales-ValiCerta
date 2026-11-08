(() => {
 'use strict';
 document.querySelectorAll('[data-show-password]').forEach(button => {
  button.addEventListener('click', () => {
   const input = document.getElementById(button.dataset.showPassword);
   if (!input) return;
   const visible = input.type === 'password';
   input.type = visible ? 'text' : 'password';
   input.toggleAttribute('data-password-visible', visible);
   button.textContent = visible ? 'Ocultar' : 'Mostrar';
   button.setAttribute('aria-label', visible ? 'Ocultar contraseña' : 'Mostrar contraseña');
   button.setAttribute('aria-pressed', String(visible));
  });
 });
})();