# Entrada botánica versión 2

Se rediseñaron la portada y el acceso con las referencias proporcionadas el 20 de octubre de 2026: verde bosque oscuro, plantas protagonistas y contraste claro. La ruta actual sigue siendo una demostración; niveles y puntos no son definitivos. Se conserva contenido público sin cuenta. /mi-aprendizaje/ exige autenticación y presenta explícitamente el recorrido de ejemplo. El CTA de portada pasa next a django-allauth para llegar a esa ruta después del acceso.

La simulación educativa con interacción sobre agua, suelo y luz, el desbloqueo de plantas por logros y el mapa comunitario son dirección de producto, no funciones implementadas en este cambio. El mapa debe representar comunidades o huertos que acepten visibilidad, no sesiones de usuario ni domicilios publicados automáticamente. No se implementaron recompensas económicas ni promesas de beneficios médicos.

El login usa la vista, CSRF y validación reales de django-allauth. Hay control accesible para mostrar/ocultar la contraseña. La verificación de correo se conserva; en desarrollo los mensajes se imprimen en consola.

Imagen: generada con la herramienta integrada image_gen y copiada al proyecto como huertos_medicinales/static/images/huertos/botanica-hero-v2.png. Es una composición decorativa, no una guía botánica ni un modelo de cómo cultivar.

Prompt utilizado: Create one premium botanical website hero photograph, landscape 1536x1024 composition. Dark forest green almost black seamless studio background, rich realistic fresh mint plant and small chamomile flowers in an earthy handmade terracotta pot, pot placed in RIGHT half under a delicate open glass bell jar on a round dark stone pedestal, soft shafts of natural light from upper right, atmospheric leafy branches framing top and far right, elegant Ecuador community medicinal garden educational website mood, cinematic product botanical photography, subtly warm lime highlights, tactile real leaf veins. LEFT HALF mostly quiet near-black forest green negative space for website HTML text overlay. No text, no lettering, no logos, no UI elements. Natural botany, calm sophisticated, not a game screenshot.

Verificación: 24 pruebas aprobadas, incluidas cuatro del acceso; nueve comprobaciones de portada/login/registro a 1440, 390 y 320 px; sin errores JavaScript ni desbordamiento horizontal. Se probaron mostrar/ocultar contraseña, redirección anónima, preservación de next y menú móvil. LOGIN_REDIRECT_URL dirige al recorrido protegido; este sigue identificado como demostración.
