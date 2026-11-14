from django.contrib import admin

from huertos_medicinales.common.admin import SoloLectura

from .models import AceptacionCondiciones
from .models import PreferenciaCookies


@admin.register(PreferenciaCookies)
class PreferenciaAdmin(SoloLectura):
    list_display = ["id", "usuario", "mapas_externos", "version", "creada"]
    list_filter = ["mapas_externos", "version"]


admin.site.register(AceptacionCondiciones, SoloLectura)
