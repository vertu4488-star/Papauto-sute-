(()=>{"use strict";
const form=document.getElementById("vehicleSearchForm");
if(!form)return;
const ids=["vehicleCountry","vehicleMake","vehicleModel","vehicleYearFrom","vehicleYearTo","vehicleMaxPrice","vehicleMileageMax","vehicleVolumeMin","vehicleVolumeMax","vehicleBody","vehicleGrade","vehicleLot"];
const key="papauto:saved-searches:v1";
const read=()=>{try{const x=JSON.parse(localStorage.getItem(key)||"[]");return Array.isArray(x)?x.filter(v=>v&&typeof v==="object").slice(0,10):[]}catch{return[]}};
const write=x=>{try{localStorage.setItem(key,JSON.stringify(x.slice(0,10)))}catch{}};
const values=()=>Object.fromEntries(ids.map(id=>[id,document.getElementById(id)?.value??""]));
const label=v=>[v.vehicleMake,v.vehicleModel,v.vehicleCountry==="japan"?"Япония":v.vehicleCountry==="china"?"Китай":"Корея",v.vehicleYearFrom&&v.vehicleYearTo?v.vehicleYearFrom+"–"+v.vehicleYearTo:""].filter(Boolean).join(" · ")||"Мой поиск";
const apply=v=>{ids.forEach(id=>{const el=document.getElementById(id);if(el&&v[id]!==undefined)el.value=String(v[id])})};
const panel=document.createElement("section");
panel.className="saved-search-panel";
panel.setAttribute("aria-label","Сохранённые поиски");
panel.innerHTML='<div class="saved-search-actions"><button type="button" class="button button-secondary" data-save-search>Сохранить поиск</button><button type="button" class="button button-secondary" data-share-search>Поделиться фильтрами</button></div><div class="saved-search-heading">Мои сохранённые поиски</div><div class="saved-search-list" data-saved-search-list></div><p class="saved-search-note">Поиски хранятся в этом браузере. Ссылка на фильтры открывается на любом устройстве.</p>';
const submit=document.getElementById("vehicleSearchButton");
submit?.insertAdjacentElement("afterend",panel);
const list=panel.querySelector("[data-saved-search-list]");
const render=()=>{list.replaceChildren();const items=read();if(!items.length){const empty=document.createElement("span");empty.className="saved-search-empty";empty.textContent="Пока нет сохранённых поисков.";list.append(empty);return}
items.forEach((item,index)=>{const row=document.createElement("div");row.className="saved-search-item";const load=document.createElement("button");load.type="button";load.className="saved-search-load";load.textContent=item.name||label(item.filters||{});load.addEventListener("click",()=>{apply(item.filters||{});form.requestSubmit()});const del=document.createElement("button");del.type="button";del.className="saved-search-delete";del.setAttribute("aria-label","Удалить сохранённый поиск");del.textContent="×";del.addEventListener("click",()=>{const next=read();next.splice(index,1);write(next);window.dispatchEvent(new CustomEvent("papauto:saved-searches-changed",{detail:next}));render()});row.append(load,del);list.append(row)})};
panel.querySelector("[data-save-search]").addEventListener("click",()=>{const filters=values(),items=read();const item={name:label(filters),filters,savedAt:new Date().toISOString()};const signature=JSON.stringify(filters);const next=[item,...items.filter(x=>JSON.stringify(x.filters)!==signature)].slice(0,10);write(next);window.dispatchEvent(new CustomEvent("papauto:saved-searches-changed",{detail:next}));render();panel.querySelector("[data-save-search]").textContent="Поиск сохранён";setTimeout(()=>{const b=panel.querySelector("[data-save-search]");if(b)b.textContent="Сохранить поиск"},1800)});
panel.querySelector("[data-share-search]").addEventListener("click",async()=>{const params=new URLSearchParams();ids.forEach(id=>{const el=document.getElementById(id);if(el&&el.value)params.set(id,el.value)});const share=new URL(location.href);share.hash="catalog";share.search=params.toString();try{await navigator.clipboard.writeText(share.href);const b=panel.querySelector("[data-share-search]");b.textContent="Ссылка скопирована";setTimeout(()=>{if(b)b.textContent="Поделиться фильтрами"},1800)}catch{const b=panel.querySelector("[data-share-search]");b.textContent="Разрешите копирование ссылки"}});
const params=new URLSearchParams(location.search);let hasParams=false;ids.forEach(id=>{if(params.has(id)){const el=document.getElementById(id);if(el){el.value=params.get(id);hasParams=true}}});
window.addEventListener("papauto:cloud-data-loaded",render);
render();
if(hasParams){const note=document.createElement("p");note.className="saved-search-note";note.textContent="Фильтры загружены из ссылки. Нажмите «Найти автомобили», чтобы выполнить поиск.";panel.prepend(note)}
})();