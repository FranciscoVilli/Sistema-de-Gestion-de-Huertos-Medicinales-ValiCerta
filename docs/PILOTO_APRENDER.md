# Informe de implementación — piloto educativo

Fecha: 28 de octubre de 2026 (America/Guayaquil).

## Alcance entregado

Primera implementación funcional del documento maestro, dentro del proyecto existente. Incluye la estructura de la fase 1 y el corte vertical de las fases 2 y 3 requerido para validar el piloto. No equivale a haber terminado las seis fases del producto.

## Diagnóstico comprobado

- Backend: Python 3.14, Django 6.0.9; PostgreSQL local mediante Docker.
- Frontend: plantillas Django, CSS y JavaScript existentes; no hay React ni motor 3D.
- Autenticación: usuario propio y django-allauth. Administración con permisos Django; participantes no pueden editar contenido oficial. Seguimiento tiene permisos específicos para acompañar y adelantar tiempo.
- Inicio: jardines persistentes de seis posiciones y referencias visuales por especie. El crecimiento mostrado es una estimación temporal, no una observación confirmada.
- Mis cultivos: Practica, Observacion (incluye fotos), EventoPractica y Devolucion; propiedad por participante e historial preservado.
- Calendario: ActividadCalendario asociada a un cultivo. Programar y marcar una actividad no fabrica una observación o foto.
- Formación anterior: seis lecciones y cuatro especies en catalogo.py; Logro conserva XP e IntentoEvaluacion conserva respuestas/versiones. Continúa disponible como recorrido anterior.
- Pruebas: pytest/pytest-django y controles de autenticación, CSRF, propiedad y operaciones transaccionales.

## Decisiones y compatibilidad

1. Se reutiliza la aplicación aprendizaje y la barra lateral actual. Los nuevos modelos conviven con los anteriores; no se convierte XP antiguo en competencias nuevas sin evaluación.
2. Se crea la estructura de seis bloques y 24 capítulos. Únicamente el capítulo 5 contiene material piloto. Los demás aparecen en preparación y sus páginas no son accesibles como contenido publicado.
3. El contenido del piloto está en PostgreSQL, administrable; no está escrito en las plantillas. El comando de carga inicial es idempotente y no sobrescribe las ediciones existentes.
4. Secciones y preguntas usan JSON validado como representación inicial. No se duplica el catálogo de especies: las rutas referencian sus identificadores existentes. La normalización futura de especies/preguntas debe conservar identificadores e historial.
5. Registrar cultivos reales y consultar fichas botánicas ya no depende de XP. Las rutas guiadas tienen requisitos separados por competencias.
6. La ruta de ejemplo de manzanilla solo cubre observación inicial de un recipiente. No se presenta como formación completa de la especie, simulador ni certificación.

## Flujo piloto implementado

- Fundamentos → Condiciones para cultivar → Suelos y sustratos.
- Tres lecciones: funciones del sustrato; suelo de jardín y mezcla para maceta; revisión del recipiente y drenaje.
- Lectura por secciones. Guardado explícito en POST; abrir páginas no completa una lección.
- Comprensión obligatoria por lección, comprobada en servidor.
- Evaluación con selección única, múltiple y verdadero/falso. Orden de preguntas aleatorio por intento; opciones conservan orden. Umbral configurable (piloto 80%).
- El intento captura el banco, umbral, competencias y versiones de lección. El servidor calcula el resultado, permite reintentos y preserva intentos finalizados.
- Competencia adquirida con fecha e intento de origen. Requisitos de ruta calculados a partir de competencias; auditoría de desbloqueo y fecha de inicio.
- Una ruta iniciada no se marca automáticamente como completada ni crea una siembra o bitácora ficticia.
- Una nueva edición de lección genera versión/historial y conserva el progreso anterior. Los intentos abiertos obsoletos requieren reiniciarse; los finalizados permanecen.

## Administración

En el administrador existente, sección Aprendizaje:

- Bloques, capítulos, fuentes, lecciones, competencias, evaluaciones y rutas son editables según permisos asignados.
- Borrador, piloto, publicado y archivado son estados editoriales separados.
- Para publicar/habilitar una lección se exigen secciones válidas, comprensión, fecha de revisión y al menos una fuente en el formulario administrativo.
- Las revisiones guardan contenido y autor administrativo. Progreso, intentos, competencias adquiridas y desbloqueos son de solo lectura en el administrador.
- El editor JSON es funcional para este piloto; falta un editor visual amigable para una administración editorial extensa.

## Archivos creados

Todos relativos a la raíz aplicacion:

- huertos_medicinales/aprendizaje/educational_models.py
- huertos_medicinales/aprendizaje/educational_services.py
- huertos_medicinales/aprendizaje/educational_views.py
- huertos_medicinales/aprendizaje/educational_admin.py
- huertos_medicinales/aprendizaje/management/__init__.py
- huertos_medicinales/aprendizaje/management/commands/__init__.py
- huertos_medicinales/aprendizaje/management/commands/seed_education_pilot.py
- huertos_medicinales/aprendizaje/test_pilot.py
- huertos_medicinales/templates/aprendizaje/pilot_catalog.html
- huertos_medicinales/templates/aprendizaje/pilot_chapter.html
- huertos_medicinales/templates/aprendizaje/pilot_lesson.html
- huertos_medicinales/templates/aprendizaje/pilot_question.html
- huertos_medicinales/templates/aprendizaje/pilot_assessment.html
- huertos_medicinales/templates/aprendizaje/pilot_result.html
- huertos_medicinales/templates/aprendizaje/pilot_progress.html
- huertos_medicinales/templates/aprendizaje/pilot_route.html
- huertos_medicinales/static/css/educacion.css
- docs/PILOTO_APRENDER.md (este informe)

## Archivos modificados

- config/urls.py: rutas del currículo, lector, evaluación, resultado, competencias y actividad guiada.
- aprendizaje/models.py y admin.py: registro de modelos y administración del currículo.
- aprendizaje/views.py: las fichas botánicas se pueden consultar sin XP.
- templates/pages/learning.html: acceso integrado al piloto y catálogo; recorrido anterior preservado.
- templates/pages/plant.html: información disponible independientemente del progreso.
- seguimiento/views.py y forms.py: cultivos reales independientes de requisitos educativos; edición conserva especies históricas.
- aprendizaje/tests.py, seguimiento/tests.py, panel/test_gardens.py: nueva política explícita de cultivos e información accesible.

## Migraciones aplicadas

- aprendizaje/0003_bloqueeducativo_competencia_fuenteeducativa_and_more.py: tablas educativas, relaciones, unicidad por usuario/versión y restricciones de umbral.
- aprendizaje/0004_alter_evaluacioneducativa_preguntas_and_more.py: permite JSON vacío en borradores; validación estricta al publicar/habilitar.

Ninguna elimina ni sobrescribe registros de cultivos, observaciones, XP o intentos anteriores.

## Pruebas y comprobaciones

Comando:

    python -m pytest huertos_medicinales/aprendizaje huertos_medicinales/seguimiento huertos_medicinales/panel -q

Resultado: 41 pruebas aprobadas. Incluyen carga idempotente, privacidad entre cuentas, lectura/comprensión obligatoria, respuestas manipuladas, reintentos, resultados inmutables, competencia, desbloqueo, requisitos cambiantes, versiones, formularios editoriales, creación administrativa real y registro de cultivos sin requisitos.

Django check: sin errores. Migraciones aplicadas.
Revisión visual de plantillas renderizadas por Django con cuenta temporal dentro de una transacción revertida. Capítulo en escritorio y lector móvil de 390 px: sin desbordamiento horizontal. Las mutaciones funcionales se verificaron con cliente de pruebas Django; no se modificó el progreso de un usuario real para tomar las capturas.

## Fuentes documentales del piloto

Consultadas el 28/10/2026. Contenido breve, para revisar en contexto local; no prescribe mezclas por especie ni dosis/beneficios medicinales.

- University of Maryland Extension: https://extension.umd.edu/resource/growing-media-potting-soil-containers
- Iowa State University Extension: https://yardandgarden.extension.iastate.edu/faq/i-would-grow-few-vegetables-containers-can-i-use-garden-soil-or-should-i-purchase-commercial
- University of Illinois Extension: https://extension.illinois.edu/houseplants/get-started

## Próximas fases y pendientes explícitos

- Validación pedagógica/agronómica del piloto y ampliación editorial de los otros 23 capítulos.
- Migrar gradualmente el recorrido anterior a contenido administrable, sin perder XP/historial.
- Niveles configurables, diagnóstico inicial opcional y más competencias/rutas completas por especie.
- Ordenamiento, relaciones, identificación visual y bancos ampliados; preguntas normalizadas/editor visual.
- Recursos multimedia, glosario y biblioteca administrable.
- Insignias configurables y criterios de finalización práctica basados en evidencia real.
- Relaciones formales de actividades educativas con calendario y bitácoras; por ahora se ofrecen enlaces contextuales y no se crean riegos automáticos.
- Simulaciones 2D diferenciadas de registros reales y estimaciones. No se ha añadido un motor 3D.
- Estadísticas educativas avanzadas y evaluación integral de accesibilidad/rendimiento.

## Riesgos técnicos y límites

- Catálogo de especies anterior sigue definido en código; las nuevas rutas usan esos slugs, sin nuevas especies duplicadas.
- Bancos y secciones JSON son apropiados para validar el piloto, pero un catálogo grande requerirá edición visual y/o normalización.
- Las consultas de elegibilidad priorizan claridad en este piloto; conviene agruparlas cuando haya muchas lecciones/rutas.
- Las competencias ya obtenidas son hechos históricos. Si cambian los requisitos, se recalcula el acceso; una nueva edición de contenido no revoca por sí sola competencias antiguas.
- Los contenidos del piloto no han recibido una revisión humana local especializada; están identificados como piloto revisable.

## Cómo revisar

1. Abrir /mi-aprendizaje/ e ingresar al piloto de Suelos y sustratos.
2. Leer cada sección, guardar y responder la comprensión de las tres lecciones.
3. Iniciar y enviar la evaluación. Ver resultado y competencia.
4. Abrir Mis competencias, revisar requisitos y comenzar la actividad guiada de manzanilla.
5. Comprobar que Mis cultivos sigue permitiendo registrar plantas sin completar este recorrido.
