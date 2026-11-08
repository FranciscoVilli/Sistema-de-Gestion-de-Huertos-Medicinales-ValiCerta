document.getElementById('google-login')?.addEventListener('click', function () {
  document.getElementById('google-status').hidden = false;
  this.setAttribute('aria-expanded', 'true');
});
