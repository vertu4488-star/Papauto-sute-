(()=>{"use strict";
const KEY="papauto:lead-drafts:v1",ids=["country","carMake","carModel","yearFrom","yearTo","maxMileage","budget","carPrompt","carListingUrl","city","leadName","contact"];
const $=id=>document.getElementById(id),form=$("assistantForm"),output=$("requestOutput");
let activeDraftId=null,saveTimer=null;
if(!form||!output)return;
const read=()=>{try{const v=JSON.parse(localStorage.getItem(KEY)||"[]");return Array.isArray(v)?v.slice(0,15):[]}catch{return[]}};
const write=v=>{try{localStorage.setItem(KEY,JSON.stringify(v.slice(0,15)));return true}catch{return false}};
const capture=()=>Object.fromEntries(ids.map(id=>[id,$(id)?.value??""]));
const label=d=>[d.fields?.carMake,d.fields?.carModel,d.fields?.country,d.fields?.city].filter(Boolean).join(" · ")||"Заявка PAPAUTO";
const panel=document.createElement("section");panel.className="lead-draft-history";
panel.innerHTML='<div class="lead-draft-head"><div><strong>Черновики и заявки</strong><p>Хранятся только в этом браузере. Здесь могут быть контактные данные.</p></div><button type="button" data-clear-drafts>Очистить</button></div><div class="lead-draft-list" aria-live="polite"></div>';
output.append(panel);
const list=panel.querySelector(".lead-draft-list");
function render(){list.replaceChildren();const items=read();if(!items.length){const p=document.createElement("p");p.className="lead-draft-empty";p.textContent="Сохранённых заявок пока нет.";list.append(p);return}
items.forEach(item=>{const row=document.createElement("article");row.className="lead-draft-row";const info=document.createElement("div"),name=document.createElement("strong"),meta=document.createElement("small");name.textContent=label(item);meta.textContent=new Date(item.updatedAt).toLocaleString("ru-RU")+" · "+(item.status==="sent"?"отправлена":"черновик");info.append(name,meta);const actions=document.createElement("div"),open=document.createElement("button"),del=document.createElement("button");open.type=del.type="button";open.textContent="Открыть";del.textContent="Удалить";open.addEventListener("click",()=>{activeDraftId=item.id;ids.forEach(id=>{if($(id)&&item.fields&&Object.hasOwn(item.fields,id))$(id).value=item.fields[id]});$("leadConsent").checked=false;output.hidden=false;const submit=form.querySelector('button[type="submit"]');submit?.scrollIntoView({behavior:"smooth",block:"center"});$("carPrompt")?.focus({preventScroll:true});});del.addEventListener("click",()=>{write(read().filter(x=>x.id!==item.id));render()});actions.append(open,del);row.append(info,actions);list.append(row)})}
panel.querySelector("[data-clear-drafts]").addEventListener("click",()=>{if(!confirm("Удалить все локальные черновики и заявки с этого устройства?"))return;write([]);render()});
function saveDraft(requestText=""){
 const fields=capture();if(!ids.some(id=>String(fields[id]||"").trim()))return;
 const items=read(),id=activeDraftId||(crypto.randomUUID?crypto.randomUUID():"lead-"+Date.now()+"-"+Math.random().toString(16).slice(2));
 activeDraftId=id;const item={id,fields,request:requestText||$("requestText")?.value||"",status:"draft",updatedAt:new Date().toISOString()};
 write([item,...items.filter(x=>x.id!==id)].slice(0,15));render();
}
function scheduleSave(){clearTimeout(saveTimer);saveTimer=setTimeout(()=>saveDraft(),500)}
ids.forEach(id=>{const field=$(id);if(field){field.addEventListener("input",scheduleSave);field.addEventListener("change",scheduleSave)}});
window.addEventListener("papauto:lead-prepared",e=>saveDraft($("requestText")?.value||""));
window.addEventListener("papauto:lead-submitted",e=>{
 const detail=e.detail||{},items=read(),idx=items.findIndex(x=>x.id===activeDraftId);
 if(idx<0)return;items[idx].status="sent";items[idx].updatedAt=new Date().toISOString();write(items);render();
});
render();
})();