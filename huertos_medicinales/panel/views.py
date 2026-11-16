from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.utils import timezone

from huertos_medicinales.aprendizaje.medicinal import FICHAS_MEDICINALES
from huertos_medicinales.aprendizaje.services import estado
from huertos_medicinales.comunidades.models import JardinCompartido
from huertos_medicinales.seguimiento.models import ActividadCalendario
from huertos_medicinales.seguimiento.models import Jardin
from huertos_medicinales.seguimiento.models import Observacion
from huertos_medicinales.seguimiento.models import Practica
from huertos_medicinales.seguimiento.views import plantas_disponibles

from .lunar import phase_on

# Horas en que cambia el saludo de la pantalla de inicio.
HORA_TARDE = 12
HORA_NOCHE = 19


@login_required
# Funcion extensa heredada; dividirla queda registrado como deuda tecnica (V2).
def inicio(request):  # noqa: C901, PLR0915
    learning = estado(request.user)
    practices = list(
        Practica.objects.filter(participante=request.user)
        .select_related("jardin")
        .prefetch_related("observaciones"),
    )
    for p in practices:
        p.foto_reciente = next((o.foto for o in p.observaciones.all() if o.foto), None)
        p.reciente = next(iter(p.observaciones.all()), None)
        p.imagen = p.foto_reciente
        p.progreso = (
            min(100, round(p.dias_transcurridos * 100 / p.info_planta["dias_madurez"]))
            if p.info_planta
            else 0
        )
    gardens = Jardin.objects.filter(propietario=request.user)
    garden_id = request.GET.get("jardin")
    if garden_id is not None:
        if not garden_id.isdecimal():
            raise Http404
        garden = get_object_or_404(gardens, pk=int(garden_id))
    else:
        garden = gardens.first()
    garden_practices = [p for p in practices if garden and p.jardin_id == garden.pk]
    selected = next(
        (p for p in garden_practices if str(p.pk) == request.GET.get("cultivo")),
        None,
    )
    slots = [
        {
            "numero": i,
            "cultivo": next((p for p in garden_practices if p.posicion == i), None),
        }
        for i in range(1, 7)
    ]
    free_count = sum(slot["cultivo"] is None for slot in slots)
    primer_libre = next(
        (slot["numero"] for slot in slots if slot["cultivo"] is None),
        None,
    )
    today = timezone.localdate()
    next_water = (
        ActividadCalendario.objects.filter(
            practica__participante=request.user,
            tipo="riego",
            fecha__gte=today,
            completada=False,
        )
        .select_related("practica")
        .first()
    )
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
        zone["seleccionada"] = (
            any(p.pk == selected.pk for p in zone["cultivos"]) if selected else False
        )
    observations = Observacion.objects.filter(
        practica__participante=request.user,
    ).select_related("practica")
    latest = selected.observaciones.first() if selected else None
    stages = []
    progress = 0
    if selected and selected.info_planta:
        info = selected.info_planta
        progress = min(
            100,
            round(selected.dias_transcurridos * 100 / info["dias_madurez"]),
        )
        stages = [
            {"name": "Siembra", "day": 0, "active": True},
            {
                "name": "Germinación",
                "day": info["dias_germinacion"],
                "active": selected.dias_transcurridos >= info["dias_germinacion"],
            },
            {
                "name": "Madurez",
                "day": info["dias_madurez"],
                "active": selected.dias_transcurridos >= info["dias_madurez"],
            },
        ]
    species = []
    for slug in ("manzanilla", "menta", "calendula", "romero"):
        items = [p for p in practices if p.planta == slug]
        if items:
            target = (
                selected
                if selected in items
                else next((p for p in items if p.estado == "activa"), items[0])
            )
            species.append(
                {
                    "slug": slug,
                    "nombre": target.planta_nombre,
                    "target": target,
                    "count": len(items),
                    "selected": selected in items,
                },
            )
    hour = timezone.localtime().hour
    compartido = (
        JardinCompartido.objects.filter(jardin=garden).first() if garden else None
    )
    clima_jardin = (garden.clima or {}) if garden else {}
    compartir_disponible = (
        bool(garden)
        and clima_jardin.get("latitude") is not None
        and clima_jardin.get("longitude") is not None
    )
    perfil_comunitario = getattr(request.user, "perfil_comunitario", None)
    sector_compartido = None
    if compartir_disponible:
        sector_compartido = (
            clima_jardin.get("name")
            if clima_jardin.get("source") != "browser"
            else None
        )
        sector_compartido = (
            sector_compartido
            or (perfil_comunitario.localidad if perfil_comunitario else None)
            or "Ubicación aproximada"
        )
    return render(
        request,
        "panel/inicio.html",
        {
            **learning,
            "jardines": gardens,
            "jardin": garden,
            "lugares": slots,
            "libres": free_count,
            "sin_colocar": sum(p.jardin_id is None for p in practices),
            "practicas": practices,
            "seleccionada": selected,
            "espacios_huerto": zones,
            "especies_escena": species,
            "primer_libre": primer_libre,
            "next_water": next_water,
            "hoy": today,
            "luna": phase_on(today),
            "saludo": "Buenos días"
            if hour < HORA_TARDE
            else "Buenas tardes"
            if hour < HORA_NOCHE
            else "Buenas noches",
            "nombre": request.user.name.split()[0]
            if request.user.name
            else "cultivador",
            "total_practicas": len(practices),
            "activas": sum(p.estado == "activa" for p in practices),
            "puede_sembrar": bool(plantas_disponibles(request.user)),
            "dias_ultima": max(
                0,
                (timezone.localdate() - max(p.inicio for p in practices)).days,
            )
            if practices
            else None,
            "observaciones": observations[:4],
            "ultima_observacion": latest,
            "etapas": stages,
            "progreso": progress,
            "medicinal": FICHAS_MEDICINALES.get(selected.planta) if selected else None,
            "detalle_registros": list(selected.observaciones.all()[:4])
            if selected
            else [],
            "detalle_total_registros": selected.observaciones.count()
            if selected
            else 0,
            "detalle_riego": ActividadCalendario.objects.filter(
                practica=selected,
                tipo="riego",
                completada=True,
            )
            .order_by("-fecha", "-pk")
            .first()
            if selected
            else None,
            "detalle_pendientes": ActividadCalendario.objects.filter(
                practica=selected,
                completada=False,
            ).order_by("fecha", "hora")[:4]
            if selected
            else [],
            "garden_compartido": bool(compartido and compartido.visible),
            "compartir_disponible": compartir_disponible,
            "sector_compartido": sector_compartido,
            "perfil_listo": bool(perfil_comunitario and perfil_comunitario.visible),
        },
    )
