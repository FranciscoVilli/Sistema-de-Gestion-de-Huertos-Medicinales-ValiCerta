(() => {
 'use strict';
 const dialog=document.getElementById('community-dialog'),content=dialog?.querySelector('[data-dialog-content]');
 let lastTrigger=null,modalRequest=0,changed=false;
 const node=(tag,text,cls)=>{const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;return el;};
 async function fetchSafe(url,options={}){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),12000);try{return await fetch(url,{...options,signal:controller.signal,credentials:'same-origin'});}finally{clearTimeout(timer);}}
 async function openModal(url,options={}){
  if(!dialog){location.href=url;return;}
  const id=++modalRequest;
  const target=new URL(url,location.href);target.searchParams.set('fragment','1');
  if(!dialog.open)dialog.showModal();
  content.replaceChildren(node('p','Cargando…'));
  try{
   const response=await fetchSafe(target,options);
   if(id!==modalRequest||!dialog.open)return;
   if(response.headers.get('content-type')?.includes('application/json')){
    const data=await response.json();
    if(data.redirect){
     changed=true;
     const dest=new URL(data.redirect,location.origin);
     if(dest.pathname==='/comunidades/'){location.href=dest;return;}
     await openModal(dest);refreshMap();return;
    }
   }
   if(response.redirected){location.href=response.url;return;}
   if(!response.ok&&response.status!==400)throw new Error();
   content.innerHTML=await response.text();
   const heading=content.querySelector('h2');if(heading){heading.tabIndex=-1;heading.focus();}
  }catch{content.replaceChildren(node('p','No pudimos abrir este contenido. Intenta nuevamente.'));const retry=node('button','Reintentar','purple-button');retry.onclick=()=>openModal(url);content.append(retry);}
 }
 document.addEventListener('click',event=>{
  const link=event.target.closest('a[data-modal]');if(link&&dialog){event.preventDefault();lastTrigger=link;openModal(link.href);}
 });
 document.addEventListener('submit',event=>{
  const form=event.target.closest('[data-community-form]');if(!form||!dialog||!dialog.open)return;
  event.preventDefault();if(form.dataset.confirm&&!confirm(form.dataset.confirm))return;
  const data=new FormData(form);openModal(form.action,{method:'POST',body:data});
 });
 if(dialog){dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});dialog.addEventListener('close',()=>{modalRequest++;lastTrigger?.focus();if(changed)location.reload();});}
 const mapElement=document.getElementById('community-map'),status=document.querySelector('[data-map-status]'),list=document.querySelector('[data-map-list]');
 let map=null,layer=null,records=[],busy=false,first=true;
 function popup(item){const wrap=node('div','','garden-popup');wrap.append(node('h3',item.owner),node('p',item.name,'popup-garden'),node('p','Experiencia: '+item.level),node('p','Plantas: '+(item.plants.join(', ')||'Sin cultivos activos')),node('p',item.species+' especies · '+item.location));if(item.years!==null)wrap.append(node('p',item.years+' años cultivando (declarados)'));const a=node('a','Ver perfil');a.href=item.profile;a.dataset.modal='';wrap.append(a);return wrap;}
 function redraw(){if(!map||!layer)return;layer.clearLayers();const groups=new Map();records.forEach(item=>{const point=map.project([item.lat,item.lon],map.getZoom());const key=Math.floor(point.x/60)+':'+Math.floor(point.y/60);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(item);});
  for(const group of groups.values()){
   const lat=group.reduce((sum,item)=>sum+item.lat,0)/group.length,lon=group.reduce((sum,item)=>sum+item.lon,0)/group.length;
   const icon=L.divIcon({className:group.length>1?'cluster-pin':'garden-pin',html:group.length>1?String(group.length):'<span>♧</span>',iconSize:[36,36],iconAnchor:[18,36]});
   const marker=L.marker([lat,lon],{icon,title:group.length>1?group.length+' jardines compartidos':group[0].name}).addTo(layer);
   if(group.length===1)marker.bindPopup(popup(group[0]),{maxWidth:Math.max(180,Math.min(280,mapElement.clientWidth-60)),maxHeight:250});else{const wrap=node('div','','cluster-content');wrap.append(node('strong',group.length+' jardines en este sector'));group.forEach(item=>wrap.append(popup(item)));marker.bindPopup(wrap,{maxWidth:Math.max(180,Math.min(280,mapElement.clientWidth-60)),maxHeight:250});}
  }
 }
 async function refreshMap(){
  if(!mapElement||busy)return;busy=true;status.textContent='Actualizando jardines…';
  try{const response=await fetchSafe(mapElement.dataset.url);if(!response.ok)throw new Error();const data=await response.json();records=data.markers;if(data.stats)Object.entries(data.stats).forEach(([key,value])=>{const el=document.querySelector(`[data-stat="${key}"]`);if(el)el.textContent=value;});
   if(!records.length){if(layer)layer.clearLayers();status.textContent='Todavía no hay jardines compartidos. Puedes publicar el tuyo desde «Tu lugar en la comunidad».';list.replaceChildren(node('p','No hay jardines públicos por ahora.'));return;}
   if(!map){if(typeof L==='undefined')throw new Error();map=L.map(mapElement,{scrollWheelZoom:false}).fitWorld();layer=L.layerGroup().addTo(map);const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,referrerPolicy:'strict-origin-when-cross-origin',attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);tiles.on('tileerror',()=>{status.textContent='No se pudo cargar parte del mapa. Los jardines siguen disponibles en la lista.';});map.on('zoomend',redraw);new ResizeObserver(()=>map.invalidateSize()).observe(mapElement);}
   redraw();if(first&&records.length){map.fitBounds(records.map(r=>[r.lat,r.lon]),{padding:[35,35],maxZoom:12});first=false;}
   list.replaceChildren();records.forEach(item=>{const a=node('a',item.name+' · '+item.owner+' · '+item.location);a.href=item.profile;a.dataset.modal='';list.append(a);});
   status.textContent=records.length?'Ubicaciones aproximadas · '+records.length+' jardines compartidos':'Todavía no hay jardines compartidos. Puedes publicar el tuyo desde «Tu lugar en la comunidad».';
   if(!records.length)list.append(node('p','No hay jardines públicos por ahora.'));
  }catch{status.textContent='No pudimos actualizar los jardines. Pulsa Actualizar para reintentar.';}finally{busy=false;}
 }
 document.querySelector('[data-map-refresh]')?.addEventListener('click',()=>{if(mapElement)refreshMap();else document.querySelector('.map-permission')?.scrollIntoView({behavior:'smooth',block:'center'});});
 refreshMap();setInterval(()=>{if(!document.hidden)refreshMap();},60000);
})();
