# Actividades según calendario lunar y ritual ancestral

Implementado el 8 de noviembre de 2026, como parte del cierre de brechas contra el enunciado oficial del proyecto (ISWD652).

## Pantallas y funciones
- El calendario de cultivo ahora incluye `siembra`, `preparación de la tierra`, `deshierbe y aporque`, `secado` y `empaquetado` como tipos de actividad, además de los que ya existían (riego, revisión, foto, poda, cosecha, otro).
- Al registrar una **siembra** se puede indicar la técnica (surcos, andenes o terrazas) y el tipo de propagación (semilla, estaca, esqueje o plántula). Al registrar una **cosecha** se puede indicar qué parte se va a usar (hojas/flores/frutos o semillas/raíces) — campos opcionales, visibles siempre pero solo relevantes para esos tipos.
- El formulario de actividad muestra un aviso **no bloqueante** con la fase lunar de la fecha elegida y si coincide con lo recomendado: preparación de tierra en luna nueva, siembra en luna creciente o llena, cosecha de hojas/flores/frutos en creciente o llena, cosecha de semillas/raíces en cuarto menguante. El aviso nunca impide guardar la actividad.
- Señalética: la ficha de cada planta (educativa, en el huerto virtual y en el nuevo formulario de empaquetado) muestra una insignia de color junto al nombre — roja para "caliente", verde para "fría" — según la clasificación tradicional ya documentada en la Fase C, siguiendo la convención del documento del MSP (rojo = calor, verde/blanco = frío, según los pueblos kichwas andinos).
- Nuevo registro de **empaquetado y etiquetado** por práctica (`/mis-practicas/<id>/empaquetar/`): peso (100 g por defecto), indicaciones de uso, dosificación, contraindicaciones, región de almacenaje y fecha de empaquetado. La fecha de caducidad se calcula sola: 12 meses en la Sierra, 6 meses en Costa o Amazonía. La pantalla muestra también el nombre científico, la familia botánica y la cualidad caliente/fría ya conocidas del catálogo, para no tener que volver a escribirlas.
- Historia visual: además de la foto ya existente, cada observación de la bitácora acepta un enlace a video opcional, mostrado como enlace reproducible.

## Investigación previa (reutilizada de la Fase C)
Durante la Fase C se leyó el documento oficial citado en el propio enunciado — MSP Ecuador (2017), *Implementación de huertos medicinales...* — y se encontraron ahí mismo las reglas exactas usadas en esta fase: la tabla de señalética con los colores caliente/fría (p. 46), la fórmula de ciclo corto/largo (p. 49), y el contenido completo de la etiqueta de empaquetado junto con la caducidad por región (p. 50-51). Esta fase conecta esos datos con el calendario real del sistema.

## Archivos
- `seguimiento/models.py`: `ActividadCalendario` ampliado (tipos, `tecnica`, `propagacion`, `parte_usada`); `Empaquetado` (nuevo modelo); `Observacion.video_url`.
- `panel/lunar.py`: función `recomendacion(tipo, fecha, parte_usada)`.
- `panel/calendar.py`: `ActividadForm` ampliado; vista `nueva` calcula la recomendación lunar para mostrarla.
- `templates/panel/calendario_form.html`: aviso lunar.
- `static/css/calendario-botanico.css`: estilos `lunar-ideal` / `lunar-alerta`.
- `seguimiento/forms.py`: `EmpaquetadoForm`; `ObservacionForm` incluye `video_url`.
- `seguimiento/views.py`: vista `empaquetar`.
- `templates/seguimiento/empaquetar.html`, `templates/seguimiento/detalle.html`, `templates/seguimiento/historial.html`.
- `templates/pages/plant.html`, `templates/panel/planta_detalle.html`: insignia de señalética (reutiliza `.badge-caliente`/`.badge-fria` de la Fase C).
- `panel/test_lunar.py`, `panel/test_calendar.py`, `seguimiento/test_empaquetado.py`.

## Migración
`seguimiento/migrations/0006_actividadcalendario_parte_usada_and_more.py` — agrega campos a `ActividadCalendario` y `Observacion`, crea `Empaquetado`. No modifica datos existentes (los tipos de actividad ya guardados siguen siendo válidos).

## Verificación
- `pytest -q` completo del proyecto: 123 pruebas aprobadas.
- Navegador: siembra de Romero programada el 24 de noviembre de 2026 (luna llena) mostró el aviso en verde "esta fecha coincide con lo recomendado"; la misma actividad editada al 1 de noviembre (cuarto menguante) mostró el aviso en naranja, no bloqueante. Insignia "● Caliente" visible en la ficha del huerto virtual. Empaquetado de Romero registrado con fecha 10/01/2026 en Sierra calculó correctamente la caducidad al 10/01/2027.
- Se detectó en el camino que el formulario de edición de actividades ya precargaba la fecha de hoy cuando se abre sin el parámetro `?dia=` (comportamiento previo a esta fase, no introducido aquí) — se documenta como nota para quien use el aviso lunar: hay que llegar al formulario de edición haciendo clic desde el día real en el calendario, no por URL directa sin ese parámetro.
- Datos de prueba creados en la cuenta de demostración eliminados al terminar.
