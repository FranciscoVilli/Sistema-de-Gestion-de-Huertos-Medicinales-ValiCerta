import unicodedata
from http import HTTPStatus

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import redirect
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from .catalogo import LECCIONES
from .catalogo import PLANTAS
from .educational_models import VISIBLE
from .educational_models import BloqueEducativo
from .educational_models import CompetenciaAdquirida
from .educational_models import LeccionEducativa
from .educational_models import ProgresoLeccion
from .educational_models import RutaEducativa
from .educational_services import chapter_progress
from .educational_services import route_status
from .module_visuals import module_cover
from .services import completar
from .services import estado

# Funcion extensa heredada; dividirla queda registrado como deuda tecnica (V2).


def learning_context(request, *, preview=False):  # noqa: C901

    section = "ruta"
    query = request.GET.get("q", "").strip()[:100]

    def normalize(text):
        return "".join(
            c
            for c in unicodedata.normalize("NFD", text.casefold())
            if not unicodedata.combining(c)
        )

    needle = normalize(query)
    completed = (
        set(
            ProgresoLeccion.objects.filter(
                user=request.user,
                completada=True,
            ).values_list("leccion_id", "revision"),
        )
        if request.user.is_authenticated
        else set()
    )
    lessons = list(
        LeccionEducativa.objects.filter(
            estado__in=VISIBLE,
            capitulo__estado__in=VISIBLE,
        ).select_related("capitulo"),
    )
    for lesson in lessons:
        lesson.done = (lesson.pk, lesson.revision) in completed
    total = len(lessons)
    done = sum(leccion.done for leccion in lessons)
    unlocked_by_chapter_id = (
        {row["chapter"].pk: row["unlocked"] for row in chapter_progress(request.user)}
        if request.user.is_authenticated
        else {}
    )

    blocks = []
    for block in BloqueEducativo.objects.prefetch_related("capitulos").all():
        chapters = [c for c in block.capitulos.all() if c.estado != "archivado"]
        block.chapter_count = len(chapters)
        block.available_count = sum(c.estado in VISIBLE for c in chapters)
        block.image = module_cover(block.numero)
        block.summary = " · ".join(c.titulo for c in chapters[:3])
        first_visible = next(
            (c for c in chapters if c.pk in unlocked_by_chapter_id),
            None,
        )
        block.locked = (
            bool(first_visible) and not unlocked_by_chapter_id[first_visible.pk]
        )
        if needle in normalize(
            block.titulo + " " + " ".join(c.titulo for c in chapters),
        ):
            blocks.append(block)
    plant_info = {}
    if request.user.is_authenticated:
        for route in RutaEducativa.objects.filter(estado__in=VISIBLE).prefetch_related(
            "requisitos",
        ):
            info = plant_info.setdefault(
                route.especie,
                {"desbloqueada": False, "requisito": None},
            )
            if route_status(request.user, route)["eligible"]:
                info["desbloqueada"] = True
            if not info["requisito"]:
                competency = route.requisitos.first()
                exam = (
                    competency.evaluacioneducativa_set.first() if competency else None
                )
                if exam:
                    info["requisito"] = exam.capitulo.titulo
    plantas_estado = []
    for p in PLANTAS:
        info = plant_info.get(p["slug"], {"desbloqueada": False, "requisito": None})
        plantas_estado.append(
            {
                "nombre": p["nombre"],
                "slug": p["slug"],
                "desbloqueada": info["desbloqueada"],
                "requisito": info["requisito"],
            },
        )
    return {
        "preview": preview,
        "section": section,
        "query": query,
        "blocks": blocks,
        "completed_count": done,
        "total_count": total,
        "progress": round(done * 100 / total) if total else 0,
        "next_lesson": next((leccion for leccion in lessons if not leccion.done), None),
        "competency_count": CompetenciaAdquirida.objects.filter(
            user=request.user,
        ).count()
        if request.user.is_authenticated
        else 0,
        "plantas_estado": plantas_estado,
    }


@login_required
def dashboard(request):
    return render(request, "pages/learning.html", learning_context(request))


def preview(request):
    return render(
        request,
        "pages/learning.html",
        learning_context(request, preview=True),
    )


@login_required
@require_http_methods(["GET", "POST"])
def lesson(request, slug):
    item = next((entry for entry in LECCIONES if entry["slug"] == slug), None)
    if item is None:
        raise Http404
    current = estado(request.user)
    state = next(entry for entry in current["lecciones"] if entry["slug"] == slug)
    if not state["abierta"]:
        messages.info(
            request,
            "Completa la lección anterior para abrir esta actividad.",
        )
        return redirect("learning")
    feedback = ""
    if request.method == "POST":
        result = completar(request.user, slug, request.POST.get("answer", ""))
        if result == "completada":
            messages.success(
                request,
                (
                    "¡Aprendizaje completado! Ganaste 25 XP. Revisa tus nuevas "
                    "plantas y tu siguiente paso."
                ),
            )
            return redirect("learning")
        if result == "repetida":
            messages.info(
                request,
                (
                    "Ya recibiste la experiencia de esta lección. Puedes "
                    "repasar sin sumar XP otra vez."
                ),
            )
            return redirect("learning")
        if result == "bloqueada":
            return redirect("learning")
        feedback = (
            "Todavía no. "
            + item["explicacion"]
            + " Puedes revisar y volver a intentarlo."
        )
    public = {key: value for key, value in item.items() if key != "correcta"}
    return render(
        request,
        "pages/lesson.html",
        {
            **current,
            "leccion": public,
            "hecha": state["hecha"],
            "feedback": feedback,
        },
    )


@login_required
def plant(request, slug):
    item = next((entry for entry in PLANTAS if entry["slug"] == slug), None)
    if item is None:
        raise Http404
    current = estado(request.user)
    locked = (
        False  # Botanical information is available regardless of educational progress.
    )
    return render(
        request,
        "pages/plant.html",
        {
            **current,
            "planta": item,
            "bloqueada": locked,
        },
        status=HTTPStatus.FORBIDDEN if locked else HTTPStatus.OK,
    )
