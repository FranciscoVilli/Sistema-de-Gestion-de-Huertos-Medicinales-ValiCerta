from django import forms

from huertos_medicinales.aprendizaje.catalogo import PLANTAS

from .models import Bodega
from .models import Comunidad
from .models import HuertoReal
from .models import Miembro

# Largo del codigo unico de cada persona.
LARGO_CODIGO = 6


class ComunidadForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["latitud"].required = True
        self.fields["longitud"].required = True

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


class AgregarPorCodigoForm(forms.Form):
    codigo = forms.CharField(
        label="Código único de la persona",
        max_length=6,
        min_length=6,
        help_text="Pídele a la persona su código de 6 dígitos (está en Mi cuenta).",
    )

    def clean_codigo(self):
        code = self.cleaned_data["codigo"].strip()
        if len(code) != LARGO_CODIGO or not code.isascii() or not code.isdigit():
            msg = "Escribe un código de seis dígitos."
            raise forms.ValidationError(msg)
        return code


class HuertoRealForm(forms.ModelForm):
    plantas = forms.MultipleChoiceField(
        label="Plantas medicinales que cultivan",
        choices=[(planta["slug"], planta["nombre"]) for planta in PLANTAS],
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=(
            "El tipo de suelo, el agua de riego y el abono se recomiendan "
            "según lo que elijas aquí."
        ),
    )

    class Meta:
        model = HuertoReal
        fields = [
            "provincia",
            "parroquia",
            "plantas",
            "tipo_diseno",
            "tecnica_diseno",
            "tipo_cerca",
            "detalle_cerca",
            "area_total",
            "unidad_area",
            "detalle_riego",
            "detalle_abono",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields["plantas"].initial = self.instance.plantas


class BodegaForm(forms.ModelForm):
    class Meta:
        model = Bodega
        fields = [
            "tiene_espacio_herramientas",
            "detalle_herramientas",
            "tiene_espacio_semillas",
            "detalle_semillas",
            "tiene_espacio_abonos",
            "detalle_abonos",
        ]
