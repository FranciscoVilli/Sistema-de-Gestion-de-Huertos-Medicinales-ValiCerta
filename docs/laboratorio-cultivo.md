# Mi siembra (antes "Laboratorio de cultivo")

Desde 2026-10-21 se retiró el laboratorio ilustrativo (escena en Canvas, turnos ficticios, sin persistencia) y se reemplazó por un único registro real: **Mis prácticas** (`huertos_medicinales/seguimiento`). Ya no existe una ruta separada `/mi-huerto/laboratorio/`.

## Cómo funciona ahora

Una práctica (`Practica`) solo puede registrarse para una planta cuya ficha ya esté desbloqueada por XP (ver `aprendizaje/catalogo.py`). Manzanilla requiere 25 XP (la primera lección); antes se abría con 0 XP. El formulario de creación (`seguimiento/forms.py: PracticaForm`) limita la lista de plantas a las que el usuario ya desbloqueó, calculado en `seguimiento/views.py: plantas_disponibles()`.

La fecha de inicio (`Practica.inicio`) es real, capturada por el usuario. La etapa de crecimiento (`Practica.etapa`: semilla / creciendo / madura) se calcula comparando los días reales transcurridos desde esa fecha contra `dias_germinacion` y `dias_madurez` de la planta en el catálogo. Estos valores son rangos generales de fuentes de jardinería (The Old Farmer's Almanac, ver `fuente_tiempos_url` por planta), **no datos agronómicos validados para Ecuador**; no deben tratarse como una predicción exacta para una siembra concreta.

Cada observación (`Observacion`) puede incluir una foto opcional (`foto`, `ImageField`) como evidencia de la siembra física. Las fotos se guardan en `MEDIA_ROOT/seguimiento/fotos/%Y/%m/` y solo son visibles para el participante y los facilitadores autorizados, igual que el resto de la bitácora.

## Adelanto de tiempo para demostraciones

`Practica.dias_adelanto` es un contador de solo administración (no se expone en el formulario del participante). Se incrementa mediante la acción de Django Admin "Adelantar 7 días (demostraciones)" en `PracticaAdmin`, protegida por el permiso `seguimiento.avanzar_tiempo_practica`. Cada uso registra un `EventoPractica` con acción `adelanto_tiempo` para mantener el historial auditable. No modifica la fecha real de inicio ni las observaciones ya registradas; solo desplaza el cálculo de la etapa estimada.

## Pendiente

Revisión agronómica local de los tiempos de germinación y madurez; calendario estacional para Ecuador; validación de las fuentes de jardinería usadas como referencia; definición de un límite de tamaño/formato para las fotos subidas.
