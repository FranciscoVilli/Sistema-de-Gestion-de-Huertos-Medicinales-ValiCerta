# Revisión institucional de la interfaz

Fecha: 20 de octubre de 2026. Alcance: portal público y pantallas existentes de participantes; el administrador interno de Django conserva su interfaz nativa. No se atribuye el sitio al MSP: sigue identificado como proyecto académico.

## Criterio visual

Navegación verde compartida, superficies claras, tipografía sin adornos, títulos directos y controles identificados mediante texto. Se revisaron inicio, guías, acerca del proyecto, bitácora de prueba, aprendizaje, lecciones, fichas, laboratorio, acceso, registro, verificación y recuperación, perfil y gestión de correo, contraseña y seguridad. Las páginas de error habituales tienen mensajes en español y regreso al inicio. Se corrigió el contenido desactualizado que anunciaba el laboratorio como no disponible.

Lupo se conserva como facilitador educativo adulto, con una ilustración SVG original del proyecto (facilitador.svg), sin símbolos oficiales. Aparece en lugares de orientación, no como una interrupción permanente. La guía del laboratorio es opcional, presenta un paso cada vez, mantiene el control señalado con un número y ofrece anterior, siguiente, repetir, salir y Escape. No avanza sola ni exige controlar un personaje con el teclado. Se conserva la opción del sistema de reducir movimiento.

## Lectura e interacción

Se añadió Aumentar texto / Restablecer texto. Esta preferencia se guarda únicamente en localStorage del navegador y no contiene datos personales. El zoom del navegador sigue disponible. Se ampliaron textos de formularios e instrucciones, tamaños de interacción y estilos de foco. La guía posiciona el objetivo en el espacio libre para que sus instrucciones no lo cubran. El retrato del facilitador permanece visible también con lectura ampliada. Se corrigió un desbordamiento del plan de aprendizaje a 320 px con texto ampliado.

La escena pixelada se reemplazó por una ilustración original Canvas de campo, con paleta moderada y superficies suaves. No cambian las reglas del modelo, los XP, los niveles ni los desbloqueos. Se mantienen los límites didácticos: sin calibración por especie, sin diagnóstico y sin persistencia de ensayos.

## Verificación

- 36 pruebas Django aprobadas.
- 12 comprobaciones del modelo de simulación aprobadas.
- 19 rutas comprobadas en 1440, 390 y 320 px: 57 casos de pantalla. Respuestas 200, un título principal, sin desbordamiento horizontal, lectura ampliada y preferencia persistente tras recargar.
- Guía de 10 pasos con texto ampliado, avatar visible, siembra durante la guía, finalización, reinicio de recorrido, cierre con Escape y menú móvil comprobados.
- Mostrar/ocultar contraseña; validación, guardado, recuperación y borrado del borrador de bitácora; página no encontrada comprobados en navegador.
- Sin errores JavaScript durante la revisión. Evidencias seleccionadas en pruebas/evidencias/frontend/revision-institucional, fuera del código de la aplicación.

Estas comprobaciones no certifican accesibilidad ni comprensión por edad. Pendiente validación con participantes de distintas edades, incluidas personas de 65 a 75 años, usando tareas: encontrar una guía, ingresar, sembrar en el laboratorio, interpretar la humedad y volver al paso anterior. Registrar ayudas necesarias, errores y comprensión de las instrucciones. No se implementaron funciones pendientes como mapa, foro o ayudas económicas.

Decisión posterior del usuario: se retira el control Aumentar texto y su script de preferencias. Se conservan el tamaño legible del diseño y el zoom del navegador. Las pruebas anteriores de lectura ampliada describen la revisión previa, no una función actualmente disponible. Inicio verificado sin el botón ni su script.

Identidad botánica recuperada por solicitud del usuario: portada verde profundo, tarjetas verdes, botones verde claro y fotografía botánica. Las áreas de lectura y formularios conservan superficies claras. Estilo limitado a home-green para compartir navegación y tipografía. Portada comprobada a 1440/390/320 px sin desbordamientos ni errores JavaScript.
