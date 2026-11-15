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

## Calendario: sin botón "Programar actividad"
A pedido del usuario, para que el calendario se entienda como "selecciono un día y registro algo ahí", igual que Google Calendar:
- Se quitaron los dos enlaces "＋ Programar actividad" / "＋ Programar" (encabezado y agenda).
- `panel/calendar.py`: la vista `calendario()` ahora también construye un `ActividadForm` vacío (con `fecha` precargada al día seleccionado) y lo pasa como `nueva_form`.
- `templates/panel/calendario.html`: ese formulario se renderiza directamente dentro de la tarjeta del día seleccionado (sección `.quick-add`), debajo de las actividades ya agendadas. Al guardar, redirige de vuelta al mismo día.
- La vista/página dedicada (`calendar_new`/`calendario_form.html`) sigue existiendo para **editar** una actividad existente ("Editar fecha o indicaciones"); solo se eliminó el paso extra para **crear** una nueva.
- CSS nuevo en `calendario.css` y `calendario-botanico.css` para la sección `.quick-add`.

## Verificación
Cambios aplicados directamente a producción a pedido del usuario, sin ejecutar la suite local/Docker (se compiló el Python modificado con `py_compile` como chequeo mínimo de sintaxis).
