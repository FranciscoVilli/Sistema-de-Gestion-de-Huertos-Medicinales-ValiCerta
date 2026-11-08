from django import forms

from .models import Bodega
from .models import Comunidad
from .models import HuertoReal
from .models import Miembro


class ComunidadForm(forms.ModelForm):
    confirmar_publicacion = forms.BooleanField(
        label=(
            "Solicito publicar esta información y confirmo que puedo "
            "representar a esta comunidad"
        ),
        required=True,
    )

    class Meta:
        model = Comunidad
        fields = [
            "nombre",
            "provincia",
            "localidad",
            "descripcion",
            "encuentro",
            "plantas_destacadas",
            "latitud",
            "longitud",
        ]
        widgets = {
            "descripcion": forms.Textarea(attrs={"rows": 4}),
            "encuentro": forms.Textarea(attrs={"rows": 3}),
        }
        help_texts = {
            "latitud": (
                "Usa solo dos decimales para señalar el sector. Ejemplo: "
                "-0.18. No uses coordenadas de un domicilio."
            ),
            "longitud": (
                "Ejemplo: -78.47. El mapa mostrará una ubicación "
                "aproximada, no un acceso exacto."
            ),
        }


class SolicitudMiembroForm(forms.ModelForm):
    confirmar_solicitud = forms.BooleanField(
        label="Solicito unirme a esta comunidad",
        required=True,
    )

    class Meta:
        model = Miembro
        fields = ["fecha_nacimiento", "genero"]
        widgets = {"fecha_nacimiento": forms.DateInput(attrs={"type": "date"})}


class HuertoRealForm(forms.ModelForm):
    class Meta:
        model = HuertoReal
        fields = [
            "provincia", "parroquia", "direccion", "latitud", "longitud",
            "tipo_diseno", "tecnica_diseno", "tipo_cerca", "detalle_cerca",
            "area_total", "unidad_area", "tipo_suelo", "tipo_agua_riego",
            "detalle_riego", "tipo_abono", "detalle_abono",
        ]


class BodegaForm(forms.ModelForm):
    class Meta:
        model = Bodega
        fields = [
            "tiene_espacio_herramientas", "detalle_herramientas",
            "tiene_espacio_semillas", "detalle_semillas",
            "tiene_espacio_abonos", "detalle_abonos",
        ]
