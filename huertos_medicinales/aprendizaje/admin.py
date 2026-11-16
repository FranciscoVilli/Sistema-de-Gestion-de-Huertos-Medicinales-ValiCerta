from django.contrib import admin

from huertos_medicinales.common.admin import SoloLectura

# Django solo descubre admin.py: sin este import la gestion editorial de
# lecciones, capitulos, evaluaciones y rutas (HU-015) no aparecia en /admin/.
from . import educational_admin  # noqa: F401
from .models import IntentoEvaluacion
from .models import Logro


@admin.register(IntentoEvaluacion)
class IntentoAdmin(SoloLectura):
    list_display = ["user", "leccion", "resultado", "creado"]
    list_filter = ["resultado", "leccion"]


@admin.register(Logro)
class LogroAdmin(SoloLectura):
    list_display = ["user", "leccion", "xp", "created_at"]
