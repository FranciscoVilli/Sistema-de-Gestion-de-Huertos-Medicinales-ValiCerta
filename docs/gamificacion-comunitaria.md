# Gamificación comunitaria y ranking

Implementado el 8 de noviembre de 2026, como parte del cierre de brechas contra el enunciado oficial del proyecto (ISWD652). Última fase del plan; con esta se completan las seis brechas identificadas en la auditoría contra el enunciado del MSP.

## Pantallas y funciones
- `Miembro.puntos` y `Miembro.nivel` (definidos como contrato vacío en la Fase A) ahora se calculan de verdad: puntos = actividades de cultivo completadas × 5, más observaciones registradas × 3, más talentos certificados × 20, más la recompensa de cualquier misión cumplida. Nivel: aprendiz (0-49 puntos), oficial (50-149), maestro (150+). Nada se guarda en la base de datos — se recalcula cada vez a partir de los registros reales de `seguimiento` (actividades/observaciones del mismo usuario) y `CertificacionTalento`, siguiendo la misma convención de "propiedad calculada" usada en `Practica.etapa` y `Practica.dias_transcurridos`.
- `Comunidad.puntos` suma los puntos de sus miembros aprobados. Nueva vista pública de **ranking** (`/comunidades/ranking/`) que ordena las comunidades publicadas por puntos. Enlazada desde la ficha de cada comunidad, que también muestra sus puntos actuales.
- **Insignias**: catálogo fijo en código (`comunidades/gamificacion.py`, mismo patrón que `aprendizaje/catalogo.py`) — "Primeros pasos" (1 actividad), "Manos en la tierra" (5), "Guardián del huerto" (20), "Talento reconocido" (primer talento certificado). Se evalúan automáticamente en dos puntos del sistema: al completar una actividad del calendario (`panel/calendar.py:completar`) y al certificar un talento desde el admin (`comunidades/admin.py:certificar`). Una vez obtenida, una insignia no se vuelve a evaluar ni se puede perder.
- **Misiones**: retos con meta de actividades a completar dentro de un rango de fechas y una recompensa en puntos, gestionados por el equipo desde el admin de Django (catálogo de contenido, no moderación de datos de usuario — por eso usa `ModelAdmin` normal en vez del patrón `SoloLectura`). El cumplimiento se evalúa en vivo (no se guarda un estado "completada" aparte): si las actividades completadas de un miembro dentro del rango de la misión alcanzan la meta, la recompensa se suma a sus puntos.
- `gestionar_miembros.html` ahora muestra puntos, nivel e insignias de cada miembro aprobado, visible para el responsable de la comunidad.

## Archivos
- `comunidades/gamificacion.py`: constantes de puntos, catálogo `INSIGNIAS`, `calcular_puntos`, `evaluar_insignias`, `misiones_completadas`.
- `comunidades/models.py`: `Miembro.puntos`/`nivel` reales, `Miembro.insignias`; `Comunidad.puntos`; modelos `InsigniaObtenida` y `Mision`.
- `comunidades/admin.py`: `InsigniaObtenidaAdmin` (solo lectura), `MisionAdmin` (CRUD normal); acción `certificar` ahora también evalúa insignias.
- `panel/calendar.py`: `completar` evalúa insignias al marcar una actividad como hecha.
- `comunidades/views.py` / `urls.py`: vista y ruta `ranking`.
- `templates/comunidades/ranking.html`, `templates/comunidades/detalle.html` (puntos + enlace al ranking), `templates/comunidades/gestionar_miembros.html` (puntos/nivel/insignias por miembro).
- `comunidades/test_gamificacion.py`: cálculo de puntos, umbrales de nivel, insignias otorgadas por completar actividad y por certificar talento, recompensa de misión, orden del ranking.

## Migración
`comunidades/migrations/0006_mision_insigniaobtenida.py` — crea `Mision` e `InsigniaObtenida`. No modifica datos existentes; `Miembro`/`Comunidad` no cambian de esquema porque `puntos`/`nivel` siguen siendo propiedades, no columnas.

## Verificación
- `pytest -q` completo del proyecto: 128 pruebas aprobadas (incluye las 5 nuevas de gamificación).
- Navegador con cuenta de prueba real: completé una actividad de riego desde el calendario → el ranking mostró "5 puntos" para la comunidad de inmediato; repetí la comprobación vía `curl` tras reiniciar el servidor de desarrollo (para descartar un falso negativo por autoreload) y la insignia "Primeros pasos" quedó registrada correctamente en la base de datos.
- Datos y cuenta de prueba eliminados al terminar.

## Cierre del plan
Con esta fase quedan implementadas las seis fases acordadas (F, A, C, B, D, E). El sistema ahora cubre, además de lo ya construido (foro, huerto virtual educativo con XP y niveles de aprendizaje), la capa comunitaria y agronómica del enunciado del MSP: miembros reales con datos demográficos y talentos certificados, huerto real estructurado con bodega, catálogo de plantas con clasificación tradicional sustentada en fuentes, actividades según calendario lunar con empaquetado y etiquetado, y gamificación entre comunidades con ranking, insignias y misiones.
