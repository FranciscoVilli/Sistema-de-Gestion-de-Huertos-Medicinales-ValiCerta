import re
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Count, Q, Prefetch, Sum
from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST, require_GET
from huertos_medicinales.seguimiento.models import Jardin, Practica
from .models import Pregunta, Respuesta, PerfilComunitario, JardinCompartido, Comunidad, Miembro, EventoComunidad, VotoPregunta, VotoRespuesta
from .access import visible_questions, member_groups, may_post, require_profile, profile_complete
from django.contrib import messages
from django.core.exceptions import ValidationError
from .community_forms import PreguntaForm, RespuestaForm, PerfilForm, CompartirForm, GrupoForm, fingerprint


def reglas(request):
    return render(request,'comunidades/reglas.html')

def public_name(user):
    profile=getattr(user,'perfil_comunitario',None)
    if profile:
        return profile.nombre if profile.visible else f'Cultivador {user.pk}'
    return user.name or f'Cultivador {user.pk}'

def allowed(user,item):
    return user.is_authenticated and (user.pk==item.autor_id or user.has_perm('comunidades.change_'+item._meta.model_name))

def decorate(items,user):
    items=list(items)
    if not items:return items
    model=VotoPregunta if isinstance(items[0],Pregunta) else VotoRespuesta
    field='pregunta_id' if model is VotoPregunta else 'respuesta_id'
    votes=model.objects.filter(valor=1,**{field+'__in':[i.pk for i in items]})
    totals={v[field]:v['total'] for v in votes.values(field).annotate(total=Sum('valor'))}
    own=dict(votes.filter(usuario=user).values_list(field,'valor')) if user.is_authenticated else {}
    for item in items:
        item.score=totals.get(item.pk,0)
        item.my_vote=own.get(item.pk,0)
        item.vote_url=reverse('comunidades:votar_pregunta' if model is VotoPregunta else 'comunidades:votar_respuesta',args=[item.pk])
        item.public_name=public_name(item.autor)
        item.can_edit=allowed(user,item)
    return items

def visible_gardens():
    return JardinCompartido.objects.filter(visible=True,jardin__propietario__is_active=True,jardin__propietario__perfil_comunitario__visible=True).select_related('jardin__propietario__perfil_comunitario','jardin__propietario__membresia__comunidad').prefetch_related(Prefetch('jardin__cultivos',queryset=Practica.objects.filter(estado='activa')))

PALETA_COMUNIDADES=['#c0392b','#1f6feb','#1a7f37','#8e44ad','#d35400','#0f7b6c','#b8860b','#c2185b','#2c3e50','#007a86']
COLOR_SIN_COMUNIDAD='#5a6b52'

def mapa_colores_comunidad():
    comunidades=list(Comunidad.objects.filter(estado=Comunidad.Estado.PUBLICADA).order_by('creada'))
    colores={c.pk:PALETA_COMUNIDADES[i%len(PALETA_COMUNIDADES)] for i,c in enumerate(sorted(comunidades,key=lambda c:c.nombre.casefold()))}
    responsables={}
    for c in comunidades:
        responsables.setdefault(c.responsable_id,c)
    return colores,responsables

def markers(user=None):
    colores,responsables=mapa_colores_comunidad()
    result=[]
    for shared in visible_gardens():
        owner=shared.jardin.propietario;profile=owner.perfil_comunitario
        plants=sorted({p.planta_nombre for p in shared.jardin.cultivos.all()})
        membresia=getattr(owner,'membresia',None)
        comunidad=membresia.comunidad if membresia and membresia.estado==Miembro.Estado.APROBADA else responsables.get(owner.pk)
        result.append({'id':shared.jardin_id,'name':shared.jardin.nombre,'owner':profile.nombre,'level':profile.get_nivel_display() or 'No declarada','years':profile.anos,'location':shared.localidad,'lat':float(shared.latitud),'lon':float(shared.longitud),'plants':plants,'species':len(plants),'profile':reverse('comunidades:perfil',args=[owner.pk]),'group_url':reverse('comunidades:listado')+'?comunidad='+str(comunidad.pk) if comunidad and comunidad.estado==Comunidad.Estado.PUBLICADA else '', 'mine':bool(user and user.is_authenticated and comunidad and member_groups(user).filter(pk=comunidad.pk).exists()),'comunidad':comunidad.nombre if comunidad else '','color':colores.get(comunidad.pk,COLOR_SIN_COMUNIDAD) if comunidad else COLOR_SIN_COMUNIDAD})
    return result

@never_cache
@require_GET
def map_data(request):
    items=markers(request.user)
    legend={}
    for item in items:
        if item['comunidad']:legend.setdefault(item['comunidad'],item['color'])
    legend=[{'nombre':nombre,'color':color} for nombre,color in sorted(legend.items(),key=lambda par:par[0].casefold())]
    if any(not item['comunidad'] for item in items):legend.append({'nombre':'Sin comunidad','color':COLOR_SIN_COMUNIDAD})
    participants={x for x in JardinCompartido.objects.filter(visible=True,jardin__propietario__perfil_comunitario__visible=True,jardin__propietario__is_active=True).values_list('jardin__propietario_id',flat=True)}
    participants.update(visible_questions(request.user).values_list('autor_id',flat=True))
    participants.update(Respuesta.objects.filter(oculta=False,pregunta__in=visible_questions(request.user),autor__is_active=True).values_list('autor_id',flat=True))
    return JsonResponse({'markers':items,'legend':legend,'stats':{'gardens':len(items),'participants':len(participants),'questions':visible_questions(request.user).filter(resuelta=False).count()}})

@never_cache
def hub(request):
    section=request.GET.get('vista','foro')
    if section not in ('foro','comunidades','mapa'):section='foro'

    query=request.GET.get('q','').strip()[:150];category=request.GET.get('categoria','');order=request.GET.get('orden','recientes')
    questions=visible_questions(request.user).select_related('autor__perfil_comunitario').annotate(total_respuestas=Count('respuestas',filter=Q(respuestas__oculta=False,respuestas__autor__is_active=True),distinct=True))
    groups=Comunidad.objects.filter(estado=Comunidad.Estado.PUBLICADA)
    selected=None
    group_id=request.GET.get('comunidad','')
    if group_id:
        try:selected=get_object_or_404(groups,pk=group_id)
        except ValidationError:
            from django.http import Http404
            raise Http404
        questions=questions.filter(comunidad=selected)
    kind=request.GET.get('tipo','')
    if kind in dict(Pregunta.TIPOS):questions=questions.filter(tipo=kind)
    else:kind=''
    saved_only=request.GET.get('guardadas')=='1'
    if saved_only:
        questions=questions.filter(guardada_por=request.user) if request.user.is_authenticated else questions.none()
    if query: questions=questions.filter(Q(titulo__icontains=query)|Q(contenido__icontains=query))
    if category in dict(Pregunta.CATEGORIAS):questions=questions.filter(categoria=category)
    else:category=''
    if request.GET.get('siguiendo')=='1':questions=questions.filter(comunidad__in=member_groups(request.user))
    if order=='utiles':questions=questions.annotate(useful_count=Count('votos',filter=Q(votos__valor=1),distinct=True)).order_by('-useful_count','-creada','-pk')
    elif order=='populares':questions=questions.order_by('-total_respuestas','-creada','-pk')
    else:
        order='recientes'
        questions=questions.order_by('-creada','-pk')
    page=Paginator(questions,6).get_page(request.GET.get('page'))
    decorate(page.object_list,request.user)
    saved_ids=set(request.user.publicaciones_guardadas.values_list('pk',flat=True)) if request.user.is_authenticated else set()
    reported_ids=set(request.user.publicaciones_reportadas.values_list('pk',flat=True)) if request.user.is_authenticated else set()
    for post in page.object_list:
        post.saved=post.pk in saved_ids
        post.reported=post.pk in reported_ids
        words=(post.titulo+' '+post.contenido).casefold()
        species=None
        for text in (post.titulo.casefold(),words):
            species=next((name for name in ('menta','manzanilla','calendula','romero') if re.search(r'\b'+name+r'\b',text.replace('é','e'))),None)
            if species:break
        post.thumbnail='images/huertos/plantas/'+species+'.png' if species else 'images/huertos/comunidad-brote.png'
    checks=[('Nombre y apellido',bool(getattr(request.user,'name',''))),('Fecha de nacimiento',bool(getattr(request.user,'fecha_nacimiento',None))),('Género',bool(getattr(request.user,'genero',''))),('Teléfono',bool(getattr(request.user,'telefono',''))),('Dirección',bool(getattr(request.user,'direccion','')))]
    profile_percentage=round(sum(int(ready) for label,ready in checks)*100/len(checks))
    my_groups=member_groups(request.user).annotate(member_count=Count('miembros',filter=Q(miembros__estado=Miembro.Estado.APROBADA),distinct=True))
    for group in my_groups:
        group.display_count=group.member_count+(0 if group.miembros.filter(usuario_id=group.responsable_id,estado=Miembro.Estado.APROBADA).exists() else 1)
    gardens=visible_gardens()
    participant_ids=set(gardens.values_list('jardin__propietario_id',flat=True))
    participant_ids.update(visible_questions(request.user).values_list('autor_id',flat=True))
    participant_ids.update(Respuesta.objects.filter(oculta=False,pregunta__in=visible_questions(request.user),autor__is_active=True).values_list('autor_id',flat=True))
    featured=PerfilComunitario.objects.filter(visible=True,usuario__is_active=True).annotate(contributions=Count('usuario__respuestas_comunidad',filter=Q(usuario__respuestas_comunidad__oculta=False,usuario__respuestas_comunidad__pregunta__in=visible_questions(request.user)),distinct=True)).order_by('-contributions','nombre')[:3]
    featured=list(featured)
    for member in featured:
        member.plants=sorted({p.planta_nombre for shared in visible_gardens().filter(jardin__propietario_id=member.usuario_id) for p in shared.jardin.cultivos.all()})
    my_rankings=[]
    if section=='comunidades' and request.user.is_authenticated:
        from .rankings import standings
        my_rankings=[row for row in standings(request.user) if row['mine']]
    active_group=None
    group_members=[]
    group_page=None
    group_panel=request.GET.get('panel','publicaciones')
    if group_panel not in ('publicaciones','integrantes'):group_panel='publicaciones'
    if section=='comunidades':
        active_id=request.GET.get('mi_grupo','')
        if active_id:
            try:active_group=get_object_or_404(my_groups,pk=active_id)
            except ValidationError:
                from django.http import Http404
                raise Http404
        else:active_group=next(iter(my_groups),None)
        if active_group:
            group_members=list(Miembro.objects.filter(comunidad=active_group,estado=Miembro.Estado.APROBADA).select_related('usuario'))
            active_group.display_count=len(group_members)+(0 if any(m.usuario_id==active_group.responsable_id for m in group_members) else 1)
            posts=visible_questions(request.user).filter(comunidad=active_group).select_related('autor__perfil_comunitario','comunidad').annotate(total_respuestas=Count('respuestas',filter=Q(respuestas__oculta=False,respuestas__autor__is_active=True),distinct=True)).order_by('-creada','-pk')
            group_page=Paginator(posts,6).get_page(request.GET.get('page'))
            decorate(group_page.object_list,request.user)
            for post in group_page.object_list:
                post.saved=post.pk in saved_ids
                post.reported=post.pk in reported_ids
                species=next((name for name in ('menta','manzanilla','calendula','romero') if name in (post.titulo+' '+post.contenido).lower().replace('é','e')),None)
                post.thumbnail='images/huertos/plantas/'+species+'.png' if species else 'images/huertos/comunidad-brote.png'
    recommended = list(groups.exclude(pk__in=my_groups.values_list('pk',flat=True)).annotate(approved_members=Count('miembros',filter=Q(miembros__estado='aprobada'),distinct=True)).order_by('-approved_members','nombre')[:3])
    for g in recommended:g.display_count=g.approved_members+(0 if g.miembros.filter(usuario=g.responsable,estado='aprobada').exists() else 1)
    social_stats={'groups':groups.count(),'posts':visible_questions(request.user).count(),'people':len(participant_ids)}
    return render(request,'comunidades/hub.html',{'active_group':active_group,'group_members':group_members,'group_page':group_page,'group_panel':group_panel,'social_topics':['Germinación','Riego','Plagas','Sustratos','Cosecha','Usos medicinales'],'recommended_groups':recommended,'social_stats':social_stats,'following_only':request.GET.get('siguiendo')=='1','my_rankings':my_rankings,'section':section,'groups':groups,'selected_group':selected,'can_participate':may_post(request.user,selected),'profile_ready':profile_complete(request.user),'profile_checks':checks,'profile_percentage':profile_percentage,'kind':kind,'post_types':Pregunta.TIPOS,'saved_only':saved_only,'my_groups':my_groups,'page':page,'query':query,'category':category,'order':order,'categories':Pregunta.CATEGORIAS,'garden_count':gardens.count(),'participant_count':len(participant_ids),'open_count':visible_questions(request.user).filter(resuelta=False).count(),'featured':featured,})

def modal(request,title,template,context,status=200):
    return render(request,'comunidades/modal_fragment.html' if request.GET.get('fragment')=='1' else 'comunidades/modal.html',{'modal_title':title,'modal_template':template,**context,'fragment':request.GET.get('fragment')=='1'},status=status)

def success(request,url):
    if request.GET.get('fragment')=='1':return JsonResponse({'redirect':url})
    return redirect(url)

@login_required
@never_cache
def question_edit(request,pk=None):
    item=get_object_or_404(visible_questions(request.user),pk=pk) if pk else None
    if item and not allowed(request.user,item):return HttpResponseForbidden('No puedes editar esta publicación.')
    form=PreguntaForm(request.POST or None,request.FILES or None,instance=item,user=request.user,initial={'comunidad':request.GET.get('comunidad')})
    social = request.GET.get('social') == '1' or request.POST.get('social') == '1'
    media_mode = request.GET.get('adjunto', request.POST.get('adjunto', ''))
    general = not item and (request.GET.get('destino') == 'general' or request.POST.get('destino') == 'general')
    if social:
        if media_mode in ('foto','video','enlace'):
            form.fields[media_mode].required = True
        if media_mode == 'encuesta':
            form.fields['opciones_encuesta'].required = True
        form.fields['titulo'].required = media_mode == 'encuesta'
        form.fields['contenido'].required = media_mode not in ('encuesta','foto','video','enlace')
        if general:
            form.fields['comunidad'].disabled = True
            form.fields['comunidad'].initial = None
            form.initial['comunidad'] = None
            form.fields['visibilidad'].disabled = True
            form.initial['visibilidad'] = 'publico'
    if request.method=='POST' and form.is_valid():
        if social:
            text = form.cleaned_data.get('contenido','').strip()
            title = form.cleaned_data.get('titulo','').strip()
            form.instance.titulo = title or text[:100] or {'foto':'Foto de mi huerto','video':'Video de mi huerto','enlace':'Enlace para compartir'}.get(media_mode,'Mi publicación')
            form.instance.contenido = text or title or 'Comparto una novedad de mi huerto.'
        with transaction.atomic():
            get_user_model().objects.select_for_update().get(pk=request.user.pk)
            if item:
                locked=Pregunta.objects.select_for_update().get(pk=item.pk)
                if locked.votos_encuesta.exists() and form.cleaned_data.get('opciones_encuesta',[]) != locked.encuesta:
                    form.add_error('opciones_encuesta','La encuesta ya recibió respuestas. No puedes cambiar sus opciones.')
                    return modal(request,'Editar publicación','comunidades/post_composer.html',{'form':form,'submit_label':'Guardar cambios','composer_name':public_name(item.autor),'composer_user':item.autor},400)
            obj=form.save(commit=False);obj.autor=item.autor if item else request.user
            obj.huella=fingerprint(str(obj.comunidad_id or ''),obj.titulo,obj.contenido)
            duplicates=Pregunta.objects.filter(autor=obj.autor,huella=obj.huella,oculta=False)
            if item:duplicates=duplicates.exclude(pk=item.pk)
            if duplicates.exists():form.add_error(None,'Ya publicaste esta pregunta. Puedes continuar en sus respuestas.')
            else:
                obj.save()
                if request.POST.get('inline')=='1':
                    target=reverse('comunidades:listado')
                    if obj.comunidad_id:target+='?comunidad='+str(obj.comunidad_id)
                    return JsonResponse({'redirect':target,'published':True})
                return success(request,reverse('comunidades:pregunta',args=[obj.pk]))
    if request.method=='POST' and request.POST.get('inline')=='1':
        return JsonResponse({'errors':form.errors.get_json_data()},status=400)
    return modal(request,'Editar publicación' if item else 'Crear publicación','comunidades/post_composer.html',{'social_editor':social,'general_publication':general,'media_mode':media_mode,'form':form,'submit_label':'Guardar cambios' if item else 'Publicar','composer_name':public_name(item.autor if item else request.user),'composer_user':item.autor if item else request.user},400 if request.method=='POST' else 200)

@never_cache
def question(request,pk):
    item=get_object_or_404(visible_questions(request.user).select_related('autor__perfil_comunitario','comunidad'),pk=pk)
    decorate([item],request.user)
    item.reported=request.user.is_authenticated and item.reportada_por.filter(pk=request.user.pk).exists()
    form=RespuestaForm(request.POST or None)
    parent=None
    if request.method=='POST':
        if not request.user.is_authenticated:return HttpResponseForbidden('Inicia sesión para participar.')
        if not may_post(request.user,item.comunidad):return HttpResponseForbidden('Únete a la comunidad para participar.')
        parent=None
        if request.POST.get('padre'):
            try:parent=get_object_or_404(Respuesta,pk=int(request.POST['padre']),pregunta=item,oculta=False,autor__is_active=True)
            except (ValueError,TypeError):return HttpResponseForbidden()
            if parent.profundidad>=5:form.add_error(None,'Este hilo alcanzó cinco niveles. Responde al comentario anterior o inicia otra respuesta.')
        if form.is_valid():
            with transaction.atomic():
                get_user_model().objects.select_for_update().get(pk=request.user.pk)
                obj=form.save(commit=False);obj.autor=request.user;obj.pregunta=item;obj.padre=parent;obj.raiz=(parent.raiz or parent) if parent else None;obj.profundidad=parent.profundidad+1 if parent else 0;obj.huella=fingerprint(obj.contenido)
                if Respuesta.objects.filter(pregunta=item,autor=request.user,huella=obj.huella,oculta=False).exists():form.add_error('contenido','Esta respuesta ya fue publicada.')
                else:
                    obj.save()
                    root=obj.raiz or obj
                    position=Respuesta.objects.filter(pregunta=item,padre__isnull=True,pk__lte=root.pk).count()
                    return success(request,reverse('comunidades:pregunta',args=[pk])+'?page='+str(max(1,(position+9)//10))+'#respuesta-'+str(obj.pk))
    roots=Respuesta.objects.filter(pregunta=item,padre__isnull=True).select_related('autor__perfil_comunitario')
    reply_query=request.GET.get('comentario','').strip()[:150]
    if reply_query:
        matched=Respuesta.objects.filter(pregunta=item,oculta=False,autor__is_active=True,contenido__icontains=reply_query)
        roots=roots.filter(Q(pk__in=matched.filter(padre__isnull=True).values('pk'))|Q(pk__in=matched.exclude(raiz=None).values('raiz_id')))
    sort=request.GET.get('comentarios','antiguos')
    roots=roots.order_by('-creada','-pk') if sort=='recientes' else roots.order_by('creada','pk')
    answers=Paginator(roots,10).get_page(request.GET.get('page'))
    root_items=list(answers.object_list)
    descendants=list(Respuesta.objects.filter(pregunta=item,raiz_id__in=[r.pk for r in root_items]).select_related('autor__perfil_comunitario').order_by('creada','pk'))
    nodes=decorate(root_items+descendants,request.user)
    by_id={n.pk:n for n in nodes}
    reported_resp_ids=set(request.user.respuestas_reportadas.values_list('pk',flat=True)) if request.user.is_authenticated else set()
    for node in nodes:
        node.children=[]
        node.removed=node.oculta or not node.autor.is_active
        node.reported=node.pk in reported_resp_ids
    for node in descendants:
        if node.padre_id in by_id:by_id[node.padre_id].children.append(node)
    answers.object_list=root_items
    from .models import VotoEncuesta
    poll_counts=dict(item.votos_encuesta.values('opcion').annotate(total=Count('pk')).values_list('opcion','total'))
    item.poll_options=[{'index':i,'text':text,'count':poll_counts.get(i,0)} for i,text in enumerate(item.encuesta)]
    item.my_poll_vote=item.votos_encuesta.filter(usuario=request.user).values_list('opcion',flat=True).first() if request.user.is_authenticated else None
    return modal(request,item.titulo,'comunidades/question_content.html',{'question':item,'answers':answers,'form':form,'reply_parent':parent,'can_reply':may_post(request.user,item.comunidad),'reply_query':reply_query,'reply_sort':sort,'reply_count':item.respuestas.filter(oculta=False,autor__is_active=True).count()},400 if request.method=='POST' else 200)


@login_required
@require_POST
def question_action(request,pk):
    item=get_object_or_404(visible_questions(request.user),pk=pk)
    if not allowed(request.user,item):return HttpResponseForbidden()
    if request.POST.get('action')=='hide':item.oculta=True;fields=['oculta']
    elif request.POST.get('action')=='resolve':item.resuelta=request.POST.get('resolved')=='1';fields=['resuelta']
    else:return HttpResponseForbidden()
    item.save(update_fields=fields)
    return success(request,reverse('comunidades:listado'))

@login_required
@never_cache
def answer_edit(request,pk):
    item=get_object_or_404(Respuesta,pk=pk,oculta=False,pregunta__in=visible_questions(request.user))
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
    form=PerfilForm(request.POST or None,instance=item,initial={'nombre':request.user.name or f'Cultivador {request.user.pk}'})
    if request.method=='POST' and form.is_valid():
        obj=form.save(commit=False);obj.usuario=request.user;obj.save();return success(request,reverse('comunidades:listado'))
    return modal(request,'Mi perfil comunitario','comunidades/form_content.html',{'form':form,'submit_label':'Guardar perfil','notice':'Tu nombre, experiencia y jardines compartidos serán visibles solo si activas tu perfil. No incluyas correo, teléfono ni dirección. El nivel es declarado por ti.'},400 if request.method=='POST' else 200)

@never_cache
def profile(request,pk):
    item=get_object_or_404(PerfilComunitario,usuario_id=pk,visible=True,usuario__is_active=True)
    shared=visible_gardens().filter(jardin__propietario_id=pk)
    plants=sorted({p.planta_nombre for s in shared for p in s.jardin.cultivos.all()})
    questions=visible_questions(request.user).filter(autor_id=pk)[:8]
    answers=Respuesta.objects.filter(autor_id=pk,oculta=False,pregunta__in=visible_questions(request.user)).select_related('pregunta')[:8]
    return modal(request,item.nombre,'comunidades/profile_content.html',{'profile':item,'plants':plants,'shared':shared,'questions':questions,'answers':answers})

@login_required
@require_POST
def share(request,pk):
    garden=get_object_or_404(Jardin,pk=pk,propietario=request.user)
    instance=JardinCompartido.objects.filter(jardin=garden).first()
    form=CompartirForm(request.POST,instance=instance)
    destino=reverse('workspace')+'?jardin='+str(garden.pk)
    if not form.is_valid():
        messages.error(request,'No se pudo actualizar la visibilidad de este jardín.')
        return redirect(destino)
    visible=form.cleaned_data['visible']
    climate=garden.clima or {}
    tiene_ubicacion=climate.get('latitude') is not None and climate.get('longitude') is not None
    perfil=getattr(request.user,'perfil_comunitario',None)
    if visible and not tiene_ubicacion:
        messages.error(request,'Configura primero la ubicación de este jardín (sección Clima) para poder mostrarlo en el mapa.')
    elif visible and not (perfil and perfil.visible):
        messages.error(request,'Activa primero tu perfil comunitario para publicar este jardín.')
    elif visible or instance is not None:
        obj=form.save(commit=False);obj.jardin=garden
        if visible:
            nombre_sector=climate.get('name') if climate.get('source')!='browser' else ''
            obj.localidad=(nombre_sector or (perfil.localidad if perfil else '') or 'Ubicación aproximada')[:120]
            obj.latitud=round(float(climate['latitude']),2)
            obj.longitud=round(float(climate['longitude']),2)
        obj.save()
        messages.success(request,'Jardín visible en el mapa comunitario.' if visible else 'Jardín retirado del mapa comunitario.')
    return redirect(destino)


@login_required
@require_profile
@never_cache
def group_create(request):
    form=GrupoForm(request.POST or None)
    if request.method=='POST' and form.is_valid():
        with transaction.atomic():
            group=form.save(commit=False)
            group.responsable=request.user
            group.grupo_virtual=True
            group.estado=Comunidad.Estado.PUBLICADA
            group.save()
            EventoComunidad.objects.create(comunidad=group,actor=request.user,accion='grupo_creado')
        return redirect('comunidades:gestionar_miembros',pk=group.pk)
    return modal(request,'Crear comunidad','comunidades/form_content.html',{'form':form,'submit_label':'Crear comunidad','notice':'Crea un espacio para conversar y agrega integrantes por su código único. El nombre y la descripción serán públicos. Tú decides la visibilidad de cada tema.'},400 if request.method=='POST' else 200)

@login_required
@require_profile
@require_POST
def join_group(request,pk):
    group=get_object_or_404(Comunidad,pk=pk,estado=Comunidad.Estado.PUBLICADA)
    with transaction.atomic():
        user=get_user_model().objects.select_for_update().get(pk=request.user.pk)
        member=Miembro.objects.filter(usuario=user).first()
        if group.responsable_id==user.pk:
            messages.info(request,'Ya administras esta comunidad.')
        elif member and member.estado!=Miembro.Estado.RETIRADA:
            messages.info(request,'Ya tienes una membresía o solicitud activa. Puedes retirarte desde tu comunidad antes de solicitar otra.')
        else:
            Miembro.objects.update_or_create(usuario=user,defaults={'comunidad':group,'fecha_nacimiento':user.fecha_nacimiento,'genero':user.genero,'estado':Miembro.Estado.SOLICITADA})
            EventoComunidad.objects.create(comunidad=group,actor=user,accion='miembro_solicitado')
            messages.success(request,'Solicitud enviada. El responsable debe aprobar tu ingreso.')
    return redirect(reverse('comunidades:listado')+'?comunidad='+str(group.pk))

@login_required
@require_POST
def leave_group(request,pk):
    with transaction.atomic():
        member=get_object_or_404(Miembro.objects.select_for_update(),usuario=request.user,comunidad_id=pk)
        member.estado=Miembro.Estado.RETIRADA
        member.save(update_fields=['estado','actualizado'])
        EventoComunidad.objects.create(comunidad=member.comunidad,actor=request.user,accion='miembro_salida')
    messages.success(request,'Saliste de la comunidad. Tus aportes se conservan, pero ya no tienes acceso a sus temas privados.')
    return redirect('comunidades:listado')

@login_required
@require_POST
def vote(request,pk,reply=False):
    if reply:
        target=get_object_or_404(Respuesta,pk=pk,oculta=False,autor__is_active=True,pregunta__in=visible_questions(request.user))
        topic=target.pregunta;model=VotoRespuesta;field='respuesta'
    else:
        target=get_object_or_404(visible_questions(request.user),pk=pk)
        topic=target;model=VotoPregunta;field='pregunta'
    if not may_post(request.user,topic.comunidad):return HttpResponseForbidden('Únete a la comunidad para indicar que una publicación te resulta útil.')
    try:value=int(request.POST.get('valor',''))
    except ValueError:return JsonResponse({'error':'Voto inválido'},status=400)
    if value not in (0,1):return JsonResponse({'error':'Voto inválido'},status=400)
    with transaction.atomic():
        get_user_model().objects.select_for_update().get(pk=request.user.pk)
        if value:model.objects.update_or_create(usuario=request.user,**{field:target},defaults={'valor':value})
        else:model.objects.filter(usuario=request.user,**{field:target}).delete()
    score=model.objects.filter(valor=1,**{field:target}).count()
    if request.headers.get('X-Requested-With')=='XMLHttpRequest':return JsonResponse({'score':score,'vote':value})
    return redirect('comunidades:pregunta',pk=topic.pk)


@login_required
@require_POST
def bookmark(request,pk):
    item=get_object_or_404(visible_questions(request.user),pk=pk)
    saved=request.POST.get('guardar')=='1'
    if saved:item.guardada_por.add(request.user)
    else:item.guardada_por.remove(request.user)
    if request.headers.get('X-Requested-With')=='XMLHttpRequest':return JsonResponse({'saved':saved})
    return redirect('comunidades:listado')


@login_required
@require_POST
def reportar_pregunta(request,pk):
    item=get_object_or_404(visible_questions(request.user),pk=pk)
    item.reportada_por.add(request.user)
    if request.headers.get('X-Requested-With')=='XMLHttpRequest':return JsonResponse({'reportada':True})
    return redirect('comunidades:listado')


@login_required
@require_POST
def reportar_respuesta(request,pk):
    item=get_object_or_404(Respuesta,pk=pk,oculta=False,pregunta__in=visible_questions(request.user))
    item.reportada_por.add(request.user)
    if request.headers.get('X-Requested-With')=='XMLHttpRequest':return JsonResponse({'reportada':True})
    return redirect('comunidades:pregunta',pk=item.pregunta_id)


@require_GET
def attachment(request, pk, kind):
    from django.http import FileResponse, Http404
    from pathlib import Path
    item=get_object_or_404(visible_questions(request.user),pk=pk)
    field=getattr(item,kind,None) if kind in ('foto','video') else None
    if not field:raise Http404
    content_type={'.jpg':'image/jpeg','.jpeg':'image/jpeg','.png':'image/png','.webp':'image/webp','.mp4':'video/mp4','.webm':'video/webm'}.get(Path(field.name).suffix.lower(),'application/octet-stream')
    response=FileResponse(field.open('rb'),content_type=content_type)
    response['Cache-Control']='private, no-store'
    response['X-Content-Type-Options']='nosniff'
    return response

@login_required
@require_POST
def poll_vote(request, pk):
    from .models import VotoEncuesta
    item=get_object_or_404(visible_questions(request.user),pk=pk)
    if not may_post(request.user,item.comunidad):return HttpResponseForbidden('Únete a la comunidad para participar.')
    try:choice=int(request.POST.get('opcion',''))
    except ValueError:return JsonResponse({'error':'Selecciona una opción.'},status=400)
    with transaction.atomic():
        item=Pregunta.objects.select_for_update().get(pk=item.pk)
        if not 0 <= choice < len(item.encuesta):return JsonResponse({'error':'Opción no válida.'},status=400)
        VotoEncuesta.objects.update_or_create(pregunta=item,usuario=request.user,defaults={'opcion':choice})
    return success(request,reverse('comunidades:pregunta',args=[pk]))
