from huertos_medicinales.aprendizaje.catalogo import PLANTAS

_PLANTAS_POR_SLUG = {planta["slug"]: planta for planta in PLANTAS}

_CAMPOS = {
    "tipo_suelo": "suelo_recomendado",
    "tipo_agua_riego": "agua_recomendada",
    "tipo_abono": "abono_recomendado",
}


def recomendar_suelo_agua_abono(slugs):
    """Deriva suelo/agua/abono de las plantas elegidas en el huerto real.

    Si ninguna planta elegida tiene una recomendación confirmada para un
    campo, o si se contradicen entre sí, ese campo queda vacío en vez de
    asumirse (mismo criterio que el resto del catálogo: sin fuente citable,
    sin dato).
    """
    plantas = [_PLANTAS_POR_SLUG[slug] for slug in slugs if slug in _PLANTAS_POR_SLUG]
    resultado = {}
    for campo_huerto, campo_planta in _CAMPOS.items():
        valores = {planta[campo_planta] for planta in plantas if planta[campo_planta]}
        resultado[campo_huerto] = valores.pop() if len(valores) == 1 else ""
    return resultado
