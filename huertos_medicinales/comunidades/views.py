from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from .forms import ComunidadForm
from .models import Comunidad
from .models import EventoComunidad


def _mapa_comunidades():
    publicadas = Comunidad.objects.filter(estado=Comunidad.Estado.PUBLICADA)
    return [
        {
            "nombre": comunidad.nombre,
            "provincia": comunidad.provincia,
            "localidad": comunidad.localidad,
            "plantas": comunidad.plantas_destacadas,
            "lat": float(comunidad.latitud),
            "lon": float(comunidad.longitud),
            "url": reverse("comunidades:detalle", args=[comunidad.pk]),
        }
        for comunidad in publicadas
    ]


def listado(request):
    comunidades = Comunidad.objects.filter(estado=Comunidad.Estado.PUBLICADA)
    provincia = request.GET.get("provincia", "").strip()[:80]
    if provincia:
        comunidades = comunidades.filter(provincia__icontains=provincia)
    page = Paginator(comunidades, 12).get_page(request.GET.get("page"))
    return render(
        request,
        "comunidades/listado.html",
        {
            "page": page,
            "provincia": provincia,
            "mapa_comunidades": _mapa_comunidades(),
        },
    )


@never_cache
def detalle(request, pk):
    allowed = Q(estado=Comunidad.Estado.PUBLICADA)
    if request.user.is_authenticated:
        allowed |= Q(responsable=request.user)
    comunidad = get_object_or_404(Comunidad.objects.filter(allowed), pk=pk)
    lon, lat = float(comunidad.longitud), float(comunidad.latitud)
    bbox = ",".join(
        str(value)
        for value in [
            max(-180, lon - 0.08),
            max(-90, lat - 0.06),
            min(180, lon + 0.08),
            min(90, lat + 0.06),
        ]
    )
    return render(
        request,
        "comunidades/detalle.html",
        {"comunidad": comunidad, "bbox": bbox},
    )


@login_required
def propias(request):
    page = Paginator(Comunidad.objects.filter(responsable=request.user), 12).get_page(
        request.GET.get("page"),
    )
    return render(request, "comunidades/propias.html", {"page": page})


@login_required
@require_http_methods(["GET", "POST"])
def crear(request):
    form = ComunidadForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            comunidad = form.save(commit=False)
            comunidad.responsable = request.user
            comunidad.save()
            EventoComunidad.objects.create(
                comunidad=comunidad,
                actor=request.user,
                accion="solicitud",
                detalle={key: str(getattr(comunidad, key)) for key in form.Meta.fields},
            )
        messages.success(
            request,
            (
                "Solicitud guardada. La comunidad será visible en el mapa "
                "cuando sea revisada y publicada."
            ),
        )
        return redirect("comunidades:detalle", pk=comunidad.pk)
    return render(request, "comunidades/formulario.html", {"form": form})


@login_required
@require_POST
def retirar(request, pk):
    with transaction.atomic():
        comunidad = get_object_or_404(
            Comunidad.objects.select_for_update(),
            pk=pk,
            responsable=request.user,
        )
        if comunidad.estado != Comunidad.Estado.RETIRADA:
            comunidad.estado = Comunidad.Estado.RETIRADA
            comunidad.save(update_fields=["estado", "actualizada"])
            EventoComunidad.objects.create(
                comunidad=comunidad,
                actor=request.user,
                accion="retirada",
            )
    messages.success(
        request,
        ("La comunidad ya no está publicada. Se conserva el registro de la solicitud."),
    )
    return redirect("comunidades:propias")
