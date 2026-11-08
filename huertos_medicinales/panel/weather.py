"""Locality weather: no precise address or browser geolocation required."""
import json
import math
from datetime import date
from urllib.parse import urlencode
from urllib.request import urlopen
from django.core import signing
from django.core.cache import cache
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods
from huertos_medicinales.seguimiento.models import Jardin

EXPOSURES = {'unknown': 'Espacio por definir', 'exterior': 'Al aire libre', 'interior': 'Dentro de casa', 'cubierto': 'Balcón o patio cubierto'}

def fetch_json(url):
    with urlopen(url, timeout=6) as response:
        return json.load(response)

@login_required
@require_GET
def places(request):
    query = request.GET.get('q', '').strip()
    if not 3 <= len(query) <= 80:
        return JsonResponse({'error': 'Escribe al menos 3 letras de tu ciudad o localidad.'}, status=400)
    key = 'weather-search:' + query.casefold()
    results = cache.get(key)
    if results is None:
        try:
            data = fetch_json('https://geocoding-api.open-meteo.com/v1/search?' + urlencode({'name':query,'count':8,'language':'es','countryCode':'EC'}))
            results = []
            for item in data.get('results', []):
                if item.get('country_code') != 'EC':
                    continue
                place = {'name': ', '.join(filter(None,[item['name'],item.get('admin1')])), 'latitude':item['latitude'], 'longitude':item['longitude'], 'timezone':item.get('timezone','America/Guayaquil')}
                results.append({'name':place['name'], 'token':signing.dumps(place,salt='garden-weather')})
            cache.set(key,results,3600)
        except (OSError, ValueError, KeyError, TypeError):
            return JsonResponse({'error':'No se pudo buscar la localidad. Intenta nuevamente en unos momentos.'},status=503)
    return JsonResponse({'results':results})

def condition(code):
    if code == 0: return ('☀️','Despejado')
    if code in (1,2): return ('🌤️','Parcialmente nublado')
    if code == 3: return ('☁️','Nublado')
    if code in (45,48): return ('🌫️','Neblina')
    if code in (51,53,55,56,57): return ('🌦️','Llovizna')
    if code in (61,63,65,66,67,80,81,82): return ('🌧️','Lluvia')
    if code in (71,73,75,77,85,86): return ('🌨️','Nieve')
    if code in (95,96,99): return ('⛈️','Tormenta')
    return ('🌡️','Estado no disponible')

def advice(exposure, rain):
    if exposure == 'unknown':
        return 'Revisa el sustrato antes de regar. Indica si tus plantas están dentro de casa, al aire libre o cubiertas para adaptar los consejos.'
    if exposure == 'interior':
        return 'La lluvia exterior no riega tus macetas de interior. Observa la luz junto a la ventana y revisa el sustrato antes de regar.'
    if exposure == 'cubierto':
        return 'Tu espacio está cubierto: comprueba si la lluvia alcanza las plantas y revisa la humedad del sustrato antes de regar.'
    if rain is not None and rain >= 50:
        return 'Hay probabilidad de lluvia. Revisa el drenaje y la humedad del sustrato antes de decidir si necesitas regar.'
    return 'Observa la luz y la humedad del sustrato. Ajusta el riego a tu especie; la humedad ambiental no indica cuánta agua tiene la maceta.'

def forecast(config, selected):
    key = 'garden-forecast:' + str(config['latitude']) + ':' + str(config['longitude'])
    data = cache.get(key)
    if data is None:
        params = {'latitude':config['latitude'],'longitude':config['longitude'],'timezone':config['timezone'],'forecast_days':7,'current':'temperature_2m,relative_humidity_2m,weather_code','daily':'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max'}
        data = fetch_json('https://api.open-meteo.com/v1/forecast?' + urlencode(params))
        if not data.get('daily',{}).get('time') or not data.get('current',{}).get('time'):
            raise ValueError('Incomplete weather response')
        data['retrieved_at'] = timezone.now().isoformat()
        cache.set(key,data,900)
    day = selected or data['current']['time'][:10]
    daily = data['daily']
    if day not in daily['time']:
        return {'available':False,'message':'Pronóstico todavía no disponible para esta fecha. Consulta los próximos 7 días; no se muestran datos históricos.'}
    index = daily['time'].index(day)
    current_day = day == data['current']['time'][:10]
    code = data['current'].get('weather_code') if current_day else daily['weather_code'][index]
    icon, label = condition(code)
    rain = daily['precipitation_probability_max'][index]
    return {'available':True,'date':day,'current':current_day,'icon':icon,'label':label,'temperature':data['current'].get('temperature_2m') if current_day else None,'humidity':data['current'].get('relative_humidity_2m') if current_day else None,'minimum':daily['temperature_2m_min'][index],'maximum':daily['temperature_2m_max'][index],'rain':rain,'updated':data['retrieved_at'],'timezone':data.get('timezone','America/Guayaquil'),'local_time':data['current']['time'],'advice':advice(config['exposure'],rain)}

@login_required
@require_http_methods(['GET','POST'])
def garden_weather(request, pk):
    garden = get_object_or_404(Jardin,pk=pk,propietario=request.user)
    if request.method == 'POST':
        exposure = request.POST.get('exposure')
        if exposure not in EXPOSURES:
            return JsonResponse({'error':'Selecciona dónde están tus plantas.'},status=400)
        config = dict(garden.clima)
        token = request.POST.get('place','')
        if request.POST.get('mode') == 'geolocation':
            try:
                lat = float(request.POST.get('latitude', ''))
                lon = float(request.POST.get('longitude', ''))
                if not (math.isfinite(lat) and math.isfinite(lon) and -90 <= lat <= 90 and -180 <= lon <= 180):
                    raise ValueError
            except (ValueError, TypeError):
                return JsonResponse({'error':'La ubicación recibida no es válida.'},status=400)
            config = {'name':'Ubicación aproximada del jardín','latitude':round(lat,2),'longitude':round(lon,2),'timezone':'auto','source':'browser'}
        elif token:
            try:
                config = signing.loads(token,salt='garden-weather',max_age=86400)
            except signing.BadSignature:
                return JsonResponse({'error':'Busca y selecciona nuevamente la localidad.'},status=400)
        if not config.get('name'):
            return JsonResponse({'error':'Busca y selecciona una localidad.'},status=400)
        config['exposure'] = exposure
        garden.clima = config
        garden.save(update_fields=['clima'])
        return JsonResponse({'saved':True})
    if not garden.clima:
        return JsonResponse({'configured':False})
    selected = request.GET.get('date','')
    if selected:
        try: date.fromisoformat(selected)
        except ValueError: return JsonResponse({'error':'Fecha no válida.'},status=400)
    result = {'configured':True,'name':garden.clima['name'],'exposure':garden.clima['exposure'],'exposure_label':EXPOSURES[garden.clima['exposure']],'timezone':garden.clima['timezone']}
    try:
        result.update(forecast(garden.clima,selected))
    except (OSError,ValueError,KeyError,TypeError,IndexError):
        result.update(available=False,message='El servicio de clima no está disponible ahora. Puedes reintentar; tus actividades siguen guardadas.')
    return JsonResponse(result)
