/* PapAuto: editable preliminary Japan tariff package. Internal totals remain RUB. */
(()=>{
"use strict";
const defaults={yen:110000,usd:400,bank:15000,docs:65000};
function calculate(p){
 const valid=n=>Number.isFinite(n)&&n>=0,positive=n=>valid(n)&&n>0;
 const yen=valid(p.yen)&&positive(p.auctionYen)?Math.round(p.yen+Math.max(0,p.auctionYen-1000000)*.05):null;
 return {yen,origin:yen!==null&&positive(p.jpyRate)?Math.round(yen*p.jpyRate):null,shipping:valid(p.usd)&&positive(p.usdRate)?Math.round(p.usd*p.usdRate):null,bank:valid(p.bank)?Math.round(p.bank):null,docs:valid(p.docs)?Math.round(p.docs):null};
}
if(typeof module!=="undefined"&&module.exports)module.exports={calculate,defaults};
if(typeof document==="undefined")return;
const $=id=>document.getElementById(id),form=$("calcForm"),panel=$("paJapanTariffs");
if(!form||!panel)return;
const mode=$("paJapanTariffMode"),status=$("paJapanTariffStatus");
const keys=["auctionFee","originDelivery","exportDocs","insurance","shipping","bankFee","brokerFee","warehouseFee","paperwork"];
const included=["auctionFee","exportDocs","insurance","brokerFee","warehouseFee"];
const rename={originDelivery:["Доставка по стране покупки","Расходы по Японии (пакет), ₽"],shipping:["Международная доставка / фрахт","Фрахт (пересчёт в ₽)"],paperwork:["СБКТС, ЭПТС и лаборатория","Брокер, СВХ, СБКТС, ЭПТС и лаборатория (пакет), ₽"]};
const relevant=new Set(["calcCountry","carCost","paForeignPrice","paForeignRate","paPriceCurrency","paJapanTariffMode","paJapanYen","paJapanUsd","paJapanYenRate","paJapanUsdRate","paJapanBank","paJapanDocs"]);
const value=id=>$(id)?.value??"",num=id=>value(id)===""?NaN:Number(value(id));
const money=n=>Number(n).toLocaleString("ru-RU",{maximumFractionDigits:0});
let previouslyAuto=false,rateInfo="",restoring=false;
function set(id,n,label,skip=false){const el=$(id);el.value=n===null?"":String(n);if(label)el.dataset.paCostLabel=label;else delete el.dataset.paCostLabel;if(skip)el.dataset.paCostIncluded="1";else delete el.dataset.paCostIncluded;}
function refresh(){
 const japan=value("calcCountry")==="Япония",auto=japan&&mode.value==="estimate";
 panel.hidden=!japan;$("paJapanAutoFields").hidden=!auto;
 for(const id of keys){const el=$(id);el.readOnly=auto;const label=el.closest("label");if(label){label.classList.toggle("pa-included-cost",auto&&included.includes(id));if(rename[id]&&label.firstChild?.nodeType===3)label.firstChild.textContent=rename[id][auto?1:0];}if(!auto){delete el.dataset.paCostLabel;delete el.dataset.paCostIncluded;}}
 if(!auto){if(previouslyAuto&&!restoring)keys.forEach(id=>{$(id).value="";});previouslyAuto=false;return;}
 previouslyAuto=true;
 const jpy=num("paJapanYenRate"),usdRate=num("paJapanUsdRate"),car=num("carCost");
 // Use the price actually transferred to the ruble quote, never a stale untransferred FX field.
 const original=value("paPriceCurrency")==="JPY"&&num("paForeignPrice")>0&&Math.round(num("paForeignPrice")*num("paForeignRate"))===car?num("paForeignPrice"):car>0&&jpy>0?car/jpy:NaN;
 const p={yen:num("paJapanYen"),usd:num("paJapanUsd"),jpyRate:jpy,usdRate,auctionYen:original,bank:num("paJapanBank"),docs:num("paJapanDocs")};
 const q=calculate(p);
 for(const id of included)set(id,0,null,true);
 set("originDelivery",q.origin,q.yen===null?"Расходы по Японии (пакет)":"Расходы по Японии · "+money(q.yen)+" ¥");
 set("shipping",q.shipping,Number.isFinite(p.usd)?"Фрахт · "+money(p.usd)+" $":"Фрахт");
 set("bankFee",q.bank);set("paperwork",q.docs,"Брокер, СВХ, СБКТС, ЭПТС и лаборатория (пакет)");
 // Unknown extra expenses stay blank, not assumed absent.
 status.textContent=[q.yen===null?"Расходы по Японии: после ввода цены автомобиля":money(q.yen)+" ¥"+(q.origin===null?" (нужен курс)":" ≈ "+money(q.origin)+" ₽"),Number.isFinite(p.usd)?"Фрахт: "+money(p.usd)+" $"+(q.shipping===null?" (нужен курс)":" ≈ "+money(q.shipping)+" ₽"):"Уточните фрахт",q.bank===null?"":"Банк: "+money(q.bank)+" ₽",q.docs===null?"":"Оформление: "+money(q.docs)+" ₽",rateInfo].filter(Boolean).join(" · ");
}
form.addEventListener("input",e=>{if(relevant.has(e.target.id))refresh();});
form.addEventListener("change",e=>{if(relevant.has(e.target.id))refresh();});
form.addEventListener("submit",()=>refresh(),true);
form.addEventListener("pa:restore-estimate",()=>{restoring=true;if(!mode.value)mode.value="manual";refresh();restoring=false;});
for(const id of ["paJapanYenRate","paJapanUsdRate"])$(id).addEventListener("input",()=>{rateInfo="Курсы уточнены вручную.";});
async function loadRates(){try{const api=String(window.PAPAUTO_CONFIG?.apiBaseUrl||"").replace(/\/$/,"");if(!api)return;const r=await fetch(api+"/api/exchange-rates",{headers:{Accept:"application/json"}});if(!r.ok)throw Error("FX");const d=await r.json();for(const [id,v] of [["paJapanYenRate",d.rub_per_jpy],["paJapanUsdRate",d.rub_per_usd]])if(!$(id).value&&Number(v)>0)$(id).value=String(v);rateInfo=(d.fallback?"Архивные курсы ЦБ":"Справочные курсы ЦБ")+(d.date?" на "+d.date:"")+". Курс банка может отличаться.";refresh();form.dispatchEvent(new Event("input",{bubbles:true}));}catch{rateInfo="Курс недоступен — укажите вручную.";refresh();}}
refresh();loadRates();
})();
