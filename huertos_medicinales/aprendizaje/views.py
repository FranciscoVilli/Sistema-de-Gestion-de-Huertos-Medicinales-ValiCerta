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
from .services import completar
from .services import estado


def learning_context(request, preview=False):
    from .educational_models import VISIBLE
    from .educational_models import BloqueEducativo
    from .educational_models import CompetenciaAdquirida
    from .educational_models import LeccionEducativa
    from .educational_models import ProgresoLeccion
    section=request.GET.get("seccion", "ruta")
    if section not in {"ruta","lecciones","plantas","guias","avances"}: section="ruta"
    query=request.GET.get("q", "").strip()[:100]
    def normalize(text):
        return "".join(c for c in unicodedata.normalize("NFD",text.casefold()) if not unicodedata.combining(c))
    needle=normalize(query)
    completed=set(ProgresoLeccion.objects.filter(user=request.user,completada=True).values_list("leccion_id","revision")) if request.user.is_authenticated else set()
    lessons=list(LeccionEducativa.objects.filter(estado__in=VISIBLE,capitulo__estado__in=VISIBLE).select_related("capitulo"))
    for lesson in lessons: lesson.done=(lesson.pk,lesson.revision) in completed
    total=len(lessons);done=sum(l.done for l in lessons)
    images=["login-garden.png","jardin-vacio.png","semillas.svg","plantas/menta.png","plantas/calendula.png","terraza-ilustrada.png"]
    blocks=[]
    for index,block in enumerate(BloqueEducativo.objects.prefetch_related("capitulos").all()):
        chapters=[c for c in block.capitulos.all() if c.estado!="archivado"]
        block.chapter_count=len(chapters)
        block.available_count=sum(c.estado in VISIBLE for c in chapters)
        block.image="images/huertos/"+images[index%len(images)]
        block.summary=" · ".join(c.titulo for c in chapters[:3])
        if needle in normalize(block.titulo+" "+" ".join(c.titulo for c in chapters)): blocks.append(block)
    return {"preview":preview,"section":section,"query":query,"blocks":blocks,"results_lessons":[l for l in lessons if needle in normalize(l.titulo+" "+l.capitulo.titulo)],"results_plants":[p for p in PLANTAS if needle in normalize(p["nombre"]+" "+p["descripcion"])],"completed_count":done,"total_count":total,"progress":round(done*100/total) if total else 0,"next_lesson":next((l for l in lessons if not l.done),None),"competency_count":CompetenciaAdquirida.objects.filter(user=request.user).count() if request.user.is_authenticated else 0}


@login_required
def dashboard(request):
    return render(request, "pages/learning.html", learning_context(request))


def preview(request):
    return render(request, "pages/learning.html", learning_context(request, True))


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
    locked = False  # Botanical information is available regardless of educational progress.
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
