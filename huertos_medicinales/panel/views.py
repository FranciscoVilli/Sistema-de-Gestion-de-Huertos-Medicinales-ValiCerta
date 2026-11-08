from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone

from huertos_medicinales.aprendizaje.services import estado
from huertos_medicinales.aprendizaje.medicinal import FICHAS_MEDICINALES
from huertos_medicinales.seguimiento.models import ActividadCalendario
from huertos_medicinales.seguimiento.models import Devolucion
from huertos_medicinales.seguimiento.models import Jardin
from huertos_medicinales.seguimiento.models import Observacion
from huertos_medicinales.seguimiento.models import Practica


@login_required
def inicio(request):
    learning = estado(request.user)
    practices = list(Practica.objects.filter(participante=request.user).prefetch_related("observaciones"))
    for p in practices:
        p.foto_reciente = next((o.foto for o in p.observaciones.all() if o.foto), None)
    gardens = Jardin.objects.filter(propietario=request.user)
    garden_id = request.GET.get("jardin")
    if garden_id is not None:
        if not garden_id.isdecimal():
            from django.http import Http404
            raise Http404
        garden = get_object_or_404(gardens, pk=int(garden_id))
    else:
        garden = gardens.first()
    garden_practices = [p for p in practices if garden and p.jardin_id == garden.pk]
    selected = next((p for p in garden_practices if str(p.pk) == request.GET.get("cultivo")), None)
    slots = [{"numero": i, "cultivo": next((p for p in garden_practices if p.posicion == i), None)} for i in range(1, 7)]
    free_count = sum(slot["cultivo"] is None for slot in slots)
    primer_libre = next((slot["numero"] for slot in slots if slot["cultivo"] is None), None)
    today = timezone.localdate()
    next_water = ActividadCalendario.objects.filter(
        practica__participante=request.user, tipo="riego", fecha__gte=today, completada=False,
    ).select_related("practica").first()
    spaces = {}
    for p in practices:
        name = p.espacio.strip() or "Mi espacio"
        key = name.casefold()
        if key not in spaces:
            spaces[key] = {"nombre": name, "cultivos": []}
        spaces[key]["cultivos"].append(p)
    zones = list(spaces.values())
    for index, zone in enumerate(zones, 1):
        zone["numero"] = index
        zone["seleccionada"] = any(p.pk == selected.pk for p in zone["cultivos"]) if selected else False
    observations = Observacion.objects.filter(practica__participante=request.user).select_related("practica")
    latest = selected.observaciones.first() if selected else None
    stages = []
    progress = 0
    if selected and selected.info_planta:
        info = selected.info_planta
        progress = min(100, round(selected.dias_transcurridos * 100 / info["dias_madurez"]))
        stages = [
            {"name": "Siembra", "day": 0, "active": True},
            {"name": "Germinación", "day": info["dias_germinacion"], "active": selected.dias_transcurridos >= info["dias_germinacion"]},
            {"name": "Madurez", "day": info["dias_madurez"], "active": selected.dias_transcurridos >= info["dias_madurez"]},
        ]
    species = []
    for slug in ("manzanilla", "menta", "calendula", "romero"):
        items = [p for p in practices if p.planta == slug]
        if items:
            target = selected if selected in items else next((p for p in items if p.estado == "activa"), items[0])
            species.append({"slug": slug, "nombre": target.planta_nombre, "target": target, "count": len(items), "selected": selected in items})
    hour = timezone.localtime().hour
    return render(request, "panel/inicio.html", {
        **learning, "jardines": gardens, "jardin": garden, "lugares": slots, "libres": free_count, "sin_colocar": sum(p.jardin_id is None for p in practices), "practicas": practices, "seleccionada": selected, "espacios_huerto": zones, "especies_escena": species,
        "primer_libre": primer_libre, "next_water": next_water, "hoy": today,
        "saludo": "Buenos días" if hour < 12 else "Buenas tardes" if hour < 19 else "Buenas noches",
        "nombre": request.user.name.split()[0] if request.user.name else "cultivador",
        "total_practicas": len(practices), "activas": sum(p.estado == "activa" for p in practices),
        "dias_ultima": max(0, (timezone.localdate()-max(p.inicio for p in practices)).days) if practices else None,
        "observaciones": observations[:4], "ultima_observacion": latest,
        "etapas": stages, "progreso": progress,
        "medicinal": FICHAS_MEDICINALES.get(selected.planta) if selected else None,
        "detalle_registros": list(selected.observaciones.all()[:4]) if selected else [],
        "detalle_total_registros": selected.observaciones.count() if selected else 0,
        "detalle_riego": ActividadCalendario.objects.filter(practica=selected, tipo="riego", completada=True).order_by("-fecha", "-pk").first() if selected else None,
        "detalle_pendientes": ActividadCalendario.objects.filter(practica=selected, completada=False).order_by("fecha", "hora")[:4] if selected else [],
        "devoluciones": Devolucion.objects.filter(practica__participante=request.user).select_related("practica")[:3],
    })
