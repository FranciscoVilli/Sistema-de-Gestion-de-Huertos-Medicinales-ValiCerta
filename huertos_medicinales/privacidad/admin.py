from django.contrib import admin

from huertos_medicinales.common.admin import SoloLectura

from .models import AceptacionCondiciones
from .models import PreferenciaCookies
from .models import RespuestaDerecho
from .models import SolicitudDerecho


@admin.register(PreferenciaCookies)
class PreferenciaAdmin(SoloLectura):
    list_display = ["id", "usuario", "mapas_externos", "version", "creada"]
    list_filter = ["mapas_externos", "version"]


@admin.register(SolicitudDerecho)
class SolicitudAdmin(SoloLectura):
    list_display = ["id", "usuario", "tipo", "creada"]
    list_filter = ["tipo"]


admin.site.register(AceptacionCondiciones, SoloLectura)
admin.site.register(RespuestaDerecho, SoloLectura)
