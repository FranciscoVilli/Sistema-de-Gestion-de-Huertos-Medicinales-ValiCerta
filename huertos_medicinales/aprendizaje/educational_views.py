from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .educational_models import VISIBLE
from .educational_models import BloqueEducativo
from .educational_models import CapituloEducativo
from .educational_models import CompetenciaAdquirida
from .educational_models import DesbloqueoRuta
from .educational_models import EvaluacionEducativa
from .educational_models import IntentoCapitulo
from .educational_models import LeccionEducativa
from .educational_models import ProgresoLeccion
from .educational_models import RutaEducativa
from .educational_services import chapter_approved
from .educational_services import chapter_progress
from .educational_services import chapter_unlocked
from .educational_services import correct
from .educational_services import lesson_progress
from .educational_services import lesson_unlocked
from .educational_services import lessons_ready
from .educational_services import question_public
from .educational_services import record_unlocks
from .educational_services import route_status
from .educational_services import start_attempt
from .educational_services import submit_attempt
from .educational_services import visible_lessons


@login_required
def catalog(request):
    blocks = list(BloqueEducativo.objects.prefetch_related("capitulos").all())
    progress_by_id = {row["chapter"].pk: row for row in chapter_progress(request.user)}
    for block in blocks:
        for item in block.capitulos.all():
            row = progress_by_id.get(item.pk)
            if row:
                item.locked = not row["unlocked"]
    return render(request, "aprendizaje/pilot_catalog.html", {"blocks": blocks})


@login_required
def chapter(request, slug):
    chapter = get_object_or_404(CapituloEducativo, slug=slug, estado__in=VISIBLE)
    if not chapter_unlocked(request.user, chapter):
        messages.info(
            request,
            "Primero debes aprobar la evaluación del capítulo anterior para abrir este.",
        )
        return redirect("lms_catalog")
    rows = []
    next_lesson = None
    for item in lesson_progress(request.user, chapter):
        rows.append(
            {"lesson": item["lesson"], "progress": item["progress"], "locked": not item["unlocked"]},
        )
        if next_lesson is None and item["unlocked"] and not item["completed"]:
            next_lesson = item["lesson"]
    if next_lesson:
        return redirect("lms_lesson", slug=next_lesson.slug)
    exam = EvaluacionEducativa.objects.filter(
        capitulo=chapter, estado__in=VISIBLE,
    ).first()
    if exam and not chapter_approved(request.user, chapter) and lessons_ready(request.user, chapter):
        return redirect("lms_assessment", slug=chapter.slug)
    first_lesson = visible_lessons(chapter).order_by("orden").first()
    if first_lesson:
        return redirect("lms_lesson", slug=first_lesson.slug)
    return render(
        request,
        "aprendizaje/pilot_chapter.html",
        {
            "chapter": chapter,
            "rows": rows,
            "exam": exam,
            "ready": lessons_ready(request.user, chapter),
        },
    )


@login_required
def block_detail(request, pk):
    block = get_object_or_404(BloqueEducativo, pk=pk)
    chapters = list(block.capitulos.exclude(estado="archivado"))
    progress_by_id = {row["chapter"].pk: row for row in chapter_progress(request.user)}
    from .module_visuals import module_cover, chapter_cover
    from .context_processors import XP_POR_LECCION, XP_POR_CAPITULO
    completed_lessons = set(ProgresoLeccion.objects.filter(
        user=request.user, completada=True,
    ).values_list("leccion_id", flat=True))
    for item in chapters:
        row = progress_by_id.get(item.pk, {})
        item.locked = not row.get("unlocked", False)
        item.approved = row.get("approved", False)
        item.cover = chapter_cover(item)
        lesson_ids = list(item.lecciones.filter(estado__in=VISIBLE).values_list("pk", flat=True))
        has_exam = EvaluacionEducativa.objects.filter(capitulo=item, estado__in=VISIBLE).exists()
        item.lesson_xp = len(lesson_ids) * XP_POR_LECCION
        item.exam_xp = XP_POR_CAPITULO if has_exam else 0
        item.total_xp = item.lesson_xp + item.exam_xp
        item.earned_xp = len(set(lesson_ids) & completed_lessons) * XP_POR_LECCION + (item.exam_xp if item.approved else 0)
    completed = sum(item.approved for item in chapters)
    related_routes = RutaEducativa.objects.filter(
        estado__in=VISIBLE, requisitos__evaluacioneducativa__capitulo__bloque=block,
    ).distinct().prefetch_related("requisitos")
    plants = []
    from .catalogo import PLANTAS
    names = {p['slug']:p['nombre'] for p in PLANTAS}
    for route in related_routes:
        plants.append({"name": names.get(route.especie, route.nombre), "slug": route.especie,
                       "image": f"images/huertos/plantas/{route.especie}.png",
                       "available": route_status(request.user, route)["eligible"]})
    return render(request, "aprendizaje/block_detail.html", {
        "block": block, "module": block, "chapters": chapters, "cover": module_cover(block.numero),
        "completed": completed, "total": len(chapters),
        "percent": round(completed * 100 / len(chapters)) if chapters else 0,
        "plants": plants,
        "total_xp": sum(item.total_xp for item in chapters),
        "earned_xp": sum(item.earned_xp for item in chapters),
    })


@login_required
@require_http_methods(["GET", "POST"])
def lesson(request, slug):
    item = get_object_or_404(
        LeccionEducativa, slug=slug, estado__in=VISIBLE, capitulo__estado__in=VISIBLE,
    )
    if not lesson_unlocked(request.user, item):
        messages.info(
            request,
            "Primero debes completar la lección anterior para abrir esta.",
        )
        return redirect("lms_chapter", slug=item.capitulo.slug)
    item.full_clean()
    progress = ProgresoLeccion.objects.filter(
        user=request.user, leccion=item, revision=item.revision,
    ).first()
    feedback = ""
    if request.method == "POST":
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            progress, _ = ProgresoLeccion.objects.get_or_create(
                user=request.user, leccion=item, revision=item.revision,
            )
            if request.POST.get("revision") != str(item.revision):
                feedback = (
                    "La lección cambió. Revisa la versión actual antes de continuar."
                )
            elif request.POST.get("action") == "next":
                if request.POST.get("section") == str(
                    progress.seccion,
                ) and progress.seccion < len(item.secciones):
                    progress.seccion += 1
                    progress.save()
                return redirect("lms_lesson", slug=slug)
            elif request.POST.get("action") == "answer" and progress.seccion >= len(
                item.secciones,
            ):
                if correct(item.comprension, request.POST.getlist("answer")):
                    progress.completada = True
                    progress.save()
                    messages.success(
                        request,
                        "Actividad de comprensión completada. Tu progreso quedó guardado.",
                    )
                    next_lesson = (
                        visible_lessons(item.capitulo)
                        .filter(orden__gt=item.orden)
                        .order_by("orden")
                        .first()
                    )
                    if next_lesson:
                        return redirect("lms_lesson", slug=next_lesson.slug)
                    if EvaluacionEducativa.objects.filter(
                        capitulo=item.capitulo, estado__in=VISIBLE,
                    ).exists() and not chapter_approved(request.user, item.capitulo):
                        return redirect("lms_assessment", slug=item.capitulo.slug)
                    return redirect("lms_chapter", slug=item.capitulo.slug)
                feedback = "Revisa la idea: " + item.comprension["explicacion"]
    position = min(progress.seccion if progress else 0, len(item.secciones))
    # Review previously read sections without advancing or losing the saved position.
    try:
        display = int(request.GET.get("seccion", position))
    except (ValueError, TypeError):
        display = position
    display = max(0, min(display, position, len(item.secciones)))
    section = item.secciones[display] if display < len(item.secciones) else None
    return render(
        request,
        "aprendizaje/pilot_lesson.html",
        {
            "lesson": item,
            "progress": progress,
            "position": position,
            "display": display,
            "section": section,
            "sections": list(range(len(item.secciones))),
            "question": question_public(item.comprension, "answer"),
            "feedback": feedback,
            "reading_percent": round(position * 100 / len(item.secciones)),
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def assessment(request, slug):
    chapter = get_object_or_404(CapituloEducativo, slug=slug, estado__in=VISIBLE)
    exam = get_object_or_404(EvaluacionEducativa, capitulo=chapter, estado__in=VISIBLE)
    if not chapter_unlocked(request.user, chapter):
        messages.info(
            request,
            "Primero debes aprobar la evaluación del capítulo anterior para abrir esta.",
        )
        return redirect("lms_catalog")
    error = ""
    attempt = None
    if request.method == "POST":
        try:
            if request.POST.get("action") == "start":
                attempt = start_attempt(request.user, exam)
                return redirect(
                    reverse("lms_assessment", args=[slug]) + f"?intento={attempt.pk}",
                )
            attempt = get_object_or_404(
                IntentoCapitulo,
                pk=request.POST.get("attempt")
                if request.POST.get("attempt", "").isdigit()
                else 0,
                user=request.user,
                evaluacion=exam,
            )
            attempt = submit_attempt(request.user, attempt.pk, request.POST)
            return redirect("lms_result", pk=attempt.pk)
        except ValidationError as exc:
            error = " ".join(exc.messages)
    elif request.GET.get("intento", "").isdigit():
        attempt = get_object_or_404(
            IntentoCapitulo,
            pk=request.GET["intento"],
            user=request.user,
            evaluacion=exam,
        )
        if attempt.finalizado:
            return redirect("lms_result", pk=attempt.pk)
    questions = (
        [
            question_public(attempt.contenido["preguntas"][i], f"q_{i}")
            for i in attempt.contenido["orden"]
        ]
        if attempt
        else []
    )
    return render(
        request,
        "aprendizaje/pilot_assessment.html",
        {
            "chapter": chapter,
            "exam": exam,
            "attempt": attempt,
            "questions": questions,
            "ready": lessons_ready(request.user, chapter),
            "error": error,
        },
    )


@login_required
def result(request, pk):
    attempt = get_object_or_404(
        IntentoCapitulo, pk=pk, user=request.user, finalizado__isnull=False,
    )
    feedback = []
    for i, q in enumerate(attempt.contenido["preguntas"]):
        feedback.append(
            {
                "title": q["enunciado"],
                "correct": correct(q, attempt.respuestas.get(str(i), [])),
                "explanation": q["explicacion"],
            },
        )
    return render(
        request,
        "aprendizaje/pilot_result.html",
        {"attempt": attempt, "feedback": feedback},
    )


@login_required
def achievements(request):
    return render(
        request,
        "aprendizaje/pilot_progress.html",
        {
            "competencies": CompetenciaAdquirida.objects.filter(
                user=request.user,
            ).select_related("competencia", "intento"),
            "attempts": IntentoCapitulo.objects.filter(
                user=request.user, finalizado__isnull=False,
            ).select_related("evaluacion")[:20],
            "routes": [
                route_status(request.user, r)
                for r in RutaEducativa.objects.filter(estado__in=VISIBLE)
            ],
        },
    )


@login_required
@require_http_methods(["GET", "POST"])
def route(request, slug):
    route = get_object_or_404(RutaEducativa, slug=slug, estado__in=VISIBLE)
    state = route_status(request.user, route)
    if request.method == "POST":
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            state = route_status(request.user, route)
            if not state["eligible"]:
                return render(
                    request, "aprendizaje/pilot_route.html", state, status=403,
                )
            record_unlocks(request.user)
            record = DesbloqueoRuta.objects.get(user=request.user, ruta=route)
            if not record.iniciada:
                record.iniciada = timezone.now()
                record.save(update_fields=["iniciada"])
        return redirect("lms_route", slug=slug)
    return render(request, "aprendizaje/pilot_route.html", state)
