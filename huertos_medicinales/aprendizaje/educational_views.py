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
from .educational_services import correct
from .educational_services import lessons_ready
from .educational_services import question_public
from .educational_services import record_unlocks
from .educational_services import route_status
from .educational_services import start_attempt
from .educational_services import submit_attempt
from .educational_services import visible_lessons


@login_required
def catalog(request):
    blocks = BloqueEducativo.objects.prefetch_related("capitulos").all()
    return render(request, "aprendizaje/pilot_catalog.html", {"blocks": blocks})


@login_required
def chapter(request, slug):
    chapter = get_object_or_404(CapituloEducativo, slug=slug, estado__in=VISIBLE)
    rows = []
    for lesson in visible_lessons(chapter):
        progress = ProgresoLeccion.objects.filter(
            user=request.user, leccion=lesson, revision=lesson.revision,
        ).first()
        rows.append({"lesson": lesson, "progress": progress})
    exam = EvaluacionEducativa.objects.filter(
        capitulo=chapter, estado__in=VISIBLE,
    ).first()
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
@require_http_methods(["GET", "POST"])
def lesson(request, slug):
    item = get_object_or_404(
        LeccionEducativa, slug=slug, estado__in=VISIBLE, capitulo__estado__in=VISIBLE,
    )
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
                    return redirect("lms_chapter", slug=item.capitulo.slug)
                feedback = "Revisa la idea: " + item.comprension["explicacion"]
    position = min(progress.seccion if progress else 0, len(item.secciones))
    # Review previously read sections without advancing or losing the saved position.
    try:
        display = int(request.GET.get("seccion", position))
    except ValueError, TypeError:
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


@login_required
def block_detail(request, pk):
    block=get_object_or_404(BloqueEducativo,pk=pk)
    return render(request,"aprendizaje/block_detail.html",{"block":block,"chapters":block.capitulos.exclude(estado="archivado")})
