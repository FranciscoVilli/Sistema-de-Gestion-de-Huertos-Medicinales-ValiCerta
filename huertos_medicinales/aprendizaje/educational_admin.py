from django import forms
from django.contrib import admin
from django.core.exceptions import ValidationError

from huertos_medicinales.common.admin import SoloLectura

from .educational_models import VISIBLE
from .educational_models import BloqueEducativo
from .educational_models import CapituloEducativo
from .educational_models import Competencia
from .educational_models import CompetenciaAdquirida
from .educational_models import DesbloqueoRuta
from .educational_models import EvaluacionEducativa
from .educational_models import FuenteEducativa
from .educational_models import IntentoCapitulo
from .educational_models import LeccionEducativa
from .educational_models import ProgresoLeccion
from .educational_models import RevisionEducativa
from .educational_models import RutaEducativa


class LessonAdminForm(forms.ModelForm):
    class Meta:
        model = LeccionEducativa
        fields = "__all__"

    def clean(self):
        data = super().clean()
        if data.get("estado") in VISIBLE and not data.get("fuentes"):
            raise ValidationError(
                "Asocia al menos una fuente antes de publicar o habilitar el piloto.",
            )
        return data


@admin.register(LeccionEducativa)
class LessonAdmin(admin.ModelAdmin):
    form = LessonAdminForm
    list_display = ["titulo", "capitulo", "estado", "revision", "revisada"]
    list_filter = ["estado", "capitulo"]
    search_fields = ["titulo", "slug"]
    filter_horizontal = ["fuentes"]
    readonly_fields = ["revision"]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        lesson = form.instance
        record = lesson.historial.get(numero=lesson.revision)
        record.actor = request.user
        record.contenido["fuentes"] = list(
            lesson.fuentes.values("titulo", "url", "institucion", "consultada"),
        )
        for source in record.contenido["fuentes"]:
            source["consultada"] = str(source["consultada"])
        record.save(update_fields=["actor", "contenido"])


@admin.register(EvaluacionEducativa)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ["titulo", "capitulo", "estado", "porcentaje_minimo"]
    filter_horizontal = ["competencias"]


@admin.register(RutaEducativa)
class RouteAdmin(admin.ModelAdmin):
    list_display = ["nombre", "especie", "estado"]
    filter_horizontal = ["requisitos", "lecciones"]


@admin.register(CapituloEducativo)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ["numero", "titulo", "bloque", "estado"]
    list_filter = ["bloque", "estado"]
    prepopulated_fields = {"slug": ("titulo",)}


for model in [BloqueEducativo, FuenteEducativa, Competencia]:
    admin.site.register(model)


@admin.register(IntentoCapitulo)
class AttemptAdmin(SoloLectura):
    list_display = [
        "user",
        "evaluacion",
        "porcentaje",
        "aprobado",
        "creado",
        "finalizado",
    ]
    list_filter = ["aprobado", "evaluacion"]


@admin.register(CompetenciaAdquirida)
class CompetencyAdmin(SoloLectura):
    list_display = ["user", "competencia", "intento", "adquirida"]


for model in [ProgresoLeccion, RevisionEducativa, DesbloqueoRuta]:
    admin.site.register(model, SoloLectura)
