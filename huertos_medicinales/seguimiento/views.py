from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

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


def tipo_de_observacion(accion):
    """Deriva un tipo/ícono a partir de cómo empieza la acción registrada por
    el participante (los botones de 'cuidado rápido' siempre la redactan
    empezando por 'Riego', 'Poda', etc.). Lo que escribas a mano cae en
    'observacion' por defecto; no se inventa una categoría que el texto no
    confirme."""
    texto = (accion or "").strip().lower()
    if texto.startswith("riego"):
        return "riego", "riego"
    if texto.startswith("poda"):
        return "poda", "poda"
    if texto.startswith("limpieza"):
        return "limpieza", "observaciones"
    if texto.startswith("revisi"):
        return "revision", "observaciones"
    return "observacion", "observaciones"


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
@require_http_methods(["GET"])
def bitacora(request, pk):
    practica = get_object_or_404(Practica, pk=pk, participante=request.user)
    observaciones = practica.observaciones.all()
    if request.GET.get("orden") == "antiguos":
        observaciones = observaciones.order_by("fecha", "creada")
    filas = []
    for item in observaciones:
        tipo, grupo = tipo_de_observacion(item.accion)
        filas.append({"item": item, "tipo": tipo, "grupo": grupo})
    inicio_semana = timezone.localdate() - timedelta(days=7)
    total_esta_semana = sum(1 for f in filas if f["item"].fecha >= inicio_semana)
    total_con_foto = sum(1 for f in filas if f["item"].foto)
    return render(
        request,
        "seguimiento/bitacora.html",
        {
            "practica": practica,
            "filas": filas,
            "total_registros": len(filas),
            "total_esta_semana": total_esta_semana,
            "total_con_foto": total_con_foto,
            "orden": request.GET.get("orden", "recientes"),
        },
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
