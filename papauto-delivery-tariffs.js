/* PapAuto: sourced, preliminary road-carrier estimates from Vladivostok / Ussuriysk. */
(()=>{
"use strict";
const labels={compact:"малолитражка",sedan:"седан / хэтчбек / универсал",crossover:"кроссовер",large:"минивэн / крупный внедорожник"};
function classify(name,bodyType=""){
 const n=(String(name||"")+" "+String(bodyType||"")).toLowerCase().replace(/ё/g,"е").replace(/[_-]/g," ");
 if(/step\s*w(?:a)?gn|step\s*wagon|степ\s*вагон|alphard|vellfire|elgrand|serena|delica|\bnoah\b|\bvoxy\b|esquire|odyssey|\bstaria\b|carnival|caravelle|multivan|land\s*cruiser|\bprado\b|patrol|pajero(?!\s*mini)|\blx\s*\d|минив[эе]н|микроавтобус/.test(n))return "large";
 if(/\b(?:yaris\s*cross|corolla\s*cross|rav\s*4|cr\s*v|hr\s*v|cx\s*[345689]|x\s*trail|qashqai|vezel|harrier|forester|outlander|tucson|sportage|seltos|monjaro|coolray|atlas|tiggo|haval|jolion|kicks|creta|rx\s*\d|nx\s*\d|x[12345]|gl[abc])\b|кроссовер/.test(n))return "crossover";
 if(/\b(?:honda\s*fit(?!\s*shuttle)|toyota\s*yaris(?!\s*cross)|toyota\s*vitz|toyota\s*passo|toyota\s*aqua|suzuki\s*alto|suzuki\s*swift|suzuki\s*spacia|suzuki\s*wagon\s*r|daihatsu\s*mira|daihatsu\s*tanto|honda\s*n\s*(?:box|one|wgn)|nissan\s*dayz|nissan\s*march|mitsubishi\s*ek)\b|кейкар|малолитражка|хонда\s*фит/.test(n))return "compact";
 if(/\b(?:fit\s*shuttle|corolla|camry|prius|civic|accord|avante|elantra|sonata|k5|rio|solaris|cerato|mazda\s*[236]|note|demio|impreza|legacy|a[346]|octavia|golf|passat|jetta|arrizo)\b|седан|хэтчбек|универсал/.test(n))return "sedan";
 return "";
}
function quote(data,city,kind,origin){if(origin!=="vlad")return null;if(city==="Владивосток")return {estimate:0,count:0,min:0,max:0};if(!Object.hasOwn(labels,kind))return null;const r=data?.table?.[city]?.[kind];return r&&Number.isFinite(r.estimate)&&r.estimate>=0?r:null;}
if(typeof module!=="undefined"&&module.exports)module.exports={classify,quote,labels};
if(typeof window!=="undefined")window.PapAutoDeliveryTariffs={classify,quote,labels};
if(typeof document==="undefined")return;
const $=id=>document.getElementById(id),form=$("calcForm"),panel=$("paDeliveryPanel");if(!form||!panel)return;
const city=$("calcCity"),country=$("calcCountry"),origin=$("paDeliveryOrigin"),kind=$("paDeliveryClass"),mode=$("paDeliveryMode"),field=$("localDelivery"),status=$("paDeliveryStatus"),search=$("paModelSearch");
let data=null,failed=false,lastCountry=country.value,lastName="";
const fmt=n=>Number(n).toLocaleString("ru-RU");
const defaultOrigin=()=>country.value==="Япония"?"vlad":"other";
origin.value=defaultOrigin();
function refresh(){
 if(!mode.value)mode.value="manual";
 field.readOnly=mode.value==="auto";
 delete field.dataset.paCostIncluded;
 if(mode.value!=="auto"){delete field.dataset.paCostLabel;status.textContent="Ручной режим: укажите фактическую стоимость перевозки в разделе расходов.";return;}
 const q=quote(data,city.value,kind.value,origin.value);
 field.value=q?String(q.estimate):"";
 field.dataset.paCostLabel="Автовоз · "+city.value+(kind.value&&labels[kind.value]?" · "+labels[kind.value]:"");
 if(origin.value!=="vlad"){status.textContent="Тарифы только для маршрута из Владивостока/Уссурийска. Подтвердите пункт отправления или введите фактическую цену.";return;}
 if(city.value==="Владивосток"){status.textContent="Самовывоз во Владивостоке: межрегиональный автовоз не требуется (0 ₽).";return;}
 if(!kind.value){status.textContent="Уточните класс автомобиля для расчёта автовоза.";return;}
 if(!q){status.textContent=failed?"Тарифы не загрузились. Выберите ручной режим.":data?"Для этого маршрута нет подтверждённых ориентиров. Выберите ручной режим.":"Загружаем таблицу тарифов…";return;}
 const extra=q.proxy?" "+q.proxy+".":q.count===1?" Только один опубликованный ориентир, не средняя рынка.":q.count>1?" "+q.count+" опубликованных ориентира: "+fmt(q.min)+"–"+fmt(q.max)+" ₽.":"";
 status.textContent="Предварительно: "+fmt(q.estimate)+" ₽."+extra+" Точную цену подтвердит перевозчик.";
}
function changed(e){
 const id=e.target?.id;
 if(country.value!==lastCountry){lastCountry=country.value;origin.value=defaultOrigin();mode.value="auto";kind.value="";field.value="";lastName="";}
 
 if(id==="calcCity"||id==="paDeliveryOrigin"||id==="paDeliveryMode")field.value="";
 const name=search.value.trim();if(name!==lastName){lastName=name;kind.value=classify(name);if(mode.value==="manual")field.value="";}
 if(["calcCity","calcCountry","paDeliveryOrigin","paDeliveryMode","paDeliveryClass","paModelSearch","carCost"].includes(id))refresh();
}
form.addEventListener("input",changed);form.addEventListener("change",changed);
form.addEventListener("pa:restore-estimate",()=>{lastCountry=country.value;lastName=search.value.trim();refresh();});
form.addEventListener("submit",refresh,true);
form.addEventListener("pa:vehicle-selected",e=>{lastName=search.value.trim();kind.value=classify(lastName,e.detail?.bodyType);if(mode.value==="manual")field.value="";refresh();});
refresh();
fetch("/data/papauto-delivery-tariffs-20261125.json",{credentials:"same-origin"}).then(r=>{if(!r.ok)throw Error("tariffs");return r.json();}).then(d=>{data=d;refresh();form.dispatchEvent(new Event("input",{bubbles:true}));}).catch(()=>{failed=true;refresh();form.dispatchEvent(new Event("input",{bubbles:true}));});
})();
