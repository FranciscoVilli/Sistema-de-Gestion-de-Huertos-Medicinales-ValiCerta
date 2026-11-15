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

## Verificación
Cambios aplicados directamente a producción a pedido del usuario, sin ejecutar la suite local/Docker (se compiló el Python modificado con `py_compile` como chequeo mínimo de sintaxis).
