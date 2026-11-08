from datetime import date
import pytest
from django.urls import reverse
from django.utils import timezone
from .models import Comunidad, Miembro, CertificacionTalento, Mision, InsigniaObtenida
from huertos_medicinales.seguimiento.models import ActividadCalendario, Observacion, Practica
pytestmark=pytest.mark.django_db

@pytest.fixture
def miembro_aprobado(client,django_user_model):
 responsable=django_user_model.objects.create_user(email='responsable-gami@example.com')
 voluntario=django_user_model.objects.create_user(email='voluntario-gami@example.com')
 comunidad=Comunidad.objects.create(responsable=responsable,nombre='Huerto Gamificacion',provincia='Imbabura',localidad='Ibarra',descripcion='x'*10,encuentro='x'*10,latitud='0.35',longitud='-78.12',estado=Comunidad.Estado.PUBLICADA)
 miembro=Miembro.objects.create(usuario=voluntario,comunidad=comunidad,fecha_nacimiento='1990-01-01',genero='femenino',estado=Miembro.Estado.APROBADA)
 return responsable,voluntario,comunidad,miembro

def practica_de(usuario):
 return Practica.objects.create(participante=usuario,titulo='Romero',planta='romero',inicio=date(2026,1,1),espacio='Patio',objetivo='x')

def test_puntos_suman_actividades_observaciones_y_talentos(client,miembro_aprobado):
 responsable,voluntario,comunidad,miembro=miembro_aprobado
 p=practica_de(voluntario)
 ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,2),tipo='riego',completada=True)
 ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,3),tipo='riego',completada=False)
 Observacion.objects.create(practica=p,fecha=date(2026,1,2),accion='x',resultado='x')
 assert miembro.puntos==5+3  # una actividad completada + una observacion
 CertificacionTalento.objects.create(miembro=miembro,talento='Injerto',estado=CertificacionTalento.Estado.CERTIFICADA,propuesto_por=responsable)
 assert miembro.puntos==5+3+20
 assert comunidad.puntos==miembro.puntos

def test_nivel_sube_segun_umbrales(client,miembro_aprobado):
 responsable,voluntario,comunidad,miembro=miembro_aprobado
 p=practica_de(voluntario)
 assert miembro.nivel==Miembro.Nivel.APRENDIZ
 for n in range(10):
  ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,n+1),tipo='riego',completada=True)
 assert miembro.puntos==50 and miembro.nivel==Miembro.Nivel.OFICIAL
 for n in range(20):
  ActividadCalendario.objects.create(practica=p,fecha=date(2026,2,n+1),tipo='riego',completada=True)
 assert miembro.nivel==Miembro.Nivel.MAESTRO

def test_completar_actividad_otorga_insignia_y_certificar_talento_tambien(client,miembro_aprobado):
 responsable,voluntario,comunidad,miembro=miembro_aprobado
 p=practica_de(voluntario)
 a=ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,2),tipo='riego')
 client.force_login(voluntario)
 client.post(reverse('calendar_complete',args=[a.pk]),{'completada':'1'})
 assert InsigniaObtenida.objects.filter(miembro=miembro,clave='primera_actividad').exists()
 cert=CertificacionTalento.objects.create(miembro=miembro,talento='Injerto',estado=CertificacionTalento.Estado.PROPUESTA,propuesto_por=responsable)
 from django.contrib.auth.models import Permission
 responsable.user_permissions.add(Permission.objects.get(codename='certificar_talento'))
 responsable.user_permissions.add(Permission.objects.get(codename='view_certificaciontalento'))
 responsable.is_staff=True;responsable.save()
 client.force_login(responsable)
 client.post(reverse('admin:comunidades_certificaciontalento_changelist'),{'action':'certificar','_selected_action':[str(cert.pk)]})
 assert InsigniaObtenida.objects.filter(miembro=miembro,clave='primer_talento').exists()

def test_mision_completada_suma_puntos_de_recompensa(client,miembro_aprobado):
 responsable,voluntario,comunidad,miembro=miembro_aprobado
 p=practica_de(voluntario)
 Mision.objects.create(titulo='Reto de enero',descripcion='x',meta_actividades=2,puntos_recompensa=15,fecha_inicio=date(2026,1,1),fecha_fin=date(2026,1,31))
 ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,2),tipo='riego',completada=True,completada_en=timezone.make_aware(timezone.datetime(2026,1,2,10,0)))
 assert miembro.puntos==5  # una sola actividad, mision no cumplida aun
 ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,5),tipo='riego',completada=True,completada_en=timezone.make_aware(timezone.datetime(2026,1,5,10,0)))
 assert miembro.puntos==5+5+15

def test_ranking_ordena_comunidades_por_puntos(client,miembro_aprobado):
 responsable,voluntario,comunidad,miembro=miembro_aprobado
 p=practica_de(voluntario)
 ActividadCalendario.objects.create(practica=p,fecha=date(2026,1,2),tipo='riego',completada=True)
 otra=Comunidad.objects.create(responsable=responsable,nombre='Huerto Sin Puntos',provincia='Imbabura',localidad='Otavalo',descripcion='x'*10,encuentro='x'*10,latitud='0.23',longitud='-78.26',estado=Comunidad.Estado.PUBLICADA)
 r=client.get(reverse('comunidades:ranking'))
 assert list(r.context['comunidades'])==[comunidad,otra]
