(()=>{"use strict";
const $=id=>document.getElementById(id),button=$("smartSearchRun"),form=$("smartSearchPrompt"),out=$("smartSearchResults"),status=$("smartSearchStatus"),cfg=window.PAPAUTO_CONFIG||{};
if(!button||!form||!out||!status)return;
const el=(tag,cls,text)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined)n.textContent=String(text);return n};
const link=(parent,url,label)=>{if(!url||!/^https:\/\//i.test(url))return;const a=el("a","",label);a.href=url;a.target="_blank";a.rel="noopener noreferrer";parent.append(a)};
const money=v=>v==null?"Цена не указана":String(v);
function render(data){
 out.replaceChildren();
 const search=data.search||{},country=search.country||data.filters?.country;
 const summary=el("div","smart-search-interpretation",data.reply||"Запрос обработан.");
 const f=data.filters||{};
 const bits=[f.make,f.model,(f.year_from||"")+"–"+(f.year_to||""),f.mileage_max?"до "+Number(f.mileage_max).toLocaleString("ru-RU")+" км":""].filter(Boolean);
 if(bits.length)summary.append(el("p","", "Распознано: "+bits.join(" · ")));
 out.append(summary);
 const records=Array.isArray(search.results)?search.results:[];
 if(country==="south-korea"&&records.length){
   const grid=el("div","smart-search-result-grid");
   records.forEach(item=>{const card=el("article","smart-search-card");card.append(el("span","smart-search-badge","АКТУАЛЬНОЕ ОБЪЯВЛЕНИЕ · "+(item.source_name||"Корея")));if(item.thumbnail){const img=document.createElement("img");img.src=item.thumbnail;img.alt=[item.make,item.model,item.year].filter(Boolean).join(" ");img.loading="lazy";card.append(img)}card.append(el("h3","",[item.make,item.model,item.year].filter(Boolean).join(" ")||"Автомобиль"));card.append(el("p","", "Пробег: "+(item.mileage!=null?Number(item.mileage).toLocaleString("ru-RU")+" км":"не указан")));card.append(el("p","", "Цена: "+money(item.price)));card.append(el("p","","Источник: "+(item.source_name||item.data_source||"XAPI Korea")));link(card,item.listing_url,"Открыть объявление ↗");grid.append(card)});out.append(grid);
   out.append(el("p","smart-search-warning",search.disclaimer||"Это текущие объявления, а не завершённые торги. Наличие и цену подтвердите у продавца."));
 }else if(country==="japan"&&Array.isArray(search.search_links)){
   const grid=el("div","smart-search-result-grid");
   search.search_links.forEach(item=>{const card=el("article","smart-search-card");card.append(el("span","smart-search-badge","АРХИВ / СТАТИСТИКА ИСТОЧНИКА"));card.append(el("h3","",item.name));card.append(el("p","",item.kind||"Поиск завершённых лотов и статистики"));card.append(el("p","",item.access||"Доступ и состав данных определяет источник."));link(card,item.url,"Открыть архив и лоты ↗");grid.append(card)});out.append(grid);
   out.append(el("p","smart-search-warning","Японские источники открываются на своих сайтах. PAPAUTO пока не получает из них лицензионную ленту отдельных завершённых лотов с фотографиями и аукционными листами внутри собственного каталога."));
 }else if(country==="china"&&Array.isArray(search.records)&&search.records.length){
   const grid=el("div","smart-search-result-grid");
   search.records.forEach(item=>{const card=el("article","smart-search-card");card.append(el("span","smart-search-badge","ЗАВЕРШЁННАЯ СДЕЛКА · ИСТОРИЯ"));card.append(el("h3","",[item.make,item.model].filter(Boolean).join(" ")||"Сделка"));card.append(el("p","",[item.date,item.description].filter(Boolean).join(" · ")||"Описание не предоставлено источником"));card.append(el("p","","Источник: "+(item.source||search.source||"TTPAI")));grid.append(card)});out.append(grid);link(out,search.source_url,"Открыть данные источника ↗");
   out.append(el("p","smart-search-warning",search.disclaimer||"Исторические сделки не являются автомобилями, доступными к покупке сейчас."));
 }else{
   out.append(el("p","smart-search-warning",search.message||search.disclaimer||"По этому запросу источник не вернул карточки автомобилей. Попробуйте изменить параметры или открыть внешние архивы."));
 }
 if(Array.isArray(data.preferences_not_applied)&&data.preferences_not_applied.length){const warning=el("div","smart-search-warning","Эти пожелания пока не участвуют в технической фильтрации: "+data.preferences_not_applied.join("; ")+". Проверьте их отдельно в карточке автомобиля.");out.append(warning)}
 if(search.count===0||search.returned_count===0)status.textContent="По точным фильтрам карточки не найдены. Ниже показаны доступные архивы или пояснение по источнику.";
 else status.textContent="Запрос разобран. Источник: "+(search.source||"несколько источников")+".";
 out.hidden=false;
}
button.addEventListener("click",async()=>{const message=form.value.trim(),api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");if(message.length<3){status.textContent="Опишите автомобиль подробнее.";return}if(!api){status.textContent="API не настроен.";return}button.disabled=true;button.textContent="Подбираем…";status.textContent="ИИ переводит описание в фильтры и запрашивает доступные источники.";out.hidden=true;try{const response=await fetch(api+"/api/assistant/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message,country:$("smartSearchCountry").value,city:$("smartSearchCity").value.trim()||"Новосибирск"})});let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.detail||"Не удалось выполнить подбор.");render(data)}catch(error){status.textContent=error.message||"Ошибка подбора."}finally{button.disabled=false;button.textContent="Найти автомобили ↗"}});
})();