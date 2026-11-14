from datetime import date
import pytest
from django.urls import reverse
from .models import Comunidad, Miembro, Pregunta, Respuesta, PerfilComunitario, VotoPregunta, VotoRespuesta
pytestmark=pytest.mark.django_db

@pytest.fixture
def forum(django_user_model):
    users=[]
    for name in ('owner','member','outsider'):
        u=django_user_model.objects.create_user(email=name+'@example.invalid',name=name,fecha_nacimiento=date(1990,1,1),genero='otro',telefono='0990000000',direccion='Ibarra')
        PerfilComunitario.objects.create(usuario=u,nombre=name,visible=True)
        users.append(u)
    owner,member,outsider=users
    group=Comunidad.objects.create(responsable=owner,nombre='Semillas compartidas',descripcion='Cultivamos juntos',grupo_virtual=True,estado='publicada')
    membership=Miembro.objects.create(usuario=member,comunidad=group,fecha_nacimiento=member.fecha_nacimiento,estado='aprobada')
    private=Pregunta.objects.create(autor=owner,comunidad=group,visibilidad='privado',titulo='Titulo exclusivo reservado',contenido='Contenido secreto del grupo',categoria='cultivo',huella='private')
    public=Pregunta.objects.create(autor=owner,comunidad=group,titulo='Pregunta abierta',contenido='Conversación pública',categoria='cultivo',huella='public')
    answer=Respuesta.objects.create(autor=member,pregunta=private,contenido='Comentario privado exclusivo',huella='secret')
    return owner,member,outsider,group,membership,private,public,answer

def test_private_visibility_all_surfaces(client,forum):
    owner,member,outsider,group,membership,private,public,answer=forum
    for user in (None,outsider):
        client.logout()
        if user:client.force_login(user)
        for params in ({},{'q':'reservado'},{'comunidad':group.pk}):
            response=client.get(reverse('comunidades:listado'),params)
            assert response.status_code==200
            assert private.titulo.encode() not in response.content
        assert client.get(reverse('comunidades:pregunta',args=[private.pk])).status_code==404
        assert client.get(reverse('comunidades:perfil',args=[owner.pk])).status_code==200
        assert private.titulo.encode() not in client.get(reverse('comunidades:perfil',args=[owner.pk])).content
        assert answer.contenido.encode() not in client.get(reverse('comunidades:perfil',args=[member.pk])).content
        assert client.get(reverse('comunidades:map_data')).json()['stats']['questions']==1
    client.force_login(outsider)
    assert client.get(reverse('comunidades:editar_respuesta',args=[answer.pk])).status_code==404
    assert client.post(reverse('comunidades:votar_respuesta',args=[answer.pk]),{'valor':1}).status_code==404
    assert client.post(reverse('comunidades:votar_pregunta',args=[private.pk]),{'valor':1}).status_code==404
    assert client.post(reverse('comunidades:pregunta',args=[public.pk]),{'contenido':'No soy integrante'}).status_code==403
    for user in (owner,member):
        client.force_login(user)
        assert client.get(reverse('comunidades:pregunta',args=[private.pk])).status_code==200
    membership.estado='retirada';membership.save()
    assert client.get(reverse('comunidades:pregunta',args=[private.pk])).status_code==404

def test_profile_gate_and_membership(client,forum):
    owner,member,outsider,group,membership,*_=forum
    outsider.telefono='';outsider.save();client.force_login(outsider)
    for url,data in [(reverse('comunidades:crear_grupo'),{'nombre':'Nuevo','descripcion':'Comunidad'}),(reverse('comunidades:unirse_grupo',args=[group.pk]),{}),(reverse('comunidades:crear'),{}),(reverse('comunidades:solicitar_membresia',args=[group.pk]),{})]:
        response=client.post(url,data)
        assert response.status_code==302 and response.url.startswith(reverse('users:update'))
    assert not Miembro.objects.filter(usuario=outsider).exists()
    client.force_login(owner)
    url=reverse('comunidades:agregar_por_codigo',args=[group.pk])
    client.post(url,{'codigo':outsider.codigo_unico})
    assert not Miembro.objects.filter(usuario=outsider).exists()
    outsider.telefono='0991111111';outsider.save()
    client.post(url,{'codigo':outsider.codigo_unico})
    assert Miembro.objects.get(usuario=outsider).estado=='aprobada'
    client.force_login(outsider)
    assert client.post(reverse('comunidades:salir_grupo',args=[group.pk])).status_code==302
    assert client.post(reverse('comunidades:unirse_grupo',args=[group.pk])).status_code==302
    m=Miembro.objects.get(usuario=outsider);assert m.estado=='solicitada'
    client.force_login(owner)
    assert client.post(reverse('comunidades:decidir_miembro',args=[group.pk,m.pk]),{'accion':'aprobar'}).status_code==302
    m.refresh_from_db();assert m.estado=='aprobada'

def test_virtual_create_and_private_form(client,forum):
    owner,member,outsider,group,_,private,*_=forum
    client.force_login(owner)
    response=client.post(reverse('comunidades:crear_grupo'),{'nombre':'Jardineros nuevos','descripcion':'Nuestro espacio compartido'})
    assert response.status_code==302
    new=Comunidad.objects.get(nombre='Jardineros nuevos')
    assert new.responsable==owner and new.latitud is None and new.grupo_virtual
    payload={'titulo':'Nuevo tema privado','contenido':'Compartir dentro del grupo','categoria':'cultivo','visibilidad':'privado'}
    url=reverse('comunidades:nueva_pregunta')
    assert client.post(url,payload).status_code==400
    assert client.post(url,{**payload,'comunidad':group.pk}).status_code==302
    client.force_login(outsider)
    assert client.post(url,{**payload,'comunidad':group.pk}).status_code==400

def test_nested_comments_votes_and_tombstone(client,forum):
    owner,member,outsider,group,_,private,public,answer=forum
    client.force_login(member)
    url=reverse('comunidades:pregunta',args=[private.pk])
    assert client.post(url,{'contenido':'Respuesta al comentario','padre':answer.pk}).status_code==302
    child=Respuesta.objects.get(contenido='Respuesta al comentario')
    assert child.padre==answer and child.raiz==answer and child.profundidad==1
    assert client.post(reverse('comunidades:pregunta',args=[public.pk]),{'contenido':'Padre ajeno','padre':answer.pk}).status_code==404
    vote=reverse('comunidades:votar_respuesta',args=[child.pk])
    for value in (1,1):
        r=client.post(vote,{'valor':value},HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        assert r.json()['score']==value
    assert client.post(vote,{"valor":-1}).status_code==400
    VotoRespuesta.objects.create(usuario=owner,respuesta=child,valor=-1)
    assert client.post(vote,{"valor":1},HTTP_X_REQUESTED_WITH="XMLHttpRequest").json()["score"]==1
    VotoRespuesta.objects.filter(usuario=owner,respuesta=child).delete()
    assert VotoRespuesta.objects.filter(respuesta=child).count()==1
    assert client.post(vote,{'valor':0},HTTP_X_REQUESTED_WITH='XMLHttpRequest').json()['score']==0
    assert not VotoRespuesta.objects.filter(respuesta=child).exists()
    assert client.post(vote,{'valor':8}).status_code==400
    answer.oculta=True;answer.save()
    response=client.get(url)
    assert child.contenido.encode() in response.content and answer.contenido.encode() not in response.content
    assert b'Comentario retirado' in response.content

def test_profile_return_url_is_local(client,forum):
    owner,*_=forum
    client.force_login(owner)
    payload={'name':'Perfil completo','fecha_nacimiento':'1990-01-01','genero':'otro','telefono':'0990000000','direccion':'Ciudad','talentos':''}
    response=client.post(reverse('users:update')+'?next=https://example.invalid/',payload)
    assert response.status_code==302 and not response.url.startswith('https://example.invalid')
    response=client.post(reverse('users:update')+'?next=/comunidades/grupos/nueva/',payload)
    assert response.status_code==302 and response.url=='/comunidades/grupos/nueva/'

def test_bookmarks_respect_private_access_and_kind_filters(client,forum):
    owner,member,outsider,group,membership,private,public,answer=forum
    client.force_login(member)
    url=reverse('comunidades:guardar_pregunta',args=[private.pk])
    assert client.post(url,{'guardar':'1'},HTTP_X_REQUESTED_WITH='XMLHttpRequest').json()['saved']
    assert private.titulo.encode() in client.get(reverse('comunidades:listado'),{'guardadas':1}).content
    membership.estado='retirada';membership.save()
    assert private.titulo.encode() not in client.get(reverse('comunidades:listado'),{'guardadas':1}).content
    assert client.post(url,{'guardar':'1'}).status_code==404
    client.force_login(owner)
    public.tipo='consejo';public.save()
    response=client.get(reverse('comunidades:listado'),{'tipo':'consejo'})
    assert public.titulo.encode() in response.content and private.titulo.encode() not in response.content
    assert response.context['profile_percentage']==100

def test_sections_are_separate_and_empty_membership_is_explicit(client,forum):
    owner,member,outsider,group,*_=forum
    client.force_login(owner)
    url=reverse('comunidades:listado')
    response=client.get(url)
    assert b'id="foro"' in response.content
    assert b'id="mis-comunidades"' not in response.content
    assert b'id="mapa-huertos"' not in response.content
    response=client.get(url,{'vista':'comunidades'})
    assert group.nombre.encode() in response.content and b'id="mis-comunidades"' in response.content
    assert b'id="foro"' not in response.content and b'id="mapa-huertos"' not in response.content
    response=client.get(url,{'vista':'mapa'})
    assert b'id="mapa-huertos"' in response.content and b'full-map-view' in response.content
    assert b'id="foro"' not in response.content and b'id="mis-comunidades"' not in response.content
    client.force_login(outsider)
    response=client.get(url,{'vista':'comunidades'})
    assert b'No tienes ninguna comunidad' in response.content
