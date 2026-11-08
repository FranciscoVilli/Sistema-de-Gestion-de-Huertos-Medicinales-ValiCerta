from datetime import date
import pytest
from django.urls import reverse
from .models import Pregunta, Respuesta, PerfilComunitario, JardinCompartido
from huertos_medicinales.seguimiento.models import Jardin, Practica
pytestmark=pytest.mark.django_db

@pytest.fixture
def people(client,django_user_model):
 a=django_user_model.objects.create_user(email='owner-private@example.com');b=django_user_model.objects.create_user(email='other-private@example.com')
 client.force_login(a)
 return a,b

def payload():return {'titulo':'Mi menta tiene hojas amarillas','contenido':'¿Cómo reviso el sustrato de mi maceta?','categoria':'riego'}

def test_publish_reply_duplicates_permissions(client,people):
 a,b=people;new=reverse('comunidades:nueva_pregunta')
 assert client.post(new,{'titulo':' ','contenido':' ','categoria':'riego'}).status_code==400
 assert client.post(new,{**payload(),'contenido':'<script>alert(1)</script>'}).status_code==400
 assert client.post(new,payload()).status_code==302
 q=Pregunta.objects.get();url=reverse('comunidades:pregunta',args=[q.pk])
 assert client.post(new,payload()).status_code==400
 assert client.post(url,{'contenido':'Revisa la humedad antes del riego.'}).status_code==302
 assert client.post(url,{'contenido':'Revisa la humedad antes del riego.'}).status_code==400
 assert Respuesta.objects.count()==1
 client.force_login(b)
 assert client.post(reverse('comunidades:editar_pregunta',args=[q.pk]),payload()).status_code==403
 assert client.post(reverse('comunidades:estado_pregunta',args=[q.pk]),{'action':'hide'}).status_code==403
 assert client.post(reverse('comunidades:editar_respuesta',args=[Respuesta.objects.get().pk]),{'action':'hide'}).status_code==403
 client.force_login(a)
 assert client.post(reverse('comunidades:estado_pregunta',args=[q.pk]),{'action':'resolve','resolved':'1'}).status_code==302
 q.refresh_from_db();assert q.resuelta
 assert client.post(reverse('comunidades:estado_pregunta',args=[q.pk]),{'action':'hide'}).status_code==302
 assert client.get(url).status_code==404
 client.logout();assert client.post(new,payload()).status_code==302

def test_search_sort_pagination_and_escape(client,people):
 a,b=people
 for n in range(9):Pregunta.objects.create(autor=a,titulo=f'Menta {n}',contenido='Observación',categoria='riego',huella=str(n))
 q=Pregunta.objects.create(autor=b,titulo='Caléndula <img src=x onerror=alert(1)>',contenido='Duda',categoria='cultivo',huella='x')
 Respuesta.objects.create(pregunta=q,autor=a,contenido='Ejemplo',huella='y')
 url=reverse('comunidades:listado');r=client.get(url);assert len(r.context['page'])==6
 assert client.get(url,{'page':2}).context['page'].number==2
 assert client.get(url,{'q':'Caléndula'}).context['page'].paginator.count==1
 assert client.get(url,{'categoria':'riego'}).context['page'].paginator.count==9
 assert client.get(url,{'orden':'populares'}).context['page'][0]==q
 assert b'<img src=x' not in client.get(reverse('comunidades:pregunta',args=[q.pk])).content

def test_privacy_markers_profiles_and_withdrawal(client,people):
 a,b=people;g=Jardin.objects.create(propietario=a,nombre='Mi terraza',clima={'latitude':-0.18,'longitude':-78.47})
 Practica.objects.create(participante=a,jardin=g,posicion=1,titulo='Menta',planta='menta',inicio=date.today(),espacio='Dirección privada',objetivo='Observar')
 api=reverse('comunidades:map_data');assert client.get(api).json()['markers']==[]
 share=reverse('comunidades:compartir',args=[g.pk]);data={'localidad':'Quito','latitud':'-0.18','longitud':'-78.47','visible':'on'}
 assert client.post(share,data).status_code==400
 profile=PerfilComunitario.objects.create(usuario=a,nombre='Ana',visible=True,nivel='inicial')
 assert client.post(share,{**data,'latitud':'-0.1234'}).status_code==400
 assert client.post(share,data).status_code==302
 content=client.get(api).json();assert len(content['markers'])==1 and content['markers'][0]['plants']==['Menta']
 assert 'Dirección privada' not in str(content) and a.email not in str(content)
 client.logout()
 public=client.get(reverse('comunidades:perfil',args=[a.pk]));assert public.status_code==200 and a.email.encode() not in public.content
 client.force_login(b);assert client.post(share,data).status_code==404
 client.force_login(a);assert client.post(share,{**data,'visible':''}).status_code==302
 assert client.get(api).json()['markers']==[]
 profile.visible=False;profile.save();assert client.get(reverse('comunidades:perfil',args=[a.pk])).status_code==404

def test_fragments_and_consent(client,people):
 a,b=people
 r=client.get(reverse('comunidades:nueva_pregunta'),{'fragment':'1'});assert b'<html' not in r.content and r.status_code==200
 r=client.post(reverse('comunidades:nueva_pregunta')+'?fragment=1',payload());assert 'redirect' in r.json()
 r=client.get(reverse('comunidades:listado'));assert b'vendor/leaflet/leaflet.js' not in r.content
 client.post(reverse('privacidad:guardar_cookies'),{'eleccion':'mapas'})
 r=client.get(reverse('comunidades:listado'));assert b'vendor/leaflet/leaflet.js' in r.content

def test_reglas_publicas_y_enlazadas(client):
 r=client.get(reverse('comunidades:reglas'));assert r.status_code==200 and b'Reglas de participaci' in r.content
 assert reverse('comunidades:reglas').encode() in client.get(reverse('comunidades:listado')).content

def test_demo_data_is_labeled_idempotent_and_separate(people,settings):
 from django.core.management import call_command
 from django.contrib.auth import get_user_model
 settings.DEBUG=True
 a,b=people
 original=Jardin.objects.create(propietario=a,nombre='Jardín privado real')
 call_command('seed_community_demo')
 call_command('seed_community_demo')
 demos=get_user_model().objects.filter(groups__name='Huertos · Comunidad de demostración')
 assert demos.count()==6 and all(not u.has_usable_password() for u in demos)
 assert Jardin.objects.filter(propietario__in=demos).count()==6
 assert Practica.objects.filter(participante__in=demos).count()==12
 assert Pregunta.objects.filter(autor__in=demos).count()==8
 assert Respuesta.objects.filter(autor__in=demos).count()==24
 assert all(q.titulo.startswith('[DEMO]') for q in Pregunta.objects.filter(autor__in=demos))
 assert not JardinCompartido.objects.filter(jardin=original).exists()
