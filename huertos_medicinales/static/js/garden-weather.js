(() => {
  document.querySelectorAll('[data-weather]').forEach(widget => {
    const endpoint = widget.dataset.endpoint;
    if (!endpoint) return;
    const result = widget.querySelector('[data-weather-result]');
    const settings = widget.querySelector('details');
    const search = widget.querySelector('[data-weather-search]');
    const save = widget.querySelector('[data-weather-save]');
    const select = widget.querySelector('[data-place-results]');
    let loading = false;
    const element = (tag, text, className) => { const node = document.createElement(tag); node.textContent = text; if (className) node.className = className; return node; };
    const display = (value, suffix) => value === null || value === undefined ? 'No disponible' : `${value}${suffix}`;
    async function request(url, options = {}) {
      const controller = new AbortController();
      const timer = setTimeout(() => controller.abort(), 12000);
      try {
        const response = await fetch(url, {...options, signal:controller.signal, credentials:'same-origin', headers:{Accept:'application/json', ...(options.headers || {})}});
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'No se pudo completar la consulta.');
        return data;
      } finally { clearTimeout(timer); }
    }
    async function load() {
      if (loading) return;
      loading = true;
      const refresh = widget.querySelector('[data-refresh]'); refresh.disabled = true;
      result.replaceChildren(element('p','Consultando el clima…'));
      try {
        const url = new URL(endpoint, location.origin);
        if (widget.dataset.date) url.searchParams.set('date', widget.dataset.date);
        const data = await request(url);
        result.replaceChildren();
        if (!data.configured) {
          result.append(element('p','Usa tu ubicación para ver el clima de este jardín, sin escribir una ciudad.'));
          return;
        }
        widget.querySelector('[data-place]').textContent = `📍 ${data.name} · ${data.exposure_label}`;
        save.elements.exposure.value = data.exposure;
        if (!data.available) { result.append(element('p',data.message)); return; }
        const headline = element('div','', 'weather-now');
        headline.append(element('span',data.icon,'weather-icon'),element('strong',data.current ? display(data.temperature,' °C') : `${display(data.minimum,'°')} – ${display(data.maximum,'°')}`),element('span',data.label));
        const metrics = element('div','','weather-metrics');
        const values = [['🌧️ Probabilidad de lluvia',display(data.rain,' %')],['🌡️ Mín. / máx.',`${display(data.minimum,'°')} / ${display(data.maximum,'°')}`]];
        if (data.current) values.push(['💧 Humedad ambiental',display(data.humidity,' %')]);
        for (const [label,value] of values) { const metric = element('div',''); metric.append(element('span',label),element('strong',value));metrics.append(metric); }
        result.append(headline, metrics, element('p',data.advice,'weather-advice'));
        const updated = new Date(data.updated).toLocaleString('es-EC',{timeZone:data.timezone,day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
        result.append(element('small',`${data.current ? 'Condiciones actuales estimadas' : 'Pronóstico para '+data.date} · Consultado ${updated} · Hora local de la localidad. Se actualiza cada 15 minutos.`,'weather-update'));
      } catch (error) { result.replaceChildren(element('p','No se pudo consultar el clima. Revisa tu conexión y pulsa Actualizar.')); }
      finally { loading = false; refresh.disabled = false; }
    }
    const locate = widget.querySelector('[data-geolocate]');
    locate.addEventListener('click', async () => {
      const status = widget.querySelector('[data-location-status]');
      if (!window.isSecureContext || !navigator.geolocation) {
        status.textContent = 'La ubicación necesita HTTPS o localhost. Puedes elegir tu localidad manualmente.';
        settings.open = true; return;
      }
      locate.disabled = true;
      status.textContent = 'Acepta el permiso de ubicación del navegador para consultar el clima.';
      try {
        const position = await new Promise((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, reject, {enableHighAccuracy:false, timeout:15000, maximumAge:60000}));
        const body = new FormData(save);
        body.set('mode','geolocation');
        body.set('latitude',position.coords.latitude.toFixed(2));
        body.set('longitude',position.coords.longitude.toFixed(2));
        body.delete('place');
        await request(endpoint,{method:'POST',body});
        status.textContent = 'Ubicación aproximada guardada para este jardín.';
        settings.open = false; select.value = '';
        await load();
      } catch (error) {
        const messages = {1:'No se autorizó la ubicación. Puedes habilitarla en los permisos del navegador o elegir tu localidad manualmente.',2:'No pudimos obtener tu ubicación. Intenta nuevamente o elige tu localidad manualmente.',3:'La ubicación tardó demasiado. Intenta nuevamente o elige tu localidad manualmente.'};
        status.textContent = messages[error.code] || 'No se pudo guardar la ubicación. Intenta nuevamente o elige tu localidad manualmente.';
        settings.open = true;
      } finally { locate.disabled = false; }
    });
    widget.querySelector('[data-refresh]').addEventListener('click',load);
    widget.querySelector('[data-weather-garden]')?.addEventListener('change', event => {
      const url = new URL(location.href);url.searchParams.set('jardin',event.target.value);location.assign(url);
    });
    search.addEventListener('submit', async event => {
      event.preventDefault();const button=search.querySelector('button');button.disabled=true;
      const status=widget.querySelector('[data-search-status]');status.textContent='Buscando localidades…';
      select.replaceChildren(new Option('Selecciona una localidad',''));
      widget.querySelector('[data-results-label]').hidden=true;
      try { const url=new URL(widget.dataset.search,location.origin);url.searchParams.set('q',search.elements.q.value.trim());const data=await request(url);
        data.results.forEach(place=>select.append(new Option(place.name,place.token)));
        widget.querySelector('[data-results-label]').hidden=!data.results.length;
        status.textContent=data.results.length ? 'Selecciona tu localidad y guarda los cambios.' : 'No encontramos esa localidad. Prueba con una ciudad cercana.';
      } catch(error) {status.textContent=error.name==='AbortError' ? 'La búsqueda tardó demasiado. Intenta nuevamente.' : error.message;}
      finally {button.disabled=false;}
    });
    save.addEventListener('submit',async event=>{
      event.preventDefault();const button=save.querySelector('button');button.disabled=true;
      const status=widget.querySelector('[data-save-status]');status.textContent='Guardando…';
      try {await request(endpoint,{method:'POST',body:new FormData(save)});status.textContent='Localidad guardada.';settings.open=false;select.value='';await load();}
      catch(error) {status.textContent=error.name==='AbortError' ? 'No se pudo guardar. Intenta nuevamente.' : error.message;}
      finally {button.disabled=false;}
    });
    load();
  });
})();
