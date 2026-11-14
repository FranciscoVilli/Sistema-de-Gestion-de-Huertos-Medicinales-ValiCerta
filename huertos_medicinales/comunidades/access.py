from functools import wraps
from urllib.parse import urlencode
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse
from .models import Comunidad, Miembro, Pregunta

REQUIRED_PROFILE = ('name','fecha_nacimiento','genero','telefono','direccion')

def profile_complete(user):
    return user.is_authenticated and all(str(getattr(user,key,'') or '').strip() for key in REQUIRED_PROFILE)

def require_profile(view):
    @wraps(view)
    def wrapped(request,*args,**kwargs):
        if not profile_complete(request.user):
            messages.info(request,'Completa tu nombre, fecha de nacimiento, género, teléfono y dirección en Mi cuenta antes de crear o unirte a una comunidad. Estos datos personales no se publican en el foro.')
            target=request.get_full_path() if request.method=='GET' else reverse('comunidades:listado')
            if request.method=='POST' and kwargs.get('pk'):
                target=reverse('comunidades:listado')+'?comunidad='+str(kwargs['pk'])
            return redirect(reverse('users:update')+'?'+urlencode({'next':target}))
        return view(request,*args,**kwargs)
    return wrapped

def member_groups(user):
    if not user.is_authenticated:return Comunidad.objects.none()
    return Comunidad.objects.filter(Q(responsable=user)|Q(miembros__usuario=user,miembros__estado=Miembro.Estado.APROBADA)).exclude(estado=Comunidad.Estado.RETIRADA).distinct()

def visible_questions(user):
    base=Pregunta.objects.filter(oculta=False,autor__is_active=True).filter(Q(comunidad__isnull=True)|~Q(comunidad__estado=Comunidad.Estado.RETIRADA))
    return base.filter(Q(visibilidad='publico')|Q(comunidad__in=member_groups(user)))

def may_post(user,group):
    return user.is_authenticated and (group is None or member_groups(user).filter(pk=group.pk).exists())
