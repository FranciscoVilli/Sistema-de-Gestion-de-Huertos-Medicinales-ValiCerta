from django import forms
from django.utils import timezone

from .models import Devolucion
from .models import Observacion
from .models import Practica


class PracticaForm(forms.ModelForm):
    class Meta:
        model = Practica
        fields = ["titulo", "planta", "inicio", "espacio", "objetivo"]
        labels = {"titulo": "Nombre del cultivo"}
        widgets = {
            "inicio": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            "objetivo": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, plantas_disponibles=(), **kwargs):
        super().__init__(*args, **kwargs)
        choices = [(item["slug"], item["nombre"]) for item in plantas_disponibles]
        if self.instance.pk and self.instance.planta not in dict(choices):
            choices.append((self.instance.planta, self.instance.planta_nombre))
        self.fields["planta"] = forms.ChoiceField(
            label="Planta cultivada",
            choices=choices,
            help_text=(
                "Puedes registrar tu cultivo real sin requisitos educativos. Las prácticas guiadas tienen su propio recorrido."
            ),
        )

    def clean_inicio(self):
        fecha = self.cleaned_data["inicio"]
        if fecha > timezone.localdate():
            message = "La fecha de inicio no puede estar en el futuro."
            raise forms.ValidationError(message)
        return fecha


class ObservacionForm(forms.ModelForm):
    class Meta:
        model = Observacion
        fields = ["fecha", "accion", "resultado", "pregunta", "foto"]
        widgets = {
            "fecha": forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}),
            **{
                key: forms.Textarea(attrs={"rows": 3})
                for key in ["accion", "resultado", "pregunta"]
            },
        }

    def __init__(self, *args, practica, **kwargs):
        super().__init__(*args, **kwargs)
        self.practica = practica

    def clean_fecha(self):
        fecha = self.cleaned_data["fecha"]
        if fecha < self.practica.inicio or fecha > timezone.localdate():
            message = "Usa una fecha entre el inicio de la práctica y hoy."
            raise forms.ValidationError(message)
        return fecha


class DevolucionForm(forms.ModelForm):
    class Meta:
        model = Devolucion
        fields = ["texto"]
        widgets = {"texto": forms.Textarea(attrs={"rows": 4})}
