from django import forms

from .models import RespuestaDerecho
from .models import SolicitudDerecho


class SolicitudForm(forms.ModelForm):
    class Meta:
        model = SolicitudDerecho
        fields = ["tipo", "detalle"]
        widgets = {"detalle": forms.Textarea(attrs={"rows": 5})}
        help_texts = {
            "detalle": (
                "No incluyas contraseñas, documentos de identidad ni "
                "información médica. La solicitud no ejecuta por sí misma "
                "una eliminación: debe gestionarse y responderse."
            ),
        }


class RespuestaForm(forms.ModelForm):
    class Meta:
        model = RespuestaDerecho
        fields = ["estado", "texto"]
        widgets = {"texto": forms.Textarea(attrs={"rows": 5})}
