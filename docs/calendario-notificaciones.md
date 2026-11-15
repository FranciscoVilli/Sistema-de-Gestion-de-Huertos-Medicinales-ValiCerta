# Notificaciones reales y recordatorios en el calendario

Implementado el 15 de noviembre de 2026, a pedido directo del usuario para que el calendario y la campanita de notificaciones (hasta ahora un aviso fijo "No tienes notificaciones nuevas") sirvan de verdad.

## Qué cambia
- Cada actividad del calendario (`ActividadCalendario`) tiene un nuevo campo **Avisarme** (`recordatorio_dias_antes`): el mismo día, 1/2/3 días antes o 1 semana antes. Por defecto 1 día antes; se puede dejar vacío para no recibir aviso. Se elige al programar o editar la actividad, igual que un recordatorio de Google Calendar.
- La campanita de notificaciones (antes estática en `base.html`) ahora es dinámica en toda la aplicación:
  - Muestra un aviso de **luna buena para sembrar**: hoy si la fase actual ya es favorable (creciente o llena), o la próxima fecha favorable dentro de 30 días.
  - Lista las **próximas actividades registradas** (no completadas, desde hoy), marcando con 🔔 las que ya entraron en su ventana de recordatorio y con 📅 el resto.
  - Un número en la campanita indica el total de avisos.

## Archivos
- `seguimiento/models.py`: `ActividadCalendario.recordatorio_dias_antes` (nuevo).
- `seguimiento/migrations/0008_actividadcalendario_recordatorio_dias_antes.py`.
- `panel/lunar.py`: `proxima_buena_para_sembrar(desde, limite_dias=30)`.
- `panel/calendar.py`: `ActividadForm` incluye el nuevo campo; nueva función `notificaciones_de(user, today=None)` reutilizada por el formulario de actividad y por el context processor.
- `panel/context_processors.py` (nuevo): `notificaciones`, registrado en `config/settings/base.py` para que la campanita tenga datos en cualquier página, no solo en el calendario.
- `templates/base.html`: dropdown de notificaciones dinámico.
- `static/css/app-ui.css`: estilos del contador y de los ítems de notificación.
- `panel/test_lunar.py`, `panel/test_calendar.py`: pruebas de `proxima_buena_para_sembrar` y `notificaciones_de`.

## Alcance y decisiones
- Las actividades siguen requiriendo un cultivo (`practica`), como ya funcionaba; no se creó un tipo de "evento libre" sin planta porque el tipo "Otro cuidado" ya cubre ese caso dentro del modelo existente.
- No hay notificaciones push ni tareas en segundo plano (el proyecto no tiene Celery/Redis en producción): el aviso se calcula en cada carga de página a partir de la fecha de hoy, por lo que aparece mientras la condición sea cierta y desaparece sola cuando la actividad se completa o la fecha pasa.

## Verificación
Cambios aplicados directamente a producción (ya desplegada en Render) a pedido del usuario, sin ejecutar antes la suite local/Docker.
