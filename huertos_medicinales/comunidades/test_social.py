import io
import pytest
from PIL import Image
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from .models import Pregunta,VotoEncuesta,VotoPregunta
from .test_forum_groups import forum

pytestmark=pytest.mark.django_db


def test_social_attachments_private_access_and_poll(client,forum,tmp_path,monkeypatch):
    owner,member,outsider,group,_,private,public,answer=forum
    for name in ('foto','video'):
        monkeypatch.setattr(Pregunta._meta.get_field(name).storage,'location',str(tmp_path))
    image=io.BytesIO();Image.new('RGB',(5,5),'green').save(image,format='PNG')
    client.force_login(owner)
    data={'titulo':'Encuesta de nuestro huerto','contenido':'¿Qué vamos a cultivar este mes?','tipo':'pregunta','visibilidad':'privado','comunidad':str(group.pk),'opciones_encuesta':'Menta\nManzanilla','enlace':'https://example.org/guia','foto':SimpleUploadedFile('foto.png',image.getvalue(),content_type='image/png'),'video':SimpleUploadedFile('video.mp4',b'\x00\x00\x00\x18ftypisom'+b'\x00'*20,content_type='video/mp4')}
    response=client.post(reverse('comunidades:nueva_pregunta'),data)
    assert response.status_code==302
    post=Pregunta.objects.get(titulo=data['titulo'])
    assert post.encuesta==['Menta','Manzanilla'] and post.enlace==data['enlace']
    for kind in ('foto','video'):
        response=client.get(reverse('comunidades:archivo',args=[post.pk,kind]))
        assert response.status_code==200 and response['Cache-Control']=='private, no-store'
        assert b"".join(response.streaming_content)
    poll=reverse('comunidades:encuesta',args=[post.pk])
    client.force_login(member)
    assert client.post(poll,{'opcion':0}).status_code==302
    assert client.post(poll,{'opcion':1}).status_code==302
    assert VotoEncuesta.objects.filter(pregunta=post).count()==1
    assert VotoEncuesta.objects.get(pregunta=post).opcion==1
    assert client.post(poll,{'opcion':8}).status_code==400
    assert b'1 voto' in client.get(reverse('comunidades:pregunta',args=[post.pk])).content
    client.force_login(owner)
    edit={k:v for k,v in data.items() if k not in ('foto','video')}
    assert client.post(reverse('comunidades:editar_pregunta',args=[post.pk]),{**edit,'opciones_encuesta':'Otro\nDistinto'}).status_code==400
    client.force_login(outsider)
    assert client.post(poll,{'opcion':0}).status_code==404
    for kind in ('foto','video'):
        assert client.get(reverse('comunidades:archivo',args=[post.pk,kind])).status_code==404
    client.logout()
    assert client.get(reverse('comunidades:archivo',args=[post.pk,'foto'])).status_code==404


def test_social_rejects_bad_upload_link_and_poll(client,forum):
    client.force_login(forum[0])
    data={'titulo':'Prueba de publicación','contenido':'Contenido de prueba','tipo':'consejo'}
    url=reverse('comunidades:nueva_pregunta')
    for extra in ({'foto':SimpleUploadedFile('foto.png',b'<script>mal</script>',content_type='image/png')},{'video':SimpleUploadedFile('video.mp4',b'not video',content_type='video/mp4')},{'enlace':'javascript:alert(1)'},{'opciones_encuesta':'Una sola'},{'opciones_encuesta':'Menta\nmenta'}):
        assert client.post(url,{**data,**extra}).status_code==400


def test_social_filters_and_navigation(client,forum):
    owner,member,outsider,group,_,private,public,answer=forum
    client.force_login(member)
    VotoPregunta.objects.create(usuario=owner,pregunta=private,valor=1)
    response=client.get(reverse('comunidades:listado'),{'orden':'utiles'})
    assert response.status_code==200 and response.context['page'][0]==private
    assert 'Ranking' in response.content.decode()
    assert 'social-quick-compose' in response.content.decode()
    assert 'Recursos' not in response.content.decode()
    response=client.get(reverse('comunidades:listado'),{'siguiendo':1})
    assert private.titulo.encode() in response.content
    client.force_login(outsider)
    response=client.get(reverse('comunidades:listado'),{'siguiendo':1})
    assert response.context['page'].paginator.count==0


def test_direct_social_modes_and_public_general(client,forum):
    owner,member,outsider,group,*_=forum
    client.force_login(owner)
    url=reverse('comunidades:nueva_pregunta')+'?social=1&destino=general'
    for mode in ('foto','video','enlace','encuesta',''):
        response=client.get(url+'&adjunto='+mode)
        assert response.status_code==200
        assert 'data-social-editor' in response.content.decode()
        assert 'Foro general · Público para todos' in response.content.decode()
        if mode: assert client.post(url+'&adjunto='+mode,{'contenido':'Hola','titulo':'Mi pregunta'}).status_code==400
    data={'contenido':'Hoy observé nuevos brotes en mi menta.','visibilidad':'privado','comunidad':str(group.pk)}
    assert client.post(url,data).status_code==302
    post=Pregunta.objects.get(contenido=data['contenido'])
    assert post.visibilidad=='publico' and post.comunidad is None
    assert post.titulo==data['contenido']
    assert client.post(url+'&adjunto=encuesta',{'titulo':'¿Qué plantas cultivas?','opciones_encuesta':'Menta\nManzanilla'}).status_code==302
    post=Pregunta.objects.get(titulo='¿Qué plantas cultivas?')
    assert post.encuesta==['Menta','Manzanilla'] and post.visibilidad=='publico'

def test_inline_publish_returns_json_and_keeps_validation_inline(client,forum):
    client.force_login(forum[0])
    url=reverse('comunidades:nueva_pregunta')+'?social=1&destino=general'
    assert client.post(url,{'inline':'1','contenido':''}).status_code==400
    response=client.post(url,{'inline':'1','contenido':'Una observación escrita en el recuadro.'})
    assert response.status_code==200 and response.json()['published']
    assert response.json()['redirect']==reverse('comunidades:listado')

def test_my_communities_detail_permissions_and_empty_style(client,forum):
    owner,member,outsider,group,_,private,public,answer=forum
    url=reverse('comunidades:listado')
    client.force_login(member)
    response=client.get(url,{'vista':'comunidades','mi_grupo':str(group.pk)})
    assert response.status_code==200
    assert private.titulo.encode() in response.content
    assert b'Comunidades que puedes explorar' not in response.content
    assert b'social-recommendations' not in response.content
    response=client.get(url,{'vista':'comunidades','mi_grupo':str(group.pk),'panel':'integrantes'})
    assert response.status_code==200 and b'my-community-members' in response.content
    client.force_login(outsider)
    assert client.get(url,{'vista':'comunidades','mi_grupo':str(group.pk)}).status_code==404
    response=client.get(url,{'vista':'comunidades'})
    assert b'my-community-cover' in response.content
    assert b'No tienes ninguna comunidad' in response.content
    assert private.titulo.encode() not in response.content
