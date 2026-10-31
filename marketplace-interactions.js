(()=>{"use strict";
const KEY_FAV="papauto:favorites:v1",KEY_COMPARE="papauto:compare:v1",$=id=>document.getElementById(id);
const read=key=>{try{const value=JSON.parse(localStorage.getItem(key)||"[]");return Array.isArray(value)?value:[]}catch{return[]}};
const write=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value));return true}catch{return false}};
let favorites=read(KEY_FAV),compare=read(KEY_COMPARE);
const title=x=>[x.make,x.model,x.year].filter(Boolean).join(" ")||"Автомобиль";
const money=x=>x.price!=null&&x.price!==""?String(x.price)+(x.currency==="KRW"?" ₩":x.currency==="JPY"?" ¥":x.currency==="CNY"?" 元":x.currency==="RUB"?" ₽":""):"Цена не указана";
const fmt=(v,suffix="")=>v==null||v===""?"Не указано":String(v)+suffix;
function render(){
 const panel=$("vehicleToolsPanel"),saved=$("vehicleSavedList"),comp=$("vehicleCompareList");
 if(!panel||!saved||!comp)return;
 panel.hidden=!favorites.length&&!compare.length;saved.replaceChildren();comp.replaceChildren();
 if(favorites.length){
  const h=document.createElement("h4");h.textContent="Избранное ("+favorites.length+")";saved.append(h);
  favorites.forEach(item=>{const row=document.createElement("div");row.className="vehicle-saved-item";const info=document.createElement("div"),strong=document.createElement("strong"),small=document.createElement("small");strong.textContent=title(item);small.textContent=money(item)+" · "+(item.source_name||item.source||"Источник не указан");info.append(strong,small);const remove=document.createElement("button");remove.type="button";remove.textContent="Убрать";remove.addEventListener("click",()=>{favorites=favorites.filter(x=>x.id!==item.id);write(KEY_FAV,favorites);window.dispatchEvent(new CustomEvent("papauto:favorites-changed",{detail:favorites}));render()});row.append(info,remove);saved.append(row)});
 }else{const p=document.createElement("p");p.textContent="В избранном пока нет автомобилей.";saved.append(p)}
 if(compare.length){
  const h=document.createElement("h4");h.textContent="Сравнение ("+compare.length+"/3)";comp.append(h);
  const table=document.createElement("table");table.className="vehicle-compare-table";
  const fields=[
   ["Год выпуска",x=>fmt(x.year)],["Пробег",x=>x.mileage==null?"Не указан":new Intl.NumberFormat("ru-RU").format(Number(x.mileage))+" км"],
   ["Кузов",x=>fmt(x.body_type||x.body)],["Двигатель",x=>x.volume_cc?new Intl.NumberFormat("ru-RU").format(Number(x.volume_cc))+" см³":fmt(x.engine)],
   ["Мощность",x=>fmt(x.power_hp??x.power," л.с.")],["Топливо",x=>fmt(x.fuel_type||x.fuel)],
   ["Коробка передач",x=>fmt(x.transmission)],["Привод",x=>fmt(x.drivetrain||x.drive)],
   ["Цена источника",money],["Источник",x=>x.source_name||x.source||x.data_source||"Не указан"]
  ];
  const head=document.createElement("tr"),blank=document.createElement("th");blank.textContent="Параметр";head.append(blank);
  compare.forEach(x=>{const th=document.createElement("th");th.textContent=title(x);head.append(th)});table.append(head);
  fields.forEach(([label,format])=>{const tr=document.createElement("tr"),th=document.createElement("th");th.textContent=label;tr.append(th);compare.forEach(x=>{const td=document.createElement("td");td.textContent=format(x);tr.append(td)});table.append(tr)});
  const removeRow=document.createElement("tr"),removeLabel=document.createElement("th");removeLabel.textContent="Действие";removeRow.append(removeLabel);
  compare.forEach(x=>{const td=document.createElement("td"),button=document.createElement("button");button.type="button";button.textContent="Убрать";button.addEventListener("click",()=>{compare=compare.filter(v=>v.id!==x.id);write(KEY_COMPARE,compare);render()});td.append(button);removeRow.append(td)});table.append(removeRow);comp.append(table);
  const clear=document.createElement("button");clear.type="button";clear.className="vehicle-compare-clear";clear.textContent="Очистить сравнение";clear.addEventListener("click",()=>{compare=[];write(KEY_COMPARE,compare);render()});comp.append(clear);
 }else{const p=document.createElement("p");p.textContent="Добавьте до трёх автомобилей для сравнения характеристик.";comp.append(p)}
}
document.addEventListener("click",event=>{
 const save=event.target.closest("[data-save-vehicle]"),cmp=event.target.closest("[data-compare-vehicle]");if(!save&&!cmp)return;
 const button=save||cmp;let item;try{item=JSON.parse(button.dataset.car||"{}")}catch{return}if(!item.id)return;
 if(save){const exists=favorites.some(x=>x.id===item.id);favorites=exists?favorites.filter(x=>x.id!==item.id):[item,...favorites].slice(0,50);write(KEY_FAV,favorites);window.dispatchEvent(new CustomEvent("papauto:favorites-changed",{detail:favorites}));button.setAttribute("aria-pressed",String(!exists));button.textContent=exists?"♡ В избранное":"♥ В избранном";render()}
 if(cmp){const exists=compare.some(x=>x.id===item.id);if(exists)compare=compare.filter(x=>x.id!==item.id);else if(compare.length>=3){button.textContent="Максимум 3 авто";return}else compare=[...compare,item];write(KEY_COMPARE,compare);button.setAttribute("aria-pressed",String(!exists));button.textContent=exists?"Сравнить":"В сравнении";render()}
});
window.addEventListener("papauto:cloud-data-loaded",()=>{favorites=read(KEY_FAV);compare=read(KEY_COMPARE);render()});document.addEventListener("DOMContentLoaded",render);render();
})();