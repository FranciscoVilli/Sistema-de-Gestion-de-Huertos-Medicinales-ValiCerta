(() => {
 'use strict';
 const root = document.querySelector('[data-bitacora]');
 if (!root) return;
 const search = root.querySelector('[data-bitacora-search]');
 const pills = root.querySelectorAll('[data-bitacora-filter]');
 const entries = root.querySelectorAll('.bitacora-entry');
 const sinResultados = root.querySelector('[data-bitacora-sin-resultados]');
 let grupo = 'todos';

 function aplicarFiltros() {
  const texto = (search?.value || '').trim().toLowerCase();
  let visibles = 0;
  entries.forEach(entry => {
   const coincideGrupo = grupo === 'todos'
    || (grupo === 'fotos' ? entry.dataset.foto === '1' : entry.dataset.grupo === grupo);
   const coincideTexto = !texto || entry.textContent.toLowerCase().includes(texto);
   const visible = coincideGrupo && coincideTexto;
   entry.hidden = !visible;
   if (visible) visibles += 1;
  });
  if (sinResultados) sinResultados.hidden = visibles !== 0;
 }

 search?.addEventListener('input', aplicarFiltros);
 pills.forEach(pill => {
  pill.addEventListener('click', () => {
   grupo = pill.dataset.bitacoraFilter;
   pills.forEach(p => p.classList.toggle('is-active', p === pill));
   aplicarFiltros();
  });
 });
})();
