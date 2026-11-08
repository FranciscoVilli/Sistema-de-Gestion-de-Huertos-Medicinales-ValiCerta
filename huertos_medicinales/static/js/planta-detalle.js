(() => {
 const dialog = document.querySelector('#plant-detail');
 if (!dialog) return;
 const tabs = [...dialog.querySelectorAll('[data-plant-tab]')];
 const panels = [...dialog.querySelectorAll('.plant-tab-panel')];
 dialog.querySelector('.plant-tabs').setAttribute('role', 'tablist');
 function activate(tab, focus = false) {
  tabs.forEach(item => {const active = item === tab; item.setAttribute('aria-selected', String(active)); item.tabIndex = active ? 0 : -1;});
  panels.forEach(panel => {panel.hidden = panel.id !== tab.dataset.plantTab;});
  if (focus) tab.focus();
 }
 tabs.forEach((tab, index) => {
  tab.id = 'tab-' + tab.dataset.plantTab;
  tab.setAttribute('role', 'tab');
  tab.setAttribute('aria-controls', tab.dataset.plantTab);
  const panel = document.getElementById(tab.dataset.plantTab);
  panel.setAttribute('role', 'tabpanel'); panel.setAttribute('aria-labelledby', tab.id); panel.tabIndex = 0;
  tab.addEventListener('click', event => {event.preventDefault(); activate(tab);});
  tab.addEventListener('keydown', event => {
   const targets = {ArrowRight:(index+1)%tabs.length, ArrowLeft:(index+tabs.length-1)%tabs.length, Home:0, End:tabs.length-1};
   if (event.key in targets) {event.preventDefault();activate(tabs[targets[event.key]],true);}
  });
 });
 activate(tabs[0]);
 const close = () => {location.assign(dialog.dataset.closeUrl);};
 dialog.addEventListener('cancel', event => {event.preventDefault();close();});
 if (typeof dialog.showModal === 'function') {dialog.removeAttribute('open');dialog.showModal();}
})();