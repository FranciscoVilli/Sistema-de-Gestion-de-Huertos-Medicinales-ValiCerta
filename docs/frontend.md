# Primera versión del frontend

Implementado en Django Templates, CSS y JavaScript, sin React ni dependencias visuales remotas.

## Pantallas

- `/`: inicio público con enlaces a guías, comunidad y cuentas.
- `/guias/primeros-pasos/`: guía introductoria de demostración, pendiente de revisión de contenido por especie.
- `/vista-previa/aprendizaje/`: progreso y retos de ejemplo; no calcula puntos reales.
- `/vista-previa/primera-siembra/`: formulario de borrador local de demostración.
- `/accounts/login/` y `/accounts/signup/`: cuentas de django-allauth con estilo integrado. El correo continúa en consola en desarrollo.

El borrador usa sessionStorage. No se envía a Django ni se vincula con una cuenta. La fotografía solo se previsualiza en memoria, no se sube ni se conserva al recargar. Hay validación de campos requeridos, fecha no futura, archivo de imagen JPG/PNG/WebP hasta 5 MB, contador de texto y confirmación de borrado. Estas validaciones deben repetirse en servidor al implementar persistencia real.

## Diseño y accesibilidad

Paleta verde bosque, crema y terracota; ilustraciones SVG originales; tipografía del sistema y Georgia, sin cargar fuentes externas. Adaptación a 1440, 390 y 320 píxeles, menú móvil con estado accesible y cierre con Escape, salto al contenido, foco visible, etiquetas de campos, mensajes de error y respeto a movimiento reducido. Esto no constituye una certificación WCAG.

Django Debug Toolbar se desactiva por defecto en local para no cubrir el diseño. Se puede habilitar con DJANGO_DEBUG_TOOLBAR=True.

## Verificación realizada

- Las 20 pruebas existentes pasan.
- Django check y Ruff sin errores.
- 18 comprobaciones de página: 6 rutas a 3 anchos, sin desbordamiento ni imágenes visibles rotas.
- Menú, cierre con Escape, enlaces, campos requeridos, fecha futura, guardado y recuperación de borrador, rechazo de archivo inválido y cancelación/confirmación de borrado comprobados en navegador.

## Pendiente

Reglas definitivas de niveles y puntos, almacenamiento de bitácora en servidor con permisos, contenidos revisados y módulos de comunidades. Foro y apoyos económicos no implementados. No se publicó el sistema ni se conectó con servicios gubernamentales.
