"""Puntos e insignias por actividad real de cultivo. No miden avance educativo."""

PUNTOS_ACTIVIDAD_COMPLETADA = 5
PUNTOS_OBSERVACION = 3
PUNTOS_TALENTO_CERTIFICADO = 20

UMBRAL_OFICIAL = 50
UMBRAL_MAESTRO = 150

INSIGNIAS = (
    {
        "clave": "primera_actividad",
        "nombre": "Primeros pasos",
        "descripcion": "Completaste tu primera actividad de cultivo.",
        "umbral_actividades": 1,
    },
    {
        "clave": "cinco_actividades",
        "nombre": "Manos en la tierra",
        "descripcion": "Completaste 5 actividades de cultivo.",
        "umbral_actividades": 5,
    },
    {
        "clave": "veinte_actividades",
        "nombre": "Guardián del huerto",
        "descripcion": "Completaste 20 actividades de cultivo.",
        "umbral_actividades": 20,
    },
    {
        "clave": "primer_talento",
        "nombre": "Talento reconocido",
        "descripcion": "Tu comunidad certificó tu primer talento.",
        "umbral_talentos": 1,
    },
)


def contar_actividades(usuario_id):
    from huertos_medicinales.seguimiento.models import ActividadCalendario
    return ActividadCalendario.objects.filter(
        practica__participante_id=usuario_id,
        completada=True,
    ).count()


def contar_observaciones(usuario_id):
    from huertos_medicinales.seguimiento.models import Observacion
    return Observacion.objects.filter(practica__participante_id=usuario_id).count()


def contar_talentos_certificados(miembro):
    from .models import CertificacionTalento
    return miembro.talentos.filter(estado=CertificacionTalento.Estado.CERTIFICADA).count()


def misiones_completadas(miembro):
    from .models import Mision
    from huertos_medicinales.seguimiento.models import ActividadCalendario
    completadas = ActividadCalendario.objects.filter(
        practica__participante_id=miembro.usuario_id,
        completada=True,
    )
    resultado = []
    for mision in Mision.objects.filter(activa=True):
        en_rango = completadas.filter(
            completada_en__date__gte=mision.fecha_inicio,
            completada_en__date__lte=mision.fecha_fin,
        ).count()
        if en_rango >= mision.meta_actividades:
            resultado.append(mision)
    return resultado


def calcular_puntos(miembro):
    puntos = contar_actividades(miembro.usuario_id) * PUNTOS_ACTIVIDAD_COMPLETADA
    puntos += contar_observaciones(miembro.usuario_id) * PUNTOS_OBSERVACION
    puntos += contar_talentos_certificados(miembro) * PUNTOS_TALENTO_CERTIFICADO
    puntos += sum(mision.puntos_recompensa for mision in misiones_completadas(miembro))
    return puntos


def evaluar_insignias(miembro):
    from .models import InsigniaObtenida
    actividades = contar_actividades(miembro.usuario_id)
    talentos = contar_talentos_certificados(miembro)
    obtenidas = set(
        InsigniaObtenida.objects.filter(miembro=miembro).values_list("clave", flat=True),
    )
    for insignia in INSIGNIAS:
        if insignia["clave"] in obtenidas:
            continue
        if "umbral_actividades" in insignia and actividades >= insignia["umbral_actividades"]:
            InsigniaObtenida.objects.create(miembro=miembro, clave=insignia["clave"])
        elif "umbral_talentos" in insignia and talentos >= insignia["umbral_talentos"]:
            InsigniaObtenida.objects.create(miembro=miembro, clave=insignia["clave"])
