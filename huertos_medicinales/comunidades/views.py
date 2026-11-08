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

from .forms import BodegaForm
from .forms import ComunidadForm
from .forms import HuertoRealForm
from .forms import SolicitudMiembroForm
from .models import CertificacionTalento
from .models import Comunidad
from .models import EventoComunidad
from .models import Miembro


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


@login_required
@require_http_methods(["GET", "POST"])
def huerto_real(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk, responsable=request.user)
    huerto = getattr(comunidad, "huerto_real", None)
    bodega = getattr(huerto, "bodega", None) if huerto else None
    huerto_form = HuertoRealForm(request.POST or None, instance=huerto)
    bodega_form = BodegaForm(request.POST or None, instance=bodega)
    if request.method == "POST" and huerto_form.is_valid() and bodega_form.is_valid():
        with transaction.atomic():
            huerto = huerto_form.save(commit=False)
            huerto.comunidad = comunidad
            huerto.save()
            bodega = bodega_form.save(commit=False)
            bodega.huerto_real = huerto
            bodega.save()
            EventoComunidad.objects.create(
                comunidad=comunidad,
                actor=request.user,
                accion="huerto_real_actualizado",
            )
        messages.success(request, "Huerto real actualizado.")
        return redirect("comunidades:detalle", pk=comunidad.pk)
    return render(
        request,
        "comunidades/huerto_real.html",
        {"comunidad": comunidad, "huerto_form": huerto_form, "bodega_form": bodega_form},
    )


@login_required
@require_http_methods(["GET", "POST"])
def solicitar_membresia(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk, estado=Comunidad.Estado.PUBLICADA)
    existente = getattr(request.user, "membresia", None)
    if existente and existente.estado != Miembro.Estado.RETIRADA:
        messages.error(
            request,
            "Ya perteneces a una comunidad. Retírate de ella antes de solicitar unirte a otra.",
        )
        return redirect("comunidades:detalle", pk=comunidad.pk)
    form = SolicitudMiembroForm(request.POST or None, instance=existente)
    if request.method == "POST" and form.is_valid():
        with transaction.atomic():
            miembro = form.save(commit=False)
            miembro.usuario = request.user
            miembro.comunidad = comunidad
            miembro.estado = Miembro.Estado.SOLICITADA
            miembro.save()
            EventoComunidad.objects.create(
                comunidad=comunidad,
                actor=request.user,
                accion="miembro_solicitado",
            )
        messages.success(
            request,
            "Solicitud enviada. El responsable de la comunidad la revisará.",
        )
        return redirect("comunidades:detalle", pk=comunidad.pk)
    return render(
        request,
        "comunidades/solicitar_membresia.html",
        {"comunidad": comunidad, "form": form},
    )


@login_required
def gestionar_miembros(request, pk):
    comunidad = get_object_or_404(Comunidad, pk=pk, responsable=request.user)
    miembros = comunidad.miembros.select_related("usuario").prefetch_related("talentos")
    return render(
        request,
        "comunidades/gestionar_miembros.html",
        {
            "comunidad": comunidad,
            "solicitudes": miembros.filter(estado=Miembro.Estado.SOLICITADA),
            "aprobados": miembros.filter(estado=Miembro.Estado.APROBADA),
        },
    )


@login_required
@require_POST
def decidir_miembro(request, pk, miembro_pk):
    accion = request.POST.get("accion")
    with transaction.atomic():
        comunidad = get_object_or_404(Comunidad, pk=pk, responsable=request.user)
        miembro = get_object_or_404(
            Miembro.objects.select_for_update(),
            pk=miembro_pk,
            comunidad=comunidad,
            estado=Miembro.Estado.SOLICITADA,
        )
        if accion == "aprobar":
            miembro.estado = Miembro.Estado.APROBADA
            registro = "miembro_aprobado"
            texto = "Miembro aprobado."
        else:
            miembro.estado = Miembro.Estado.RETIRADA
            registro = "miembro_rechazado"
            texto = "Solicitud rechazada."
        miembro.save(update_fields=["estado", "actualizado"])
        EventoComunidad.objects.create(comunidad=comunidad, actor=request.user, accion=registro)
    messages.success(request, texto)
    return redirect("comunidades:gestionar_miembros", pk=comunidad.pk)


@login_required
@require_POST
def retirar_miembro(request, pk, miembro_pk):
    with transaction.atomic():
        comunidad = get_object_or_404(Comunidad, pk=pk, responsable=request.user)
        miembro = get_object_or_404(
            Miembro.objects.select_for_update(),
            pk=miembro_pk,
            comunidad=comunidad,
            estado=Miembro.Estado.APROBADA,
        )
        miembro.estado = Miembro.Estado.RETIRADA
        miembro.save(update_fields=["estado", "actualizado"])
        EventoComunidad.objects.create(comunidad=comunidad, actor=request.user, accion="miembro_retirado")
    messages.success(request, "Miembro retirado de la comunidad.")
    return redirect("comunidades:gestionar_miembros", pk=comunidad.pk)


@login_required
@require_POST
def proponer_talento(request, pk, miembro_pk):
    talento = request.POST.get("talento", "").strip()[:80]
    comunidad = get_object_or_404(Comunidad, pk=pk, responsable=request.user)
    miembro = get_object_or_404(
        Miembro,
        pk=miembro_pk,
        comunidad=comunidad,
        estado=Miembro.Estado.APROBADA,
    )
    if talento:
        ya_existe = CertificacionTalento.objects.filter(
            miembro=miembro,
            talento=talento,
            estado__in=[CertificacionTalento.Estado.PROPUESTA, CertificacionTalento.Estado.CERTIFICADA],
        ).exists()
        if ya_existe:
            messages.info(request, "Ese talento ya está propuesto o certificado para este miembro.")
        else:
            CertificacionTalento.objects.create(miembro=miembro, talento=talento, propuesto_por=request.user)
            messages.success(request, "Talento propuesto. Queda pendiente de certificación.")
    return redirect("comunidades:gestionar_miembros", pk=comunidad.pk)
