(() => {
 'use strict';
 const body=document.body, cookie=document.querySelector('.cookie-banner'), guide=document.getElementById('garden-guide');
 let frame=0;
 function reserve(){
  frame=0;
  const cookieHeight=cookie&&!cookie.hidden?cookie.getBoundingClientRect().height+32:0;
  const guideHeight=guide&&!guide.hidden?guide.getBoundingClientRect().height+32:0;
  body.style.setProperty('--overlay-reserve',`${Math.ceil(Math.max(cookieHeight,guideHeight))}px`);
 }
 function schedule(){if(!frame)frame=requestAnimationFrame(reserve);}
 if('ResizeObserver' in window){const observer=new ResizeObserver(schedule);[cookie,guide].filter(Boolean).forEach(el=>observer.observe(el));}
 if(guide)new MutationObserver(schedule).observe(guide,{attributes:true,attributeFilter:['hidden']});
 addEventListener('resize',schedule,{passive:true});reserve();
 // All content stays visible when JavaScript or motion is unavailable.
 const preference=matchMedia('(prefers-reduced-motion: reduce)'),running=new Set();
 function entrance(element){
  if(preference.matches||!element.animate)return;
  const animation=element.animate([{opacity:.75,transform:'translateY(8px)'},{opacity:1,transform:'none'}],{duration:320,easing:'cubic-bezier(.2,.7,.3,1)'});
  running.add(animation);animation.finished.then(()=>running.delete(animation),()=>running.delete(animation));
 }
 if('IntersectionObserver' in window){
  const observer=new IntersectionObserver(entries=>{entries.forEach(entry=>{if(entry.isIntersecting){observer.unobserve(entry.target);entrance(entry.target);}});},{threshold:.12});
  document.querySelectorAll('.portal-hero-grid>div,.portal-hero figure,.discovery-card,.level-preview,.facilitator-card,.product-stats,.product-main>section,.notice').forEach(el=>observer.observe(el));
 }
 if(guide)new MutationObserver(()=>{if(!guide.hidden)entrance(guide);}).observe(guide,{attributes:true,attributeFilter:['hidden']});
 preference.addEventListener('change',()=>{if(preference.matches){running.forEach(animation=>animation.cancel());running.clear();}});
})();
