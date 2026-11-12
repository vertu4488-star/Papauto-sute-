/* Local showroom filter. No remote dependencies and no unverified prices. */
(()=>{"use strict";const panel=document.querySelector("#pa-vitrine");if(!panel)return;
const cards=Array.from(panel.querySelectorAll(".pa-car-card"));const controls=Array.from(panel.querySelectorAll("[data-pa-market]"));const query=panel.querySelector("#pa-model-search");const empty=panel.querySelector("#pa-showroom-empty");let market="all";const fuel=panel.querySelector("#pa-fuel-filter");
for(const card of cards){const spec=card.querySelector(".pa-car-meta");const note=card.querySelector(".pa-car-note");const types=PapAutoMetadata.fuelTypes((spec?.textContent||"")+" / "+(note?.textContent||""));card.dataset.fuel=types.join(",");const badge=document.createElement("p");badge.className="vehicle-fuel";badge.textContent="Варианты двигателя: "+PapAutoMetadata.fuelLabel(types);spec.after(badge);}
fuel.addEventListener("change",update);
function update(){const needle=(query.value||"").trim().toLocaleLowerCase("ru");let count=0;
for(const card of cards){const shown=(!fuel.value||card.dataset.fuel.split(",").includes(fuel.value))&&(market==="all"||card.dataset.market===market)&&(!needle||card.dataset.search.includes(needle));card.hidden=!shown;if(shown)count++;}
empty.hidden=count>0;controls.forEach(el=>el.setAttribute("aria-pressed",String(el.dataset.paMarket===market)));
}
controls.forEach(el=>el.addEventListener("click",()=>{market=el.dataset.paMarket;update();}));query.addEventListener("input",update);update();
})();