# Jardín debe estar completo antes de crear otro; Mis plantas indica su jardín; notificaciones se marcan como vistas

Implementado el 15 de noviembre de 2026, a pedido del usuario.

## 1. No se puede crear un jardín nuevo si el actual tiene espacios libres
- `panel/gardens.py`: nueva función `primer_jardin_incompleto(user)` — recorre los jardines del usuario y devuelve el primero con menos de 6 cultivos colocados.
- La vista `nuevo()` (`garden_new`) ahora revisa esto antes de mostrar o procesar el formulario: si hay un jardín incompleto, redirige a ese jardín con un mensaje ("Completa los seis espacios de 'X' antes de crear otro jardín.") en vez de dejar crear uno nuevo. Si todos los jardines existentes están completos (o no hay ninguno), el alta funciona igual que antes.
- `panel/test_gardens.py`: `test_empty_garden_and_creation` actualizado — primero confirma que crear falla mientras el jardín tiene espacios libres (sigue existiendo solo 1), llena los 6 espacios directamente por ORM, y recién ahí confirma que crear un segundo jardín funciona.
- El aviso visual que ya existía ("Jardín lleno · Crear otro →", visible solo cuando el jardín que se está viendo está lleno) no se tocó; ahora coincide con una regla real del servidor en vez de ser solo una sugerencia de la interfaz.

## 2. "Mis plantas" indica a qué jardín pertenece cada una
- `panel/views.py`: la vista `inicio()` agrega `.select_related("jardin")` a la consulta de prácticas (evita una consulta extra por planta al mostrar el nombre del jardín).
- `templates/panel/inicio.html`: cada tarjeta de "Mis plantas" ahora muestra `🏡 {{ p.jardin.nombre }}` dentro de los metadatos de la tarjeta (junto al día y la estimación de madurez). Si por algún registro antiguo la práctica no tiene jardín asignado, muestra "Sin jardín asignado" en vez de quedar vacío.
- Relevante porque "Mis plantas" lista las prácticas de **todos** los jardines del usuario a la vez (no solo el que está abierto arriba), así que antes no había forma de saber a cuál pertenecía cada una.

## 3. Las notificaciones se marcan como vistas al abrir la campanita
El usuario pidió que, una vez vistas, las notificaciones dejen de aparecer — no solo que el contador baje.

- `panel/calendar.py`: `notificaciones_de(user, today=None, vistas=frozenset())` ahora calcula una "clave" por notificación (`actividad:<id>:<recordatorio_activo>` para actividades, `luna:<fecha>:<hoy>` para el aviso lunar) y excluye del resultado (lista y total) cualquier clave ya presente en `vistas`. Si la actividad cambia de estado (p. ej. entra en su ventana de recordatorio) o la luna recomienda otra fecha, la clave cambia y vuelve a aparecer aunque ya se hubiera visto antes.
- Nueva vista `marcar_notificaciones_vistas` (`POST /notificaciones/vistas/`, URL `notificaciones_vistas`): agrega las claves actuales del usuario a `request.session["notificaciones_vistas"]`.
- `panel/context_processors.py`: `notificaciones()` lee `request.session["notificaciones_vistas"]` y lo pasa como `vistas` a `notificaciones_de`, así el contador/lista en la campanita de cualquier página ya reflejan lo que el usuario descartó.
- `templates/base.html`: la campanita incluye un `<form data-notif-seen hidden>{% csrf_token %}</form>` (necesario porque `CSRF_COOKIE_HTTPONLY=True` impide leer el token desde JS) y un listener en el evento `toggle` del `<details class="notif-menu">`: al abrirse, hace `POST` a `notificaciones_vistas` y quita el número rojo de inmediato en pantalla. La lista ya renderizada en esa apertura no desaparece sola (no hay re-render de lo ya mostrado sin recargar), pero en la siguiente carga de cualquier página esos ítems ya no vuelven a contarse ni listarse, salvo que cambien como se explica arriba.
- Esto vive en la sesión del navegador (no en la base de datos): es deliberadamente liviano, ya que son recordatorios transitorios, no datos que deban sobrevivir a un cierre de sesión completo.
- `panel/test_calendar.py`: `test_notificaciones_de_vistas_oculta_lo_ya_visto` (prueba la función directamente, incluyendo que reaparece si cambia de estado) y `test_endpoint_marcar_notificaciones_vistas` (prueba el endpoint real de extremo a extremo).

## Verificación
No se corrió la suite local/Docker (se agregaron pruebas nuevas a `test_gardens.py` y `test_calendar.py`, revisadas a mano y con `py_compile`, pero no ejecutadas), siguiendo la preferencia del usuario de probar en producción.
