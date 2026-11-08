(() => {
 const form = document.querySelector('#plant-selection');
 if (!form) return;
 const search = document.querySelector('#plant-search');
 const cards = [...form.querySelectorAll('.plant-choice')];
 const button = form.querySelector('button[type=submit]');
 const normalize = value => value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLowerCase().trim();
 const sync = () => { button.disabled = !form.querySelector('input[name=planta]:checked'); };
 form.addEventListener('change', sync);
 search.addEventListener('input', () => {
  const query = normalize(search.value);
  cards.forEach(card => {
   card.hidden = !normalize(card.dataset.plantName).includes(query);
   if (card.hidden) card.querySelector('input').checked = false;
  });
  document.querySelector('#plant-no-results').hidden = cards.some(card => !card.hidden);
  sync();
 });
 sync();
})();