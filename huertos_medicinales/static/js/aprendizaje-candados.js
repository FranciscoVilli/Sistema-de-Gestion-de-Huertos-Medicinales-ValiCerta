function candadoToast() {
  var el = document.getElementById("candado-toast");
  if (!el) {
    el = document.createElement("div");
    el.id = "candado-toast";
    el.setAttribute("role", "status");
    el.setAttribute("aria-live", "polite");
    el.hidden = true;
    el.innerHTML =
      '<svg aria-hidden="true"><use href="#i-lock"></use></svg><span></span>';
    document.body.appendChild(el);
  }
  return el;
}

var candadoOcultarTimer = null;

function mostrarCandadoMensaje(texto) {
  var toast = candadoToast();
  toast.querySelector("span").textContent = texto;
  toast.hidden = false;
  requestAnimationFrame(function () {
    toast.classList.add("is-visible");
  });
  clearTimeout(candadoOcultarTimer);
  candadoOcultarTimer = setTimeout(function () {
    toast.classList.remove("is-visible");
    setTimeout(function () {
      toast.hidden = true;
    }, 250);
  }, 4000);
}

document.querySelectorAll("[data-locked-alert]").forEach(function (el) {
  el.addEventListener("click", function () {
    mostrarCandadoMensaje(el.dataset.lockedAlert);
  });
  el.addEventListener("keydown", function (event) {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      mostrarCandadoMensaje(el.dataset.lockedAlert);
    }
  });
});
