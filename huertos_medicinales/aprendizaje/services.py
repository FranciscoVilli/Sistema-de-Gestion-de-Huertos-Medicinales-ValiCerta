import hashlib
import json

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Sum

from .catalogo import LECCIONES
from .catalogo import NIVELES
from .catalogo import PLANTAS
from .catalogo import XP_POR_LECCION
from .models import IntentoEvaluacion
from .models import Logro


def estado(user):
    completed = set()
    xp = 0
    if user.is_authenticated:
        events = Logro.objects.filter(user=user)
        completed = set(events.values_list("leccion", flat=True))
        xp = events.aggregate(total=Sum("xp"))["total"] or 0
    level = next(name for threshold, name in reversed(NIVELES) if xp >= threshold)
    next_level = next(
        ((threshold, name) for threshold, name in NIVELES if threshold > xp),
        None,
    )
    previous_threshold = next(threshold for threshold, name in NIVELES if name == level)
    progress = (
        round((xp - previous_threshold) * 100 / (next_level[0] - previous_threshold))
        if next_level
        else 100
    )
    lessons = []
    previous_done = True
    for index, lesson in enumerate(LECCIONES, start=1):
        done = lesson["slug"] in completed
        lessons.append(
            {
                "slug": lesson["slug"],
                "titulo": lesson["titulo"],
                "tema": lesson["tema"],
                "numero": index,
                "hecha": done,
                "abierta": previous_done,
            },
        )
        previous_done = previous_done and done
    plants = [
        {**plant, "abierta": xp >= plant["xp"], "faltan": max(0, plant["xp"] - xp)}
        for plant in PLANTAS
    ]
    next_lesson = next((lesson for lesson in lessons if not lesson["hecha"]), None)
    return {
        "xp": xp,
        "nivel": level,
        "siguiente_nivel": next_level,
        "porcentaje_nivel": min(100, progress),
        "lecciones": lessons,
        "completadas": len(completed),
        "total_lecciones": len(LECCIONES),
        "plantas": plants,
        "plantas_abiertas": sum(plant["abierta"] for plant in plants),
        "siguiente_leccion": next_lesson,
        "xp_por_leccion": XP_POR_LECCION,
    }


@transaction.atomic
def completar(user, slug, answer):
    # Serialize awards for one account, including its first achievement.
    get_user_model().objects.select_for_update().get(pk=user.pk)
    lesson = next((item for item in LECCIONES if item["slug"] == slug), None)
    if lesson is None:
        return "inexistente"
    current = estado(user)
    if Logro.objects.filter(user=user, leccion=slug).exists():
        return "repetida"
    available = next(item for item in current["lecciones"] if item["slug"] == slug)
    if not available["abierta"]:
        return "bloqueada"
    result = "completada" if answer == lesson["correcta"] else "incorrecta"
    serialized = json.dumps(lesson, ensure_ascii=False, sort_keys=True)
    IntentoEvaluacion.objects.create(
        user=user,
        leccion=slug,
        respuesta=str(answer)[:8],
        resultado=result,
        version_contenido=hashlib.sha256(serialized.encode()).hexdigest(),
        contenido=json.loads(serialized),
    )
    if result == "incorrecta":
        return "incorrecta"
    Logro.objects.create(user=user, leccion=slug, xp=XP_POR_LECCION)
    return "completada"
