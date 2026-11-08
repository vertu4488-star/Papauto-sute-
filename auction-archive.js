(()=>{"use strict";
const by=id=>document.getElementById(id),grid=by("auctionGrid"),status=by("auctionStatus"),count=by("auctionCount"),country=by("auctionCountry"),search=by("auctionSearch");
if(!grid||!status)return;
const names={japan:"Япония","south-korea":"Южная Корея",china:"Китай"};
const element=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=String(text);if(cls)n.className=cls;return n};
const safePhoto=p=>typeof p==="string"&&/^\/assets\/auction\/[a-z0-9._/-]+\.(jpg|jpeg|png|webp)$/i.test(p)&&!p.includes("..");
const valid=r=>r&&r.image_rights==="approved"&&r.make&&r.model&&Number.isInteger(Number(r.year))&&Array.isArray(r.photos)&&r.photos.length>0&&r.photos.every(safePhoto);
let rows=[];
function render(){
 const q=search.value.trim().toLowerCase(),c=country.value;
 const filtered=rows.filter(r=>(!c||c===r.country)&&(!q||[r.make,r.model,r.year,r.body,r.color,r.lot].join(" ").toLowerCase().includes(q)));
 count.hidden=!filtered.length;status.hidden=!filtered.length;grid.hidden=!filtered.length;
 count.textContent="Подтверждённых аукционных лотов: "+filtered.length;grid.replaceChildren();
 for(const r of filtered){
 const card=element("article",undefined,"lot"),img=element("img");img.src=r.photos[0];img.alt="Фото аукционного лота: "+r.make+" "+r.model+" "+r.year;img.loading="lazy";img.onerror=()=>{card.remove()};card.append(img);
 const body=element("div",undefined,"lot-body");body.append(element("div",names[r.country]||"Не указано","market"),element("h2",r.make+" "+r.model+" · "+r.year));
 const specs=element("div",undefined,"specs");
 for(const [k,v] of [["Кузов",r.body],["Цвет",r.color],["Пробег",r.mileage_km==null?null:Number(r.mileage_km).toLocaleString("ru-RU")+" км"],["Оценка",r.grade],["Лот",r.lot],["Аукцион",r.auction]]){
 const cell=element("div");cell.append(element("small",k),element("strong",v||"Не указано"));specs.append(cell)}
 body.append(specs);
 const money=r.sale_status==="verified_sold"&&Number.isFinite(Number(r.sold_price))?Number(r.sold_price).toLocaleString("ru-RU")+" "+(r.currency||""):"Фактическая цена не подтверждена";
 body.append(element("p",money,"price"),element("p","Архивный автомобиль. Не объявление о наличии.","note"));
 const a=element("a","Подобрать похожий автомобиль","cta");a.href="/?view=select&similar="+encodeURIComponent(r.make+" "+r.model+" "+r.year)+"#assistant";body.append(a);card.append(body);grid.append(card);
 }
 status.textContent=filtered.length?"Указаны архивные экземпляры, не машины в наличии.":"Подтверждённых реальных лотов пока нет; ниже уже доступны четыре демонстрационные карточки с изображениями и полным условным расчётом. Это не реальные результаты аукционов.";
}
country.addEventListener("change",render);search.addEventListener("input",render);
fetch("/data/approved-auction-lots.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("HTTP");return r.json()}).then(j=>{rows=(Array.isArray(j.lots)?j.lots:[]).filter(valid);render()}).catch(()=>{rows=[];render()});
})();