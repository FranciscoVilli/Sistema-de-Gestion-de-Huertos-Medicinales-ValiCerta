# Miembros de comunidad

Implementado el 8 de noviembre de 2026, como parte del cierre de brechas contra el enunciado oficial del proyecto (ISWD652).

## Pantallas y funciones
- Un usuario autenticado sin membresía activa ve "Solicitar unirme a esta comunidad" en la ficha pública de cualquier comunidad publicada (`/comunidades/<id>/`). El formulario (`/comunidades/<id>/unirme/`) pide fecha de nacimiento (obligatoria) y género (opcional) y crea la solicitud en estado "Solicitud enviada".
- Solo puede existir una membresía activa (solicitada o aprobada) por usuario a la vez; reintentar la solicitud mientras sigue activa no crea una segunda fila y redirige con aviso.
- El responsable de la comunidad ve "Gestionar miembros" en lugar del enlace de unirse, y en `/comunidades/<id>/miembros/` puede aprobar o rechazar solicitudes pendientes, y retirar miembros aprobados.
- Un miembro retirado puede volver a solicitar unirse (a la misma comunidad o a otra): su registro se reutiliza en vez de crear uno nuevo.
- El responsable puede proponer talentos por nombre libre para cada miembro aprobado; quedan en estado "Propuesta por la comunidad" hasta que el equipo de gestión los certifique o rechace desde el admin (acciones `certificar`/`rechazar` sobre `CertificacionTalento`, con el mismo patrón `SoloLectura` + acción explícita que el resto del admin).
- `Miembro.nivel` (aprendiz/oficial/maestro) y `Miembro.puntos` existen como propiedades calculadas; por ahora devuelven siempre "Aprendiz"/0 — se conectan a las actividades reales de cultivo en la fase de gamificación.
- Cada cambio de estado de membresía queda registrado en `EventoComunidad` (mismo mecanismo de auditoría que publicar/retirar una comunidad).

## Archivos
- `comunidades/models.py`: modelos `Miembro` y `CertificacionTalento`.
- `comunidades/forms.py`: `SolicitudMiembroForm`.
- `comunidades/views.py`: `solicitar_membresia`, `gestionar_miembros`, `decidir_miembro`, `retirar_miembro`, `proponer_talento`.
- `comunidades/urls.py`: rutas `unirme/`, `miembros/`, `miembros/<id>/decidir/`, `miembros/<id>/retirar/`, `miembros/<id>/talento/`.
- `comunidades/admin.py`: `MiembroAdmin`, `CertificacionTalentoAdmin` (acciones `certificar`/`rechazar`).
- `templates/comunidades/solicitar_membresia.html`, `templates/comunidades/gestionar_miembros.html`.
- `templates/comunidades/detalle.html`: enlaces condicionales de unirse/gestionar.
- `comunidades/test_membresia.py`: solicitud, aprobación, retiro, re-solicitud, permisos de gestión, propuesta y duplicado de talentos.

## Migración
`comunidades/migrations/0004_miembro_certificaciontalento.py` — crea `Miembro` y `CertificacionTalento`. No modifica datos existentes.

## Verificación
- `pytest -q` completo del proyecto: 110 pruebas aprobadas (incluye las 4 nuevas de membresía).
- Navegador, flujo completo con dos cuentas de prueba: voluntaria solicita unirse → responsable aprueba → responsable propone un talento → certificación desde el admin. Se detectó y corrigió en el camino que `nivel` es una propiedad calculada (no un campo con `choices`), así que la plantilla debía usar `miembro.nivel.label` y no `get_nivel_display`.
- Cuentas y comunidad de prueba eliminadas de la base al terminar.

## Fuentes técnicas
Ninguna externa; el diseño replica los patrones ya existentes en `comunidades/views.py` (ownership por `responsable=request.user`, `transaction.atomic()` + `select_for_update()`, registro en `EventoComunidad`) y `comunidades/admin.py` (`SoloLectura` + acciones con permiso explícito).
