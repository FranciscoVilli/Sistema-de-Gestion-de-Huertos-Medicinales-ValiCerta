import hashlib
import re
from django import forms
from .models import Pregunta, Respuesta, PerfilComunitario, JardinCompartido, Comunidad
from .access import member_groups

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

class GrupoForm(PlainForm):
    class Meta:
        model=Comunidad
        fields=['nombre','descripcion']
        widgets={'descripcion':forms.Textarea(attrs={'rows':3})}

class PreguntaForm(PlainForm):
    opciones_encuesta = forms.CharField(required=False, label='Opciones de la encuesta', widget=forms.Textarea(attrs={'rows':3, 'placeholder':'Una opción por línea (de 2 a 6)'}))
    def clean_foto(self):
        value = self.cleaned_data.get('foto')
        if value and getattr(value, 'size', 0) > 8 * 1024 * 1024:
            raise forms.ValidationError('La foto debe pesar como máximo 8 MB.')
        if value and hasattr(value, 'image') and value.image.format not in ('JPEG','PNG','WEBP'):
            raise forms.ValidationError('Usa una foto JPG, PNG o WebP.')
        return value
    def clean_enlace(self):
        value=self.cleaned_data.get('enlace','')
        if value and not value.lower().startswith(('http://','https://')):
            raise forms.ValidationError('Usa un enlace que empiece por https:// o http://.')
        return value
    def clean_video(self):
        from pathlib import Path
        value = self.cleaned_data.get('video')
        if value and hasattr(value, 'content_type'):
            if value.size > 40 * 1024 * 1024:
                raise forms.ValidationError('El video debe pesar como máximo 40 MB.')
            head = value.read(32); value.seek(0)
            ext = Path(value.name).suffix.lower()
            if not ((ext == '.mp4' and head[4:8] == b'ftyp') or (ext == '.webm' and head[:4] == bytes.fromhex('1a45dfa3'))):
                raise forms.ValidationError('Usa un archivo de video MP4 o WebM válido.')
        return value
    def clean_opciones_encuesta(self):
        options = [line.strip() for line in self.cleaned_data.get('opciones_encuesta','').splitlines() if line.strip()]
        if options and (not 2 <= len(options) <= 6 or any(len(x)>100 for x in options) or len(set(x.casefold() for x in options)) != len(options)):
            raise forms.ValidationError('Escribe entre 2 y 6 opciones diferentes, de hasta 100 caracteres.')
        if self.instance.pk and self.instance.votos_encuesta.exists() and options != self.instance.encuesta:
            raise forms.ValidationError('Una encuesta con respuestas ya no puede cambiar sus opciones.')
        return options
    def save(self, commit=True):
        obj=super().save(commit=False)
        obj.encuesta=self.cleaned_data.get('opciones_encuesta', [])
        if commit: obj.save()
        return obj

    def __init__(self,*args,user=None,**kwargs):
        super().__init__(*args,**kwargs)
        self.fields['opciones_encuesta'].initial='\n'.join(self.instance.encuesta or [])
        self.fields['foto'].widget=forms.FileInput(attrs={'accept':'image/jpeg,image/png,image/webp'})
        self.fields['video'].widget=forms.FileInput(attrs={'accept':'video/mp4,video/webm'})
        self.fields['comunidad'].queryset=member_groups(user)
        self.fields['comunidad'].empty_label='Foro general'
        self.fields['visibilidad'].required=False
        self.fields['tipo'].required=False
        self.fields['tipo'].widget=forms.RadioSelect(choices=Pregunta.TIPOS)
        self.fields['titulo'].widget.attrs.update({'placeholder':'Dale un título a tu publicación…','class':'composer-title','aria-label':'Título de la publicación'})
        self.fields['contenido'].widget.attrs.update({'placeholder':'¿Qué quieres compartir con la comunidad? Cuenta tu experiencia, pregunta o consejo…','class':'composer-text','rows':6,'aria-label':'Contenido de la publicación'})
        self.fields['visibilidad'].choices=[('publico','Público'),('privado','Solo mi comunidad')]
        if self.instance.pk:
            self.fields['comunidad'].disabled=True
    def clean(self):
        data=super().clean()
        data['visibilidad']=data.get('visibilidad') or 'publico'
        data['tipo']=data.get('tipo') or 'pregunta'
        if data['visibilidad']=='privado' and not data.get('comunidad'):
            self.add_error('comunidad','Selecciona tu comunidad para publicar un tema privado.')
        return data
    class Meta:
        model=Pregunta
        fields=['comunidad','visibilidad','tipo','titulo','contenido','foto','video','enlace']
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

class CompartirForm(forms.ModelForm):
    visible=forms.BooleanField(required=False,label='Mostrar este jardín en el mapa comunitario')
    class Meta:
        model=JardinCompartido
        fields=['visible']
