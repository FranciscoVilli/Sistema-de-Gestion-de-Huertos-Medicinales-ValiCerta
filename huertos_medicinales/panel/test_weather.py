from unittest.mock import patch
import pytest
from django.core import signing
from django.core.cache import cache
from django.urls import reverse
from huertos_medicinales.panel.weather import advice
from huertos_medicinales.seguimiento.models import Jardin
pytestmark=pytest.mark.django_db
PLACE={'name':'Cuenca, Azuay','latitude':-2.9,'longitude':-79.0,'timezone':'America/Guayaquil'}
DATA={'current':{'time':'2026-11-06T16:00','temperature_2m':19,'relative_humidity_2m':68,'weather_code':3},'daily':{'time':['2026-11-06','2026-11-07'],'weather_code':[3,61],'temperature_2m_min':[11,12],'temperature_2m_max':[22,21],'precipitation_probability_max':[30,80]}}
@pytest.fixture
def gardens(client,django_user_model):
 cache.clear()
 u=django_user_model.objects.create_user(email='weather@example.com');o=django_user_model.objects.create_user(email='weather-other@example.com');client.force_login(u)
 return Jardin.objects.create(propietario=u,nombre='Ventana'),Jardin.objects.create(propietario=o,nombre='Privado')
def test_config(client,gardens):
 g,f=gardens;url=reverse('garden_weather',args=[g.pk])
 assert client.get(url).json()=={'configured':False}
 assert client.get(reverse('garden_weather',args=[f.pk])).status_code==404
 assert client.post(reverse('garden_weather',args=[f.pk]),{'exposure':'interior'}).status_code==404
 assert client.post(url,{'place':'forged','exposure':'interior'}).status_code==400
 assert client.post(url,{'place':signing.dumps(PLACE,salt='garden-weather'),'exposure':'interior'}).status_code==200
 g.refresh_from_db();assert g.clima['name']=='Cuenca, Azuay'
 assert client.post(url,{'exposure':'cubierto'}).status_code==200
 g.refresh_from_db();assert g.clima['exposure']=='cubierto'
 client.logout();assert client.get(url).status_code==302

def test_forecast(client,gardens):
 g,_=gardens;g.clima={**PLACE,'exposure':'exterior'};g.save();url=reverse('garden_weather',args=[g.pk])
 with patch('huertos_medicinales.panel.weather.fetch_json',return_value=DATA.copy()) as remote:
  current=client.get(url).json();assert current['humidity']==68 and current['current']
  future=client.get(url,{'date':'2026-11-07'}).json();assert future['humidity'] is None and not future['current'] and future['rain']==80
  assert not client.get(url,{'date':'2027-01-01'}).json()['available'];assert remote.call_count==1
 assert client.get(url,{'date':'bad'}).status_code==400
 cache.clear()
 with patch('huertos_medicinales.panel.weather.fetch_json',side_effect=OSError('offline')):
  r=client.get(url).json();assert r['configured'] and not r['available']

def test_search(client,gardens):
 url=reverse('weather_places');assert client.get(url,{'q':'a'}).status_code==400
 with patch('huertos_medicinales.panel.weather.fetch_json',return_value={'results':[{'name':'Cuenca','admin1':'Azuay','country_code':'EC','latitude':-2.9,'longitude':-79.0},{'name':'Cuenca','country_code':'ES'}]}):
  rows=client.get(url,{'q':'Cuenca'}).json()['results'];assert len(rows)==1
  assert signing.loads(rows[0]['token'],salt='garden-weather')['name']=='Cuenca, Azuay'
 assert 'interior' in advice('interior',90)
 assert 'cubierto' in advice('cubierto',90)
 assert 'humedad ambiental' in advice('exterior',None)

def test_calendar(client,gardens):
 g,_=gardens;r=client.get(reverse('calendar'),{'jardin':g.pk,'dia':'2026-11-24'})
 assert r.status_code==200 and r.context['weather_garden']==g
 assert 'jardin='+str(g.pk) in r.context['next']
 assert b'data-weather' in r.content

def test_geolocation(client,gardens):
 g,f=gardens;url=reverse('garden_weather',args=[g.pk])
 payload={'mode':'geolocation','latitude':'-2.901234','longitude':'-79.001234','exposure':'unknown'}
 assert client.post(url,payload).status_code==200
 g.refresh_from_db();assert g.clima['latitude']==-2.9 and g.clima['longitude']==-79.0
 assert g.clima['timezone']=='auto'
 assert client.post(reverse('garden_weather',args=[f.pk]),payload).status_code==404
 for bad in ['NaN','inf','91','bad','']:
  assert client.post(url,{**payload,'latitude':bad}).status_code==400
 with patch('huertos_medicinales.panel.weather.fetch_json',return_value={**DATA,'timezone':'Pacific/Galapagos'}):
  assert client.get(url).json()['timezone']=='Pacific/Galapagos'
