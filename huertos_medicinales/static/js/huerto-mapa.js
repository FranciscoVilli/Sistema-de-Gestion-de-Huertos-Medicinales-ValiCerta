(() => {
 'use strict';
 const viewport = document.querySelector('.map-viewport');
 if (!viewport) return;
 const world = viewport.querySelector('.map-world');
 const output = document.querySelector('.map-scale');
 let scale=1, minimum=.4, x=0, y=0, moved=false;
 const points=new Map(); let gesture=null;
 const paint=()=>{
  const w=world.offsetWidth*scale,h=world.offsetHeight*scale;
  x=w<viewport.clientWidth?(viewport.clientWidth-w)/2:Math.min(0,Math.max(viewport.clientWidth-w,x));
  y=h<viewport.clientHeight?(viewport.clientHeight-h)/2:Math.min(0,Math.max(viewport.clientHeight-h,y));
  world.style.transform=`translate(${x}px,${y}px) scale(${scale})`;
  output.textContent=`${Math.round(scale*100)}%`;
 };
 const reset=()=>{minimum=Math.min(viewport.clientWidth/world.offsetWidth,viewport.clientHeight/world.offsetHeight);scale=minimum;x=0;y=0;paint();};
 const zoom=(value,cx=viewport.clientWidth/2,cy=viewport.clientHeight/2)=>{
  const next=Math.max(minimum,Math.min(1.8,value));
  x=cx-(cx-x)*next/scale;y=cy-(cy-y)*next/scale;scale=next;paint();
 };
 document.querySelectorAll('[data-map-action]').forEach(button=>button.addEventListener('click',()=>{
  if(button.dataset.mapAction==='reset')reset();else zoom(scale*(button.dataset.mapAction==='in'?1.25:.8));
 }));
 viewport.classList.add('enhanced');
 const begin=()=>{const p=[...points.values()];gesture=p.length===2?{distance:Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y),scale}:null;};
 viewport.addEventListener('pointerdown',e=>{if(e.button!==0)return;points.set(e.pointerId,{x:e.clientX,y:e.clientY});if(points.size===1)moved=false;begin();});
 viewport.addEventListener('pointermove',e=>{
  const prev=points.get(e.pointerId);if(!prev)return;
  const dx=e.clientX-prev.x,dy=e.clientY-prev.y;
  if(!moved&&Math.abs(dx)+Math.abs(dy)<4)return;
  moved=true;viewport.setPointerCapture(e.pointerId);viewport.classList.add('dragging');
  points.set(e.pointerId,{x:e.clientX,y:e.clientY});
  if(points.size===2&&gesture){const p=[...points.values()],r=viewport.getBoundingClientRect();zoom(gesture.scale*Math.hypot(p[1].x-p[0].x,p[1].y-p[0].y)/Math.max(1,gesture.distance),(p[0].x+p[1].x)/2-r.left,(p[0].y+p[1].y)/2-r.top);}else{x+=dx;y+=dy;paint();}
 });
 const end=e=>{points.delete(e.pointerId);if(viewport.hasPointerCapture(e.pointerId))viewport.releasePointerCapture(e.pointerId);begin();if(!points.size)viewport.classList.remove('dragging');};
 viewport.addEventListener('pointerup',end);viewport.addEventListener('pointercancel',end);
 viewport.addEventListener('pointerleave',e=>{if(!viewport.hasPointerCapture(e.pointerId))end(e);});
 viewport.addEventListener('click',e=>{if(moved){e.preventDefault();e.stopPropagation();moved=false;}},true);
 viewport.addEventListener('dragstart',e=>e.preventDefault());
 viewport.addEventListener('wheel',e=>{if(!e.ctrlKey)return;e.preventDefault();const r=viewport.getBoundingClientRect();zoom(scale*Math.exp(-e.deltaY*.005),e.clientX-r.left,e.clientY-r.top);},{passive:false});
 viewport.addEventListener('keydown',e=>{if(e.target!==viewport)return;const delta={ArrowLeft:[60,0],ArrowRight:[-60,0],ArrowUp:[0,60],ArrowDown:[0,-60]}[e.key];if(delta){e.preventDefault();x+=delta[0];y+=delta[1];paint();}else if(e.key==='+'||e.key==='='){e.preventDefault();zoom(scale*1.25);}else if(e.key==='-'){e.preventDefault();zoom(scale*.8);}else if(e.key==='Home'){e.preventDefault();reset();}});
 new ResizeObserver(reset).observe(viewport);
 new ResizeObserver(reset).observe(world);
 reset();
})();
