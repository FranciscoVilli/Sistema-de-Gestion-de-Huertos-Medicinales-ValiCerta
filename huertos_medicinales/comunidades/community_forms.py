import hashlib
import re
from django import forms
from .models import Pregunta, Respuesta, PerfilComunitario, JardinCompartido

def fingerprint(*parts):
    return hashlib.sha256(' '.join(' '.join(parts).casefold().split()).encode()).hexdigest()

class PlainForm(forms.ModelForm):
    def clean(self):
        data=super().clean()
        for key in ('titulo','contenido','nombre','localidad','experiencia'):
            if key in data and isinstance(data[key],str):
                data[key]=data[key].strip()
                if re.search(r'<\s*/?\s*[a-z!]',data[key],re.I):
                    self.add_error(key,'Escribe texto sin etiquetas HTML.')
        return data

class PreguntaForm(PlainForm):
    class Meta:
        model=Pregunta
        fields=['titulo','categoria','contenido']
        widgets={'contenido':forms.Textarea(attrs={'rows':5})}

class RespuestaForm(PlainForm):
    class Meta:
        model=Respuesta
        fields=['contenido']
        widgets={'contenido':forms.Textarea(attrs={'rows':4})}

class PerfilForm(PlainForm):
    class Meta:
        model=PerfilComunitario
        fields=['nombre','localidad','nivel','anos','experiencia','visible']
        widgets={'experiencia':forms.Textarea(attrs={'rows':3})}
    def clean_nombre(self):
        name=self.cleaned_data['nombre'].strip()
        if '@' in name: raise forms.ValidationError('Usa un nombre público, no tu correo electrónico.')
        return name

class CompartirForm(PlainForm):
    class Meta:
        model=JardinCompartido
        fields=['localidad','latitud','longitud','visible']
        labels={'latitud':'Latitud aproximada (2 decimales)','longitud':'Longitud aproximada (2 decimales)'}
