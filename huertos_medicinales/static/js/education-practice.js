"use strict";
const emergenceForm = document.getElementById("emergence-form");
if (emergenceForm) emergenceForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const total = Number(document.getElementById("seeds-total").value);
  const emerged = Number(document.getElementById("seeds-sprouted").value);
  const output = document.getElementById("emergence-result");
  if (!Number.isInteger(total) || !Number.isInteger(emerged) || total <= 0 || emerged < 0 || emerged > total) {
    output.textContent = "Revisa los datos: las emergidas no pueden superar las sembradas.";
    return;
  }
  output.textContent = `${emerged} de ${total}: ${(100 * emerged / total).toLocaleString("es", {maximumFractionDigits: 1})} % de emergencia observada.`;
});
