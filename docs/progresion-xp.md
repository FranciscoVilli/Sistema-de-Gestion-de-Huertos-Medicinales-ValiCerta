# Progresión inicial de aprendizaje

La experiencia ahora persiste por cuenta en PostgreSQL. Cada lección aprobada concede 25 XP una sola vez. Las seis lecciones se abren secuencialmente. El servidor valida respuesta, orden y autenticación. No acepta valores de XP del navegador. Un registro único por usuario y lección, una transacción y un bloqueo de la fila del usuario evitan duplicados y carreras entre premios.

Reglas provisionales del piloto: Aprendiz 0 XP; Oficial 75 XP; Maestro 150 XP. Manzanilla 0 XP, Menta 50 XP, Caléndula 100 XP y Romero 150 XP. Las plantas desbloquean fichas iniciales; no son inventario ni certificación de capacidades profesionales, ni un orden botánico de dificultad. Las instrucciones específicas por especie siguen pendientes de revisión. Los valores son configurables en aprendizaje/catalogo.py.

La ruta suma conocimiento comprobado mediante preguntas. No acredita que se haya realizado una siembra real. La bitácora sigue siendo un borrador de demostración y la simulación y el mapa comunitario no están implementados. No se acreditó experiencia a cuentas existentes sin completar actividades.

El tema verde oscuro se aplica desde base.html a portada, autenticación, aprendizaje, guías, bitácora y páginas públicas de la aplicación. El administrador interno conserva su interfaz propia de Django.

Verificado: 36 pruebas aprobadas. Navegador: 18 combinaciones de seis páginas a 1440/390/320 px, mismo fondo oscuro y sin desbordamiento. Recorrido probado con cuenta temporal: 0 → 25 → 50 → 75 XP, respuesta incorrecta sin premio, desbloqueo de Menta a 50 XP, nivel Oficial a 75 XP y persistencia al recargar. La cuenta temporal fue eliminada; la cuenta personal no se modificó.
