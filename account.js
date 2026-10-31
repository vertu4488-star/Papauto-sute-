(()=>{"use strict";
const KEY="papauto_local_requests_v1",root=document.getElementById("accountLocalRequests"),status=document.getElementById("accountStatus"),clear=document.getElementById("clearLocalRequests"),exportButton=document.getElementById("exportLocalRequests");
const read=()=>{try{const x=JSON.parse(localStorage.getItem(KEY)||"[]");return Array.isArray(x)?x:[]}catch{return[]}};
const write=x=>{try{localStorage.setItem(KEY,JSON.stringify(x.slice(0,20)));return true}catch{return false}};
const fmt=x=>new Date(x).toLocaleString("ru-RU");
function render(){
 if(!root)return;
 const items=read();root.replaceChildren();
 if(!items.length){const p=document.createElement("p");p.textContent="Подготовленных заявок пока нет.";root.append(p);return}
 items.forEach(item=>{
  const card=document.createElement("article");card.className="account-order-card";
  const title=document.createElement("strong");title.textContent=[item.make,item.model,item.year].filter(Boolean).join(" ")||"Заявка на подбор";
  const meta=document.createElement("p");meta.textContent=[item.country||"Направление не указано",fmt(item.saved_at),item.sent?"отправлена менеджеру":"сохранена на устройстве"].join(" · ");
  const body=document.createElement("p");body.textContent=item.request||"Описание не сохранено";
  const actions=document.createElement("div");actions.className="account-local-actions";
  const copy=document.createElement("button");copy.type="button";copy.textContent="Скопировать";copy.addEventListener("click",async()=>{try{await navigator.clipboard.writeText(item.request||"");if(status)status.textContent="Текст заявки скопирован."}catch{if(status)status.textContent="Не удалось скопировать автоматически."}});
  const remove=document.createElement("button");remove.type="button";remove.textContent="Удалить";remove.addEventListener("click",()=>{write(read().filter(x=>x.id!==item.id));render()});
  actions.append(copy,remove);card.append(title,meta,body,actions);root.append(card);
 });
}
function save(lead,sent){
 if(!lead||!lead.request)return;
 const items=read(),key=String(lead.request)+"|"+String(lead.contact||"");
 const existing=items.find(x=>x.dedupe===key);
 if(existing){existing.sent=existing.sent||Boolean(sent);existing.saved_at=Date.now()}
 else items.unshift({id:(Date.now().toString(36)+Math.random().toString(36).slice(2,7)),dedupe:key,make:lead.make||"",model:lead.model||"",year:lead.yearTo||lead.yearFrom||"",country:lead.country||"",request:lead.request,contact:lead.contact||"",saved_at:Date.now(),sent:Boolean(sent)});
 const ok=write(items);render();if(status)status.textContent=ok?(sent?"Заявка отмечена как отправленная менеджеру.":"Заявка сохранена локально в этом браузере."):"Не удалось сохранить историю: проверьте свободное место браузера.";
}
window.PAPAUTO_ACCOUNT={saveRequest:lead=>save(lead,false)};
window.addEventListener("papauto:lead-prepared",e=>save(e.detail,false));
window.addEventListener("papauto:lead-submitted",e=>save(e.detail,true));
if(exportButton)exportButton.addEventListener("click",()=>{const data=JSON.stringify(read(),null,2),blob=new Blob([data],{type:"application/json;charset=utf-8"}),url=URL.createObjectURL(blob),link=document.createElement("a");link.href=url;link.download="papauto-local-requests-"+new Date().toISOString().slice(0,10)+".json";document.body.append(link);link.click();link.remove();URL.revokeObjectURL(url)});
if(clear)clear.addEventListener("click",()=>{localStorage.removeItem(KEY);render();if(status)status.textContent="Локальная история очищена."});
render();
})();