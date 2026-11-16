import hashlib
import json
import secrets

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .educational_models import VISIBLE
from .educational_models import CapituloEducativo
from .educational_models import CompetenciaAdquirida
from .educational_models import DesbloqueoRuta
from .educational_models import IntentoCapitulo
from .educational_models import ProgresoLeccion
from .educational_models import RutaEducativa


def visible_lessons(chapter):
    return chapter.lecciones.filter(estado__in=VISIBLE)


def ordered_chapters():
    return list(
        CapituloEducativo.objects.filter(estado__in=VISIBLE)
        .select_related("bloque")
        .order_by("numero"),
    )


def chapter_approved(user, chapter):
    return IntentoCapitulo.objects.filter(
        user=user,
        evaluacion__capitulo=chapter,
        aprobado=True,
    ).exists()


def chapter_progress(user):
    """Avance por el temario: cada capítulo requiere el anterior aprobado."""
    rows = []
    unlocked = True
    for chapter in ordered_chapters():
        approved = chapter_approved(user, chapter)
        rows.append({"chapter": chapter, "approved": approved, "unlocked": unlocked})
        unlocked = unlocked and approved
    return rows


def chapter_unlocked(user, chapter):
    return next(
        (
            row["unlocked"]
            for row in chapter_progress(user)
            if row["chapter"].pk == chapter.pk
        ),
        False,
    )


def lesson_progress(user, chapter):
    """Avance dentro de un capítulo: cada lección requiere la anterior completada."""
    rows = []
    unlocked = True
    for lesson in visible_lessons(chapter).order_by("orden"):
        progress = ProgresoLeccion.objects.filter(
            user=user,
            leccion=lesson,
            revision=lesson.revision,
        ).first()
        completed = bool(progress and progress.completada)
        rows.append(
            {
                "lesson": lesson,
                "progress": progress,
                "completed": completed,
                "unlocked": unlocked,
            },
        )
        unlocked = unlocked and completed
    return rows


def lesson_unlocked(user, lesson):
    if not chapter_unlocked(user, lesson.capitulo):
        return False
    return next(
        (
            row["unlocked"]
            for row in lesson_progress(user, lesson.capitulo)
            if row["lesson"].pk == lesson.pk
        ),
        False,
    )


def lessons_ready(user, chapter):
    lessons = list(visible_lessons(chapter))
    return bool(lessons) and all(
        ProgresoLeccion.objects.filter(
            user=user,
            leccion=leccion,
            revision=leccion.revision,
            completada=True,
        ).exists()
        for leccion in lessons
    )


def question_public(question, key):
    return {
        "key": key,
        "enunciado": question["enunciado"],
        "multiple": question.get("tipo") == "multiple",
        "options": [
            {"value": str(i), "label": label}
            for i, label in enumerate(question["opciones"])
        ],
    }


def correct(question, values):
    return len(values) == len(set(values)) and set(values) == {
        str(i) for i in question["correctas"]
    }


def snapshot(exam):
    return {
        "titulo": exam.titulo,
        "preguntas": exam.preguntas,
        "minimo": exam.porcentaje_minimo,
        "competencias": list(
            exam.competencias.order_by("pk").values_list("pk", flat=True),
        ),
        "lecciones": [
            [leccion.pk, leccion.revision] for leccion in visible_lessons(exam.capitulo)
        ],
    }


def fingerprint(content):
    return hashlib.sha256(
        json.dumps(content, sort_keys=True, ensure_ascii=False).encode(),
    ).hexdigest()


def route_status(user, route):
    acquired = set(
        CompetenciaAdquirida.objects.filter(user=user).values_list(
            "competencia_id",
            flat=True,
        ),
    )
    requirements = list(route.requisitos.all())
    missing = [c for c in requirements if c.pk not in acquired]
    record = DesbloqueoRuta.objects.filter(user=user, ruta=route).first()
    eligible = bool(requirements) and not missing
    return {
        "route": route,
        "requirements": requirements,
        "missing": missing,
        "eligible": eligible,
        "started": eligible and bool(record and record.iniciada),
    }


def record_unlocks(user):
    for route in RutaEducativa.objects.filter(estado__in=VISIBLE).prefetch_related(
        "requisitos",
    ):
        state = route_status(user, route)
        if state["eligible"]:
            evidence = list(
                CompetenciaAdquirida.objects.filter(
                    user=user,
                    competencia__in=state["requirements"],
                ).values("competencia_id", "intento_id"),
            )
            DesbloqueoRuta.objects.get_or_create(
                user=user,
                ruta=route,
                defaults={"evidencia": {"competencias": evidence}},
            )


@transaction.atomic
def start_attempt(user, exam):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    exam.full_clean()
    if not lessons_ready(user, exam.capitulo):
        msg = (
            "Completa las lecciones y sus actividades de comprensión antes de evaluar."
        )
        raise ValidationError(
            msg,
        )
    content = snapshot(exam)
    order = list(range(len(exam.preguntas)))
    secrets.SystemRandom().shuffle(order)
    return IntentoCapitulo.objects.create(
        user=user,
        evaluacion=exam,
        version=fingerprint(content),
        contenido={**content, "orden": order},
    )


@transaction.atomic
def submit_attempt(user, attempt_id, post):
    get_user_model().objects.select_for_update().get(pk=user.pk)
    attempt = (
        IntentoCapitulo.objects.select_for_update()
        .select_related("evaluacion__capitulo")
        .get(pk=attempt_id, user=user)
    )
    if attempt.finalizado:
        return attempt
    exam = attempt.evaluacion
    if (
        exam.estado not in VISIBLE
        or exam.capitulo.estado not in VISIBLE
        or fingerprint(snapshot(exam)) != attempt.version
    ):
        msg = "El contenido cambió. Inicia un nuevo intento con la versión actual."
        raise ValidationError(
            msg,
        )
    if not lessons_ready(user, exam.capitulo):
        msg = "Completa las lecciones de esta versión antes de evaluar."
        raise ValidationError(
            msg,
        )
    questions = attempt.contenido["preguntas"]
    answers = {str(i): post.getlist(f"q_{i}") for i in range(len(questions))}
    if any(not values for values in answers.values()):
        msg = "Responde todas las preguntas antes de enviar."
        raise ValidationError(msg)
    hits = sum(correct(q, answers[str(i)]) for i, q in enumerate(questions))
    attempt.respuestas = answers
    attempt.porcentaje = (hits * 100) // len(questions)
    attempt.aprobado = hits * 100 >= attempt.contenido["minimo"] * len(questions)
    attempt.finalizado = timezone.now()
    attempt.save(update_fields=["respuestas", "porcentaje", "aprobado", "finalizado"])
    if attempt.aprobado:
        for competency_id in attempt.contenido["competencias"]:
            CompetenciaAdquirida.objects.get_or_create(
                user=user,
                competencia_id=competency_id,
                defaults={"intento": attempt},
            )
        record_unlocks(user)
    return attempt
