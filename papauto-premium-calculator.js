/* PapAuto: only published, exact vehicle photos. No invented prices or external imagery. */
(()=>{
"use strict";
const $=id=>document.getElementById(id),form=$("calcForm"),search=$("paModelSearch");
if(!form||!search)return;
const country=$("calcCountry"),tabs=$("paEstimateTabs"),options=$("paModelOptions"),status=$("paModelStatus"),card=$("paVehicleCard"),photo=$("paVehiclePhoto"),currency=$("paPriceCurrency"),foreign=$("paForeignPrice"),rate=$("paForeignRate"),rateStatus=$("paRateStatus"),car=$("carCost"),order=$("paEstimateOrder");
const marketByCountry={"Япония":"japan","Южная Корея":"south-korea","Китай":"china"},countryByMarket={japan:"Япония","south-korea":"Южная Корея",china:"Китай"},currencies={japan:"JPY","south-korea":"KRW",china:"CNY"},money=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(n);
const translit={а:"a",б:"b",в:"v",г:"g",д:"d",е:"e",ё:"e",ж:"zh",з:"z",и:"i",й:"y",к:"k",л:"l",м:"m",н:"n",о:"o",п:"p",р:"r",с:"s",т:"t",у:"u",ф:"f",х:"h",ц:"ts",ч:"ch",ш:"sh",щ:"shch",ъ:"",ы:"y",ь:"",э:"e",ю:"yu",я:"ya"};
const aliases={"хонда":"Honda","тойота":"Toyota","ниссан":"Nissan","сузуки":"Suzuki","мазда":"Mazda","хендай":"Hyundai","хундай":"Hyundai","киа":"Kia","джили":"Geely","чери":"Chery","хавал":"Haval","чанган":"Changan","бмв":"BMW","мерседес":"Mercedes","ауди":"Audi","фит":"Fit","авант":"Avante","монжаро":"Monjaro","королла":"Corolla","кулрей":"Coolray","соната":"Sonata","эльантра":"Elantra","к5":"K5"};
const norm=s=>String(s||"").toLowerCase().replace(/[а-яё0-9]+/g,w=>aliases[w]||[...w].map(c=>translit[c]??c).join("")).toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
const validAsset=s=>typeof s==="string"&&/^\/assets\/(?:auction\/(?:home|approved)|premium-auctions|china-order)\/[a-z0-9/-]+\.(?:jpe?g|webp|png)$/i.test(s)&&!s.includes("..");
const lotKey=$("paSelectedLot")||Object.assign(document.createElement("input"),{id:"paSelectedLot",type:"hidden"});if(!lotKey.parentNode)form.append(lotKey);
const market=()=>marketByCountry[country.value]||"japan";
let rows=[],loaded=false,loading=null,selected=null,rates=null,ratePromise=null,selectionToken=0,partialSources=[];
const priceKeys=["carCost","auctionFee","originDelivery","exportDocs","insurance","shipping","bankFee","customs","customsFee","utilFee","brokerFee","warehouseFee","paperwork","localDelivery","otherCosts","marketReferencePrice"];
const notify=el=>el.dispatchEvent(new Event("input",{bubbles:true}));
function clearQuote(){priceKeys.forEach(id=>{const el=$(id);if(el)el.value=id==="localDelivery"&&$("calcCity")?.value==="Владивосток"?"0":""});notify(car);}
function cleanCard(){card.hidden=true;photo.replaceChildren();photo.hidden=true;$("paVehicleDetail").hidden=true;}
function clearVehicle(resetMoney=true){selectionToken++;selected=null;lotKey.value="";cleanCard();["paVehicleYear","paVehicleEngine","paVehiclePower","paVehicleTrim","paForeignPrice","paForeignRate","paBuildDate","paAgeBand","paEngineType","paCustomsValue","paUtilEligibility"].forEach(id=>{if($(id))$(id).value=""});rateStatus.textContent="Курс банка можно указать вручную.";if(resetMoney)clearQuote();updateOrder();}
function updateOrder(){const model=search.value.trim(),year=$("paVehicleYear").value;const p=new URLSearchParams();if(model)p.set("similar",[model,year,country.value].filter(Boolean).join(" · "));order.href="/podbor.html"+(p.size?"?"+p.toString():"");}
function updateTabs(){tabs.querySelectorAll("button").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.country===country.value)));}
function rateFor(c){return ({JPY:Number(rates?.rub_per_jpy),KRW:Number(rates?.rub_per_1000_krw)/1000,CNY:Number(rates?.rub_per_cny),USD:Number(rates?.rub_per_usd)})[c];}
async function getRates(){if(rates)return rates;if(!ratePromise){const api=String(window.PAPAUTO_CONFIG?.apiBaseUrl||"").replace(/\/$/,"");ratePromise=api?fetch(api+"/api/exchange-rates",{headers:{Accept:"application/json"}}).then(r=>{if(!r.ok)throw Error("rate");return r.json()}).then(d=>{rates=d;return d}).catch(()=>{ratePromise=null;return null}):Promise.resolve(null)}return ratePromise;}
let syncingFx=false;function applyFx(){const p=Number(foreign.value),r=Number(rate.value),n=Math.round(p*r);const ok=!!foreign.value&&!!rate.value&&Number.isFinite(n)&&p>0&&r>0&&n>=1&&n<=1e9;syncingFx=true;car.value=ok?String(n):"";notify(car);syncingFx=false;return ok;}
async function suggestRate(auto=false){const token=++selectionToken,cc=currency.value;const data=await getRates();if(token!==selectionToken||currency.value!==cc||rate.value)return;const n=rateFor(cc);if(!data||!Number.isFinite(n)||n<=0){rateStatus.textContent="Курс недоступен. Укажите фактический курс банка.";return;}rate.value=String(Number(n.toPrecision(10)));rateStatus.textContent=(data.fallback?"Архивный ориентир":"Справочный курс Банка России")+(data.date?" на "+data.date:"; дата не указана")+". Не является курсом банка.";if(auto&&foreign.value)applyFx();}
function showCard(x){
 cleanCard();
 if(!x.photo){status.textContent="Модель выбрана. Подтверждённой фотографии конкретного автомобиля пока нет — рассчитайте смету вручную.";return;}
 card.hidden=false;photo.hidden=false;const img=document.createElement("img");img.alt="Оригинальное фото "+x.name;img.decoding="async";img.addEventListener("error",()=>{if(!photo.contains(img))return;photo.hidden=true;photo.replaceChildren();card.hidden=true;status.textContent="Фото этого автомобиля недоступно. Другая фотография не подставляется.";},{once:true});img.src=x.photo;photo.append(img);
 $("paVehicleTitle").textContent=x.name+(x.year?" · "+x.year:"");
 $("paVehicleFacts").textContent=[x.mileage,x.engineText,x.trim,x.grade&&"Оценка "+x.grade].filter(Boolean).join(" · ");
 $("paVehicleSource").textContent=[x.source,x.amount>0?money(x.amount)+" "+x.currency:"Цена требует уточнения",x.restricted?"Прямой экспорт ограничен; возможность ввоза уточняется.":""].filter(Boolean).join(" · ");
 const detail=$("paVehicleDetail");if(x.detail){detail.href=x.detail;detail.hidden=false;}status.textContent="Выбран конкретный опубликованный пример. Наличие и цена нового автомобиля уточняются.";
}
function inferredEngine(x){
 const raw=[x.engineType,x.engineText,x.trim,x.name].filter(Boolean).join(" ");
 if(/\b(?:e\s*[:\-]?\s*hev|phev|mhev|hev|hybrid|e[ -]?power)\b|гибрид/i.test(raw))return "hybrid";
 if(/\b(?:bev|electric|ev)\b|электромобил/i.test(raw))return "ev";
 if(/\b(?:petrol|gasoline|diesel|ice)\b|бензин|дизель/i.test(raw))return "ice";
 return "";
}
function select(x,{restore=false}={}){
 if(!restore){clearVehicle();search.value=x.name;lotKey.value=x.key;$("paVehicleYear").value=x.year||"";$("paVehicleEngine").value=x.engine||"";$("paVehiclePower").value=x.power||"";if($("paVehicleTrim"))$("paVehicleTrim").value=x.trim||"";if($("paEngineType"))$("paEngineType").value=inferredEngine(x);currency.value=x.currency||currencies[market()];foreign.value=x.amount>0?String(x.amount):"";}
 selected=x;options.replaceChildren();showCard(x);updateOrder();if(!restore){form.dispatchEvent(new CustomEvent("pa:vehicle-selected",{detail:{bodyType:x.bodyType||""}}));notify(car);suggestRate(true);}
}
const fetchJson=async path=>{const r=await fetch(path,{credentials:"same-origin"});if(!r.ok)throw Error(path);return r.json();};
async function readChina(){const r=await fetch("/china-order.html",{credentials:"same-origin"});if(!r.ok)throw Error("china");const html=await r.text();const doc=new DOMParser().parseFromString(html.replace(/\bsrc\s*=/gi,"data-pa-src="),"text/html");return [...doc.querySelectorAll("article.cn-example")].flatMap(el=>{const img=el.querySelector("img[data-pa-src]"),path=img?.getAttribute("data-pa-src"),title=el.querySelector("h2")?.textContent.trim();if(!title||!validAsset(path)||!path.startsWith("/assets/china-order/"))return [];const get=label=>[...el.querySelectorAll("dl>div")].find(d=>d.querySelector("dt")?.textContent.includes(label))?.querySelector("dd")?.textContent.trim()||"";const y=title.match(/\b(19\d{2}|20\d{2})$/),name=y?title.slice(0,y.index).trim():title;const raw=get("Цена FOB"),amount=/USD/i.test(raw)?Number(raw.replace(/[^\d]/g,"")):0;const source=[...el.querySelectorAll("dt")].find(n=>n.textContent.includes("Цена FOB"))?.textContent||"Цена FOB";const engineText=get("Двигатель");return [{key:"cn:"+path,market:"china",name,year:y?Number(y[1]):null,photo:path,mileage:get("Пробег"),engineText,amount,currency:"USD",source:source+"; расходы до FOB могут быть включены в цену",detail:"/china-order.html"}];});}
function auctionRows(d){return (d.lots||[]).flatMap(l=>{const p=l.photos?.[0];if(!l.id||!l.model||!countryByMarket[l.market]||!validAsset(p)||!validAsset(l.inspection_image)||l.inspection_kind!=="Аукционный лист")return [];const raw=l.price_amount??l.price_jpy;const amount=typeof raw==="number"?raw:Number(String(raw||"").replace(/[^\d]/g,""));return [{key:"lot:"+l.id,market:l.market,name:l.model,year:l.year,photo:p,mileage:l.mileage_km?money(l.mileage_km)+" км":l.mileage,engine:l.engine_cc,power:l.power_hp,engineType:l.engine_type||l.fuel_type||l.fuel||"",description:l.description||"",buildDate:l.build_date||l.manufacture_date||"",bodyType:l.body_type||l.body_style||"",trim:l.trim,grade:l.grade,amount:Number.isFinite(amount)&&amount>0?amount:0,currency:l.currency||currencies[l.market],source:(l.sale_label||"Аукционный пример")+(l.auction_date?" · "+l.auction_date:""),restricted:l.export_restricted,detail:"/lots/"+encodeURIComponent(l.id)+".html"}];});}
function references(d){return (d.items||[]).flatMap(x=>{const m=x.market==="korea"?"south-korea":x.market;if(!countryByMarket[m]||!x.brand||!x.model)return [];return [{key:"ref:"+x.id,market:m,name:x.brand+" "+x.model,engineText:x.engine,engineType:x.engine_type||x.fuel_type||x.fuel||"",bodyType:x.body_type||x.body_style||"",currency:currencies[m]}];});}
async function load(){if(loading)return loading;status.textContent="Загружаем опубликованные автомобили…";loading=Promise.allSettled([fetchJson("/data/gallery-lots.json").then(auctionRows),readChina(),fetchJson("/data/papauto-expanded-45x3-2026.json").then(references)]).then(results=>{rows=results.flatMap((r,i)=>{if(r.status==="fulfilled")return r.value;partialSources.push(i);return [];});loaded=true;return rows;});return loading;}
function matches(x,q){const name=norm(x.name+" "+(x.year||""));const terms=q.split(" ").filter(Boolean);return terms.every(t=>name.includes(t));}
function renderOptions(){options.replaceChildren();if(selected&&search.value===selected.name)return;const raw=search.value.trim(),q=norm(raw),m=market();if(!loaded){status.textContent="Загружаем опубликованные автомобили…";return;}if(!q){status.textContent="Начните вводить марку или модель автомобиля.";return;}const matching=rows.filter(x=>x.market===m&&matches(x,q));matching.sort((a,b)=>Number(!!b.photo)-Number(!!a.photo)||Number(norm(b.name).startsWith(q))-Number(norm(a.name).startsWith(q))||(b.year||0)-(a.year||0));const shown=matching.slice(0,12);for(const x of shown){const b=document.createElement("button");b.type="button";b.textContent=x.name+(x.year?" · "+x.year:"");const sub=document.createElement("small");sub.textContent=x.photo?[x.mileage,x.amount>0?money(x.amount)+" "+x.currency:"Цена по запросу"].filter(Boolean).join(" · "):"Справочник моделей · без фото конкретного авто";b.append(sub);b.addEventListener("click",()=>select(x));options.append(b);}status.textContent=shown.length?"Найдено вариантов: "+matching.length+". Выберите конкретный автомобиль.": "Совпадений нет. Можно ввести модель и цену вручную.";if(partialSources.length)status.textContent+=" Часть каталога временно недоступна.";}
async function ensureLoad(){await load();renderOptions();}
function changeCountry(){updateTabs();clearVehicle();search.value="";currency.value=currencies[market()];updateOrder();suggestRate(true);ensureLoad();}
tabs.hidden=false;country.hidden=true;tabs.querySelectorAll("button").forEach(b=>b.addEventListener("click",()=>{if(country.value!==b.dataset.country){country.value=b.dataset.country;country.dispatchEvent(new Event("change",{bubbles:true}));}}));
country.addEventListener("change",changeCountry);
search.addEventListener("input",()=>{if(selected&&search.value!==selected.name)clearVehicle();updateOrder();ensureLoad();});
search.addEventListener("focus",ensureLoad);
search.addEventListener("keydown",e=>{if(e.key==="ArrowDown"){const first=options.querySelector("button");if(first){e.preventDefault();first.focus();}}if(e.key==="Enter"&&options.querySelector("button")){e.preventDefault();options.querySelector("button").click();}});
options.addEventListener("keydown",e=>{if(e.key==="Escape"){options.replaceChildren();search.focus();}if(e.key==="ArrowDown"||e.key==="ArrowUp"){e.preventDefault();const b=e.target.closest("button");(e.key==="ArrowDown"?b?.nextElementSibling:b?.previousElementSibling)?.focus();}});
$("paVehicleYear").addEventListener("input",updateOrder);
currency.addEventListener("change",()=>{selectionToken++;rate.value="";foreign.value="";applyFx();suggestRate(true);});
rate.addEventListener("input",()=>{selectionToken++;rateStatus.textContent=rate.value?"Курс введён вручную. Цена пересчитывается автоматически.":"Укажите курс валюты.";applyFx();});
foreign.addEventListener("input",()=>{selectionToken++;applyFx();if(foreign.value&&!rate.value)suggestRate(true);});
form.addEventListener("pa:restore-estimate",async()=>{selectionToken++;selected=null;cleanCard();updateTabs();if(!currency.value)currency.value=currencies[market()];updateOrder();await load();const x=rows.find(r=>r.key===lotKey.value&&r.market===market());if(x)select(x,{restore:true});else{status.textContent="Сохранённая смета открыта. Выберите автомобиль, если хотите обновить его данные.";options.replaceChildren();}});
/* Existing converter transfers a value by changing the select without emitting change. */
car.addEventListener("input",()=>{if(syncingFx)return;if(tabs.querySelector('[aria-pressed="true"]')?.dataset.country!==country.value){const v=car.value;updateTabs();clearVehicle();search.value="";currency.value=currencies[market()];car.value=v;updateOrder();suggestRate(false);}else if(foreign.value&&Math.round(Number(foreign.value)*Number(rate.value))!==Number(car.value)){selectionToken++;foreign.value="";rateStatus.textContent="Цена автомобиля указана в рублях вручную.";}});
const params=new URLSearchParams(location.search),key=params.get("vehicle"),m=params.get("market");if(countryByMarket[m])country.value=countryByMarket[m];currency.value=currencies[market()];updateTabs();
if(key){load().then(()=>{const x=rows.find(r=>r.key===key);if(x){country.value=countryByMarket[x.market];updateTabs();select(x);}else{status.textContent="Эта карточка больше недоступна. Выберите другой автомобиль.";}});}
else if(params.get("view")==="calculator"||location.hash==="#calculator")ensureLoad();
const observer=new MutationObserver(()=>{if(document.body.dataset.siteView==="calculator"&&!loaded)ensureLoad();});observer.observe(document.body,{attributes:true,attributeFilter:["data-site-view"]});

/* Budget discovery uses the same approved catalogue and FX as the calculator.
   Foreign price + fixed commission is only a lower bound, not a landed quote. */
const budgetForm=$("paBudgetForm");
if(budgetForm){
 const amount=$("paBudgetAmount"), direction=$("paBudgetMarket"), out=$("paBudgetResults"), note=$("paBudgetStatus"), request=$("paBudgetOrder"), submit=budgetForm.querySelector('[type="submit"]');
 const syncBudget=()=>{const p=new URLSearchParams();if(amount.validity.valid)p.set("budget",amount.value);if(countryByMarket[direction.value])p.set("market",direction.value);request.href="/podbor.html?"+p.toString();budgetForm.querySelectorAll("[data-pa-budget]").forEach(b=>b.setAttribute("aria-pressed",String(b.dataset.paBudget===amount.value)));};
 let revision=0;
 const invalidate=()=>{revision++;out.hidden=true;out.replaceChildren();note.textContent="Нажмите «Подобрать автомобили» для выбранного бюджета.";submit.disabled=false;syncBudget();};
 budgetForm.querySelectorAll("[data-pa-budget]").forEach(b=>b.addEventListener("click",()=>{amount.value=b.dataset.paBudget;invalidate();}));
 amount.addEventListener("input",invalidate);direction.addEventListener("change",invalidate);$("paBudgetEligibility")?.addEventListener("change",invalidate);syncBudget();
 budgetForm.addEventListener("submit",async e=>{
  e.preventDefault();if(!amount.reportValidity())return;
  const token=++revision,limit=Number(amount.value),marketFilter=direction.value;
  submit.disabled=true;out.hidden=true;out.replaceChildren();note.textContent="Проверяем опубликованные примеры и справочный курс…";
  try{
   const [items,fx]=await Promise.all([load(),getRates()]);if(token!==revision)return;
   if(!fx)throw Error("Справочный курс недоступен. Оставьте запрос на подбор — бюджет будет передан.");
   let tariffData=null;
   try{tariffData=await fetchJson("/data/papauto-delivery-tariffs-20261125.json");}catch{}
   if(token!==revision)return;
   const date=new Date(),clearDate=[date.getFullYear(),String(date.getMonth()+1).padStart(2,"0"),String(date.getDate()).padStart(2,"0")].join("-");
   const eligibility=$("paBudgetEligibility")?.value||"";
   const typeOf=x=>{
    const raw=[x.engineType,x.engineText,x.trim,x.name,x.description].filter(Boolean).join(" ");
    if(/\b(?:e\s*[:-]?\s*hev|phev|mhev|hev|hybrid|e[ -]?power)\b|гибрид/i.test(raw))return "hybrid";
    if(/\b(?:bev|electric|ev)\b|электромобил/i.test(raw))return "ev";
    if(/\b(?:petrol|gasoline|diesel|ice)\b|бензин|дизель/i.test(raw))return "ice";
    return "";
   };
   const candidates=items.filter(x=>x.photo&&x.amount>0&&!x.restricted&&(marketFilter==="all"||x.market===marketFilter)).map(x=>({...x,baseRub:Math.round(x.amount*rateFor(x.currency)),q:window.PapAutoQuickQuote?.quote({...x,type:typeOf(x)},fx,tariffData,{clearDate,eligibility})||{total:null,reason:"Модуль сметы недоступен."}})).filter(x=>Number.isFinite(x.baseRub)&&x.baseRub>0&&x.baseRub+50000<=limit);
   const fits=candidates.filter(x=>x.q.total!==null&&x.q.total<=limit).sort((a,b)=>b.q.total-a.q.total);
   const pending=candidates.filter(x=>x.q.total===null).sort((a,b)=>b.year-a.year||a.baseRub-b.baseRub);
   const distinct=(xs,n)=>{const seen=new Set();return xs.filter(x=>{const key=x.market+":"+norm(x.name);if(seen.has(key))return false;seen.add(key);return true;}).slice(0,n);};
   const confirmed=distinct(fits,12),unconfirmed=distinct(pending,8);
   const showGroup=(title,rows,full)=>{
    if(!rows.length)return;
    const heading=document.createElement("h3");heading.textContent=title;out.append(heading);
    for(const x of rows){
     const card=document.createElement("article");card.className="vehicle-result-card";
     const img=document.createElement("img");img.alt=x.name;img.loading="lazy";img.style.cssText="width:100%;max-height:180px;object-fit:contain";img.addEventListener("error",()=>card.remove(),{once:true});img.src=x.photo;
     const name=document.createElement("h3");name.textContent=x.name+(x.year?" · "+x.year:"");
     const meta=document.createElement("p");meta.textContent=[countryByMarket[x.market],x.mileage,x.source].filter(Boolean).join(" · ");
     const price=document.createElement("strong");price.textContent=full?money(x.q.total)+" ₽ — предварительно до Новосибирска":money(x.baseRub)+" ₽ — цена за рубежом";
     const disclaimer=document.createElement("p");disclaimer.textContent=full?"Стандартная смета личного ввоза на дату расчёта; исторический пример, не наличие. Дополнительные расходы и фактический курс уточняются.":x.q.reason+" Попадание в бюджет под ключ не подтверждено.";
     const link=document.createElement("a");link.className="button button-secondary";link.href="/?"+new URLSearchParams({view:"calculator",market:x.market,vehicle:x.key}).toString();link.textContent="Рассчитать стоимость";
     const lead=document.createElement("a");lead.className="button button-primary";lead.href="/podbor.html?"+new URLSearchParams({budget:String(limit),market:x.market,similar:[x.name,x.year,countryByMarket[x.market]].filter(Boolean).join(" · ")}).toString();lead.textContent="Подобрать аналог";
     card.append(img,name,meta,price);
     if(full){const details=document.createElement("details");const summary=document.createElement("summary");summary.textContent="Состав сметы";details.append(summary);const labels={car:"Автомобиль",japan:"Расходы по Японии",shipping:"Фрахт",bank:"Банк",docs:"Оформление",duty:"Пошлина",customsFee:"Таможенный сбор",util:"Утильсбор",commission:"Комиссия PapAuto",delivery:"Автовоз"};for(const [k,v] of Object.entries(x.q.costs)){const row=document.createElement("p");row.textContent=labels[k]+": "+money(v)+" ₽";details.append(row);}card.append(details);}
     card.append(disclaimer,link,lead);out.append(card);
    }
   };
   showGroup("В рамках бюджета по предварительной полной смете",confirmed,true);
   showGroup("Требуют отдельного расчёта — не подтверждены по бюджету",unconfirmed,false);
   out.hidden=!(confirmed.length||unconfirmed.length);
   note.textContent="Полная стандартная смета: "+confirmed.length+" вариантов. Отдельный расчёт: "+unconfirmed.length+" примеров. "+(confirmed.length?"":"Подтверждённых по смете вариантов пока нет. ")+(fx.date?"Курс на "+fx.date+".":"Дата курса не указана.")+(fx.fallback?" Архивный курс.":"")+(partialSources.length?" Часть источников недоступна.":"");
  }catch(err){if(token===revision)note.textContent=err.message||"Каталог временно недоступен. Запросите подбор.";}
  finally{if(token===revision)submit.disabled=false;}
 });
}

updateOrder();suggestRate(true);
})();
