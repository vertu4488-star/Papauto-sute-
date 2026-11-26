(()=>{"use strict";
if(!("IntersectionObserver" in window))return;
const reduced=matchMedia("(prefers-reduced-motion: reduce)");
if(reduced.matches)return;
const selector=[".pa-approved-intro .hero-copy",".budget-start-head",".pa-thursday-statbar>div",".pa-thursday-market",".pa-thursday-feature-head",".pa-thursday-card","#pa-vitrine .pa-real-lot","#pa-vitrine .section-title-row",".marketplace-intro-copy",".proof-strip>div","#quick-selection .section-title-row","#directions .section-title-row","#directions .direction-card","#regional-delivery .section-title-row","#seo-guides .section-title-row","#market-sources .market-source-card",".gallery-section-title",".gallery-grid .gallery-card"].join(",");
const seen=new WeakSet(),observed=new WeakSet();
let io;
function reveal(el,delay){
  seen.add(el);io.unobserve(el);observed.delete(el);
  if(reduced.matches||el.contains(document.activeElement))return;
  el.style.setProperty("--pa-scroll-delay",delay+"ms");
  el.classList.add("pa-scroll-enter");
  // No persistent compositor layers or hidden content after the effect.
  const clean=()=>{el.classList.remove("pa-scroll-enter");el.style.removeProperty("--pa-scroll-delay");el.removeEventListener("animationend",clean);el.removeEventListener("animationcancel",clean)};
  el.addEventListener("animationend",clean);el.addEventListener("animationcancel",clean);
  setTimeout(clean,1100);
}
io=new IntersectionObserver(entries=>{
  let stagger=0;
  for(const entry of entries){
    if(!entry.target.isConnected){io.unobserve(entry.target);observed.delete(entry.target);continue}
    if(!entry.isIntersecting||entry.intersectionRect.height===0||seen.has(entry.target))continue;
    reveal(entry.target,Math.min(stagger++*55,165));
  }
},{threshold:0,rootMargin:"0px 0px 0px 0px"});
function register(el){
  if(seen.has(el)||observed.has(el)||!el.isConnected)return;
  const rect=el.getBoundingClientRect();
  // First-screen and already-scrolled content should never blink on startup/filtering.
  if(rect.height>0&&rect.top<innerHeight&&rect.bottom>0){seen.add(el);return}
  observed.add(el);io.observe(el);
}
function scan(node){
  if(node.nodeType!==1&&node.nodeType!==9)return;
  if(node.nodeType===1&&node.matches(selector))register(node);
  node.querySelectorAll(selector).forEach(register);
}
scan(document);
const grid=document.getElementById("gallery-grid");
if(grid)new MutationObserver(records=>{for(const record of records){for(const node of record.removedNodes){if(node.nodeType!==1)continue;const release=el=>{if(!el.isConnected&&observed.has(el)){io.unobserve(el);observed.delete(el)}};release(node);node.querySelectorAll(selector).forEach(release)}for(const node of record.addedNodes)scan(node)}}).observe(grid,{childList:true,subtree:false});
if(reduced.addEventListener)reduced.addEventListener("change",()=>{if(reduced.matches){document.querySelectorAll(".pa-scroll-enter").forEach(el=>{el.classList.remove("pa-scroll-enter");el.style.removeProperty("--pa-scroll-delay")})}});
})();
