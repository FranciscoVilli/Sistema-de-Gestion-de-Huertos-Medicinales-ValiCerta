from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from .forms import DevolucionForm
from .forms import EmpaquetadoForm
from .forms import ObservacionForm
from .forms import PracticaForm
from .models import EventoPractica
from .models import Practica


def plantas_disponibles(user):
    from huertos_medicinales.aprendizaje.catalogo import PLANTAS
    return list(PLANTAS)


def snapshot(practica):
    return {
        key: str(getattr(practica, key))
        for key in ["titulo", "planta", "inicio", "espacio", "objetivo", "estado"]
    }


@login_required
def listado(request):
    from django.db.models import Q

    from .models import Observacion
    owned = Practica.objects.filter(participante=request.user)
    query = request.GET.get("q", "").strip()[:120]
    status = request.GET.get("estado", "")
    mode = "lista" if request.GET.get("vista") == "lista" else "tarjetas"
    filtered = owned
    if query:
        filtered = filtered.filter(Q(titulo__icontains=query) | Q(planta__icontains=query) | Q(espacio__icontains=query))
    if status in ("activa", "finalizada"):
        filtered = filtered.filter(estado=status)
    else:
        status = ""
    page = Paginator(filtered.prefetch_related("observaciones"), 9).get_page(request.GET.get("page"))
    for p in page:
        p.reciente = next(iter(p.observaciones.all()), None)
        p.imagen = next((o.foto for o in p.observaciones.all() if o.foto), None)
        p.progreso = min(100, round(p.dias_transcurridos * 100 / p.info_planta["dias_madurez"])) if p.info_planta else 0
    selected = next((p for p in page if str(p.pk) == request.GET.get("cultivo")), None)
    selected = selected or next(iter(page), None)
    params = request.GET.copy()
    for key in ("page", "cultivo"):
        params.pop(key, None)
    return render(request, "seguimiento/listado.html", {
        "page": page, "seleccionada": selected, "q": query, "filtro_estado": status, "vista": mode,
        "total": owned.count(), "activas": owned.filter(estado="activa").count(),
        "finalizadas": owned.filter(estado="finalizada").count(), "params": params.urlencode(),
        "puede_sembrar": bool(plantas_disponibles(request.user)),
        "recientes": Observacion.objects.filter(practica__participante=request.user).select_related("practica")[:4],
    })


@login_required
@require_http_methods(["GET", "POST"])
def crear(request):
    plantas = plantas_disponibles(request.user)
    if not plantas:
        messages.info(
            request,
            (
                "Todavía no tienes ninguna ficha de planta desbloqueada. "
                "Completa la primera lección de Formación para empezar a sembrar."
            ),
        )
        return redirect("learning")
    slug_inicial = request.GET.get("planta", "")
    valido = any(item["slug"] == slug_inicial for item in plantas)
    form = PracticaForm(
        request.POST or None,
        plantas_disponibles=plantas,
        initial={
            "inicio": timezone.localdate(),
            "planta": slug_inicial if valido else None,
        },
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            practica = form.save(commit=False)
            practica.participante = request.user
            practica.save()
            EventoPractica.objects.create(
                practica=practica,
                actor=request.user,
                accion="creada",
                detalle=snapshot(practica),
            )
        messages.success(
            request,
            "Tu práctica se guardó en tu cuenta. Ya puedes añadir observaciones.",
        )
        return redirect("seguimiento:detalle", pk=practica.pk)
    return render(
        request,
        "seguimiento/formulario.html",
        {"form": form, "titulo": "Registrar una práctica"},
    )


@login_required
@require_http_methods(["GET", "POST"])
def detalle(request, pk):
    with transaction.atomic():
        practica = get_object_or_404(
            Practica.objects.select_for_update(),
            pk=pk,
            participante=request.user,
        )
        form = ObservacionForm(
            request.POST or None,
            request.FILES or None,
            practica=practica,
            initial={"fecha": timezone.localdate()},
        )
        if request.method == "POST":
            if practica.estado != Practica.Estado.ACTIVA:
                messages.error(
                    request,
                    "Esta práctica está finalizada. "
                    "Reábrela para añadir observaciones.",
                )
                return redirect("seguimiento:detalle", pk=pk)
            if form.is_valid():
                observacion = form.save(commit=False)
                observacion.practica = practica
                observacion.save()
                EventoPractica.objects.create(
                    practica=practica,
                    actor=request.user,
                    accion="observacion",
                    detalle={
                        "id": observacion.pk,
                        **{
                            key: str(getattr(observacion, key))
                            for key in ["fecha", "accion", "resultado", "pregunta"]
                        },
                    },
                )
                messages.success(request, "Observación guardada.")
                return redirect("seguimiento:detalle", pk=pk)
    return render(
        request,
        "seguimiento/detalle.html",
        {"practica": practica, "form": form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def editar(request, pk):
    with transaction.atomic():
        practica = get_object_or_404(
            Practica.objects.select_for_update(),
            pk=pk,
            participante=request.user,
        )
        form = PracticaForm(
            request.POST or None,
            instance=practica,
            plantas_disponibles=plantas_disponibles(request.user),
        )
        if request.method == "POST" and form.is_valid():
            first_date = (
                practica.observaciones.order_by("fecha")
                .values_list("fecha", flat=True)
                .first()
            )
            if first_date and form.cleaned_data["inicio"] > first_date:
                form.add_error(
                    "inicio",
                    "El inicio no puede ser posterior a una observación registrada.",
                )
            else:
                form.save()
                EventoPractica.objects.create(
                    practica=practica,
                    actor=request.user,
                    accion="actualizada",
                    detalle=snapshot(practica),
                )
                messages.success(
                    request,
                    "Datos actualizados; se conservó el historial.",
                )
                return redirect("seguimiento:detalle", pk=pk)
    return render(
        request,
        "seguimiento/formulario.html",
        {"form": form, "titulo": "Editar datos de la práctica", "practica": practica},
    )


@login_required
@require_http_methods(["GET", "POST"])
def empaquetar(request, pk):
    practica = get_object_or_404(Practica, pk=pk, participante=request.user)
    form = EmpaquetadoForm(
        request.POST or None,
        initial={"fecha_empaquetado": timezone.localdate()},
    )
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            registro = form.save(commit=False)
            registro.practica = practica
            registro.save()
            EventoPractica.objects.create(
                practica=practica,
                actor=request.user,
                accion="empaquetado",
                detalle={
                    "id": registro.pk,
                    "fecha_empaquetado": str(registro.fecha_empaquetado),
                    "fecha_caducidad": str(registro.fecha_caducidad),
                    "region": registro.region,
                },
            )
        messages.success(
            request,
            f"Empaquetado registrado. Caduca el {registro.fecha_caducidad:%d/%m/%Y}.",
        )
        return redirect("seguimiento:detalle", pk=pk)
    return render(
        request,
        "seguimiento/empaquetar.html",
        {"practica": practica, "form": form},
    )


@login_required
@require_POST
def cambiar_estado(request, pk):
    with transaction.atomic():
        practica = get_object_or_404(
            Practica.objects.select_for_update(),
            pk=pk,
            participante=request.user,
        )
        action = request.POST.get("estado")
        if action in Practica.Estado.values and action != practica.estado:
            practica.estado = action
            practica.save(update_fields=["estado", "actualizada"])
            EventoPractica.objects.create(
                practica=practica,
                actor=request.user,
                accion="estado",
                detalle={"estado": action},
            )
            messages.success(request, "Estado actualizado.")
    return redirect("seguimiento:detalle", pk=pk)


@login_required
@permission_required("seguimiento.revisar_practica", raise_exception=True)
def acompanamiento(request):
    page = Paginator(
        Practica.objects.select_related("participante").filter(
            estado=Practica.Estado.ACTIVA,
        ),
        12,
    ).get_page(request.GET.get("page"))
    return render(request, "seguimiento/acompanamiento.html", {"page": page})


@login_required
@permission_required("seguimiento.revisar_practica", raise_exception=True)
@require_http_methods(["GET", "POST"])
def revisar(request, pk):
    practica = get_object_or_404(Practica.objects.select_related("participante"), pk=pk)
    form = DevolucionForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            revision = form.save(commit=False)
            revision.practica = practica
            revision.facilitador = request.user
            revision.save()
            EventoPractica.objects.create(
                practica=practica,
                actor=request.user,
                accion="orientacion",
                detalle={"id": revision.pk, "texto": revision.texto},
            )
        messages.success(request, "Orientación enviada a la práctica del participante.")
        return redirect("seguimiento:revisar", pk=pk)
    return render(
        request,
        "seguimiento/revisar.html",
        {"practica": practica, "form": form},
    )
