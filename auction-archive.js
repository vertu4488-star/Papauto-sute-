(()=>{
"use strict";
const by=id=>document.getElementById(id);
const grid=by("auctionGrid"),status=by("auctionStatus"),count=by("auctionCount"),country=by("auctionCountry"),search=by("auctionSearch");
if(!grid||!status||!count||!country||!search)return;
const countryNames={japan:"Япония","south-korea":"Южная Корея",china:"Китай"};
const make=(tag,value,cls)=>{const el=document.createElement(tag);if(value!==undefined)el.textContent=String(value);if(cls)el.className=cls;return el};
const securePath=p=>typeof p==="string"&&/^\/assets\/auction\/[a-z0-9._/-]+\.(jpg|jpeg|png|webp)$/i.test(p)&&!p.includes("..");
const permitted=r=>r&&r.image_rights==="approved"&&r.commercial_use_permission===true&&r.self_host_permission===true&&r.sheet_permission===true&&r.make&&r.model&&r.country in countryNames&&Number.isInteger(Number(r.year))&&Array.isArray(r.photos)&&r.photos.length>0&&r.photos.every(securePath)&&securePath(r.auction_sheet);
const number=v=>Number.isFinite(Number(v))?Number(v).toLocaleString("ru-RU"):"";
const valid=v=>v!==null&&v!==undefined&&String(v).trim()!=="";
let records=[];
function fact(label,value){
 if(!valid(value))return null;
 const item=make("div",undefined,"lot-fact");
 item.append(make("small",label),make("strong",value));
 return item;
}
function addFact(host,label,value){
 const node=fact(label,value);
 if(node)host.append(node);
}
function zoomable(src,label,buttonLabel){
 const button=make("button",buttonLabel,"lot-media-zoom");
 button.type="button";button.setAttribute("aria-label",buttonLabel);
 button.addEventListener("click",()=>{
  const dialog=make("dialog",undefined,"lot-image-dialog");
  const close=make("button","Закрыть ×","lot-dialog-close");
  close.type="button";close.addEventListener("click",()=>dialog.close());
  const img=make("img");img.src=src;img.alt=label;img.decoding="async";
  dialog.append(close,img,make("p",label));
  dialog.addEventListener("close",()=>dialog.remove());
  dialog.addEventListener("click",e=>{if(e.target===dialog)dialog.close()});
  document.body.append(dialog);
  if(typeof dialog.showModal==="function")dialog.showModal();
  else dialog.setAttribute("open","");
 });
 return button;
}
function photoGallery(r){
 const container=make("div",undefined,"lot-media");
 const photoArea=make("div",undefined,"lot-photo-area");
 const hero=make("div",undefined,"lot-main");
 const image=make("img");
 image.src=r.photos[0];image.loading="lazy";image.decoding="async";
 image.alt="Фотография конкретного автомобиля "+r.make+" "+r.model+" "+r.year;
 const caption=make("p","Фото автомобиля · 1 / "+r.photos.length,"lot-gallery-caption");
 hero.append(image,caption);
 const zoomHolder=make("div",undefined,"lot-photo-zoom");
 const setZoom=src=>{
  zoomHolder.replaceChildren(zoomable(src,"Фото автомобиля "+r.make+" "+r.model,"Увеличить фото"));
 };
 setZoom(r.photos[0]);photoArea.append(hero,zoomHolder);
 const thumbs=make("div",undefined,"lot-thumbs");
 r.photos.forEach((src,i)=>{
  const btn=make("button",undefined,"lot-thumb"+(i===0?" selected":""));
  btn.type="button";btn.setAttribute("aria-label","Фотография "+(i+1)+" из "+r.photos.length);
  btn.setAttribute("aria-pressed",String(i===0));
  const preview=make("img");preview.src=src;preview.alt="";preview.loading="lazy";
  btn.append(preview);
  btn.addEventListener("click",()=>{
   image.src=src;caption.textContent="Фото автомобиля · "+(i+1)+" / "+r.photos.length;
   setZoom(src);
   [...thumbs.children].forEach((el,index)=>{el.classList.toggle("selected",index===i);el.setAttribute("aria-pressed",String(index===i));});
  });
  thumbs.append(btn);
 });
 photoArea.append(thumbs);
 const sheet=make("div",undefined,"lot-sheet-panel");
 sheet.append(make("h3","Аукционный лист"));
 const sheetPic=make("img");sheetPic.src=r.auction_sheet;sheetPic.alt="Оригинальный аукционный лист лота "+(r.lot||"")+" — "+r.make+" "+r.model;
 sheetPic.loading="lazy";sheetPic.decoding="async";
 sheet.append(sheetPic,zoomable(r.auction_sheet,sheetPic.alt,"Открыть лист крупно"));
 container.append(photoArea,sheet);
 return container;
}
function presentPrice(r){
 const block=make("div",undefined,"lot-price-block");
 if(r.sale_status==="verified_sold"&&valid(r.currency)&&Number(r.sold_price)>0){
  block.append(make("small","Цена продажи на аукционе"),make("strong",number(r.sold_price)+" "+r.currency));
 }else{
  block.append(make("small","Цена продажи"),make("strong","Нет подтверждённой цены"));
 }
 if(Number(r.start_price)>0&&r.currency){
  block.append(make("p","Начальная ставка: "+number(r.start_price)+" "+r.currency));
 }
 return block;
}
function costDetails(r){
 if(!r.costs||typeof r.costs!=="object")return null;
 const names=[["auction_rub","Покупка автомобиля"],["japan_fees_rub","Расходы в стране"],["freight_rub","Фрахт"],["duty_rub","Таможенная пошлина"],["util_fee_rub","Утильсбор"],["documents_rub","Документы и оформление"],["commission_rub","Комиссия PapAuto"],["delivery_novosibirsk_rub","Доставка в Новосибирск"]];
 const verified=names.filter(([key])=>Number.isFinite(Number(r.costs[key]))&&Number(r.costs[key])>=0);
 if(!verified.length||r.costs.verified!==true)return null;
 const details=make("details",undefined,"lot-costs");
 details.append(make("summary","Все расходы"));
 const lines=make("div",undefined,"lot-cost-lines");
 verified.forEach(([key,label])=>{
  const row=make("div",undefined,"lot-cost-line");
  row.append(make("span",label),make("strong",number(r.costs[key])+" ₽"));lines.append(row);
 });
 details.append(lines);
 if(Number(r.costs.total_novosibirsk_rub)>0){
  details.append(make("div","Итого до Новосибирска: "+number(r.costs.total_novosibirsk_rub)+" ₽","lot-cost-total"));
 }
 return details;
}
function render(){
 const needle=search.value.toLocaleLowerCase("ru").trim(),selectedCountry=country.value;
 const filtered=records.filter(r=>(!selectedCountry||r.country===selectedCountry)&&(!needle||[r.make,r.model,r.body,r.year,r.grade,r.lot,r.trim].join(" ").toLocaleLowerCase("ru").includes(needle)));
 grid.replaceChildren();
 const filters=by("auctionFilters");if(filters)filters.hidden=!records.length;
 count.hidden=!records.length;count.textContent="Автомобилей: "+filtered.length;
 grid.hidden=!filtered.length;
 filtered.forEach(r=>{
  const card=make("article",undefined,"lot lot-full");
  card.id="lot-"+String(r.id||r.lot).replace(/[^a-zA-Z0-9-]/g,"");
  card.append(photoGallery(r));
  const body=make("div",undefined,"lot-body");
  const prefix=make("div",countryNames[r.country]+" · "+(r.auction||"Аукцион"),"lot-kicker");
  body.append(prefix,make("h2",r.make+" "+r.model+" · "+r.year));
  const specs=make("div",undefined,"lot-facts");
  addFact(specs,"Пробег",r.mileage_km==null?"":number(r.mileage_km)+" км");
  addFact(specs,"Аукционная оценка",r.grade);
  addFact(specs,"Объём двигателя",r.engine_cc?number(r.engine_cc)+" см³":r.engine);
  addFact(specs,"Кузов",r.body);
  addFact(specs,"Мощность",r.power_hp?number(r.power_hp)+" л.с.":null);
  addFact(specs,"Тип топлива",r.fuel_type);
  addFact(specs,"Привод",r.drive);
  addFact(specs,"КПП",r.transmission);
  addFact(specs,"Комплектация",r.trim);
  addFact(specs,"Цвет",r.color);
  addFact(specs,"Номер лота",r.lot);
  addFact(specs,"Дата торгов",r.auction_date);
  body.append(specs,presentPrice(r));
  const costs=costDetails(r);if(costs)body.append(costs);
  body.append(make("p","Подберём автомобиль с похожими характеристиками и рассчитаем доставку в ваш город.","lot-intro-note"));
  const a=make("a","Подобрать похожий автомобиль","cta");
  a.href="/podbor.html?similar="+encodeURIComponent(r.make+" "+r.model+" "+r.year);
  body.append(a);card.append(body);grid.append(card);
 });
 status.hidden=filtered.length>0;
 status.textContent=records.length?"По выбранным условиям автомобилей нет.":"Подтверждённых фотокарточек пока нет. Вы можете оставить заявку на подбор автомобиля.";
}
country.addEventListener("change",render);search.addEventListener("input",render);
fetch("/data/approved-auction-lots.json",{cache:"no-store"}).then(resp=>{if(!resp.ok)throw Error("Unable to load lots");return resp.json()})
.then(j=>{records=(Array.isArray(j.lots)?j.lots:[]).filter(permitted);render()})
.catch(()=>{records=[];render();status.textContent="Не удалось загрузить каталог. Форма подбора доступна."});
})();