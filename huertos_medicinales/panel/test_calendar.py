from datetime import date

import pytest
from django.urls import reverse

from huertos_medicinales.seguimiento.models import ActividadCalendario
from huertos_medicinales.seguimiento.models import Practica

pytestmark = pytest.mark.django_db

@pytest.fixture
def data(client, django_user_model):
    u=django_user_model.objects.create_user(email="calendar@example.com")
    other=django_user_model.objects.create_user(email="other-calendar@example.com")
    def crop(user):
        return Practica.objects.create(participante=user,titulo="Menta de ventana",planta="menta",inicio=date(2026,1,1),espacio="Ventana",objetivo="Observar")
    p=crop(u); foreign=crop(other)
    client.force_login(u)
    return p,foreign

def test_month_dates_and_filters(client,data):
    p,foreign=data
    a=ActividadCalendario.objects.create(practica=p,fecha=date(2026,2,28),tipo="riego")
    ActividadCalendario.objects.create(practica=foreign,fecha=a.fecha,tipo="riego")
    response=client.get(reverse("calendar"),{"dia":"2026-02-28"})
    assert response.status_code==200
    assert list(response.context["agenda"])==[a]
    assert len(response.context["weeks"])==5
    assert response.context["weeks"][0][0]["date"]==date(2026,1,26)
    assert client.get(reverse("calendar"),{"dia":"2026-02-28","tipo":"foto"}).context["agenda"].count()==0
    assert client.get(reverse("calendar"),{"dia":"invalid","mes":"99999-99","cultivo":"bad"}).status_code==200

def test_create_edit_and_foreign_crop(client,data):
    p,foreign=data
    payload={"practica":str(p.pk),"fecha":"2026-10-28","hora":"08:00","tipo":"riego","notas":"Revisar humedad"}
    assert client.post(reverse("calendar_new"),payload).status_code==302
    a=ActividadCalendario.objects.get(practica=p)
    payload["fecha"]="2026-10-30"
    assert client.post(reverse("calendar_edit",args=[a.pk]),payload).status_code==302
    a.refresh_from_db(); assert a.fecha==date(2026,10,30)
    payload["practica"]=str(foreign.pk)
    response=client.post(reverse("calendar_new"),payload)
    assert response.status_code==200 and response.context["form"].errors
    assert ActividadCalendario.objects.count()==1
    payload["fecha"]="not-a-date"
    assert client.post(reverse("calendar_new"),payload).context["form"].errors

def test_complete_idempotent_and_permissions(client,data):
    p,foreign=data
    a=ActividadCalendario.objects.create(practica=p,fecha=date(2026,10,28),tipo="foto")
    url=reverse("calendar_complete",args=[a.pk])
    assert client.get(url).status_code==405
    for _ in range(2): assert client.post(url,{"completada":"1"}).status_code==302
    a.refresh_from_db();assert a.completada and a.completada_en
    assert p.observaciones.count()==0
    client.post(url,{"completada":"0"});a.refresh_from_db();assert not a.completada
    f=ActividadCalendario.objects.create(practica=foreign,fecha=a.fecha,tipo="riego")
    assert client.post(reverse("calendar_complete",args=[f.pk]),{"completada":"1"}).status_code==404
    assert client.get(reverse("calendar_edit",args=[f.pk])).status_code==404
    client.logout()
    assert client.get(reverse("calendar")).status_code==302

def test_siembra_con_tecnica_propagacion_y_aviso_lunar(client,data):
    p,foreign=data
    from .lunar import events
    llena=next(e for e in events() if e['phase']=='Full Moon')
    payload={"practica":str(p.pk),"fecha":llena['date'].isoformat(),"tipo":"siembra","tecnica":"surcos","propagacion":"semilla"}
    assert client.post(reverse("calendar_new"),payload).status_code==302
    a=ActividadCalendario.objects.get(practica=p)
    assert a.tecnica=="surcos" and a.propagacion=="semilla"
    response=client.get(reverse("calendar_new"),{"dia":llena['date'].isoformat()})
    assert response.context["luna"] is None  # formulario nuevo y vacio: "tipo" todavia no tiene valor
    editar=client.get(reverse("calendar_edit",args=[a.pk]),{"dia":llena['date'].isoformat()})
    assert editar.context["luna"]["ideal"] is True and editar.context["luna"]["fase"]=="Luna llena"

def test_empaquetado_hereda_fecha_de_caducidad_por_region(client,data):
    from huertos_medicinales.seguimiento.models import Empaquetado
    p,foreign=data
    sierra=Empaquetado.objects.create(practica=p,indicaciones="x",dosificacion="x",fecha_empaquetado=date(2026,1,1),region="sierra")
    costa=Empaquetado.objects.create(practica=p,indicaciones="x",dosificacion="x",fecha_empaquetado=date(2026,1,1),region="costa")
    assert sierra.fecha_caducidad==date(2027,1,1)
    assert costa.fecha_caducidad==date(2026,6,30)
