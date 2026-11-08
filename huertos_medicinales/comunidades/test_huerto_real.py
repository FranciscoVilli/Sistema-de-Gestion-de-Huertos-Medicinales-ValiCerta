import pytest
from django.urls import reverse
from .models import Comunidad, HuertoReal, Bodega
pytestmark=pytest.mark.django_db

@pytest.fixture
def escenario(client,django_user_model):
 responsable=django_user_model.objects.create_user(email='responsable-huerto@example.com')
 otro=django_user_model.objects.create_user(email='otro-huerto@example.com')
 comunidad=Comunidad.objects.create(responsable=responsable,nombre='Huerto Real Ibarra',provincia='Imbabura',localidad='Ibarra',descripcion='x'*10,encuentro='x'*10,latitud='0.35',longitud='-78.12',estado=Comunidad.Estado.PUBLICADA)
 client.force_login(responsable)
 return responsable,otro,comunidad

def payload():
 return {
  'provincia':'Imbabura','parroquia':'San Antonio','direccion':'Vía a la loma, km 2',
  'latitud':'0.354521','longitud':'-78.121345',
  'tipo_diseno':'en_tierra','tecnica_diseno':'Surcos',
  'tipo_cerca':'viva','detalle_cerca':'Higuerilla y floripondio',
  'area_total':'45.5','unidad_area':'m2',
  'tipo_suelo':'arcilloso',
  'tipo_agua_riego':'canal','detalle_riego':'Canal comunitario los martes',
  'tipo_abono':'compost','detalle_abono':'Compost propio',
  'tiene_espacio_herramientas':'on','detalle_herramientas':'Estante de madera',
  'tiene_espacio_semillas':'on','detalle_semillas':'',
  'tiene_espacio_abonos':'','detalle_abonos':'',
 }

def test_responsable_registra_huerto_real_y_bodega(client,escenario):
 responsable,otro,comunidad=escenario
 url=reverse('comunidades:huerto_real',args=[comunidad.pk])
 assert client.get(url).status_code==200
 assert client.post(url,payload()).status_code==302
 huerto=HuertoReal.objects.get(comunidad=comunidad)
 assert huerto.tipo_diseno=='en_tierra' and huerto.tipo_cerca=='viva' and str(huerto.area_total)=='45.50'
 bodega=Bodega.objects.get(huerto_real=huerto)
 assert bodega.tiene_espacio_herramientas and bodega.tiene_espacio_semillas and not bodega.tiene_espacio_abonos
 detalle=client.get(reverse('comunidades:detalle',args=[comunidad.pk]))
 assert b'Higuerilla y floripondio' in detalle.content and b'0.354521' not in detalle.content

def test_editar_reutiliza_el_mismo_registro(client,escenario):
 responsable,otro,comunidad=escenario
 url=reverse('comunidades:huerto_real',args=[comunidad.pk])
 client.post(url,payload())
 nueva=payload();nueva['area_total']='60.0'
 client.post(url,nueva)
 assert HuertoReal.objects.filter(comunidad=comunidad).count()==1
 assert str(HuertoReal.objects.get(comunidad=comunidad).area_total)=='60.00'

def test_solo_el_responsable_puede_gestionar_el_huerto_real(client,escenario):
 responsable,otro,comunidad=escenario
 client.force_login(otro)
 url=reverse('comunidades:huerto_real',args=[comunidad.pk])
 assert client.get(url).status_code==404
 assert client.post(url,payload()).status_code==404
