/* Indicative landed prices on approved archived auction cards. */
(()=>{
"use strict";
const root=window.PapAutoQuickQuote;
if(!root)return;
const fmt=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(n);
const el=(tag,text)=>{const n=document.createElement(tag);n.textContent=text;return n;};
const date=new Date(),clearDate=[date.getFullYear(),String(date.getMonth()+1).padStart(2,"0"),String(date.getDate()).padStart(2,"0")].join("-");
const fetchJson=async(url)=>{const r=await fetch(url,{credentials:url.startsWith("/")?"same-origin":"omit"});if(!r.ok)throw Error("data");return r.json();};
let ready=null;
const labels={car:"Автомобиль",japan:"Расходы по Японии",shipping:"Фрахт",bank:"Банк",docs:"Оформление",duty:"Пошлина",customsFee:"Таможенный сбор",util:"Утильсбор",commission:"Комиссия PapAuto",delivery:"Автовоз"};
function render(block,id){
 if(block.dataset.paRendered==="1")return;
 block.dataset.paRendered="1";
 const lot=ready?.lots.get(id);
 const snap=ready?.snapshot?.quotes?.[id];
 const verified=ready?.snapshot?.enriched?.[id];
 const q=lot?root.quote(root.fromLot(verified?{...lot,...verified}:lot),ready.fx,ready.tariffs,{clearDate,eligibility:"yes"}):{total:null,reason:"Данные для расчёта недоступны."};
 block.replaceChildren(el("span","Под ключ до Новосибирска"));
 if(q.total===null){
  if(snap){const value=snap.total!=null?"≈ "+fmt(Math.round(snap.total/10000)*10000)+" ₽":"≈ "+fmt(Math.floor(snap.low/10000)*10000)+"–"+fmt(Math.ceil(snap.high/10000)*10000)+" ₽";block.append(el("strong",value),el("small","Архивный ориентир · курс ЦБ на "+ready.snapshot.fx.date+" · личный ввоз при соблюдении условий льготы. Не оферта."));return;}
  block.append(el("strong","Стоимость по запросу"),el("small",q.reason));return;}
 const rounded=Math.round(q.total/10000)*10000;
 block.append(el("strong","≈ "+fmt(rounded)+" ₽"),el("small","Ориентир по архивному лоту · личный ввоз при соблюдении условий льготы · курс ЦБ на "+ready.fx.date+". Не оферта."));
 const details=el("details",""),summary=el("summary","Состав сметы");details.append(summary);
 for(const [k,v] of Object.entries(q.costs))details.append(el("small",labels[k]+": "+fmt(v)+" ₽"));
 details.append(el("small","Расчёт на "+clearDate+". Фактический курс, цена покупки и дополнительные расходы уточняются."));block.append(details);
}
function scan(){
 for(const card of document.querySelectorAll(".gallery-card[data-lot-id]")){
  const id=card.dataset.lotId;if(!id)continue;
  let block=card.querySelector(".pa-card-quote");
  if(!block){block=el("section","");block.className="pa-card-quote";block.dataset.paQuoteId=id;(card.querySelector(".gallery-card-body")||card).append(block);}
 }
 for(const block of document.querySelectorAll("[data-pa-quote-id]"))render(block,block.dataset.paQuoteId);
}
const api=String(window.PAPAUTO_CONFIG?.apiBaseUrl||"").replace(/\/$/,"");
Promise.allSettled([fetchJson("/data/gallery-lots.json"),fetchJson("/data/papauto-delivery-tariffs-20261125.json"),api?fetchJson(api+"/api/exchange-rates"):Promise.reject(Error("FX")),fetchJson("/data/papauto-japan-quote-snapshot-20261125.json")]).then(([lots,tariffs,fx,snapshot])=>{
 ready={lots:new Map((lots.value?.lots||[]).map(l=>[l.id,l])),tariffs:tariffs.value,fx:fx.value,snapshot:snapshot.value};scan();
 const grid=document.querySelector("#gallery-grid");if(grid)new MutationObserver(scan).observe(grid,{childList:true,subtree:true});
});
})();