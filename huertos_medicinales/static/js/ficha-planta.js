(() => {
 'use strict';
 const stage = document.querySelector('.plant-illustration');
 const bubble = document.getElementById('plant-bubble');
 if (!stage || !bubble) return;
 const tags = stage.querySelectorAll('.plant-tag');
 const titleEl = bubble.querySelector('.plant-bubble-title');
 const textEl = bubble.querySelector('.plant-bubble-text');
 const linkEl = bubble.querySelector('.plant-bubble-link');
 const closeBtn = document.getElementById('plant-bubble-close');

 function close(returnFocus) {
  bubble.hidden = true;
  tags.forEach((tag) => tag.setAttribute('aria-pressed', 'false'));
  if (returnFocus) returnFocus.focus();
 }

 tags.forEach((tag) => {
  tag.setAttribute('aria-pressed', 'false');
  tag.addEventListener('click', (event) => {
   event.preventDefault();
   titleEl.textContent = tag.dataset.bubbleTitle || '';
   textEl.textContent = tag.dataset.bubbleText || '';
   linkEl.setAttribute('href', tag.getAttribute('href'));
   bubble.hidden = false;
   tags.forEach((other) => other.setAttribute('aria-pressed', String(other === tag)));
   bubble.focus();
  });
 });

 closeBtn.addEventListener('click', () => close());
 linkEl.addEventListener('click', () => {
  bubble.hidden = true;
  tags.forEach((tag) => tag.setAttribute('aria-pressed', 'false'));
 });
 document.addEventListener('keydown', (event) => {
  if (event.key === 'Escape' && !bubble.hidden) close();
 });
 document.addEventListener('click', (event) => {
  if (bubble.hidden) return;
  if (bubble.contains(event.target) || [...tags].includes(event.target.closest?.('.plant-tag'))) return;
  close();
 });
})();
