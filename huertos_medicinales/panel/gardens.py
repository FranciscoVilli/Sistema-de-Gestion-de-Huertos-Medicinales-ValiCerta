from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_POST

from huertos_medicinales.seguimiento.models import EventoPractica
from huertos_medicinales.seguimiento.models import Jardin
from huertos_medicinales.seguimiento.models import Practica
from huertos_medicinales.aprendizaje.catalogo import PLANTAS
from huertos_medicinales.aprendizaje.educational_models import RutaEducativa, VISIBLE
from huertos_medicinales.aprendizaje.educational_services import route_status


def plantas_desbloqueadas(user):
    # Explicit demo membership only; ordinary accounts retain educational requirements.
    if user.groups.filter(name="Huertos · Demostración de aprendizaje completo").exists():
        return list(PLANTAS)
    especies = {
        route.especie
        for route in RutaEducativa.objects.filter(estado__in=VISIBLE).prefetch_related("requisitos")
        if route_status(user, route)["eligible"]
    }
    return [p for p in PLANTAS if p["slug"] in especies]


class JardinForm(forms.ModelForm):
    class Meta:
        model = Jardin
        fields = ["nombre"]
        widgets = {"nombre": forms.TextInput(attrs={"placeholder": "Por ejemplo: Mi balcón"})}


def garden_url(jardin):
    return reverse("workspace") + f"?jardin={jardin.pk}"


@login_required
@require_http_methods(["GET", "POST"])
def nuevo(request):
    form = JardinForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        jardin = form.save(commit=False)
        jardin.propietario = request.user
        jardin.save()
        messages.success(request, "Tu jardín está listo: elige uno de sus seis espacios.")
        return redirect(garden_url(jardin))
    return render(request, "panel/jardin_form.html", {"form": form, "nuevo": True})


@login_required
@require_http_methods(["GET", "POST"])
def colocar(request, pk, posicion):
    jardin = get_object_or_404(Jardin, pk=pk, propietario=request.user)
    if posicion not in range(1, 7):
        from django.http import Http404
        raise Http404
    plants = plantas_desbloqueadas(request.user)
    mode = request.POST.get("modo", "")
    # Garden is a visual space; retain the separately recorded real cultivation location.
    existing = Practica.objects.filter(participante=request.user, planta__in=[p["slug"] for p in plants]).select_related("jardin")
    occupied = jardin.cultivos.filter(posicion=posicion).exists()
    error = "Este lugar ya está ocupado. Elige otro espacio." if occupied else ""
    if request.method == "POST" and not occupied:
        with transaction.atomic():
            # Serialize all placements for this account, including moves across gardens.
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            if jardin.cultivos.filter(posicion=posicion).exists():
                error = "Alguien acaba de ocupar este lugar. Elige otro espacio."
            else:
                practice = None
                if mode == "existente":
                    candidate = request.POST.get("cultivo", "")
                    import uuid
                    try:
                        candidate = uuid.UUID(candidate)
                    except (ValueError, TypeError):
                        error = "Selecciona uno de tus cultivos."
                    else:
                        practice = get_object_or_404(existing, pk=candidate)
                elif mode == "seleccionar":
                    # Re-check educational access on POST, never trust the visible cards.
                    plant = next((p for p in plantas_desbloqueadas(request.user)
                                  if p["slug"] == request.POST.get("planta")), None)
                    if plant is None:
                        error = "Esta planta todavía no está desbloqueada. Continúa tu aprendizaje."
                    else:
                        practice = Practica(
                            participante=request.user, planta=plant["slug"],
                            titulo=f"{plant['nombre']} · Espacio {posicion}",
                            inicio=timezone.localdate(), espacio="Lugar real por confirmar",
                            objetivo="Observar y registrar los cambios de mi planta.",
                        )
                else:
                    error = "Elige una forma de ocupar el espacio."
                if practice is not None:
                    previous = {"jardin": practice.jardin_id, "posicion": practice.posicion}
                    practice.jardin = jardin
                    practice.posicion = posicion
                    practice.save()
                    EventoPractica.objects.create(practica=practice, actor=request.user,
                        accion="ubicada_en_jardin", detalle={"antes": previous, "jardin": jardin.pk, "posicion": posicion})
                    messages.success(request, "Tu cultivo quedó en el espacio elegido. Su historial se conserva.")
                    return redirect(garden_url(jardin) + f"&cultivo={practice.pk}")
    return render(request, "panel/seleccionar_planta.html", {"hoy": timezone.localdate(), "seleccion": request.POST.get("planta", ""), "jardin": jardin, "posicion": posicion,
        "existentes": existing, "error": error, "ocupado": occupied, "plantas_disponibles": plants})


@login_required
@require_POST
def liberar(request, pk):
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        practice = get_object_or_404(Practica, pk=pk, participante=request.user)
        garden = practice.jardin
        before = {"jardin": practice.jardin_id, "posicion": practice.posicion}
        practice.jardin = None
        practice.posicion = None
        practice.save(update_fields=["jardin", "posicion"])
        EventoPractica.objects.create(practica=practice, actor=request.user, accion="espacio_liberado", detalle=before)
    messages.success(request, "Espacio libre. El cultivo y su bitácora siguen en Mis cultivos.")
    return redirect(garden_url(garden) if garden else reverse("workspace"))
