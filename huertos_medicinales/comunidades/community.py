from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from huertos_medicinales.seguimiento.models import Jardin, Practica
from .models import Pregunta, Respuesta, PerfilComunitario, JardinCompartido
from .community_forms import PreguntaForm, RespuestaForm, PerfilForm, CompartirForm, fingerprint


def reglas(request):
    return render(request,'comunidades/reglas.html')

def public_name(user):
    profile=getattr(user,'perfil_comunitario',None)
    return profile.nombre if profile and profile.visible else f'Cultivador {user.pk}'

def allowed(user,item):
    return user.is_authenticated and (user.pk==item.autor_id or user.has_perm('comunidades.change_'+item._meta.model_name))

def decorate(items,user):
    for item in items:
        item.public_name=public_name(item.autor)
        item.can_edit=allowed(user,item)
    return items

def visible_gardens():
    return JardinCompartido.objects.filter(visible=True,jardin__propietario__is_active=True,jardin__propietario__perfil_comunitario__visible=True).select_related('jardin__propietario__perfil_comunitario').prefetch_related(Prefetch('jardin__cultivos',queryset=Practica.objects.filter(estado='activa')))

def markers():
    result=[]
    for shared in visible_gardens():
        owner=shared.jardin.propietario;profile=owner.perfil_comunitario
        plants=sorted({p.planta_nombre for p in shared.jardin.cultivos.all()})
        result.append({'id':shared.jardin_id,'name':shared.jardin.nombre,'owner':profile.nombre,'level':profile.get_nivel_display() or 'No declarada','years':profile.anos,'location':shared.localidad,'lat':float(shared.latitud),'lon':float(shared.longitud),'plants':plants,'species':len(plants),'profile':reverse('comunidades:perfil',args=[owner.pk])})
    return result

@never_cache
@require_GET
def map_data(request):
    items=markers()
    participants={x for x in JardinCompartido.objects.filter(visible=True,jardin__propietario__perfil_comunitario__visible=True,jardin__propietario__is_active=True).values_list('jardin__propietario_id',flat=True)}
    participants.update(Pregunta.objects.filter(oculta=False,autor__is_active=True).values_list('autor_id',flat=True))
    participants.update(Respuesta.objects.filter(oculta=False,pregunta__oculta=False,autor__is_active=True).values_list('autor_id',flat=True))
    return JsonResponse({'markers':items,'stats':{'gardens':len(items),'participants':len(participants),'questions':Pregunta.objects.filter(oculta=False,resuelta=False,autor__is_active=True).count()}})

@never_cache
def hub(request):
    query=request.GET.get('q','').strip()[:150];category=request.GET.get('categoria','');order=request.GET.get('orden','recientes')
    questions=Pregunta.objects.filter(oculta=False,autor__is_active=True).select_related('autor__perfil_comunitario').annotate(total_respuestas=Count('respuestas',filter=Q(respuestas__oculta=False,respuestas__autor__is_active=True)))
    if query: questions=questions.filter(Q(titulo__icontains=query)|Q(contenido__icontains=query))
    if category in dict(Pregunta.CATEGORIAS):questions=questions.filter(categoria=category)
    else:category=''
    if order=='populares':questions=questions.order_by('-total_respuestas','-creada','-pk')
    else:
        order='recientes'
        questions=questions.order_by('-creada','-pk')
    page=Paginator(questions,6).get_page(request.GET.get('page'))
    decorate(page.object_list,request.user)
    gardens=visible_gardens()
    participant_ids=set(gardens.values_list('jardin__propietario_id',flat=True))
    participant_ids.update(Pregunta.objects.filter(oculta=False,autor__is_active=True).values_list('autor_id',flat=True))
    participant_ids.update(Respuesta.objects.filter(oculta=False,pregunta__oculta=False,autor__is_active=True).values_list('autor_id',flat=True))
    featured=PerfilComunitario.objects.filter(visible=True,usuario__is_active=True).annotate(contributions=Count('usuario__respuestas_comunidad',filter=Q(usuario__respuestas_comunidad__oculta=False,usuario__respuestas_comunidad__pregunta__oculta=False),distinct=True)).order_by('-contributions','nombre')[:3]
    featured=list(featured)
    for member in featured:
        member.plants=sorted({p.planta_nombre for shared in visible_gardens().filter(jardin__propietario_id=member.usuario_id) for p in shared.jardin.cultivos.all()})
    return render(request,'comunidades/hub.html',{'page':page,'query':query,'category':category,'order':order,'categories':Pregunta.CATEGORIAS,'garden_count':gardens.count(),'participant_count':len(participant_ids),'open_count':Pregunta.objects.filter(oculta=False,resuelta=False,autor__is_active=True).count(),'featured':featured,'own_gardens':Jardin.objects.filter(propietario=request.user) if request.user.is_authenticated else []})

def modal(request,title,template,context,status=200):
    return render(request,'comunidades/modal_fragment.html' if request.GET.get('fragment')=='1' else 'comunidades/modal.html',{'modal_title':title,'modal_template':template,**context,'fragment':request.GET.get('fragment')=='1'},status=status)

def success(request,url):
    if request.GET.get('fragment')=='1':return JsonResponse({'redirect':url})
    return redirect(url)

@login_required
@never_cache
def question_edit(request,pk=None):
    item=get_object_or_404(Pregunta,pk=pk,oculta=False) if pk else None
    if item and not allowed(request.user,item):return HttpResponseForbidden('No puedes editar esta publicación.')
    form=PreguntaForm(request.POST or None,instance=item)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            obj=form.save(commit=False);obj.autor=item.autor if item else request.user
            obj.huella=fingerprint(obj.titulo,obj.contenido)
            duplicates=Pregunta.objects.filter(autor=obj.autor,huella=obj.huella,oculta=False)
            if item:duplicates=duplicates.exclude(pk=item.pk)
            if duplicates.exists():form.add_error(None,'Ya publicaste esta pregunta. Puedes continuar en sus respuestas.')
            else:
                obj.save();return success(request,reverse('comunidades:pregunta',args=[obj.pk]))
    return modal(request,'Editar pregunta' if item else 'Nueva pregunta','comunidades/form_content.html',{'form':form,'submit_label':'Guardar pregunta'},400 if request.method=='POST' else 200)

@never_cache
def question(request,pk):
    item=get_object_or_404(Pregunta.objects.select_related('autor__perfil_comunitario'),pk=pk,oculta=False,autor__is_active=True)
    decorate([item],request.user)
    form=RespuestaForm(request.POST or None)
    if request.method=='POST':
        if not request.user.is_authenticated:return HttpResponseForbidden('Inicia sesión para participar.')
        if form.is_valid():
            with transaction.atomic():
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
                obj=form.save(commit=False);obj.autor=request.user;obj.pregunta=item;obj.huella=fingerprint(obj.contenido)
                if Respuesta.objects.filter(pregunta=item,autor=request.user,huella=obj.huella,oculta=False).exists():form.add_error('contenido','Esta respuesta ya fue publicada.')
                else:
                    obj.save();return success(request,reverse('comunidades:pregunta',args=[pk]))
    answers=Paginator(Respuesta.objects.filter(pregunta=item,oculta=False,autor__is_active=True).select_related('autor__perfil_comunitario'),10).get_page(request.GET.get('page'))
    decorate(answers.object_list,request.user)
    return modal(request,item.titulo,'comunidades/question_content.html',{'question':item,'answers':answers,'form':form},400 if request.method=='POST' else 200)

@login_required
@require_POST
def question_action(request,pk):
    item=get_object_or_404(Pregunta,pk=pk,oculta=False)
    if not allowed(request.user,item):return HttpResponseForbidden()
    if request.POST.get('action')=='hide':item.oculta=True;fields=['oculta']
    elif request.POST.get('action')=='resolve':item.resuelta=request.POST.get('resolved')=='1';fields=['resuelta']
    else:return HttpResponseForbidden()
    item.save(update_fields=fields)
    return success(request,reverse('comunidades:listado'))

@login_required
@never_cache
def answer_edit(request,pk):
    item=get_object_or_404(Respuesta,pk=pk,oculta=False,pregunta__oculta=False)
    if not allowed(request.user,item):return HttpResponseForbidden()
    form=RespuestaForm(request.POST or None,instance=item)
    if request.method=='POST' and request.POST.get('action')=='hide':
        item.oculta=True;item.save(update_fields=['oculta']);return success(request,reverse('comunidades:pregunta',args=[item.pregunta_id]))
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            obj=form.save(commit=False);obj.huella=fingerprint(obj.contenido)
            if Respuesta.objects.filter(pregunta=obj.pregunta,autor=obj.autor,huella=obj.huella,oculta=False).exclude(pk=obj.pk).exists():form.add_error(None,'Ya compartiste esa respuesta.')
            else:obj.save();return success(request,reverse('comunidades:pregunta',args=[obj.pregunta_id]))
    return modal(request,'Editar respuesta','comunidades/form_content.html',{'form':form,'submit_label':'Guardar respuesta'},400 if request.method=='POST' else 200)

@login_required
@never_cache
def profile_edit(request):
    item=PerfilComunitario.objects.filter(usuario=request.user).first()
    form=PerfilForm(request.POST or None,instance=item,initial={'nombre':f'Cultivador {request.user.pk}'})
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False);obj.usuario=request.user;obj.save();return success(request,reverse('comunidades:listado'))
    return modal(request,'Mi perfil comunitario','comunidades/form_content.html',{'form':form,'submit_label':'Guardar perfil','notice':'Tu nombre, experiencia y jardines compartidos serán visibles solo si activas tu perfil. No incluyas correo, teléfono ni dirección. El nivel es declarado por ti.'},400 if request.method=='POST' else 200)

@never_cache
def profile(request,pk):
    item=get_object_or_404(PerfilComunitario,usuario_id=pk,visible=True,usuario__is_active=True)
    shared=visible_gardens().filter(jardin__propietario_id=pk)
    plants=sorted({p.planta_nombre for s in shared for p in s.jardin.cultivos.all()})
    questions=Pregunta.objects.filter(autor_id=pk,oculta=False)[:8]
    answers=Respuesta.objects.filter(autor_id=pk,oculta=False,pregunta__oculta=False).select_related('pregunta')[:8]
    return modal(request,item.nombre,'comunidades/profile_content.html',{'profile':item,'plants':plants,'shared':shared,'questions':questions,'answers':answers})

@login_required
@never_cache
def share(request,pk):
    garden=get_object_or_404(Jardin,pk=pk,propietario=request.user)
    instance=JardinCompartido.objects.filter(jardin=garden).first()
    climate=garden.clima or {}
    form=CompartirForm(request.POST or None,instance=instance,initial={'localidad':climate.get('name','') if climate.get('source')!='browser' else '', 'latitud':round(float(climate['latitude']),2) if climate.get('latitude') is not None else None,'longitud':round(float(climate['longitude']),2) if climate.get('longitude') is not None else None})
    if request.method=='POST' and form.is_valid():
        if form.cleaned_data['visible'] and not PerfilComunitario.objects.filter(usuario=request.user,visible=True).exists():form.add_error('visible','Activa primero tu perfil comunitario para publicar este jardín.')
        else:
            obj=form.save(commit=False);obj.jardin=garden;obj.save();return success(request,reverse('comunidades:listado'))
    return modal(request,'Compartir '+garden.nombre,'comunidades/form_content.html',{'form':form,'submit_label':'Guardar privacidad','notice':'Compartes el nombre del jardín, sus plantas y este sector aproximado. La ubicación del clima no se publica automáticamente. Desmarca la autorización para retirar el jardín del mapa. Nunca escribas una dirección exacta.'},400 if request.method=='POST' else 200)
