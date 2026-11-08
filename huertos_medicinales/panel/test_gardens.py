import pytest
from django.db import IntegrityError
from django.db import transaction
from django.urls import reverse
from django.utils import timezone

from huertos_medicinales.seguimiento.models import Jardin
from huertos_medicinales.seguimiento.models import Practica

pytestmark=pytest.mark.django_db


def unlock(user, species):
 from django.core.management import call_command
 from huertos_medicinales.aprendizaje.educational_models import RutaEducativa, CompetenciaAdquirida, IntentoCapitulo, EvaluacionEducativa
 call_command("seed_education_pilot",verbosity=0)
 route=RutaEducativa.objects.get(slug="manzanilla-observar-recipiente")
 exam=EvaluacionEducativa.objects.get(capitulo__numero=5)
 attempt=IntentoCapitulo.objects.create(user=user,evaluacion=exam,version="test",contenido={},aprobado=True,finalizado=timezone.now())
 for competency in route.requisitos.all():
  CompetenciaAdquirida.objects.get_or_create(user=user,competencia=competency,defaults={"intento":attempt})
 if species!="manzanilla":
  other=RutaEducativa.objects.create(slug="test-"+species,nombre=species,especie=species,estado="publicado")
  other.requisitos.set(route.requisitos.all())

@pytest.fixture
def setup(client,django_user_model):
 u=django_user_model.objects.create_user(email="garden-test@example.com")
 other=django_user_model.objects.create_user(email="other-garden@example.com")
 client.force_login(u)
 g=Jardin.objects.create(propietario=u,nombre="Mi balcón")
 foreign=Jardin.objects.create(propietario=other,nombre="Privado")
 p=Practica.objects.create(participante=u,titulo="Menta de prueba",planta="menta",inicio=timezone.localdate(),espacio="Ventana",objetivo="Observar")
 return u,other,g,foreign,p

def test_empty_garden_and_creation(client,setup):
 u,other,g,foreign,p=setup
 response=client.get(reverse("workspace"),{"jardin":g.pk})
 assert response.status_code==200
 assert response.context["libres"]==6
 assert response.context["seleccionada"] is None
 assert response.content.count(b"empty-ring")==6
 response=client.post(reverse("garden_new"),{"nombre":"Segundo jardín"})
 assert response.status_code==302
 assert Jardin.objects.filter(propietario=u).count()==2

def test_place_move_release_preserves_crop(client,setup):
 u,other,g,foreign,p=setup
 unlock(u,"menta")
 url=reverse("garden_place",args=[g.pk,2])
 assert client.post(url,{"modo":"existente","cultivo":p.pk}).status_code==302
 p.refresh_from_db();assert (p.jardin_id,p.posicion)==(g.pk,2)
 response=client.get(reverse("workspace"),{"jardin":g.pk,"cultivo":p.pk})
 assert response.status_code==200 and response.context["libres"]==5
 assert response.context["seleccionada"].pk==p.pk
 second=Jardin.objects.create(propietario=u,nombre="Patio")
 assert client.post(reverse("garden_place",args=[second.pk,4]),{"modo":"existente","cultivo":p.pk}).status_code==302
 p.refresh_from_db();assert p.jardin_id==second.pk and p.posicion==4
 assert not g.cultivos.exists()
 assert client.post(reverse("garden_release",args=[p.pk])).status_code==302
 p.refresh_from_db();assert p.jardin_id is None and p.posicion is None
 assert p.espacio=="Ventana" and p.eventos.count()==3

def test_ownership_and_free_real_cultivation(client,setup):
 u,other,g,foreign,p=setup
 assert client.get(reverse("workspace"),{"jardin":foreign.pk}).status_code==404
 assert client.post(reverse("garden_place",args=[foreign.pk,1]),{"modo":"existente","cultivo":p.pk}).status_code==404
 outsider=Practica.objects.create(participante=other,titulo="Privado",planta="menta",inicio=timezone.localdate(),espacio="Privado",objetivo="Privado")
 assert client.post(reverse("garden_place",args=[g.pk,1]),{"modo":"existente","cultivo":outsider.pk}).status_code==404
 assert client.post(reverse("garden_release",args=[outsider.pk])).status_code==404
 response=client.post(reverse("garden_place",args=[g.pk,1]),{"modo":"nueva","titulo":"Bloqueada","planta":"menta","inicio":timezone.localdate(),"espacio":"Patio","objetivo":"Observar"})
 assert response.status_code==200 and not g.cultivos.filter(participante=u,planta="menta").exists()
 assert client.get(reverse("garden_place",args=[g.pk,7])).status_code==404

def test_full_garden_and_constraints(client,setup):
 u,other,g,foreign,p=setup
 for i in range(1,7):
  Practica.objects.create(participante=u,titulo=f"Planta {i}",planta="menta",inicio=timezone.localdate(),espacio="Patio",objetivo="Observar",jardin=g,posicion=i)
 response=client.get(reverse("workspace"),{"jardin":g.pk})
 assert response.context["libres"]==0 and "Jardín lleno" in response.content.decode()
 assert client.post(reverse("garden_place",args=[g.pk,1]),{"modo":"existente","cultivo":p.pk}).status_code==200
 p.refresh_from_db();assert p.jardin_id is None
 with pytest.raises(IntegrityError),transaction.atomic():
  p.jardin=g;p.posicion=1;p.save()
 with pytest.raises(IntegrityError),transaction.atomic():
  p.posicion=7;p.save()

def test_new_unlocked_crop_and_post_only_release(client,setup):
 from huertos_medicinales.aprendizaje.catalogo import LECCIONES
 from huertos_medicinales.aprendizaje.models import Logro
 u,other,g,foreign,p=setup
 unlock(u,"manzanilla")
 response=client.post(reverse("garden_place",args=[g.pk,3]),{"modo":"seleccionar","planta":"manzanilla"})
 assert response.status_code==302
 created=g.cultivos.get(posicion=3)
 assert created.participante_id==u.pk and created.planta=="manzanilla"
 assert client.get(reverse("garden_release",args=[created.pk])).status_code==405
 assert client.get(reverse("workspace"),{"jardin":g.pk,"cultivo":created.pk}).status_code==200


def test_visual_selector_checks_learning_and_occupied_slot(client,setup):
 u,other,g,foreign,p=setup
 url=reverse("garden_place",args=[g.pk,1])
 assert "Continuar aprendiendo" in client.get(url).content.decode()
 assert client.post(url,{"modo":"seleccionar","planta":"manzanilla"}).status_code==200
 assert not g.cultivos.exists()
 unlock(u,"manzanilla")
 response=client.get(url)
 assert [item["slug"] for item in response.context["plantas_disponibles"]]==["manzanilla"]
 assert 'name="titulo"' not in response.content.decode()
 assert client.post(url,{"modo":"seleccionar","planta":"menta"}).status_code==200
 assert not g.cultivos.exists()
 assert client.post(url,{"modo":"seleccionar","planta":"manzanilla","inicio":"2000-01-01"}).status_code==302
 crop=g.cultivos.get()
 assert crop.inicio==timezone.localdate() and crop.participante==u
 assert client.post(url,{"modo":"seleccionar","planta":"manzanilla"}).status_code==200
 assert g.cultivos.count()==1

def test_route_without_requirements_does_not_unlock(client,setup):
 from huertos_medicinales.aprendizaje.educational_models import RutaEducativa
 u,other,g,foreign,p=setup
 RutaEducativa.objects.create(slug="empty",nombre="Menta",especie="menta",estado="publicado")
 response=client.get(reverse("garden_place",args=[g.pk,1]))
 assert not response.context["plantas_disponibles"]

def test_demo_access_is_explicit_and_does_not_unlock_other_accounts(client,setup):
 from django.contrib.auth.models import Group
 from huertos_medicinales.panel.gardens import plantas_desbloqueadas
 u,other,g,foreign,p=setup
 group=Group.objects.create(name="Huertos · Demostración de aprendizaje completo")
 u.groups.add(group)
 assert len(plantas_desbloqueadas(u))==4
 assert plantas_desbloqueadas(other)==[]
 u.groups.remove(group)
 assert plantas_desbloqueadas(u)==[]
