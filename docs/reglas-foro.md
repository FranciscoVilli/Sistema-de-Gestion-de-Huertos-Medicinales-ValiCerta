# Reglas de participación del foro

Implementado el 8 de noviembre de 2026, como parte del cierre de brechas contra el enunciado oficial del proyecto (ISWD652).

## Pantallas y funciones
- Entrada: `/comunidades/reglas/`. Página pública (no requiere sesión), con el mismo diseño botánico crema/verde del resto de Comunidad y mapa.
- Cinco secciones fijas: respeto, qué compartir, qué evitar (domicilios, contacto, publicidad, afirmaciones de salud como certeza médica), moderación (qué hace y qué no hace: nunca reescribe autoría ni contenido), y recordatorio de que compartir perfil/jardín/contacto es independiente de participar en el foro.
- Enlazada desde el pie de página del hub (`/comunidades/`), junto a "Explorar iniciativas".
- Contenido estático; no introduce modelos ni formularios nuevos.

## Archivos
- `comunidades/community.py`: vista `reglas`.
- `comunidades/urls.py`: ruta `reglas/`.
- `templates/comunidades/reglas.html`: contenido, extiende `comunidades/community_base.html`.
- `templates/comunidades/hub.html`: enlace añadido al pie de página.
- `comunidades/test_community.py`: prueba de la página y del enlace.

## Migración
Ninguna. No se tocaron modelos.

## Verificación
- `pytest -q` completo del proyecto: 106 pruebas aprobadas (incluye la nueva).
- Navegador: hub → clic en "Reglas de participación" → página carga con el mismo estilo de tarjetas, sin desborde horizontal, escritorio y con scroll a la última sección.
