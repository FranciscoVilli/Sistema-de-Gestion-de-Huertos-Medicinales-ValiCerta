# Revisión del diseño y navegación — 29/10/2026

Se sustituyó la base de sitio público anterior por la estructura de aplicación actual: fondo claro, tarjetas, botones verdes y menú lateral compartido. Los módulos conservan sus hojas específicas para el jardín, cultivos, aprendizaje y calendario.

## Cambios

- `templates/base.html` y `components/app_sidebar.html`: una estructura compartida, una región principal, menú activo por módulo, acceso a privacidad y enlaces de gestión según permisos.
- `producto/base.html`: elimina el segundo menú y la cabecera anterior. Afecta formularios de cultivos, bitácoras, acompañamiento, comunidades y solicitudes de privacidad.
- Inicio, Mis cultivos, organización del jardín, Aprender y Calendario heredan la misma base sin duplicar menús, mensajes ni iconos.
- Bitácora: resumen ilustrado y formulario en columnas en escritorio, disposición vertical en móvil; anclas Resumen, Registrar cuidado y Ver bitácora. Los cultivos finalizados enlazan al historial en lugar de un formulario inexistente.
- Fichas: ilustraciones botánicas de las especies y etiquetas interactivas conservadas. Enlaces de regreso actualizados a la pestaña actual de plantas.
- Cuenta, comunidades, guías, privacidad y páginas de error reciben la misma presentación. La guía y Acerca del sistema ya no anuncian el recorrido obsoleto de seis lecciones.
- Registro, recuperación y confirmaciones de acceso usan la base clara del login. Se normalizaron los campos que dependían del estilo anterior.
- Cookies: tarjeta integrada, sin panel superpuesto del diseño anterior. Las decisiones y el consentimiento para mapas siguen usando los mismos formularios y controles del servidor. El acceso a Configurar cookies permanece disponible.
- Administración: paleta coherente, identidad Huertos, enlace de regreso al huerto y corrección de títulos con caracteres corruptos. Mantiene las herramientas administrativas de Django.

## Archivos de estilos

`static/css/app-ui.css`, `cookies-ui.css`, `account-ui.css`, `admin-ui.css`.
La base activa ya no carga `huertos.css`, `campus.css`, `institucional.css`, `institucional-global.css`, `producto.css`, `privacidad.css` ni `interfaz.css`. Los archivos históricos permanecen en disco; no se borraron datos ni recursos necesarios para recuperar versiones anteriores.

## Validación

- 86 pruebas existentes de aprendizaje, seguimiento, panel, privacidad, comunidades y usuarios aprobadas tras la unificación.
- Tres nuevas pruebas de diseño/navegación aprobadas: estructura común y enlace de registro, acceso por permisos y diseño de recuperación de cuenta.
- Revisión final de 23 pruebas afectadas por los últimos ajustes: aprobadas.
- Django system check sin incidencias.
- 39 pantallas renderizadas y 57 enlaces internos revisados con cliente Django. Incluye administración y los estados de error esperados 403, 404 y 500.
- Chrome de prueba: 117 vistas (1366, 390 y 320 px), sin imágenes rotas, desbordamiento horizontal ni errores de JavaScript. Se inspeccionaron capturas de bitácora, formularios, cookies, fichas y recuperación.
- Las previsualizaciones usan datos temporales dentro de una transacción revertida. No se alteraron cuentas, cultivos, observaciones ni elecciones de privacidad reales.

## Pruebas añadidas y evidencia local

- `huertos_medicinales/panel/test_design.py`.
- `C:/Users/HOME/style-audit/routes.json` y `browser-results.json`.
- Capturas de revisión en `C:/Users/HOME/style-audit/`.
- Respaldos previos a cada cambio en `C:/Users/HOME/huertos-backups/` (directorios estilo-unificado, estilo-detalles, navegacion-roles y enlaces-finales).
