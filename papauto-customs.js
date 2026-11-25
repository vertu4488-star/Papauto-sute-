/* PapAuto customs estimator. M1 ordinary ICE, personal import cleared in Russia.
 Sources: EEC Council 107 Annex 2 table 2 item 3; RF 1637 as amended 1638/1907;
 RF 1291 as amended 1713, section I items 2 and 3. Verified 2026-11-25.
 2027 scheduled coefficients are provisional; no assumption of future FX. */
(()=>{
"use strict";
const dutyBands=[[1000,1.5,3],[1500,1.7,3.2],[1800,2.5,3.5],[2300,2.7,4.8],[3000,3,5],[Infinity,3.6,5.7]];
const valueBands=[[8500,.54,2.5],[16700,.48,3.5],[42300,.48,5.5],[84500,.48,7.5],[169000,.48,15],[Infinity,.48,20]];
const fees=[[200000,1231],[450000,2462],[1200000,4924],[2700000,13541],[4200000,18465],[5500000,21344],[10000000,49240],[Infinity,73860]];
const kwBands=[117.68,139.75,161.81,183.88,205.94,228,250.07,272.13,294.20,316.26,338.33,367.75,Infinity];
// Each row: [2026 new, 2026 used, 2027 new, 2027 used] coefficient, not RUB.
const fullSmall=[[14.88,27.6,16.37,30.36],[15.36,28.43,16.9,31.27],[15.84,29.28,17.42,32.21],[16.2,30.12,17.82,33.13],...Array.from({length:9},()=>[17.28,30.12,19.01,33.13])];
const fullMedium=[[40.04,70.44,44.04,77.48],[45,74.64,49.5,82.1],[47.64,79.2,52.4,87.12],[50.52,83.88,55.57,92.27],[57.12,91.92,62.83,101.11],[64.56,100.56,71.02,110.62],[72.96,110.16,80.26,121.18],[83.16,120.6,91.48,132.66],[94.8,132,104.28,145.2],[108,144.6,118.8,159.06],[123.24,158.4,135.56,174.24],[140.4,173.4,154.44,190.74],[160.08,189.84,176.09,208.82]];
const valid=n=>Number.isFinite(n)&&n>0;
const parseDate=s=>{if(!/^\d{4}-\d{2}-\d{2}$/.test(s||""))return null;const d=new Date(s+"T00:00:00Z");return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===s?d:null;};
function ageAt(build,clear){if(!build||!clear||build>clear)return "";const anniversary=n=>{let d=new Date(build);d.setUTCFullYear(d.getUTCFullYear()+n);if(d.getUTCMonth()!==build.getUTCMonth())d.setUTCDate(0);return d;};return clear<=anniversary(3)?"new":clear<=anniversary(5)?"mid":"old";}
function ageByYear(y,clear){if(!Number.isInteger(y)||y<1950||!clear)return "";const a=parseDate(y+"-01-01"),b=parseDate(y+"-12-31");if(a>clear)return "";const x=ageAt(a,clear),z=ageAt(b>clear?clear:b,clear);return x===z?x:"";}
function estimate({cc,hp,age,year,eur,value,eligibility,type}){const result={duty:null,fee:null,util:null,reason:[]};if(![2026,2027].includes(year)){result.reason.push("Выберите дату оформления в 2026–2027 годах.");return result;}
if(type==="hybrid"||type==="ev"){result.reason.push("Для гибрида или электромобиля нужен отдельный подтверждённый расчёт. Не применяем ставки обычного ДВС автоматически.");return result;}
if(type!=="ice"){result.reason.push("Уточните тип двигателя.");return result;}
if(valid(value)&&value<=1e9)result.fee=fees.find(r=>value<=r[0])[1];else result.reason.push("Укажите стоимость для таможенного сбора.");
const hasCC=Number.isInteger(cc)&&cc>0&&cc<=12000;const hasAge=["new","mid","old"].includes(age);
if(hasCC&&hasAge&&valid(eur)&&eur<=10000){if(age==="new"){if(valid(value)&&value<=1e9){const b=valueBands.find(r=>value/eur<=r[0]);result.duty=Math.round(Math.max(value*b[1],cc*b[2]*eur));}else result.reason.push("Для авто не старше 3 лет нужна стоимость.");}else{const b=dutyBands.find(r=>cc<=r[0]);result.duty=Math.round(cc*b[age==="mid"?1:2]*eur);}}else result.reason.push("Для пошлины нужны точный объём, возраст и курс евро.");
if(hasCC&&hasAge&&valid(hp)&&hp<=2000){const kw=Math.round(hp*.73549875*100)/100;const band=kwBands.findIndex(n=>kw<=n);if(cc<=3000&&kw<=117.68&&eligibility==="yes")result.util=age==="new"?3400:5200;else if(cc<=2000&&(kw>117.68||eligibility==="no")){const table=cc<=1000?fullSmall:fullMedium;result.util=Math.round(table[band][(year===2027?2:0)+(age==="new"?0:1)]*20000);}else result.reason.push(cc>2000?"Полная ставка для объёма свыше 2 л требует уточнения.":"Подтвердите условия льготного утильсбора.");}else result.reason.push("Для утильсбора нужны точные мощность, объём и возраст.");
return result;}
if(typeof module!=="undefined"&&module.exports)module.exports={estimate,ageAt,ageByYear,parseDate};
if(typeof window!=="undefined")window.PapAutoCustoms={estimate,ageAt,ageByYear,parseDate};
if(typeof document==="undefined")return;
const $=id=>document.getElementById(id),form=$("calcForm"),mode=$("paCustomsMode");if(!form||!mode)return;
const status=$("paCustomsStatus"),eur=$("paEurRate"),note=$("paEurNote"),fields=["customs","customsFee","utilFee"];
const relevant=new Set(["paEngineType","paBuildDate","paClearDate","paAgeBand","paCustomsValue","paEurRate","paUtilEligibility","paVehicleYear","paVehicleEngine","paVehiclePower","carCost","calcCountry","paModelSearch","paForeignPrice","paForeignRate","paPriceCurrency"]);
const val=id=>$(id)?.value||"",num=id=>val(id)===""?NaN:Number(val(id));
const localDate=()=>{const d=new Date();return [d.getFullYear(),String(d.getMonth()+1).padStart(2,"0"),String(d.getDate()).padStart(2,"0")].join("-");};
$("paClearDate").value=localDate();
function refresh(){
 const auto=mode.value==="auto";fields.forEach(id=>$(id).readOnly=auto);
 if(!auto){status.textContent="Ручной режим: введите подтверждённые суммы самостоятельно.";return;}
 const clear=parseDate(val("paClearDate")),build=parseDate(val("paBuildDate")),y=num("paVehicleYear");
 const known=ageByYear(y,clear);
 const reset=$("paResetBuildDate");if(reset)reset.hidden=!val("paBuildDate")&&!val("paAgeBand");
 let age=val("paAgeBand");
 if(build){const exact=ageAt(build,clear);if(!exact||(age&&age!==exact)||(Number.isInteger(y)&&build.getUTCFullYear()!==y)){fields.forEach(id=>$(id).value="");status.textContent="Указанная дата выпуска "+val("paBuildDate")+" не согласуется с годом "+(Number.isInteger(y)?y:"не указан")+" или датой оформления/возрастом. Исправьте дату либо нажмите «Определить возраст по году».";return;}age=exact;}else {if((Number.isInteger(y)&&clear&&y>clear.getUTCFullYear())||(known&&age&&known!==age)){fields.forEach(id=>$(id).value="");status.textContent="Год "+(Number.isInteger(y)?y:"не указан")+" не соответствует выбранному возрасту или дате оформления. Нажмите «Определить возраст по году».";return;}if(!age)age=known;}
 const value=val("paCustomsValue")?num("paCustomsValue"):num("carCost");
 const r=estimate({cc:num("paVehicleEngine"),hp:num("paVehiclePower"),age,year:clear?.getUTCFullYear(),eur:num("paEurRate"),value,eligibility:val("paUtilEligibility"),type:val("paEngineType")});
 fields.forEach((id,i)=>{const n=[r.duty,r.fee,r.util][i];$(id).value=n===null?"":String(n);});
 const label={new:"Не старше 3 лет",mid:"Старше 3, до 5 лет",old:"Старше 5 лет"}[age];
 status.textContent=[label||"Уточните возраст по дате изготовления.",r.reason.length?r.reason.join(" "):"Три платежа рассчитаны.",!val("paCustomsValue")&&valid(value)?"Цена автомобиля использована как предварительная таможенная стоимость.":"", "Суммы ориентировочные; фактическую стоимость и курс на дату оформления подтверждает таможня."].filter(Boolean).join(" ");
}
function invalidate(){form.dispatchEvent(new Event("input",{bubbles:true}));}
form.addEventListener("input",e=>{if(relevant.has(e.target.id))refresh();});
form.addEventListener("change",e=>{if(e.target===mode||relevant.has(e.target.id))refresh();});
form.addEventListener("submit",()=>refresh(),true);
form.addEventListener("pa:restore-estimate",()=>{if(!mode.value)mode.value="manual";if(!$("paClearDate").value)$("paClearDate").value=localDate();refresh();});

$("paResetBuildDate")?.addEventListener("click",()=>{$("paBuildDate").value="";$("paAgeBand").value="";refresh();invalidate();});
$("paVehicleYear")?.addEventListener("input",()=>{const build=parseDate(val("paBuildDate")),y=num("paVehicleYear");if(build&&Number.isInteger(y)&&build.getUTCFullYear()!==y)$("paBuildDate").value="";$("paAgeBand").value="";});
eur.addEventListener("input",()=>{note.textContent="Курс введён вручную. Для будущей даты это прогноз."});
async function loadRate(){try{const api=String(window.PAPAUTO_CONFIG?.apiBaseUrl||"").replace(/\/$/,"");if(!api)return;const r=await fetch(api+"/api/exchange-rates",{headers:{Accept:"application/json"}});if(!r.ok)throw Error("rate");const data=await r.json();if(!valid(Number(data.rub_per_eur))||data.fallback)throw Error("rate");if(!eur.value){eur.value=String(data.rub_per_eur);note.textContent="Справочный курс ЦБ на "+(data.date||"неуказанную дату")+". Не прогноз курса на будущую дату.";refresh();invalidate();}}catch{if(!eur.value)note.textContent="Курс евро пока недоступен. Введите справочный курс вручную."}}
refresh();loadRate();
})();
