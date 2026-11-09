/* Local showroom filter. No remote dependencies and no unverified prices. */
(()=>{"use strict";const panel=document.querySelector("#pa-vitrine");if(!panel)return;
const cards=Array.from(panel.querySelectorAll(".pa-car-card"));const controls=Array.from(panel.querySelectorAll("[data-pa-market]"));const query=panel.querySelector("#pa-model-search");const empty=panel.querySelector("#pa-showroom-empty");let market="all";
function update(){const needle=(query.value||"").trim().toLocaleLowerCase("ru");let count=0;
for(const card of cards){const shown=(market==="all"||card.dataset.market===market)&&(!needle||card.dataset.search.includes(needle));card.hidden=!shown;if(shown)count++;}
empty.hidden=count>0;controls.forEach(el=>el.setAttribute("aria-pressed",String(el.dataset.paMarket===market)));
}
controls.forEach(el=>el.addEventListener("click",()=>{market=el.dataset.paMarket;update();}));query.addEventListener("input",update);update();
})();