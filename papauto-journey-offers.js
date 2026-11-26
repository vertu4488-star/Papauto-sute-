(()=>{"use strict";
const reduced=matchMedia("(prefers-reduced-motion: reduce)");
function enter(el){if(reduced.matches)return;el.classList.add("is-entering");setTimeout(()=>el.classList.remove("is-entering"),650)}
const journey=document.querySelector(".pa-journey"),track=journey?.querySelector(".pa-journey-track");
if(track&&"IntersectionObserver"in window){const steps=[...track.querySelectorAll(".pa-journey-step")];let max=-1;const io=new IntersectionObserver(entries=>{for(const e of entries){if(!e.isIntersecting||e.target.closest("[hidden]"))continue;const n=steps.indexOf(e.target);e.target.classList.add("is-passed");enter(e.target);max=Math.max(max,n);io.unobserve(e.target)}if(max>=0){const mark=steps[max].querySelector(".pa-journey-number");const ratio=Math.min(1,Math.max(0,(mark.offsetTop+mark.offsetHeight/2-16)/(track.offsetHeight-32||1)));track.style.setProperty("--pa-route-fraction",max===steps.length-1?1:ratio)}},{threshold:.15});steps.forEach(s=>io.observe(s))}
const root=document.querySelector(".pa-offers");if(!root)return;
const cards=[...root.querySelectorAll("[data-pa-offer]")],dots=[...root.querySelectorAll("[data-pa-offer-dot]")],controls=root.querySelector(".pa-offer-controls"),pause=root.querySelector("[data-pa-offer-pause]");if(cards.length!==3||dots.length!==3||!controls||!pause)return;
let index=0,timer=null,paused=reduced.matches,hover=false,focus=false,visible=false;
function stop(){if(timer!==null)clearTimeout(timer);timer=null}
function schedule(){stop();if(!paused&&!hover&&!focus&&visible&&!document.hidden&&!root.hidden)timer=setTimeout(()=>show(index+1),8000)}
function show(i,animate=true){index=(i+cards.length)%cards.length;cards.forEach((el,j)=>el.hidden=j!==index);dots.forEach((el,j)=>el.setAttribute("aria-pressed",String(j===index)));if(animate)enter(cards[index]);schedule()}
function updatePause(){pause.textContent=paused?"▶":"Ⅱ";pause.setAttribute("aria-pressed",String(paused));pause.setAttribute("aria-label",paused?"Возобновить смену предложений":"Приостановить смену предложений");schedule()}
dots.forEach((el,i)=>el.addEventListener("click",()=>show(i)));root.querySelector("[data-pa-offer-prev]").addEventListener("click",()=>show(index-1));root.querySelector("[data-pa-offer-next]").addEventListener("click",()=>show(index+1));pause.addEventListener("click",()=>{paused=!paused;updatePause()});
root.addEventListener("mouseenter",()=>{hover=true;stop()});root.addEventListener("mouseleave",()=>{hover=false;schedule()});root.addEventListener("focusin",()=>{focus=true;stop()});root.addEventListener("focusout",e=>{if(!root.contains(e.relatedTarget)){focus=false;schedule()}});
document.addEventListener("visibilitychange",schedule);new MutationObserver(schedule).observe(root,{attributes:true,attributeFilter:["hidden"]});if("IntersectionObserver"in window)new IntersectionObserver(e=>{visible=e[0].isIntersecting;schedule()},{threshold:.15}).observe(root);else visible=true;
if(reduced.addEventListener)reduced.addEventListener("change",()=>{paused=reduced.matches;updatePause()});controls.hidden=false;show(0,false);updatePause();
})();
