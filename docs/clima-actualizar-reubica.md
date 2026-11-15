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

## Actualización 2026-11-15 (misma tarde): "El servicio de clima no está disponible ahora"
El usuario reportó ver este mensaje en producción. `panel/weather.py` usaba `urllib.request.urlopen` para llamar a Open-Meteo/GeoNames, y las excepciones se tragaban en silencio (`except (OSError,ValueError,KeyError,TypeError,IndexError)` sin loguear nada) — no había manera de saber la causa real desde los logs de Render.

- La API de Open-Meteo responde bien desde fuera (probado con `curl` y con `fetch_json` directo en local); el problema más probable es que `urlopen` depende del almacén de certificados del sistema operativo del contenedor de Render, que puede no tener un bundle de CAs actualizado — un problema común en imágenes mínimas. `requests` (ya es dependencia del proyecto, agregada para Supabase Storage) trae su propio bundle vía `certifi` y evita ese problema.
- Cambio: `fetch_json()` ahora usa `requests.get(...).raise_for_status()` en vez de `urlopen`. `requests.exceptions.RequestException` hereda de `OSError`, así que lo sigue capturando el mismo `except` existente, sin tocar esa lista.
- Se agregó `logger.exception(...)` en los dos `except` (`places()` y `garden_weather()`) para que la próxima vez que esto falle, el traceback real quede en los logs de Render en vez de perderse.
- Verificado localmente con `fetch_json` real contra la API (sin mocks) después del cambio; los tests existentes en `test_weather.py` no necesitaron cambios porque mockean `fetch_json` directamente, no su implementación interna.
