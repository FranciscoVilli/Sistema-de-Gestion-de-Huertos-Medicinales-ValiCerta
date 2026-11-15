# Fotos persistentes en Supabase Storage + calendario sin botón intermedio

Implementado el 15 de noviembre de 2026, a pedido directo del usuario tras reportar que las fotos de las publicaciones del foro parecían no guardarse.

## Diagnóstico: no era un bug de código
Render (plan gratuito) usa disco efímero: se borra en cada deploy/restart del servicio. Toda la media del proyecto (`FileSystemStorage` local, tanto `MEDIA_ROOT` como `private_forum/` del foro) vivía ahí, así que cualquier foto subida se perdía en el siguiente redeploy o reinicio — no al momento de subirla. Esto afecta por igual a fotos de perfil, fotos de observaciones de seguimiento y fotos/videos del foro.

## Solución: Supabase Storage vía su API REST
- `huertos_medicinales/storage.py` (nuevo): `SupabaseStorage`, un backend de Django `Storage` que sube/baja/borra objetos contra `{SUPABASE_URL}/storage/v1/object/...` usando el `service_role` key. No usa el protocolo S3 (se evaluó, pero la compatibilidad de lecturas anónimas de Supabase con ese protocolo es incierta); usa los endpoints REST documentados de Supabase directamente.
- Dos buckets creados en el proyecto Supabase del proyecto (`xzghcwkcnsuydeyuhudn`) por SQL (`storage.buckets`): `media` (público, límite 10 MB) y `private-forum` (privado, límite 40 MB).
- `config/settings/production.py`: si `SUPABASE_URL` y `SUPABASE_SERVICE_ROLE_KEY` están configuradas como variables de entorno, `STORAGES["default"]` pasa a `SupabaseStorage`; si no están, sigue exactamente como antes (sin riesgo de romper el despliegue actual mientras se configuran).
- `huertos_medicinales/comunidades/media_storage.py`: nueva función `forum_storage()` (no una instancia fija) que elige Supabase o el disco local según `settings.SUPABASE_STORAGE_BUCKET_FORUM`. La clase `ForumStorage` original se mantiene con ese nombre porque migraciones ya aplicadas la referencian por ruta de importación.
- `huertos_medicinales/comunidades/models.py`: `Pregunta.foto`/`.video` ahora usan `storage=forum_storage` (función, resuelta en cada acceso) en vez de una instancia fija.
- Migración `comunidades/migrations/0012_alter_pregunta_foto_alter_pregunta_video.py`.
- `pyproject.toml`: se agregó `requests` como dependencia explícita (ya estaba instalada de forma transitiva, pero el nuevo backend depende de ella directamente).

## Pendiente para activarlo en producción
Faltan dos variables de entorno en Render (Settings → Environment del servicio web):
- `SUPABASE_URL` = `https://xzghcwkcnsuydeyuhudn.supabase.co`
- `SUPABASE_SERVICE_ROLE_KEY` = la clave `service_role` del proyecto (Supabase → Project Settings → API). Es secreta; no se pegó en el chat ni se guardó en el repo.

Sin esas variables, el sistema sigue funcionando igual que antes (disco local, mismo problema de pérdida de fotos). En cuanto se agreguen, Render reinicia el servicio solo y el almacenamiento pasa a ser persistente sin necesidad de otro deploy.

## Nota de seguridad aparte (no se tocó)
El advisor de Supabase marcó que las tablas de este proyecto no tienen Row Level Security habilitado. No aplica el riesgo real que advierte (exposición vía `anon key`/PostgREST) porque Django se conecta directamente con credenciales completas de base de datos, no a través del cliente público de Supabase. Se deja anotado por transparencia, sin cambios.

## Calendario: modal al seleccionar un día (no un formulario a un costado)
A pedido del usuario, dos iteraciones:

**Primero** se quitó el botón "＋ Programar actividad" y el formulario se puso embebido en la barra lateral del día seleccionado. El usuario pidió un segundo ajuste: no le gustó verlo "a un costado" con demasiados campos — pidió una ventana modal centrada, con solo día, hora y actividad.

**Diseño final:**
- `templates/panel/calendario.html`: el formulario vive ahora en un `<dialog id="quick-add-dialog">` (mismo patrón nativo que el diálogo de confirmación de `base.html`), centrado con fondo oscurecido. Se abre solo automáticamente cuando la URL trae `?dia=` explícito (click en una celda del calendario o redirección tras guardar) — **no** en la primera carga de `/calendario/` sin parámetros, para no ser intrusivo. También hay un botón pequeño "＋ Registrar actividad" en la agenda por si el usuario cierra el modal y quiere reabrirlo.
- `panel/calendar.py`: nuevo `ActividadRapidaForm` (`practica`, `tipo`, `fecha`, `hora` — nada más) usado para **crear** actividades nuevas, tanto en el modal del calendario como en `calendar_new`. El `ActividadForm` completo (técnica, propagación, parte usada, notas, recordatorio) se sigue usando únicamente para **editar** una actividad existente ("Editar fecha o indicaciones"), así el detalle no se pierde, solo se pospone.
- Se preguntó al usuario qué hacer con el campo Cultivo (obligatorio en el modelo): eligió mantenerlo como un cuarto campo siempre visible, en vez de autoseleccionarlo.
- `panel/test_calendar.py`: `test_siembra_con_tecnica_propagacion_y_aviso_lunar` actualizado (técnica/propagación ahora se agregan editando, no al crear); nuevo test `test_modal_rapido_solo_tiene_los_campos_minimos`.
- CSS: `.quick-add-dialog` en `calendario.css` y `calendario-botanico.css` (reemplaza el `.quick-add` inline de la primera iteración, ya no existe en el HTML).

**Tercer ajuste — campo "Actividad" como texto libre con sugerencias.** El usuario encontró el `<select>` de tipo de actividad demasiado rígido. Se preguntó si quería texto libre total (perdiendo el aviso lunar, la estadística "Próximo riego" y los colores por tipo en el calendario) o texto libre con sugerencias que preserva esas funciones cuando el texto coincide con una categoría conocida; eligió la segunda.
- `panel/calendar.py`: `TIPO_POR_ETIQUETA` (mapa etiqueta-en-minúscula → valor) y `TipoLibreMixin` (compartido por `ActividadForm` y `ActividadRapidaForm`): reemplaza el campo `tipo` por un `CharField` libre con `<input list="actividad-sugerencias">`; en `clean_tipo` normaliza a la categoría conocida si el texto coincide (sin importar mayúsculas/tildes exactas en may/min, no acentos), si no, guarda el texto tal cual.
- `seguimiento/models.py` + migración `0009_alter_actividadcalendario_tipo.py`: `tipo` pasa de `max_length=18` a `60` para admitir texto libre más largo. `choices=TIPOS` se mantiene (documentación/admin), ya no se valida estrictamente porque el formulario usa su propio `CharField`.
- `templates/panel/calendario.html` y `calendario_form.html`: `<datalist id="actividad-sugerencias">` con las etiquetas de `ActividadCalendario.TIPOS` (Riego, Siembra, Cosecha...); el filtro por tipo del calendario (el `<select>` de "Actividad" en los filtros) no cambió, sigue siendo una lista cerrada porque ahí se trata de agrupar lo ya guardado, no de crear texto nuevo.
- Si el texto escrito no coincide con ninguna categoría conocida (p. ej. "Fertilizar con compost"), la actividad se guarda igual, pero sin aviso lunar, sin contar para "Próximo riego" y sin el color específico en el calendario — se queda con el estilo genérico.
- `panel/test_calendar.py`: nuevo test `test_tipo_texto_libre_con_sugerencias`.

**Cuarto ajuste — sin cultivos activos.** El usuario pidió que si no tiene ninguna planta activa, el selector de cultivo invite a "completar las lecciones para desbloquear". Se investigó el sistema de desbloqueo (`huertos_medicinales/aprendizaje/educational_services.py`, `panel/gardens.py`) antes de construir algo: **registrar un cultivo nuevo no tiene ningún bloqueo por lecciones** — eso confirmado explícitamente por los tests `test_sin_leccion_se_puede_registrar_cultivo_real` y `test_se_puede_elegir_especie_sin_desbloqueo_educativo` en `seguimiento/tests.py`. El bloqueo educativo solo existe para *colocar* una planta en una casilla del jardín visual (`panel/gardens.py` `colocar`/`plantas_desbloqueadas`), un paso distinto y posterior. Mostrar "completa las lecciones" en el calendario habría sido información falsa.
- Implementado en su lugar: si el usuario no tiene ningún cultivo con `estado="activa"`, tanto el modal del calendario como la página dedicada de crear actividad muestran "Aún no tienes ningún cultivo activo. Registra uno para poder programar actividades." con un enlace a `seguimiento:crear` (`/mis-practicas/nueva/`), que es la acción real y sin restricciones para conseguir uno.
- `panel/calendar.py`: `calendario()` y `nueva()` calculan `sin_cultivos_activos` a partir de si el queryset de `practica` del formulario tiene resultados.
- `panel/test_calendar.py`: nuevo test `test_sin_cultivos_activos_invita_a_registrar_uno`.

**Corrección — se elimina el registro de cultivo independiente.** El usuario señaló que ya había pedido eliminar `seguimiento:crear` (formulario aparte para registrar una práctica, sin relación con el jardín): según su diseño, elegir una planta disponible y colocarla en un espacio del jardín visual (`panel/gardens.py` `colocar`, modo "seleccionar") **ya es** el acto de plantar, y no debía existir un segundo camino paralelo sin ese flujo.

- Eliminado: `seguimiento:crear` (URL, vista `crear` en `seguimiento/views.py`). `PracticaForm` y `plantas_disponibles()` se mantienen porque `seguimiento:editar` los sigue usando para modificar una práctica ya existente (ahí sí se permite cambiar de especie libremente, sin bloqueo, porque es edición de datos, no alta de una planta nueva).
- Único camino para obtener un cultivo activo: `panel/gardens.py` `colocar()` (URL `garden_place`), que exige que la especie esté desbloqueada por lecciones vía `plantas_desbloqueadas()`.
- Botones que apuntaban a `seguimiento:crear` ahora llevan a `workspace` (la página del jardín), sin preseleccionar la especie — opción elegida por el usuario frente a quitar el botón sin reemplazo:
  - Ficha de planta (`templates/pages/plant.html`): "Ir a mi jardín para sembrarla".
  - Página de ruta guiada (`templates/aprendizaje/pilot_route.html`): ahora el enlace solo aparece si la ruta ya es `eligible` (antes decía, incorrectamente, que el registro "no requiere aprobar esta ruta").
  - Resumen de rutas (`templates/aprendizaje/pilot_progress.html`).
  - El aviso de "sin cultivos activos" del calendario (este mismo documento, apartado anterior) — mismo cambio de destino.
- `PracticaForm` perdió el `help_text` que decía "puedes registrar tu cultivo real sin requisitos educativos" (ya no es cierto para el alta; para edición no aplicaba ese mensaje).
- Tests actualizados/eliminados: `seguimiento/tests.py` (se quitan `test_practica_se_guarda_con_propietario_y_evento`, `test_sin_leccion_se_puede_registrar_cultivo_real`, `test_se_puede_elegir_especie_sin_desbloqueo_educativo`; `test_fechas_futuras_no_crean_practicas` y el test de CSRF/autenticación se reescriben contra `seguimiento:editar`, que ya cubre las mismas invariantes); `aprendizaje/test_pilot.py` (se quita `test_real_cultivation_and_botanical_info_do_not_require_training`, cuyo nombre describía exactamente el comportamiento que se eliminó); `panel/test_design.py` (se quita `seguimiento:crear` de la lista de rutas recorridas); `panel/test_calendar.py` (el test del aviso ahora verifica el enlace a `workspace`). La cobertura de "crear una práctica correctamente" ya existe del lado del jardín en `panel/test_gardens.py` (`test_new_unlocked_crop_and_post_only_release`, `test_visual_selector_checks_learning_and_occupied_slot`).

## Verificación
Cambios aplicados directamente a producción a pedido del usuario, sin ejecutar la suite local/Docker (se compiló el Python modificado con `py_compile` como chequeo mínimo de sintaxis).
