(() => {
 'use strict';
 const TEXTOS = {
  riego: 'Riego realizado',
  limpieza: 'Retiré hojas secas y limpié el espacio',
  poda: 'Poda realizada',
  revision: 'Revisé la planta',
 };
 const botones = document.querySelectorAll('[data-care]');
 const form = document.querySelector('[data-observacion-form]');
 if (!botones.length || !form) return;
 const accion = form.querySelector('[name=accion]');
 const resultado = form.querySelector('[name=resultado]');
 botones.forEach(boton => {
  boton.addEventListener('click', () => {
   if (accion) accion.value = TEXTOS[boton.dataset.care] || '';
   botones.forEach(b => b.classList.toggle('is-selected', b === boton));
   resultado?.focus();
  });
 });
})();
