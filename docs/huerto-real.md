# Huerto real y bodega

Implementado el 8 de noviembre de 2026, como parte del cierre de brechas contra el enunciado oficial del proyecto (ISWD652).

## Pantallas y funciones
- Cada comunidad tiene a lo sumo un huerto real (`HuertoReal`, uno por comunidad). Solo el responsable puede registrarlo o editarlo, desde `/comunidades/<id>/huerto-real/` — un único formulario que cubre el huerto y su bodega a la vez.
- Campos del huerto real: provincia, parroquia, dirección/referencia (uso interno), latitud/longitud de alta precisión (uso interno), diseño (en tierra/vertical/colgante/piso) con técnica específica libre, tipo de cerca de seguridad (viva/natural/reciclada/metálica/convencional) con detalle libre, área total con unidad (m²/ha), tipo de suelo (arcilloso/limoso/arenoso/margoso/gredoso/pantanoso), agua de riego (río/canal/goteo/otro) con detalle, abono natural (barbecho/restos vegetales/hoja/compost/otro) con detalle.
- Bodega (`Bodega`, uno por huerto real): tres espacios booleanos con detalle libre — herramientas e implementos, semillas/estacas/esquejes/plántulas, abonos orgánicos y compost.
- La dirección exacta y las coordenadas de alta precisión **no se muestran en ninguna página pública** — son de uso interno del establecimiento de salud, a diferencia de la ubicación aproximada de `Comunidad` (ya pensada para el mapa público). El resto de los campos sí se muestra en la ficha pública de la comunidad cuando existe un huerto real registrado.
- Cada actualización queda registrada en `EventoComunidad` (`accion="huerto_real_actualizado"`), igual que el resto de cambios de una comunidad.

## Archivos
- `comunidades/models.py`: `HuertoReal`, `Bodega`.
- `comunidades/forms.py`: `HuertoRealForm`, `BodegaForm`.
- `comunidades/views.py`: `huerto_real` (un solo view maneja ambos formularios).
- `comunidades/urls.py`: ruta `huerto-real/`.
- `comunidades/admin.py`: `HuertoRealAdmin`, `BodegaAdmin` (solo lectura; se editan desde la app, no desde el admin).
- `templates/comunidades/huerto_real.html`.
- `templates/comunidades/detalle.html`: sección pública "Huerto real" + enlace de edición para el responsable.
- `comunidades/test_huerto_real.py`: registro, reutilización del mismo registro al editar, permisos y que las coordenadas no se filtran a la ficha pública.

## Migración
`comunidades/migrations/0005_huertoreal_bodega.py` — crea `HuertoReal` y `Bodega`. No modifica datos existentes.

## Verificación
- `pytest -q` completo del proyecto: 116 pruebas aprobadas (incluye las 3 nuevas de huerto real).
- Navegador con cuenta de prueba: responsable llena el formulario completo (huerto + bodega) → mensaje de confirmación → la ficha pública de la comunidad muestra diseño, cerca, área, suelo, riego, abono y bodega, sin exponer la dirección ni las coordenadas exactas.
- Cuenta y comunidad de prueba eliminadas al terminar.
