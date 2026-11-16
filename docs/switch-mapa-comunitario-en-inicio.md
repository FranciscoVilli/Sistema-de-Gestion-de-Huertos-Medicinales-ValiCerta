# El switch de "mostrar en el mapa comunitario" vuelve a estar alcanzable

Implementado el 15 de noviembre de 2026, a pedido del usuario: quería un interruptor para que cada dueño de huerto decida si su ubicación aparece en el mapa comunitario, accesible desde donde administra sus propios integrantes/jardín (no desde la página de "Gestionar integrantes" del responsable, que es de otra persona — se confirmó con el usuario que debía ser autoservicio, cada quien el suyo).

## Diagnóstico
La función ya existía por completo en el backend (`comunidades.share`, modelo `JardinCompartido`, formulario `CompartirForm`) y la vista `panel.views.inicio()` ya calculaba todo lo necesario (`garden_compartido`, `compartir_disponible`, `sector_compartido`, `perfil_listo`) — pero el único lugar que leía esas variables era el bloque `{% if not compact %}` dentro de `weather_widget.html`, y ese widget **siempre** se incluye con `compact=True` en la página de inicio. Es decir, el interruptor nunca tuvo una pantalla real donde mostrarse, independientemente de los cambios de hoy al calendario.

## Cambio
- `templates/panel/inicio.html`: se agregó el bloque de "Visible/Oculto del mapa comunitario" con su switch, justo debajo del widget compacto de clima, usando las variables que la vista ya calculaba. Publica hacia `comunidades:compartir` con el jardín actualmente abierto (`jardin.pk`).
- `templates/panel/weather_widget.html`: se quitó el bloque duplicado (que nunca se renderizaba, ya que esa plantilla solo se usa en modo compacto).
- `panel/views.py` y `comunidades/community.py` no cambiaron — toda la lógica de permisos (`JardinCompartido.jardin.propietario == request.user`) ya era autoservicio desde antes.
- `comunidades/test_community.py::test_privacy_markers_profiles_and_withdrawal`: se agregaron dos verificaciones de que el interruptor aparece en `/mi-espacio/` y que su estado (`garden_compartido`) refleja correctamente si el jardín ya se activó.

## Verificación
No se corrió la suite local/Docker (cambio de plantilla, revisado a mano; las clases CSS usadas —`.garden-sharing`, `.switch-control`, etc.— ya estaban definidas sin dependencia de un contenedor padre, y la hoja `garden-weather.css` ya se carga en esta página).
