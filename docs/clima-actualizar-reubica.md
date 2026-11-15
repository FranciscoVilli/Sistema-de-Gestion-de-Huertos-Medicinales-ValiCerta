# "Actualizar" clima vuelve a ubicar si el jardín usa geolocalización

Implementado el 15 de noviembre de 2026, a pedido del usuario: "Actualizar" solo volvía a pedir el pronóstico para las mismas coordenadas guardadas, sin consultar dónde está el dispositivo ahora.

## Comportamiento

- Si la ubicación del jardín se guardó por geolocalización (botón "⌖ Usar mi ubicación"), al pulsar "↻ Actualizar" el widget primero vuelve a pedir la ubicación del navegador y la guarda, y **después** trae el clima. Así el jardín queda al día si el dispositivo está en otro lugar.
- Si la ubicación se guardó buscando una ciudad manualmente (el buscador del widget completo), "Actualizar" sigue haciendo solo lo de antes: refrescar el pronóstico para esa misma localidad. No se sobreescribe una elección manual con la posición GPS del dispositivo sin que el usuario lo pida explícitamente (para eso sigue estando el botón de geolocalización, cuando es visible).
- Si la re-geolocalización falla (permiso denegado, sin HTTPS, timeout), se ignora en silencio y igual se refresca el clima con la última ubicación conocida — "Actualizar" nunca debe fallar ruidosamente solo por esto.

## Archivos
- `panel/weather.py`: el GET de `garden_weather` ahora incluye `source` (`'browser'` o `'manual'`, según `garden.clima.get('source')`).
- `static/js/garden-weather.js`: la lógica de pedir y guardar la geolocalización se separó a `geolocateAndSave()`, reutilizada por el botón "Usar mi ubicación" (con mensajes de error) y por "Actualizar" (en silencio, solo si `source === 'browser'`). De paso se corrigió un `settings`/`select` sin verificar null en el formulario de guardado manual (solo relevante en el widget compacto, donde esos elementos no existen).
- `panel/test_weather.py`: `test_config` y `test_geolocation` ahora verifican el campo `source` en la respuesta.

## Investigación previa
Se reprodujo en local (cuenta y jardín de prueba, borrados al terminar) que el botón "Usar mi ubicación" sí aparece cuando el jardín no tiene ubicación guardada y se oculta solo al guardarla — comportamiento ya correcto, documentado como respuesta a una duda del usuario antes de este cambio. El pedido real era que "Actualizar" hiciera más que solo refrescar.

## Verificación
Probado en local con un jardín de prueba: se simuló `navigator.geolocation.getCurrentPosition` para evitar el permiso real del navegador durante la prueba automatizada, se confirmó que un clic en "Actualizar" con `source=browser` actualiza `Jardin.clima` a las nuevas coordenadas. No se ejecutó la suite completa de pytest (se agregaron aserciones nuevas a `test_weather.py` pero no se corrieron en Docker).
