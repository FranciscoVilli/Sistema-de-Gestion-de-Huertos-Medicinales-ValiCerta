# Contenido de aprendizaje — 29 de octubre de 2026

## Resultado

Los seis módulos y sus 24 capítulos tienen contenido disponible. Se añadieron 24 lecciones de cuatro secciones (96 secciones nuevas), conservando las tres lecciones iniciales de Suelos y sustratos: 27 lecciones en total. Cada capítulo tiene evaluación. Se añadieron 72 preguntas; el capítulo 5 conserva también sus tres preguntas originales.

Cada lección nueva incorpora una imagen o esquema, exploración desplegable de conceptos, un caso con respuestas explicadas y una práctica de observación. El capítulo 11 incluye una calculadora de emergencia con validación. Los ejercicios de exploración no modifican cultivos ni otorgan aprobación: lectura y comprensión se guardan mediante los formularios existentes; las evaluaciones se corrigen en el servidor.

## Criterio editorial

Síntesis educativa original basada en fuentes primarias universitarias y NCCIH, con referencias y consulta documental del 29/10/2026. Las actividades y esquemas son originales. La revisión documental no equivale a revisión profesional agronómica local. No se trasladan temporadas del hemisferio norte a Ecuador ni se fijan dosis médicas, pesticidas o frecuencias universales. Se distingue tradición de evidencia, síntoma de diagnóstico y estimación virtual de observación física.

Las imágenes de especies son ilustraciones botánicas ya existentes, no fotografías del usuario. Se añadieron 21 esquemas SVG de conceptos. Las fotografías de la siembra real siguen siendo responsabilidad del registro del participante. Las fuentes externas conservan sus propios derechos; no se copiaron sus fotografías.

## Conservación del historial

El comando `seed_curriculum` es transaccional e idempotente: no reemplaza lecciones existentes, revisiones del editor ni progreso; tampoco reactiva capítulos archivados. Puede ejecutarse para instalar en otro entorno. Los nuevos contenidos quedan en la base de datos y se pueden editar desde la administración. Los cambios posteriores se realizan en la administración; modificar el JSON y repetir la carga no sobrescribe una edición existente.

La nueva lección de suelos amplía el recorrido: quien completó el piloto conserva su historial y puede completar el material añadido. Los intentos anteriores conservan su contenido, nota y competencias. El porcentaje general usa el nuevo total de lecciones.

## Archivos principales

- `huertos_medicinales/aprendizaje/data/curriculum.json`: contenido, casos y referencias.
- `huertos_medicinales/aprendizaje/management/commands/seed_curriculum.py`: carga conservadora.
- `huertos_medicinales/aprendizaje/test_curriculum.py`: cobertura, idempotencia y recorridos completos.
- `huertos_medicinales/templates/aprendizaje/pilot_lesson.html`: lector con imágenes y prácticas.
- `huertos_medicinales/templates/pages/learning.html` y `templates/aprendizaje/pilot_catalog.html`: presentación actualizada.
- `huertos_medicinales/static/css/educacion.css`, `static/js/education-practice.js`, `static/images/educacion/`: presentación y recursos.

## Verificación realizada

- Django check: sin incidencias.
- 37 pruebas de aprendizaje y seguimiento aprobadas.
- Las pruebas nuevas recorren los 24 capítulos, sus lecturas, comprensión, evaluaciones y resultados; verifican 100 % de avance y 25 competencias contando la del piloto.
- Idempotencia: no duplicación y conservación de ediciones y progreso.
- Chrome de prueba: 37 páginas renderizadas por Django en tres anchuras (1366, 390 y 320 px), 111 vistas sin desbordamiento ni imágenes rotas; teclado y calculadora comprobados. La cuenta y avances de previsualización se generaron dentro de una transacción revertida.
- Servidor real: HTTP 200 en vista previa de aprendizaje y nuevo SVG.

## Fuentes por capítulo

### Capítulo 1

- [NCCIH: Plantas: evidencia y seguridad](https://www.nccih.nih.gov/health/herbsataglance)
- [NCCIH: Manzanilla: evidencia y seguridad](https://www.nccih.nih.gov/health/chamomile)

### Capítulo 2

- [Oregon State University: Órganos vegetativos](https://extension.oregonstate.edu/catalog/em-9904-vegetative-plant-parts)
- [NC State Extension: Botánica](https://content.ces.ncsu.edu/extension-gardener-handbook/3-botany)

### Capítulo 3

- [Oregon State University: Ciclos anuales, bienales y perennes](https://extension.oregonstate.edu/catalog/em-9899-know-life-cycles-plants-annuals-biennials-perennials)

### Capítulo 4

- [NC State Extension: Cultivo en recipientes](https://content.ces.ncsu.edu/extension-gardener-handbook/18-plants-grown-in-containers)

### Capítulo 5

- [NC State Extension: Suelo y nutrientes](https://content.ces.ncsu.edu/extension-gardener-handbook/1-soils-and-plant-nutrients)

### Capítulo 6

- [NC State Extension: Suelo y nutrientes](https://content.ces.ncsu.edu/extension-gardener-handbook/1-soils-and-plant-nutrients)
- [NC State Extension: Compostaje](https://content.ces.ncsu.edu/extension-gardener-handbook/2-composting)

### Capítulo 7

- [Iowa State University: Cuidados de plantas en recipientes](https://yardandgarden.extension.iastate.edu/how-to/care-plants-growing-containers)

### Capítulo 8

- [NC State Extension: Botánica](https://content.ces.ncsu.edu/extension-gardener-handbook/3-botany)
- [Oregon State University: Factores ambientales del crecimiento](https://extension.oregonstate.edu/catalog/em-9903-environmental-factors-affecting-plant-growth)

### Capítulo 9

- [Oregon State University: Factores ambientales del crecimiento](https://extension.oregonstate.edu/catalog/em-9903-environmental-factors-affecting-plant-growth)

### Capítulo 10

- [University of Minnesota: Preparar jardín y recipientes](https://extension.umn.edu/about/our-stories/news/starting-your-garden-and-containers-off-right)
- [NC State Extension: Cultivo en recipientes](https://content.ces.ncsu.edu/extension-gardener-handbook/18-plants-grown-in-containers)

### Capítulo 11

- [University of Minnesota: Semilleros en interiores](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/starting-seeds-indoors)

### Capítulo 12

- [NC State Extension: Propagación vegetal](https://content.ces.ncsu.edu/extension-gardener-handbook/13-propagation)

### Capítulo 13

- [Clemson University: Preparar y trasplantar plántulas](https://hgic.clemson.edu/factsheet/starting-seeds-indoors/)
- [University of Minnesota: Semilleros en interiores](https://extension.umn.edu/garden-and-home/yard-and-garden/gardening-in-minnesota/starting-seeds-indoors)

### Capítulo 14

- [Iowa State University: Cultivar y mantener hierbas](https://yardandgarden.extension.iastate.edu/how-to/growing-harvesting-and-drying-herbs)

### Capítulo 15

- [University of Illinois: Luna y jardinería](https://extension.illinois.edu/blogs/garden-scoop/2022-04-16-lunar-influence-gardening)

### Capítulo 16

- [NC State Extension: Insectos y otros artrópodos](https://content.ces.ncsu.edu/extension-gardener-handbook/4-insects)

### Capítulo 17

- [NC State Extension: Enfermedades y trastornos](https://content.ces.ncsu.edu/extension-gardener-handbook/5-diseases-and-disorders)

### Capítulo 18

- [NC State Extension: Diagnóstico vegetal](https://content.ces.ncsu.edu/extension-gardener-handbook/7-diagnostics)

### Capítulo 19

- [NC State Extension: Manejo integrado de plagas](https://content.ces.ncsu.edu/extension-gardener-handbook/8-integrated-pest-management-ipm)

### Capítulo 20

- [Iowa State University: Cómo cosechar hierbas](https://yardandgarden.extension.iastate.edu/faq/how-do-i-harvest-herbs)

### Capítulo 21

- [University of Maryland: Cosecha y conservación de hierbas](https://extension.umd.edu/resource/harvesting-and-preserving-herbs)

### Capítulo 22

- [NCCIH: Uso responsable de suplementos](https://www.nccih.nih.gov/health/using-dietary-supplements-wisely)
- [NCCIH: Manzanilla: evidencia y seguridad](https://www.nccih.nih.gov/health/chamomile)

### Capítulo 23

- [NC State Extension: Jardinería orgánica](https://content.ces.ncsu.edu/extension-gardener-handbook/17-organic-gardening)
- [NC State Extension: Compostaje](https://content.ces.ncsu.edu/extension-gardener-handbook/2-composting)

### Capítulo 24

- [NC State Extension: Planificación y registros del huerto](https://content.ces.ncsu.edu/extension-gardener-handbook/16-vegetable-gardening)

