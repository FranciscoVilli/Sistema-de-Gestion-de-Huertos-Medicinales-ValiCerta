from .educational_models import VISIBLE
from .educational_models import EvaluacionEducativa
from .educational_models import IntentoCapitulo
from .educational_models import LeccionEducativa
from .educational_models import ProgresoLeccion

XP_POR_LECCION = 10
XP_POR_CAPITULO = 40
FRACCIONES_NIVEL = ((0.0, "Aprendiz"), (0.35, "Oficial"), (0.7, "Maestro"))
TITULOS_NIVEL = {
    "Aprendiz": "Primeras semillas",
    "Oficial": "Cultivando conocimientos",
    "Maestro": "Compartiendo saberes",
}


def nivel_actual(request):
    """Refleja el avance real del módulo de Aprender (lecciones y capítulos aprobados)."""
    if not request.user.is_authenticated:
        return {}
    user = request.user
    total_lecciones = LeccionEducativa.objects.filter(estado__in=VISIBLE).count()
    total_capitulos = EvaluacionEducativa.objects.filter(estado__in=VISIBLE).count()
    lecciones_hechas = (
        ProgresoLeccion.objects.filter(user=user, completada=True)
        .values("leccion_id").distinct().count()
    )
    capitulos_aprobados = (
        IntentoCapitulo.objects.filter(user=user, aprobado=True)
        .values("evaluacion_id").distinct().count()
    )
    xp = lecciones_hechas * XP_POR_LECCION + capitulos_aprobados * XP_POR_CAPITULO
    max_xp = total_lecciones * XP_POR_LECCION + total_capitulos * XP_POR_CAPITULO
    niveles = [(round(max_xp * fraccion), nombre) for fraccion, nombre in FRACCIONES_NIVEL] if max_xp else [(0, "Aprendiz")]
    nivel = next(nombre for umbral, nombre in reversed(niveles) if xp >= umbral)
    numero = next(i for i, (umbral, nombre) in enumerate(niveles, start=1) if nombre == nivel)
    umbral_actual = next(umbral for umbral, nombre in niveles if nombre == nivel)
    siguiente = next(((umbral, nombre) for umbral, nombre in niveles if umbral > xp), None)
    porcentaje = (
        round((xp - umbral_actual) * 100 / (siguiente[0] - umbral_actual)) if siguiente else 100
    )
    progress = {
        "xp": xp,
        "nivel": nivel,
        "numero_nivel": numero,
        "titulo_nivel": TITULOS_NIVEL.get(nivel, nivel),
        "siguiente_nivel": siguiente,
        "porcentaje_nivel": min(100, max(0, porcentaje)),
        "xp_faltante": max(0, siguiente[0] - xp) if siguiente else 0,
        "lecciones_completadas": lecciones_hechas,
        "lecciones_totales": total_lecciones,
        "capitulos_aprobados": capitulos_aprobados,
        "capitulos_totales": total_capitulos,
    }
    display_name = user.name.strip() or ("Administrador" if user.is_superuser else "Cultivador")
    return {"estado_aprendizaje": progress, "nombre_cabecera": display_name}
