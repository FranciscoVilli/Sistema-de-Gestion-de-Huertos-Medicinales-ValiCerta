# Comunidad y mapa

Implementado el 7 de noviembre de 2026.

## Pantallas y funciones
- Entrada: /comunidades/. Diseño botánico crema, verde y morado, foro y mapa 40/60 en escritorio; pestañas en móvil.
- Preguntas con categorías, búsqueda, recientes, orden por cantidad de respuestas y paginación de seis preguntas.
- Crear, editar, responder, marcar resuelta/reabrir y retirar publicaciones mediante modales. Rutas completas disponibles como alternativa.
- Respuestas paginadas; detección de duplicados normalizados, validación de texto y escape HTML. Solo autor o permiso administrativo de cambio puede modificar publicaciones.
- Perfil público optativo: alias, avatar de iniciales, nivel y años declarados, localidad, experiencia, preguntas y respuestas recientes. No usa correo ni nombre privado como alias automático.
- Compartir jardines existentes: consentimiento independiente del clima, sector y coordenadas con dos decimales. Solo perfiles activos y públicos con jardín autorizado aparecen en la API y el mapa. Plantas obtenidas de cultivos activos existentes.
- Leaflet existente + OpenStreetMap; límites ajustados a registros, marcadores agrupados por proximidad visual, popup y perfil. Actualización manual y cada minuto mientras la página está visible. Lista alternativa de jardines.
- Estadísticas calculadas desde registros visibles. Miembros destacados ordenados por respuestas compartidas. No se insertaron publicaciones o perfiles de demostración en producción.
- El directorio anterior conserva solicitudes, revisión, mapa y retirada en /comunidades/iniciativas/.
- Administración: consultas de perfiles/jardines en modo lectura; moderación de preguntas/respuestas con permiso de cambio. No permite conceder consentimiento de publicación desde administración.

## Archivos
- comunidades/models.py: PerfilComunitario, JardinCompartido, Pregunta, Respuesta.
- comunidades/community.py: vistas, privacidad, API y consultas.
- comunidades/community_forms.py: formularios y validación.
- comunidades/urls.py y admin.py: rutas y moderación.
- comunidades/migrations/0003_jardincompartido_perfilcomunitario_pregunta_and_more.py.
- templates/comunidades/community_base.html, hub.html, modal.html, modal_fragment.html, form_content.html, question_content.html, profile_content.html.
- static/css/community.css y static/js/community.js.
- comunidades/test_community.py y tests.py (la comprobación del mapa anterior utiliza ahora la ruta iniciativas).

## Migración
La migración 0003 ya fue aplicada a la base local. En otra instalación, ejecutar `python manage.py migrate` con la configuración de ese entorno. No modifica ni elimina usuarios, cultivos o comunidades anteriores.

## Verificación
- Django check sin errores.
- 10 pruebas aprobadas: publicación, edición no autorizada, respuestas duplicadas, búsqueda, orden, paginación, escape de contenido, consentimiento, perfiles, retirada y flujo anterior.
- 35 vistas en 1672, 1366, 768, 390 y 320 px, sin desbordamiento horizontal ni errores JavaScript.
- Navegador: ventanas, cierre Escape, popup, perfil y pestaña móvil; carga real de teselas de OpenStreetMap.
- Datos de revisión creados dentro de una transacción revertida; no permanecen en la base.

## Fuentes técnicas
- Leaflet: https://leafletjs.com/reference
- OpenStreetMap: https://operations.osmfoundation.org/policies/tiles/

El mapa externo requiere el consentimiento ya existente del sistema y conexión a Internet. La ubicación meteorológica no se publica automáticamente.
