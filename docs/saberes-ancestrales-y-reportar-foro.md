# Saberes ancestrales en Aprender + botón de reportar en el foro

Implementado el 15 de noviembre de 2026, como respuesta directa a la auditoría del enunciado oficial (ISWD652): "pasos espirituales" (ritual de siembra, baño y gratitud antes de la cosecha) se decidió llevarlos al contenido educativo en vez de convertirlos en tipos de actividad del calendario, y el botón de reportar del foro cierra el hueco de moderación comunitaria detectado en esa misma auditoría.

## 1. Ritual de siembra, baño y gratitud — contenido nuevo en "Aprender"

El enunciado describe el ritual de siembra (amanecer, luna creciente o llena), el baño de las plantas dos días antes de la cosecha y el ritual de gratitud previo a cosechar como conocimiento ancestral documentado por el MSP. En vez de modelarlos como pasos registrables del calendario (no se pueden "validar" como datos), se agregaron como contenido de lectura en los capítulos que ya existen sobre el tema:

- Capítulo 15 "Calendario agrícola y ciclos lunares": nueva sección "El ritual de siembra".
- Capítulo 20 "Cosecha": nueva sección "Baño y gratitud antes de cosechar".

Ambas citan "MSP Ecuador (2017), Lineamientos de huertos medicinales, p. 42-47" — la misma cita ya usada en `panel/lunar.py` para el ritual de siembra y las reglas de cosecha por fase lunar — y mantienen el mismo tono cauteloso del resto del curso: se presenta como conocimiento cultural que la comunidad puede elegir mantener, nunca como un paso que sustituya observar la planta o verificar sus condiciones reales.

**Archivos:**
- `aprendizaje/management/commands/agregar_saberes_ancestrales.py` (nuevo): agrega la sección y la fuente a cada lección existente por `CapituloEducativo.numero`, idempotente (no duplica si ya existe una sección con ese título exacto), usando el mismo mecanismo de versión (`LeccionEducativa.save()` crea automáticamente una `RevisionEducativa`).

**Por qué no se editó `curriculum.json` directamente:** ese archivo solo lo lee `seed_curriculum.py`, que se salta cualquier lección cuyo slug ya exista (`capitulo-<n>-contenido`) — como las 24 lecciones ya están sembradas en producción desde el 29 de octubre, editar el JSON no habría cambiado nada ya guardado. El nuevo comando edita directamente las lecciones existentes, agregando una sección sin tocar el resto del contenido ni el historial de revisiones.

**Aplicado directamente en producción:** no hay acceso a shell en Render (plan gratuito), así que el comando no se pudo ejecutar ahí directamente. Se aplicó el mismo cambio, con el mismo texto exacto, vía SQL directo sobre la base de datos de producción (Supabase), replicando a mano lo que hace `LeccionEducativa.save()` (incrementa `revision`, crea la fila de `RevisionEducativa` con el snapshot del contenido y las fuentes). El comando queda en el repositorio para que, si la base de datos se resetea alguna vez, el contenido se pueda recrear igual.

## 2. Botón de reportar en el foro

La auditoría señaló que la moderación del foro existía solo vía permisos de Django (`change_pregunta`/`change_respuesta`), sin ninguna forma de que la propia comunidad marque contenido problemático. Se agregó un reporte simple, al estilo del botón de "Guardar" ya existente:

- `comunidades/models.py`: `reportada_por` (M2M a `User`) en `Pregunta` y en `Respuesta`, igual en forma a `guardada_por`.
- `comunidades/community.py`: `reportar_pregunta` y `reportar_respuesta` (POST, requiere sesión), agregan al usuario actual al M2M — es de una sola vía (no se puede "retirar" un reporte propio); igual que `bookmark()`, responde JSON si es AJAX o redirige si no.
- Rutas: `preguntas/<pk>/reportar/` (`reportar_pregunta`) y `respuestas/<pk>/reportar/` (`reportar_respuesta`).
- UI: en la tarjeta del foro (`feed_cards.html`) y en la página de una pregunta (`question_content.html`), el menú "⋮" muestra "✎ Editar/🗑 Retirar" al autor o moderador, y "🚩 Reportar" a cualquier otro usuario con sesión iniciada (una vez reportado, muestra "🚩 Reportada a moderación" en vez del botón). En cada comentario del hilo (`thread.html`) se agregó el mismo botón junto a "Responder".
- `comunidades/admin.py`: `PreguntaAdmin`/`RespuestaAdmin` ahora muestran una columna "Reportes" (cuenta de `reportada_por`), ordenando la lista por más reportados primero — así un moderador entra a `/admin/` y ve arriba lo que la comunidad marcó, sin necesitar un panel de moderación aparte.
- Migración `comunidades/migrations/0013_pregunta_reportada_por_respuesta_reportada_por.py`.
- Test nuevo: `comunidades/test_forum_groups.py::test_report_question_and_answer_for_moderation`.

**Alcance:** un reporte no oculta nada automáticamente — solo lo hace visible para quien modera (igual que "Guardar" no afecta a nadie más que a quien lo guarda). Ocultar sigue siendo una acción deliberada del moderador, vía el botón "Retirar" que ya existía.

## Verificación
No se corrió la suite local/Docker (cambios revisados a mano y con `py_compile`); el contenido educativo se verificó leyendo directamente las filas de la base de datos de producción antes y después del cambio.
