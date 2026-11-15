(() => {
 'use strict';
 const dialog=document.getElementById('community-dialog'),content=dialog?.querySelector('[data-dialog-content]');
 let lastTrigger=null,modalRequest=0,changed=false;
 const node=(tag,text,cls)=>{const el=document.createElement(tag);el.textContent=text;if(cls)el.className=cls;return el;};
 async function fetchSafe(url,options={}){const controller=new AbortController(),timer=setTimeout(()=>controller.abort(),options.method==='POST'?120000:12000);try{return await fetch(url,{...options,signal:controller.signal,credentials:'same-origin'});}finally{clearTimeout(timer);}}
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
   const editor=content.querySelector('[data-social-editor]');if(editor){const mode=editor.dataset.mode;const focus=editor.querySelector(mode==='encuesta'?'[name=titulo]':mode==='enlace'?'[name=enlace]':'[name=contenido]');focus?.focus();return;}
   const heading=content.querySelector('h2');if(heading){heading.tabIndex=-1;heading.focus();}
  }catch{content.replaceChildren(node('p','No pudimos abrir este contenido. Intenta nuevamente.'));const retry=node('button','Reintentar','purple-button');retry.onclick=()=>openModal(url);content.append(retry);}
 }
 document.addEventListener('click',event=>{
  const link=event.target.closest('a[data-modal]');if(link&&dialog){event.preventDefault();lastTrigger=link;
 const target=new URL(link.href),mode=target.searchParams.get('adjunto');
 if(target.searchParams.get('social')==='1'&&mode==='foto'){
  const picker=document.createElement('input');picker.type='file';picker.accept='image/jpeg,image/png,image/webp';
  picker.onchange=async()=>{await openModal(link.href);const input=content.querySelector(`[name=${mode}]`);if(input&&picker.files.length){input.files=picker.files;input.dispatchEvent(new Event('change',{bubbles:true}));}};
  picker.oncancel=()=>openModal(link.href);picker.click();
 }else openModal(link.href);}
 });
 document.addEventListener('submit',event=>{
  const form=event.target.closest('[data-community-form]');if(!form)return;
  if(form.dataset.confirm&&!confirm(form.dataset.confirm)){event.preventDefault();return;}
  if(!dialog||!dialog.open)return;
  event.preventDefault();
  const data=new FormData(form);openModal(form.action,{method:'POST',body:data});
 });
 if(dialog){dialog.querySelector('[data-close]').onclick=()=>dialog.close();dialog.addEventListener('click',event=>{if(event.target===dialog){const r=dialog.getBoundingClientRect();if(event.clientX<r.left||event.clientX>r.right||event.clientY<r.top||event.clientY>r.bottom)dialog.close();}});dialog.addEventListener('close',()=>{modalRequest++;lastTrigger?.focus();if(changed)location.reload();});}
 const mapElement=document.getElementById('community-map'),status=document.querySelector('[data-map-status]'),list=document.querySelector('[data-map-list]');
 let map=null,layer=null,records=[],busy=false,first=true;
 function popup(item){const wrap=node('div','','garden-popup');wrap.append(node('h3',item.owner),node('p',item.name,'popup-garden'),node('p','Comunidad: '+(item.comunidad||'Sin comunidad'),'popup-community'),node('p','Experiencia: '+item.level),node('p','Plantas: '+(item.plants.join(', ')||'Sin cultivos activos')),node('p',item.species+' especies · '+item.location));if(item.years!==null)wrap.append(node('p',item.years+' años cultivando (declarados)'));const a=node('a','Ver perfil');a.href=item.profile;a.dataset.modal='';wrap.append(a);return wrap;}
 function redraw(){if(!map||!layer)return;layer.clearLayers();const groups=new Map();records.forEach(item=>{const point=map.project([item.lat,item.lon],map.getZoom());const key=Math.floor(point.x/60)+':'+Math.floor(point.y/60);if(!groups.has(key))groups.set(key,[]);groups.get(key).push(item);});
  for(const group of groups.values()){
   const lat=group.reduce((sum,item)=>sum+item.lat,0)/group.length,lon=group.reduce((sum,item)=>sum+item.lon,0)/group.length;
   const colors=new Set(group.map(item=>item.color));
   const color=colors.size===1?group[0].color:'#3c4a35';
   const icon=L.divIcon({className:group.length>1?'cluster-pin':'garden-pin',html:group.length>1?String(group.length):'<span>♧</span>',iconSize:[36,36],iconAnchor:[18,36]});
   const marker=L.marker([lat,lon],{icon,title:group.length>1?group.length+' jardines compartidos':group[0].name}).addTo(layer);
   marker.getElement()?.style.setProperty('background',color,'important');
   if(group.length===1)marker.bindPopup(popup(group[0]),{maxWidth:Math.max(180,Math.min(280,mapElement.clientWidth-60)),maxHeight:250});else{const wrap=node('div','','cluster-content');wrap.append(node('strong',group.length+' jardines en este sector'));group.forEach(item=>wrap.append(popup(item)));marker.bindPopup(wrap,{maxWidth:Math.max(180,Math.min(280,mapElement.clientWidth-60)),maxHeight:250});}
  }
 }
 function renderLegend(legend){const legendElement=document.querySelector('[data-map-legend]');if(!legendElement)return;legendElement.replaceChildren();(legend||[]).forEach(entry=>{const chip=node('span','','legend-chip');const dot=node('span','','legend-dot');dot.style.background=entry.color;chip.append(dot,document.createTextNode(entry.nombre));legendElement.append(chip);});}
 async function refreshMap(){
  if(!mapElement||busy)return;busy=true;status.textContent='Actualizando jardines…';
  try{const response=await fetchSafe(mapElement.dataset.url);if(!response.ok)throw new Error();const data=await response.json();records=data.markers;renderLegend(data.legend);if(data.stats)Object.entries(data.stats).forEach(([key,value])=>{const el=document.querySelector(`[data-stat="${key}"]`);if(el)el.textContent=value;});
   if(!records.length){if(layer)layer.clearLayers();status.textContent='Todavía no hay jardines compartidos. Puedes publicar el tuyo desde Mi rincón verde, sección Clima.';list.replaceChildren(node('p','No hay jardines públicos por ahora.','map-list-empty'));return;}
   if(!map){if(typeof L==='undefined')throw new Error();map=L.map(mapElement,{scrollWheelZoom:false}).fitWorld();layer=L.layerGroup().addTo(map);const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,referrerPolicy:'strict-origin-when-cross-origin',attribution:'&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'}).addTo(map);tiles.on('tileerror',()=>{status.textContent='No se pudo cargar parte del mapa. Los jardines siguen disponibles en la lista.';});map.on('zoomend',redraw);new ResizeObserver(()=>map.invalidateSize()).observe(mapElement);}
   redraw();if(first&&records.length){map.fitBounds(records.map(r=>[r.lat,r.lon]),{padding:[35,35],maxZoom:12});first=false;}
   list.replaceChildren();records.forEach(item=>{
    const a=document.createElement('a');a.className='map-list-item';a.href=item.profile;a.dataset.modal='';
    const dot=node('span','','map-list-dot');dot.style.background=item.color;
    const text=node('span','','map-list-text');
    text.append(node('strong',item.name),node('small',item.owner+' · '+(item.comunidad||'Sin comunidad')+' · '+item.location));
    const arrow=node('span','→','map-list-arrow');arrow.setAttribute('aria-hidden','true');
    a.append(dot,text,arrow);list.append(a);
   });
   status.textContent=records.length?'Ubicaciones aproximadas · '+records.length+' jardines compartidos':'Todavía no hay jardines compartidos. Puedes publicar el tuyo desde Mi rincón verde, sección Clima.';
   if(!records.length)list.append(node('p','No hay jardines públicos por ahora.','map-list-empty'));
  }catch{status.textContent='No pudimos actualizar los jardines. Pulsa Actualizar para reintentar.';}finally{busy=false;}
 }
 document.querySelector('[data-map-refresh]')?.addEventListener('click',()=>{if(mapElement)refreshMap();else document.querySelector('.map-permission')?.scrollIntoView({behavior:'smooth',block:'center'});});
 refreshMap();setInterval(()=>{if(!document.hidden)refreshMap();},60000);
})();
(() => {
 'use strict';
 document.addEventListener('click',async event=>{
  const reply=event.target.closest('[data-reply]'),cancel=event.target.closest('[data-reply-cancel]');
  if(reply||cancel){const form=document.querySelector('#reply-composer');if(!form)return;form.elements.padre.value=reply?.dataset.reply||'';const label=form.querySelector('[data-reply-label]');label.hidden=!reply;label.textContent=reply?'Respondiendo a '+reply.dataset.author:'';form.querySelector('[data-reply-cancel]').hidden=!reply;form.scrollIntoView({block:'center',behavior:'smooth'});form.querySelector('textarea').focus();}
  const share=event.target.closest('[data-share-url]');if(share){try{await navigator.clipboard.writeText(new URL(share.dataset.shareUrl,location.origin).href);share.textContent='Enlace copiado';}catch{share.textContent='No se pudo copiar el enlace';}}
 });
 document.addEventListener('submit',async event=>{
  const form=event.target.closest('[data-vote-form]');if(!form)return;event.preventDefault();const button=event.submitter;if(!button||form.dataset.busy)return;form.dataset.busy='1';const data=new FormData(form);data.set('valor',button.value);
  try{const response=await fetch(form.action,{method:'POST',body:data,credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest'}});if(response.redirected){location.href=response.url;return;}if(!response.ok)throw new Error(response.status===403?'Únete a la comunidad para votar.':'No se pudo guardar el voto.');const result=await response.json();form.querySelector('[data-score]').textContent=result.score;form.querySelectorAll('[data-direction]').forEach(el=>{const direction=Number(el.dataset.direction),selected=direction===result.vote;el.value=selected?'0':String(direction);el.setAttribute('aria-pressed',String(selected));});form.parentElement.querySelector('[data-vote-error]')?.remove();}catch(error){let notice=form.parentElement.querySelector('[data-vote-error]');if(!notice){notice=document.createElement('span');notice.dataset.voteError='';notice.setAttribute('role','status');form.after(notice);}notice.textContent=error.message;}finally{delete form.dataset.busy;}
 });
})();
document.addEventListener('submit',async event=>{
 const form=event.target.closest('[data-bookmark-form]');if(!form)return;event.preventDefault();if(form.dataset.busy)return;form.dataset.busy='1';const button=form.querySelector('button');const body=new FormData(form);body.set('guardar',button.value);
 try{const response=await fetch(form.action,{method:'POST',body,credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest'}});if(response.redirected){location.href=response.url;return;}if(!response.ok)throw Error();const result=await response.json();button.value=result.saved?'0':'1';button.setAttribute('aria-pressed',String(result.saved));button.querySelector('span').textContent=result.saved?'Guardada':'Guardar';}catch{button.querySelector('span').textContent='Reintentar';}finally{delete form.dataset.busy;}
});

document.addEventListener('input',event=>{if(!event.target.matches('.post-composer textarea[name="contenido"]'))return;const counter=event.target.closest('form').querySelector('[data-composer-count]');if(counter)counter.textContent=event.target.value.length+' / 5000';});

document.addEventListener('change',event=>{
 const input=event.target;if(!input.matches('[data-social-editor] input[type=file]'))return;
 const form=input.closest('form'),file=input.files[0];if(!file)return;
 const preview=form.querySelector('[data-upload-preview]');
 if(preview&&input.name==='foto'){if(preview.dataset.objectUrl)URL.revokeObjectURL(preview.dataset.objectUrl);const url=URL.createObjectURL(file);preview.src=url;preview.dataset.objectUrl=url;preview.hidden=false;}
 const name=form.querySelector('[data-upload-name]');if(name)name.textContent=file.name;
});

(() => {
 const form=document.querySelector('[data-inline-composer]');if(!form)return;
 const status=form.querySelector('[data-inline-status]'),body=form.elements.contenido;
 body.addEventListener('input',()=>{body.style.height='auto';body.style.height=Math.min(body.scrollHeight,260)+'px';});
 form.addEventListener('click',event=>{
  const pick=event.target.closest('[data-pick-file]');if(pick)form.elements[pick.dataset.pickFile].click();
  const remove=event.target.closest('[data-remove-file]');if(remove){const input=form.elements[remove.dataset.removeFile];input.value='';input.dispatchEvent(new Event('change',{bubbles:true}));}
  const toggle=event.target.closest('[data-toggle-panel]');if(toggle){const panel=form.querySelector('[data-inline-panel="'+toggle.dataset.togglePanel+'"]');panel.hidden=!panel.hidden;panel.querySelectorAll('input,textarea').forEach(el=>{el.disabled=panel.hidden;});if(!panel.hidden)panel.querySelector('input').focus();}
 });
 form.addEventListener('change',event=>{
  const input=event.target;if(input.type!=='file')return;const file=input.files[0],panel=form.querySelector('[data-inline-'+input.name+']');panel.hidden=!file;
  if(input.name==='foto'){const img=panel.querySelector('img');if(img.dataset.url)URL.revokeObjectURL(img.dataset.url);if(file){img.dataset.url=URL.createObjectURL(file);img.src=img.dataset.url;}}
  else panel.querySelector('span').textContent=file?file.name:'';
 });
 form.addEventListener('submit',async event=>{
  event.preventDefault();if(form.dataset.busy)return;
  const poll=!form.querySelector('[data-inline-panel="encuesta"]').hidden;
  form.elements.adjunto.value=poll?'encuesta':form.elements.foto.files.length?'foto':!form.elements.enlace.disabled&&form.elements.enlace.value?'enlace':'';
  form.elements.tipo.value=poll?'pregunta':'experiencia';
  const data=new FormData(form),button=form.querySelector('[type=submit]');form.dataset.busy='1';button.disabled=true;status.hidden=false;status.textContent='Publicando…';
  try{const response=await fetch(form.action,{method:'POST',body:data,credentials:'same-origin',headers:{'X-Requested-With':'XMLHttpRequest'}});
   if(response.redirected){status.textContent='Tu sesión terminó. Inicia sesión para publicar; tu texto permanece aquí.';return;}
   const result=await response.json();if(!response.ok){status.textContent=Object.values(result.errors||{}).flat().map(e=>e.message).join(' ')||'No se pudo publicar. Revisa los datos.';return;}
   if(result.published){location.href=result.redirect;return;}throw Error();
  }catch{status.textContent='No se pudo publicar. Tu texto y archivos siguen aquí; intenta nuevamente.';}finally{delete form.dataset.busy;button.disabled=false;}
 });
})();
