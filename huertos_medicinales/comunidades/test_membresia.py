from datetime import date
import pytest
from django.urls import reverse
from .models import Comunidad, Miembro, CertificacionTalento
pytestmark=pytest.mark.django_db

@pytest.fixture
def escenario(client,django_user_model):
 responsable=django_user_model.objects.create_user(email='responsable@example.com')
 voluntario=django_user_model.objects.create_user(email='voluntario@example.com')
 comunidad=Comunidad.objects.create(responsable=responsable,nombre='Huerto Ibarra',provincia='Imbabura',localidad='Ibarra',descripcion='x'*10,encuentro='x'*10,latitud='0.35',longitud='-78.12',estado=Comunidad.Estado.PUBLICADA)
 return responsable,voluntario,comunidad

def test_solicitar_aprobar_y_retirar_miembro(client,escenario):
 responsable,voluntario,comunidad=escenario
 client.force_login(voluntario)
 solicitar=reverse('comunidades:solicitar_membresia',args=[comunidad.pk])
 assert client.post(solicitar,{'fecha_nacimiento':'1990-05-01','genero':'femenino','confirmar_solicitud':'on'}).status_code==302
 miembro=Miembro.objects.get(usuario=voluntario)
 assert miembro.estado==Miembro.Estado.SOLICITADA and miembro.comunidad_id==comunidad.pk
 assert miembro.nivel==Miembro.Nivel.APRENDIZ and miembro.puntos==0
 assert client.post(solicitar,{'fecha_nacimiento':'1990-05-01','genero':'femenino','confirmar_solicitud':'on'}).status_code==302
 miembro.refresh_from_db();assert miembro.estado==Miembro.Estado.SOLICITADA
 client.force_login(responsable)
 gestionar=reverse('comunidades:gestionar_miembros',args=[comunidad.pk])
 assert list(client.get(gestionar).context['solicitudes'])==[miembro]
 decidir=reverse('comunidades:decidir_miembro',args=[comunidad.pk,miembro.pk])
 assert client.post(decidir,{'accion':'aprobar'}).status_code==302
 miembro.refresh_from_db();assert miembro.estado==Miembro.Estado.APROBADA
 assert b'Aprendiz' in client.get(gestionar).content
 retirar=reverse('comunidades:retirar_miembro',args=[comunidad.pk,miembro.pk])
 assert client.post(retirar).status_code==302
 miembro.refresh_from_db();assert miembro.estado==Miembro.Estado.RETIRADA

def test_no_puede_tener_dos_comunidades_a_la_vez(client,escenario,django_user_model):
 responsable,voluntario,comunidad=escenario
 otra=Comunidad.objects.create(responsable=responsable,nombre='Huerto Otavalo',provincia='Imbabura',localidad='Otavalo',descripcion='x'*10,encuentro='x'*10,latitud='0.23',longitud='-78.26',estado=Comunidad.Estado.PUBLICADA)
 client.force_login(voluntario)
 client.post(reverse('comunidades:solicitar_membresia',args=[comunidad.pk]),{'fecha_nacimiento':'1990-05-01','genero':'femenino','confirmar_solicitud':'on'})
 r=client.post(reverse('comunidades:solicitar_membresia',args=[otra.pk]),{'fecha_nacimiento':'1990-05-01','genero':'femenino','confirmar_solicitud':'on'})
 assert r.status_code==302 and Miembro.objects.get(usuario=voluntario).comunidad_id==comunidad.pk

def test_gestion_solo_del_responsable(client,escenario):
 responsable,voluntario,comunidad=escenario
 client.force_login(voluntario)
 assert client.get(reverse('comunidades:gestionar_miembros',args=[comunidad.pk])).status_code==404

def test_proponer_y_certificar_talento(client,escenario):
 responsable,voluntario,comunidad=escenario
 client.force_login(voluntario)
 client.post(reverse('comunidades:solicitar_membresia',args=[comunidad.pk]),{'fecha_nacimiento':'1990-05-01','genero':'femenino','confirmar_solicitud':'on'})
 miembro=Miembro.objects.get(usuario=voluntario)
 client.force_login(responsable)
 client.post(reverse('comunidades:decidir_miembro',args=[comunidad.pk,miembro.pk]),{'accion':'aprobar'})
 proponer=reverse('comunidades:proponer_talento',args=[comunidad.pk,miembro.pk])
 client.post(proponer,{'talento':'Injerto de romero'})
 client.post(proponer,{'talento':'Injerto de romero'})
 assert CertificacionTalento.objects.filter(miembro=miembro,talento='Injerto de romero').count()==1
 cert=CertificacionTalento.objects.get(miembro=miembro,talento='Injerto de romero')
 assert cert.estado==CertificacionTalento.Estado.PROPUESTA and cert.propuesto_por==responsable
