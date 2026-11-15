from datetime import date

import pytest
from django.urls import reverse

from huertos_medicinales.seguimiento.models import ActividadCalendario
from huertos_medicinales.seguimiento.models import Practica
from .calendar import notificaciones_de

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

def test_modal_rapido_solo_tiene_los_campos_minimos(client,data):
    p,foreign=data
    response=client.get(reverse("calendar"),{"dia":"2026-02-28"})
    assert list(response.context["nueva_form"].fields)==["practica","tipo","fecha","hora"]
    nuevo=client.get(reverse("calendar_new"),{"dia":"2026-02-28"})
    assert list(nuevo.context["form"].fields)==["practica","tipo","fecha","hora"]
    a=ActividadCalendario.objects.create(practica=p,fecha=date(2026,2,28),tipo="riego")
    editar=client.get(reverse("calendar_edit",args=[a.pk]))
    assert "notas" in editar.context["form"].fields and "recordatorio_dias_antes" in editar.context["form"].fields

def test_tipo_texto_libre_con_sugerencias(client,data):
    p,foreign=data
    payload={"practica":str(p.pk),"fecha":"2026-10-28","hora":"08:00","tipo":"RIEGO"}
    assert client.post(reverse("calendar_new"),payload).status_code==302
    a=ActividadCalendario.objects.get(practica=p)
    assert a.tipo=="riego" and a.get_tipo_display()=="Riego"
    payload["fecha"]="2026-10-29"
    payload["tipo"]="Fertilizar con compost"
    assert client.post(reverse("calendar_new"),payload).status_code==302
    b=ActividadCalendario.objects.get(practica=p,fecha=date(2026,10,29))
    assert b.tipo=="Fertilizar con compost" and b.get_tipo_display()=="Fertilizar con compost"

def test_sin_cultivos_activos_invita_a_ir_al_jardin(client,data):
    p,foreign=data
    p.estado="finalizada"; p.save()
    response=client.get(reverse("calendar"),{"dia":"2026-02-28"})
    assert response.context["sin_cultivos_activos"] is True
    assert reverse("workspace").encode() in response.content
    nuevo=client.get(reverse("calendar_new"))
    assert nuevo.context["sin_cultivos_activos"] is True
    assert reverse("workspace").encode() in nuevo.content

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
    payload={"practica":str(p.pk),"fecha":llena['date'].isoformat(),"tipo":"siembra"}
    assert client.post(reverse("calendar_new"),payload).status_code==302
    a=ActividadCalendario.objects.get(practica=p)
    payload["tecnica"]="surcos"
    payload["propagacion"]="semilla"
    assert client.post(reverse("calendar_edit",args=[a.pk]),payload).status_code==302
    a.refresh_from_db()
    assert a.tecnica=="surcos" and a.propagacion=="semilla"
    response=client.get(reverse("calendar_new"),{"dia":llena['date'].isoformat()})
    assert response.context["luna"] is None  # formulario nuevo y vacio: "tipo" todavia no tiene valor
    editar=client.get(reverse("calendar_edit",args=[a.pk]),{"dia":llena['date'].isoformat()})
    assert editar.context["luna"]["ideal"] is True and editar.context["luna"]["fase"]=="Luna llena"

def test_notificaciones_de_proximas_actividades_y_recordatorio_activo(client,data):
    p,foreign=data
    hoy=date(2026,10,28)
    pendiente=ActividadCalendario.objects.create(practica=p,fecha=date(2026,10,30),tipo="riego",recordatorio_dias_antes=3)
    lejana=ActividadCalendario.objects.create(practica=p,fecha=date(2026,11,2),tipo="riego",recordatorio_dias_antes=3)
    ActividadCalendario.objects.create(practica=p,fecha=date(2026,10,29),tipo="riego",completada=True)
    ActividadCalendario.objects.create(practica=foreign,fecha=date(2026,10,29),tipo="riego")
    resultado=notificaciones_de(p.participante,today=hoy)
    actividades=resultado["actividades"]
    assert [a.pk for a in actividades]==[pendiente.pk,lejana.pk]
    assert actividades[0].recordatorio_activo is True
    assert actividades[1].recordatorio_activo is False
    esperado_luna=1 if resultado["luna"] and resultado["luna"]["hoy"] else 0
    assert resultado["total"]==len(actividades)+esperado_luna

def test_notificaciones_de_incluye_aviso_lunar_cuando_hoy_es_favorable(client,data):
    p,foreign=data
    from .lunar import events
    llena=next(e for e in events() if e['phase']=='Full Moon')
    resultado=notificaciones_de(p.participante,today=llena['date'])
    assert resultado["actividades"]==[]
    assert resultado["luna"]["hoy"] is True
    assert resultado["total"]==1

def test_empaquetado_hereda_fecha_de_caducidad_por_region(client,data):
    from huertos_medicinales.seguimiento.models import Empaquetado
    p,foreign=data
    sierra=Empaquetado.objects.create(practica=p,indicaciones="x",dosificacion="x",fecha_empaquetado=date(2026,1,1),region="sierra")
    costa=Empaquetado.objects.create(practica=p,indicaciones="x",dosificacion="x",fecha_empaquetado=date(2026,1,1),region="costa")
    assert sierra.fecha_caducidad==date(2027,1,1)
    assert costa.fecha_caducidad==date(2026,6,30)
