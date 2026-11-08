from django.contrib import admin
from django.db import transaction

from huertos_medicinales.common.admin import SoloLectura

from .models import Devolucion
from .models import EventoPractica
from .models import Observacion
from .models import Practica


@admin.register(Practica)
class PracticaAdmin(SoloLectura):
    list_display = [
        "titulo",
        "planta",
        "participante",
        "estado",
        "dias_adelanto",
        "creada",
    ]
    list_filter = ["estado"]
    search_fields = ["titulo", "planta", "participante__email"]
    actions = ["adelantar_una_semana"]

    def has_adelantar_permission(self, request):
        return request.user.has_perm("seguimiento.avanzar_tiempo_practica")

    @admin.action(
        description="Adelantar 7 días (demostraciones)",
        permissions=["adelantar"],
    )
    def adelantar_una_semana(self, request, queryset):
        with transaction.atomic():
            for practica in queryset.select_for_update():
                practica.dias_adelanto += 7
                practica.save(update_fields=["dias_adelanto", "actualizada"])
                EventoPractica.objects.create(
                    practica=practica,
                    actor=request.user,
                    accion="adelanto_tiempo",
                    detalle={"dias_adelanto": practica.dias_adelanto},
                )
        self.message_user(request, "Se adelantaron 7 días en las prácticas elegidas.")


@admin.register(EventoPractica)
class EventoAdmin(SoloLectura):
    list_display = ["practica", "actor", "accion", "creado"]
    list_filter = ["accion"]


admin.site.register(Observacion, SoloLectura)
admin.site.register(Devolucion, SoloLectura)
