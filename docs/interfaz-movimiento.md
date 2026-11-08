# Pie de página y movimiento

21 de octubre de 2026. Se reprodujo un hueco de 330 px bajo el pie en móvil, provocado por padding-bottom aplicado a body al mostrar cookies. La guía añadía otro padding de 330 px al documento. Se retiraron ambos ajustes.

La estructura compartida usa columna flexible y altura mínima de viewport. El contenido crece y el pie permanece al final, tanto con páginas cortas como largas. La reserva para paneles superpuestos se incorpora dentro del pie, manteniendo su fondo continuo. ResizeObserver ajusta el tamaño real de cookies y guía y restaura la reserva al cerrar. Existen valores CSS de respaldo sin JavaScript.

Movimiento: apariciones breves de 320 ms al entrar en el área visible, una sola vez por elemento; transiciones de color/borde en botones y tarjetas. No hay bucles, carruseles automáticos ni animaciones que exijan reaccionar. Los contenidos no se ocultan como requisito de funcionamiento. Se respeta prefers-reduced-motion, incluidos cambios de preferencia durante la sesión. No se instalaron bibliotecas ni servicios externos.

Se consultó el catálogo curado mediante skill-installer; no ofreció una skill específica de movimiento para este Django. Las habilidades de Figma disponibles se orientan a diseños de Figma y no son un requisito para esta implementación nativa.

Verificación: 48 combinaciones de cuatro pantallas, tres anchos, dos preferencias de movimiento y dos estados de cookies; sin separación bajo el pie ni desbordamiento, animaciones presentes solo cuando están permitidas y sin errores JavaScript. Cookies operativas sin JavaScript. Laboratorio comprobado con guía abierta y cerrada: reserva ajustada y pie continuo. Evidencia en pruebas/evidencias/interfaz.
