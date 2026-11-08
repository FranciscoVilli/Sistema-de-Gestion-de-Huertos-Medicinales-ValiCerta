(() => {
 'use strict';
 document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('mapa-comunidades');
  const datos = document.getElementById('mapa-comunidades-datos');
  if (!el || !datos || typeof L === 'undefined') return;
  let comunidades;
  try {
   comunidades = JSON.parse(datos.textContent);
  } catch {
   return;
  }
  if (!Array.isArray(comunidades) || !comunidades.length) return;

  const iconBase = el.dataset.iconBase || '';
  L.Icon.Default.mergeOptions({
   iconUrl: iconBase + 'marker-icon.png',
   iconRetinaUrl: iconBase + 'marker-icon-2x.png',
   shadowUrl: iconBase + 'marker-shadow.png',
  });

  const map = L.map(el, { scrollWheelZoom: false }).setView([-1.5, -78.4], 6);
  // tile.openstreetmap.org bloquea el uso directo desde apps (politica de uso
  // de OSM) y CARTO ahora exige API key. Esri ofrece este servicio sin registro.
  L.tileLayer(
   'https://server.arcgisonline.com/ArcGIS/rest/services/World_Street_Map/MapServer/tile/{z}/{y}/{x}',
   {
    maxZoom: 18,
    attribution:
     'Tiles &copy; Esri &mdash; Source: Esri, HERE, Garmin, OpenStreetMap contributors',
   },
  ).addTo(map);

  const popupContent = (comunidad) => {
   const wrap = document.createElement('div');
   const title = document.createElement('strong');
   title.textContent = comunidad.nombre;
   wrap.appendChild(title);
   const ubicacion = document.createElement('p');
   ubicacion.textContent = `${comunidad.provincia} · ${comunidad.localidad}`;
   wrap.appendChild(ubicacion);
   if (comunidad.plantas) {
    const plantas = document.createElement('p');
    plantas.textContent = `Cultiva: ${comunidad.plantas}`;
    wrap.appendChild(plantas);
   }
   const link = document.createElement('a');
   link.href = comunidad.url;
   link.textContent = 'Ver ficha';
   wrap.appendChild(link);
   return wrap;
  };

  const puntos = [];
  comunidades.forEach((comunidad) => {
   if (typeof comunidad.lat !== 'number' || typeof comunidad.lon !== 'number') return;
   const marker = L.marker([comunidad.lat, comunidad.lon]).addTo(map);
   marker.bindPopup(popupContent(comunidad));
   puntos.push([comunidad.lat, comunidad.lon]);
  });
  if (puntos.length > 1) map.fitBounds(puntos, { padding: [24, 24] });
 });
})();
