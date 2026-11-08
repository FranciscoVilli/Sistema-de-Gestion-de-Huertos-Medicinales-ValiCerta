# Catálogo de plantas enriquecido

Implementado el 8 de noviembre de 2026, como parte del cierre de brechas contra el enunciado oficial del proyecto (ISWD652).

## Pantallas y funciones
- La ficha de cada planta (`/mi-aprendizaje/planta/<slug>/`, disponible sin requisito de XP) ahora muestra: familia botánica, otros nombres (cuando hay fuente), ciclo corto/largo con los días de madurez que lo sustentan, distribución recomendada en Ecuador con sus provincias cuando está documentada, y la clasificación tradicional caliente/fría con una insignia de color (roja para caliente, verde para fría) y su fuente.
- **Ciclo** no se guarda por planta: se deriva de `dias_madurez` (ya citado) contra un umbral de 63 días, calibrado con los ejemplos explícitos del documento del MSP ("ciclo corto" ≈ 6-8 semanas: lavanda, salvia, menta, ortiga, manzanilla; "ciclo largo": cedrón, romero, laurel, marco). Así una planta nueva no necesita una fuente adicional solo para esto.
- **Distribución** (provincias de la Sierra) y **clasificación caliente/fría** solo se completan cuando hay una fuente que las confirma explícitamente para esa especie. Investigué el documento oficial citado en el propio enunciado — MSP Ecuador (2017), *Implementación de huertos medicinales...* — y encontré ahí mismo la tabla "Plantas calientes / Plantas frescas" (Cachiguango, 2012, DNSI 2016, p. 73-74) y la recomendación explícita de especies para huertos de la Sierra (p. 20).
  - Manzanilla, menta (citada como "hierba buena y menta") y romero: documentadas como **calientes** y recomendadas para huertos de la Sierra.
  - Caléndula: no aparece en ese documento ni en otra fuente que haya podido confirmar. Su clasificación queda vacía y la ficha muestra "No documentada para esta especie" en vez de asumir un valor.
- La misma investigación confirmó, de paso, el diseño ya planeado para la señalética de la Fase D (rojo = caliente, verde/blanco = frío, según los pueblos kichwas andinos, p. 46) y los datos exactos del etiquetado de empaquetado (familia, peso, dosificación, contraindicación, fechas, cualidad caliente/fría; caducidad: 6 meses en Costa/Amazonía, 12 meses en Sierra, p. 50-51) — quedan documentados aquí para reutilizarse cuando se implemente esa fase.

## Archivos
- `aprendizaje/catalogo.py`: nuevos campos por planta (`otros_nombres`, `familia_botanica`, `provincias`, `fuente_distribucion_nombre/url`, `temperatura`, `fuente_temperatura_nombre/url`) y la función `ciclo()` + constante `UMBRAL_CICLO_CORTO_DIAS`, aplicada a cada entrada de `PLANTAS` tras definirla.
- `templates/pages/plant.html`: sección "Sobre esta planta" ampliada con los datos nuevos y sus fuentes.
- `static/css/ficha-planta.css`: `.badge-caliente` / `.badge-fria`.
- `aprendizaje/test_catalogo.py`: integridad de los datos (toda planta con `temperatura` o `provincias` trae su fuente; nunca una sin la otra), clasificación esperada de las 4 plantas, y que la ficha renderiza la insignia.

## Migración
Ninguna. `catalogo.py` sigue siendo datos en código, no tabla de base de datos — coherente con el diseño ya existente.

## Verificación
- `pytest -q` completo del proyecto: 113 pruebas aprobadas (incluye las 3 nuevas de catálogo).
- Navegador: ficha de Romero muestra familia, ciclo, provincias de la Sierra con fuente MSP, e insignia "● Planta caliente" con su fuente (Cachiguango/MSP). Ficha de Caléndula muestra los mismos campos generales pero sin distribución ni clasificación, con el aviso de "no documentada" en vez de un dato inventado.
- Cuenta de prueba eliminada al terminar.

## Fuentes técnicas
- Ministerio de Salud Pública del Ecuador (2017), *Implementación de huertos medicinales en los establecimientos de salud del primer nivel de atención. Lineamientos* — https://www.salud.gob.ec/wp-content/uploads/2022/09/MSP-Lineamientos-implementaci%D0%B2n-huertos-medicinales-PNA-2017-2.pdf (es la misma fuente [1] citada en el enunciado del proyecto).
- Cachiguango, Luis Enrique (2012), *Herbolaria simbólica andina*, Instituto Jatun Yachay Wasi, Colta, Chimborazo — citado dentro del documento anterior (p. 73-74, tabla de plantas calientes/frescas), elaborado por la DNSI en 2016.
