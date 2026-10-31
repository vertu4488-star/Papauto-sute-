(()=>{"use strict";const $=id=>document.getElementById(id),cfg=window.PAPAUTO_CONFIG||{},url=v=>{try{const u=new URL(v);return u.protocol==="https:"?u.href:""}catch{return""}};
const currencyCountry=$("currencyCountry"),currencyAmount=$("currencyAmount"),currencyAmountLabel=$("currencyAmountLabel"),currencyRubResult=$("currencyRubResult"),currencyUsdResult=$("currencyUsdResult"),currencyLocalResult=$("currencyLocalResult"),currencyLocalResultWrap=$("currencyLocalResultWrap"),currencyLocalResultLabel=$("currencyLocalResultLabel"),currencyRateNote=$("currencyRateNote");
if(currencyCountry&&currencyAmount&&currencyRubResult&&currencyUsdResult&&currencyRateNote){
  let currencyRates=null;
  const currencyModes={
    "south-korea":{name:"корейских вонах",symbol:"₩",step:"10000",initial:"21400000",perLocal:"rub_per_1000_krw",localScale:1000,usdPer:"usd_per_1000_krw",usdScale:1000,localDisplay:"KRW"},
    "japan":{name:"японских иенах",symbol:"¥",step:"10000",initial:"1500000",perLocal:"rub_per_jpy",localScale:1,usdPer:"usd_per_jpy",usdScale:1,localDisplay:"JPY"},
    "china":{name:"китайских юанях",symbol:"元",step:"1000",initial:"100000",perLocal:"rub_per_cny",localScale:1,usdPer:"usd_per_cny",usdScale:1,localDisplay:"CNY"}
  };
  const fmtMoney=(value,currency)=>new Intl.NumberFormat("ru-RU",{style:"currency",currency,maximumFractionDigits:currency==="USD"?2:0}).format(value);
  const mode=()=>currencyModes[currencyCountry.value]||currencyModes["south-korea"];
  const renderCurrency=()=>{
    const m=mode(),amount=Number(currencyAmount.value);
    if(!currencyRates||!Number.isFinite(amount)||amount<0){currencyRubResult.textContent="—";currencyUsdResult.textContent="—";return}
    currencyRubResult.textContent=fmtMoney(amount*Number(currencyRates[m.perLocal])/m.localScale,"RUB");
    currencyUsdResult.textContent=fmtMoney(amount*Number(currencyRates[m.usdPer])/m.usdScale,"USD");
    currencyLocalResultWrap.hidden=false;currencyLocalResultLabel.textContent="В "+(currencyCountry.value==="japan"?"японских иенах":currencyCountry.value==="china"?"китайских юанях":"корейских вонах");currencyLocalResult.textContent=fmtMoney(amount,m.localDisplay);
  };
  const updateCurrencyMode=(resetAmount)=>{
    const m=mode();
    currencyAmountLabel.childNodes[0].textContent="Цена в "+m.name+" ("+m.symbol+")";
    currencyAmount.step=m.step;
    if(resetAmount)currencyAmount.value=m.initial;
    renderCurrency();
  };
  currencyCountry.addEventListener("change",()=>updateCurrencyMode(true));
  currencyAmount.addEventListener("input",renderCurrency);
  (async()=>{
    try{
      const api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");
      if(!api)throw new Error("API не настроен");
      const response=await fetch(api+"/api/exchange-rates",{headers:{Accept:"application/json"}});
      if(!response.ok)throw new Error("Курс временно недоступен");
      const rates=await response.json();
      const needed=["rub_per_1000_krw","rub_per_jpy","rub_per_cny","rub_per_usd","usd_per_1000_krw","usd_per_jpy","usd_per_cny"];
      if(!needed.every(k=>Number.isFinite(Number(rates[k]))&&Number(rates[k])>0))throw new Error("Некорректный курс");
      currencyRates=rates;
      const date=rates.date?(" на "+rates.date):"";
      currencyRateNote.textContent="Источник: "+(rates.source||"Банк России")+date+". Курсы справочные, не курс продажи банка."+(rates.fallback?" Используется последний сохранённый ориентир, так как источник временно недоступен.":"");
      updateCurrencyMode(false);
    }catch(error){
      currencyRubResult.textContent="Курс недоступен";
      currencyUsdResult.textContent="Курс недоступен";
      currencyRateNote.textContent="Не удалось загрузить курс Банка России. Обновите страницу позже; конвертер не использует выдуманный текущий курс.";
    }
  })();
}
document.querySelectorAll("[data-integration]").forEach(a=>{const u=url(cfg[a.dataset.integration]);if(u){a.href=u;a.hidden=false;a.target="_blank";a.rel="noopener noreferrer"}});const social=document.querySelector("[data-social-links]");if(social){social.replaceChildren();const items=[["telegramChannelUrl","Telegram-канал"],["vkUrl","ВКонтакте"],["instagramUrl","Instagram"],["youtubeUrl","YouTube"]].map(([k,label])=>({label,url:url(cfg[k])})).filter(x=>x.url);if(items.length)items.forEach(x=>{const a=document.createElement("a");a.href=x.url;a.textContent=x.label;a.target="_blank";a.rel="noopener noreferrer";social.append(a)});else{const s=document.createElement("span");s.className="social-pending";s.textContent="Официальные ссылки будут добавлены после настройки каналов";social.append(s)}}const mb=document.querySelector(".menu-toggle"),nav=document.querySelector(".main-nav");if(mb&&nav)mb.addEventListener("click",()=>{const open=nav.classList.toggle("open");mb.setAttribute("aria-expanded",String(open))});document.querySelectorAll("[data-budget-shortcut]").forEach(button=>button.addEventListener("click",()=>{const budget=$("budget");if(budget)budget.value=button.dataset.budgetShortcut||"";const prompt=$("carPrompt");if(prompt&&!prompt.value.trim())prompt.value="Подберите реальные варианты в рамках бюджета до "+new Intl.NumberFormat("ru-RU").format(Number(button.dataset.budgetShortcut||0))+" ₽. Сравните стоимость доставки и оформления до Новосибирска.";const assistant=$("assistant");if(assistant)assistant.scrollIntoView({behavior:"smooth",block:"start"});const status=$("aiSelectStatus");if(status)status.textContent="Бюджет перенесён в PAPAUTO SELECT. Результаты будут рекомендательными, пока источник не подтвердит конкретные объявления.";if(prompt)setTimeout(()=>prompt.focus({preventScroll:true}),350)}));document.querySelectorAll("[data-market-shortcut]").forEach(button=>button.addEventListener("click",()=>{const market=button.dataset.marketShortcut||"japan";const selector=$("country");if(selector)selector.value=market;const catalogCountry=$("vehicleCountry");if(catalogCountry)catalogCountry.value=market;const prompt=$("carPrompt");const labels={"japan":"Япония","south-korea":"Южная Корея","china":"Китай"};if(prompt&&!prompt.value.trim())prompt.value="Подберите автомобиль из направления: "+(labels[market]||market)+". Нужны актуальные предложения и расчёт до Новосибирска.";const assistant=$("assistant");if(assistant)assistant.scrollIntoView({behavior:"smooth",block:"start"});if(prompt)setTimeout(()=>prompt.focus({preventScroll:true}),350)}));const year=$("year");if(year)year.textContent=new Date().getFullYear();const money=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(n)+" ₽";const calc=$("calcForm");if(calc)calc.addEventListener("submit",e=>{e.preventDefault();const fields=[["carCost","Автомобиль"],["auctionFee","Аукционная / дилерская комиссия"],["originDelivery","Доставка по стране покупки"],["exportDocs","Экспортные документы и порт"],["insurance","Страхование и хранение"],["shipping","Доставка до России"],["customs","Таможня и сборы"],["paperwork","Оформление"],["localDelivery","Доставка до Новосибирска"],["fee","Услуги компании"],["otherCosts","Другие расходы"]];let total=0,count=0;const out=$("resultLines");out.replaceChildren();fields.forEach(([id,label])=>{const input=$(id);if(!input||input.value.trim()==="")return;const n=Number(input.value);if(!Number.isFinite(n)||n<0)return;total+=n;count++;const row=document.createElement("div"),s=document.createElement("span"),b=document.createElement("b");s.textContent=label;b.textContent=money(n);row.append(s,b);out.append(row)});$("resultTotal").textContent=count?money(total):"— ₽";$("resultNote").textContent=count?"Направление: "+$("calcCountry").value+". Учтено статей: "+count+" из "+fields.length+". Неуказанные расходы не включены; уточните актуальные платежи перед сделкой.":"Заполните известные суммы — пустые статьи не учитываются.";const ref=Number($("marketReferencePrice")?.value||0),compare=$("marketComparison");if(compare){if(ref>0&&count){const diff=ref-total;compare.textContent="Разница с указанной ценой аналога в России: "+money(Math.abs(diff))+(diff>=0?" ниже российского предложения по заполненным статьям":" выше российского предложения по заполненным статьям")+". Сравнение предварительное: "+count+" из "+fields.length+" статей заполнено, остальные расходы не учтены."}else compare.textContent="Введите цену российского аналога, чтобы сравнить её с суммой заполненных расходов. Это не автоматическая рыночная оценка."}});const carrierButton=$("fillCarrierTariff");if(carrierButton)carrierButton.addEventListener("click",()=>{const field=$("localDelivery"),amount=Number($("carrierClass").value);if(field){field.value=String(amount);$("resultNote").textContent="Тариф автовоза подставлен как опубликованный ориентир; перед оплатой подтвердите цену у перевозчика.";calc?.dispatchEvent(new Event("submit",{cancelable:true,bubbles:true}))}});const copy=$("copyEstimate");if(copy)copy.addEventListener("click",async()=>{const t=["Предварительная смета PAPAUTO","Направление: "+$("calcCountry").value,...Array.from(document.querySelectorAll("#resultLines > div")).map(x=>x.innerText.replace(/\n/g,": ")),"Итого: "+$("resultTotal").textContent,$("resultNote").textContent,$("marketComparison")?.textContent].filter(Boolean).join("\n");try{await navigator.clipboard.writeText(t);copy.textContent="Смета скопирована"}catch{copy.textContent="Не удалось скопировать"}setTimeout(()=>copy.textContent="Скопировать смету",2200)});const exportEstimate=$("exportEstimate");
if(exportEstimate)exportEstimate.addEventListener("click",()=>{
 const rows=[["Показатель","Значение"],["Дата",new Date().toLocaleString("ru-RU")],["Направление",$("calcCountry").value]];
 document.querySelectorAll("#resultLines > div").forEach(row=>{const cells=row.querySelectorAll("span,b");if(cells.length===2)rows.push([cells[0].textContent,cells[1].textContent])});
 rows.push(["Сумма заполненных статей",$("resultTotal").textContent],["Цена аналога в России",$("marketReferencePrice")?.value||"не указана"],["Сравнение",$("marketComparison")?.textContent||""],["Ограничения",$("resultNote").textContent]);
 const csv=String.fromCharCode(65279)+rows.map(row=>row.map(value=>{let cell=String(value??"");if(/^[=+@-]/.test(cell))cell="'"+cell;return '"'+cell.replace(/"/g,'""')+'"'}).join(";")).join(String.fromCharCode(13,10));
 const blob=new Blob([csv],{type:"text/csv;charset=utf-8"}),url=URL.createObjectURL(blob),link=document.createElement("a");
 link.href=url;link.download="papauto-estimate-"+new Date().toISOString().slice(0,10)+".csv";document.body.append(link);link.click();link.remove();URL.revokeObjectURL(url);
});
const printEstimate=$("printEstimate");if(printEstimate)printEstimate.addEventListener("click",()=>window.print());
const vehicleForm=$("vehicleSearchForm");if(vehicleForm)vehicleForm.addEventListener("submit",async e=>{e.preventDefault();const status=$("vehicleSearchStatus"),out=$("vehicleSearchResults"),button=$("vehicleSearchButton"),api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");if(!api){status.textContent="Серверный API не настроен.";return}const from=Number($("vehicleYearFrom").value),to=Number($("vehicleYearTo").value);if(from>to){status.textContent="Год выпуска «от» не может быть больше года «до».";return}const p=new URLSearchParams({country:$("vehicleCountry").value,make:$("vehicleMake").value.trim(),model:$("vehicleModel").value.trim(),year_from:String(from),year_to:String(to),max_price:$("vehicleMaxPrice").value||"0",body:$("vehicleBody")?.value.trim()||"",grade:$("vehicleGrade")?.value.trim()||"",lot_number:$("vehicleLot")?.value.trim()||"",limit:"20"});for(const [key,id] of [["mileage_max","vehicleMileageMax"],["volume_min","vehicleVolumeMin"],["volume_max","vehicleVolumeMax"]]){const value=$(id)?.value.trim();if(value!==" "&&value!==undefined&&value!==null&&value!=="")p.set(key,value)}button.disabled=true;button.textContent="Ищем…";status.textContent="Проверяем открытые источники…";out.hidden=true;try{const r=await fetch(api+"/api/vehicles?"+p.toString());let data={};try{data=await r.json()}catch{}if(!r.ok)throw new Error(data.detail||"Не удалось загрузить предложения.");if(data.data_type==="historical_transactions"){out.replaceChildren();const heading=document.createElement("h3");heading.textContent="История сделок · "+(data.model||"Китайский рынок");out.append(heading);const note=document.createElement("p");note.textContent="Город: "+(data.city||"указан источником")+". Ниже завершённые сделки TTPAI, а не автомобили, доступные сейчас к покупке.";out.append(note);(Array.isArray(data.records)?data.records:[]).forEach(item=>{const card=document.createElement("article");card.className="vehicle-result-card";const title=document.createElement("h4");title.textContent=[item.date,item.description].filter(Boolean).join(" · ")||"Историческая сделка";card.append(title);const meta=document.createElement("p");meta.className="vehicle-result-meta";meta.textContent="Источник: TTPAI · "+(item.city||data.city||"Китай");card.append(meta);out.append(card)});if(data.source_url){const link=document.createElement("a");link.href=data.source_url;link.target="_blank";link.rel="noopener noreferrer";link.textContent="Открыть историю TTPAI ↗";out.append(link)}const disclaimer=document.createElement("p");disclaimer.className="auction-disclaimer";disclaimer.textContent=data.disclaimer||"Исторические сделки не являются активными объявлениями.";out.append(disclaimer);out.hidden=false;status.textContent="Получено исторических сделок: "+(data.count||0)+". Это не список доступных к покупке автомобилей.";return}if(data.data_type==="external_search"&&Array.isArray(data.search_links)){out.replaceChildren();const heading=document.createElement("h3");heading.textContent="Поиск по японским источникам";out.append(heading);const note=document.createElement("p");note.textContent=data.message||"Откройте архивы с уже заданной маркой, моделью и диапазоном годов.";out.append(note);data.search_links.forEach(source=>{const card=document.createElement("article");card.className="vehicle-result-card";const title=document.createElement("h4");title.textContent=source.name||"Источник";card.append(title);const detail=document.createElement("p");detail.textContent=[source.kind,source.access].filter(Boolean).join(" · ");card.append(detail);const link=document.createElement("a");link.href=String(source.url||"");link.target="_blank";link.rel="noopener noreferrer";link.textContent="Открыть поиск в источнике ↗";card.append(link);out.append(card)});out.hidden=false;status.textContent="Поиск подготовлен по выбранной модели. Источники откроются в новых вкладках; результаты и ограничения доступа показываются на их сайтах.";return}if(data.data_type==="source_hub"&&Array.isArray(data.sources)){out.replaceChildren();const heading=document.createElement("h3");heading.textContent="Статистика рынка · "+(data.source||"Южная Корея");out.append(heading);const note=document.createElement("p");note.textContent=data.message||"Это агрегированные данные рынка, а не карточки доступных автомобилей.";out.append(note);data.sources.forEach(source=>{const card=document.createElement("article");card.className="vehicle-result-card";const title=document.createElement("h4");title.textContent=source.name||"Источник статистики";card.append(title);const detail=document.createElement("p");detail.textContent=[source.data_kind,source.note].filter(Boolean).join(" · ");card.append(detail);const link=document.createElement("a");link.href=String(source.url||"");link.target="_blank";link.rel="noopener noreferrer";link.textContent="Открыть источник статистики ↗";card.append(link);out.append(card)});const disclaimer=document.createElement("p");disclaimer.className="auction-disclaimer";disclaimer.textContent=data.disclaimer||"Агрегированная статистика не является актуальным каталогом автомобилей.";out.append(disclaimer);const request=document.createElement("button");request.type="button";request.className="button button-primary";request.textContent="Запросить актуальный подбор";request.addEventListener("click",()=>{const prompt=$("carPrompt");if(prompt){prompt.value="Нужен актуальный автомобиль из Южной Кореи. "+[$("vehicleMake").value.trim(),$("vehicleModel").value.trim()].filter(Boolean).join(" ")+"; годы "+$("vehicleYearFrom").value+"–"+$("vehicleYearTo").value+". Бюджет до "+($("vehicleMaxPrice").value||"не указан")+" ₽. Прошу проверить действующие объявления и рассчитать доставку до Новосибирска."; $("assistant").scrollIntoView({behavior:"smooth",block:"center"});prompt.focus()}});out.append(request);out.hidden=false;status.textContent="Показаны открытые источники. Актуальные объявления проверяются непосредственно на сайтах площадок.";return}const raw=data.results;const rows=Array.isArray(raw)?raw:(raw&&Array.isArray(raw.results)?raw.results:(raw&&Array.isArray(raw.items)?raw.items:(raw&&Array.isArray(raw.data)?raw.data:null)));out.replaceChildren();if(rows&&rows.length){rows.slice(0,50).forEach((item,i)=>{const card=document.createElement("article");card.className="vehicle-result-card";const title=document.createElement("h3");title.textContent=[item.make||item.brand,item.model,item.year||item.year_from].filter(Boolean).join(" ")||("Предложение "+(i+1));card.append(title);card.dataset.vehicleKey=String(item.id||item.listing_url||[item.make,item.model,item.year].filter(Boolean).join("-")||("result-"+i));const carPayload={id:card.dataset.vehicleKey,make:item.make||item.brand||"",model:item.model||"",year:item.year||item.year_from||"",mileage:item.mileage??item.mileage_km??null,volume_cc:item.volume_cc??null,price:item.price||item.price_krw||item.price_rub||"",currency:item.currency||"",source:item.source_name||item.source||item.data_source||"",listing_url:item.listing_url||""};const photos=Array.isArray(item.photos)?item.photos.filter(p=>typeof p==="string"&&/^https:\/\//i.test(p)):[];if(!photos.length&&typeof item.thumbnail==="string"&&/^https:\/\//i.test(item.thumbnail))photos.push(item.thumbnail);if(photos.length){const gallery=document.createElement("div");gallery.className="vehicle-result-gallery";gallery.style.display="grid";gallery.style.gridTemplateColumns="repeat(auto-fit,minmax(120px,1fr))";gallery.style.gap="8px";photos.slice(0,5).forEach((photo,index)=>{const img=document.createElement("img");img.src=photo;img.alt=title.textContent+" — фото "+(index+1);img.loading="lazy";img.referrerPolicy="no-referrer";img.style.width="100%";img.style.height=index===0?"210px":"130px";img.style.objectFit="cover";img.style.borderRadius="12px";img.onerror=()=>{img.style.display="none"};gallery.append(img)});card.append(gallery)}else{const noPhoto=document.createElement("p");noPhoto.className="vehicle-result-meta";noPhoto.textContent="Фотографии не переданы исходной площадкой для этого объявления.";card.append(noPhoto)}const meta=document.createElement("p");meta.className="vehicle-result-meta";meta.textContent=[item.source_name||item.source||item.data_source?"Источник: "+(item.source_name||item.source||item.data_source):"",item.listing_date?("Объявление: "+String(item.listing_date).slice(0,10)):"Актуальное объявление",item.mileage!==undefined&&item.mileage!==null?("Пробег: "+new Intl.NumberFormat("ru-RU").format(Number(item.mileage))+" км"):"",item.volume_cc?("Объём: "+new Intl.NumberFormat("ru-RU").format(Number(item.volume_cc))+" см³"):"",item.grade?("Оценка: "+item.grade):"",item.lot_number||item.lot?("Лот: "+(item.lot_number||item.lot)):""].filter(Boolean).join(" · ")||"Характеристики уточняются у поставщика";card.append(meta);const price=document.createElement("strong");const priceRub=item.price_rub??item.priceRub??item.total_price_rub;if(priceRub!==undefined&&priceRub!==null&&priceRub!=="")price.textContent=typeof priceRub==="number"?money(priceRub):String(priceRub);else if(item.price_krw!==undefined&&item.price_krw!==null&&Number.isFinite(Number(item.price_krw)))price.textContent=new Intl.NumberFormat("ru-RU").format(Number(item.price_krw))+" ₩ — цена в Корее, без доставки и оформления в РФ";else if(item.price!==undefined&&item.price!==null&&item.price!=="")price.textContent=String(item.price);else price.textContent="Цена уточняется";card.append(price);const note=document.createElement("p");note.textContent="Наличие, состояние и цену нужно повторно подтвердить у исходной площадки. Цена в Корее не включает доставку и оформление в России.";card.append(note);if(item.listing_url&&/^https?:\/\//i.test(item.listing_url)){const link=document.createElement("a");link.href=item.listing_url;link.target="_blank";link.rel="noopener noreferrer";link.textContent="Открыть исходное объявление ↗";card.append(link)}const actions=document.createElement("div");actions.className="vehicle-card-actions";const save=document.createElement("button");save.type="button";save.className="vehicle-save-button";save.dataset.saveVehicle="";save.dataset.car=JSON.stringify(carPayload);save.textContent="♡ В избранное";const compare=document.createElement("button");compare.type="button";compare.className="vehicle-compare-button";compare.dataset.compareVehicle="";compare.dataset.car=JSON.stringify(carPayload);compare.textContent="Сравнить";actions.append(save,compare);card.append(actions);out.append(card)});status.textContent="Получено актуальных объявлений: "+rows.length+". Источник: "+(data.source||"поставщик данных")+". Актуальность лота и итоговую стоимость необходимо подтвердить."+(data.partial?" Часть источников не ответила.":"")+(data.budget_note?" "+data.budget_note:"")}else{out.textContent=JSON.stringify(raw,null,2);status.textContent="По заданным параметрам активных объявлений не найдено. Попробуйте изменить марку, модель или диапазон годов."}out.hidden=false;}catch(err){status.textContent=err.message||"Ошибка поиска"}finally{button.disabled=false;button.textContent="Найти автомобили"}});
const aiSend=$("vehicleAiSend");
if(aiSend)aiSend.addEventListener("click",()=>{
 const status=$("vehicleAiStatus"),message=$("vehicleAiMessage").value.trim();
 if(!message){status.textContent="Введите описание автомобиля, цену и известные характеристики.";return}
 const t=message.toLowerCase().replace(/ё/g,"е"),found=[];
 const set=(id,value,label)=>{const el=$(id);if(el&&value!==null&&value!==undefined&&value!==""){el.value=String(value);found.push(label+" — "+value)}};
 const price=t.match(/(\d[\d\s.,]*)\s*(млн|миллион(?:а|ов)?|тыс(?:яч|ячи)?|тысяч)?\s*(иен|йен|jpy|¥|вон|krw|₩|юан(?:ей|я)?|cny|руб(?:лей|ля)?|₽)/i);
 if(price){
  let amount=Number(price[1].replace(/[\s\u00a0]/g,"").replace(",","."));
  if(/млн|миллион/i.test(price[2]||""))amount*=1000000;else if(/тыс/i.test(price[2]||""))amount*=1000;
  const cur=/иен|йен|jpy|¥/i.test(price[3])?"392":/вон|krw|₩/i.test(price[3])?"410":/юан|cny/i.test(price[3])?"156":"643";
  set("tksCost",Math.round(amount),"Цена");$("tksCurrency").value=cur;found.push("Валюта — "+({392:"JPY",410:"KRW",156:"CNY",643:"RUB"}[cur]));
 }
 const cc=t.match(/(\d{3,5})\s*(?:см\s*[³3]|куб(?:ических)?\s*см)/i)||t.match(/(\d(?:[.,]\d+)?)\s*(?:л(?:итр(?:а|ов)?)?)(?![а-я])/i);
 if(cc){const n=Number(cc[1].replace(",", "."));set("tksVolume",Math.round(n*(cc[0].includes("см")?1:1000)),"Объём, см³")}
 const hp=t.match(/(\d{2,4})\s*(?:л\.?\s*с\.?|лошад(?:и|ей)?\s*сил)/i);
 if(hp)set("tksPower",Number(hp[1]),"Мощность, л.с.");
 if(/электро|\bev\b/.test(t)){$("tksEngine").value="electric";found.push("Тип двигателя — электромобиль")}
 else if(/дизел/.test(t)){$("tksEngine").value="diesel";found.push("Тип двигателя — дизель")}
 else if(/гибрид/.test(t)){$("tksEngine").value=/дизел/.test(t)?"diesel_electric":"petrol_electric";found.push("Тип двигателя — гибрид")}
 else if(/бензин/.test(t)){$("tksEngine").value="petrol";found.push("Тип двигателя — бензин")}
 if(/юрлиц|компан|организац|на фирм/.test(t)){$("tksFace").value="jur";found.push("Импортёр — юридическое лицо")}
 else if(/физлиц|для себя|личн(?:ый|ого) ввоз/.test(t)){$("tksFace").value="nat";found.push("Импортёр — физическое лицо")}
 const prompt=$("carPrompt");
 if(prompt){const line="Данные из локального разбора: "+message;if(!prompt.value.includes(line))prompt.value=(prompt.value.trim()?prompt.value.trim()+"\n":"")+line}
 status.textContent=found.length?"Локально выделено (без отправки данных на сервер): "+found.join("; ")+". Возрастную категорию и неизвестные параметры проверьте вручную. Автоматический платный расчёт отключён.":"Не удалось надёжно выделить числовые параметры. Заполните поля вручную; запрос никуда не отправлялся.";
});
const tksButton=$("runTks");
if(tksButton)tksButton.addEventListener("click",()=>{
 const status=$("tksStatus");
 if(status)status.textContent="TKS.RU отключён в бесплатном режиме. Никакой запрос и никакое списание не выполняются. Введите подтверждённую сумму в общую смету вручную.";
});
const aiSelectButton=$("runAiSelect");
if(aiSelectButton)aiSelectButton.addEventListener("click",async()=>{
 const status=$("aiSelectStatus"),out=$("aiSelectResults"),api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");
 if(!api){status.textContent="Серверный API не настроен.";return}
 const message=[$("carMake").value.trim(),$("carModel").value.trim(),$("yearFrom").value&&$("yearTo").value?$("yearFrom").value+"–"+$("yearTo").value:"",$("maxMileage").value?"пробег до "+$("maxMileage").value+" км":"",$("carPrompt").value.trim()].filter(Boolean).join(" ");
 if(message.length<5){status.textContent="Опишите автомобиль или заполните марку и модель.";$("carPrompt").focus();return}
 const label=$("country").value.toLowerCase();
 const country=label.includes("коре")?"south-korea":label.includes("кита")?"china":"japan";
 aiSelectButton.disabled=true;aiSelectButton.textContent="Подбираю бесплатно…";
 status.textContent="Разбираю запрос локально, без платного ИИ-сервиса…";out.hidden=true;
 try{
  const response=await fetch(api+"/api/assistant/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message,country,city:$("city").value.trim()||"Новосибирск"})});
  const data=await response.json().catch(()=>({}));
  if(!response.ok)throw new Error(data.detail||"Не удалось разобрать запрос.");
  const f=data.filters||{};
  const set=(id,value)=>{const el=$(id);if(el&&value!==undefined&&value!==null&&value!=="")el.value=String(value)};
  set("vehicleCountry",f.country);set("vehicleMake",f.make);set("vehicleModel",f.model);
  set("vehicleYearFrom",f.year_from);set("vehicleYearTo",f.year_to);
  set("vehicleMileageMax",f.mileage_max);set("vehicleVolumeMin",f.volume_min);set("vehicleVolumeMax",f.volume_max);
  set("vehicleBody",f.body);set("vehicleGrade",f.grade);set("vehicleLot",f.lot_number);
  const summary=document.createElement("p");summary.className="ai-select-summary";
  summary.textContent="Запрос разобран бесплатно на устройстве сервера. "+[f.make,f.model,f.year_from&&f.year_to?f.year_from+"–"+f.year_to:""].filter(Boolean).join(" · ");
  out.replaceChildren(summary);
  const note=document.createElement("p");note.className="ai-select-disclaimer";
  note.textContent="Поиск использует доступные открытые источники. Бюджет, тип привода и коробка не применяются как фильтры, если источник их не предоставляет.";
  out.append(note);
   try{
    const budgetValue=Number($("budget").value||0);
    const selectionResponse=await fetch(api+"/api/assistant/select",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
     message,country,budget:budgetValue>0?budgetValue:null,city:$("city").value.trim()||"Новосибирск",
     make:$("carMake").value.trim()||f.make||"",model:$("carModel").value.trim()||f.model||"",
     year_from:$("yearFrom").value?Number($("yearFrom").value):(f.year_from>1990&&f.year_from<=2027?f.year_from:null),
     year_to:$("yearTo").value?Number($("yearTo").value):(f.year_to<2030&&f.year_to<=2027?f.year_to:null),
     mileage_max:$("maxMileage").value?Number($("maxMileage").value):(f.mileage_max||null)
    })});
    const shortlist=await selectionResponse.json().catch(()=>({}));
    if(selectionResponse.ok&&Array.isArray(shortlist.recommendations)){
     const heading=document.createElement("h3");heading.className="ai-select-summary";heading.textContent=shortlist.summary||"Предварительные рекомендации PAPAUTO";out.append(heading);
     shortlist.recommendations.forEach(item=>{
      const card=document.createElement("article");card.className="ai-select-card";
      const title=document.createElement("h3");title.textContent=[item.make,item.model].filter(Boolean).join(" ");
      const why=document.createElement("p");why.textContent=item.why||"Подходит для дальнейшего рассмотрения.";
      const checks=document.createElement("p");checks.textContent="Что проверить: "+(item.checks||"комплектацию и состояние конкретного автомобиля.");
      const market=document.createElement("small");market.textContent="Рынки: "+(Array.isArray(item.markets)?item.markets.join(", "):"уточняются")+" · актуальные лоты не подтверждены";
      card.append(title,why,checks,market);out.append(card);
     });
     if(Array.isArray(shortlist.questions)&&shortlist.questions.length){
      const questions=document.createElement("p");questions.className="ai-select-disclaimer";questions.textContent="Чтобы уточнить подбор: "+shortlist.questions.join(" ");
      out.append(questions);
     }
     if(shortlist.disclaimer){const disclaimer=document.createElement("p");disclaimer.className="ai-select-disclaimer";disclaimer.textContent=shortlist.disclaimer;out.append(disclaimer)}
    }
   }catch(shortlistError){
    const fallback=document.createElement("p");fallback.className="ai-select-disclaimer";fallback.textContent="Справочный список моделей временно недоступен; параметры поиска сохранены.";
    out.append(fallback);
   }
   out.hidden=false;
  status.textContent="Параметры перенесены в каталог. Выполняю бесплатный поиск…";
  const form=$("vehicleSearchForm");if(form)form.requestSubmit();else status.textContent="Параметры готовы. Перейдите в каталог и нажмите «Найти автомобили».";
 }catch(error){status.textContent=error.message||"Ошибка бесплатного подбора."}
 finally{aiSelectButton.disabled=false;aiSelectButton.textContent="Подобрать бесплатно ↗"}
});
const form=$("assistantForm");let preparedLead=null;if(form)form.addEventListener("submit",e=>{e.preventDefault();const p=$("carPrompt").value.trim();if(!p){$("carPrompt").focus();return}const country=$("country").value;const budget=$("budget").value.trim();const city=$("city").value.trim()||"Новосибирск";const contact=$("contact").value.trim();const name=$("leadName")?.value.trim()||"";const make=$("carMake").value.trim();const model=$("carModel").value.trim();const yearFrom=$("yearFrom").value.trim();const yearTo=$("yearTo").value.trim();const mileage=$("maxMileage").value.trim();const listingUrl=$("carListingUrl")?.value.trim()||"";if(listingUrl&&!/^https?:\/\//i.test(listingUrl)){$("copyStatus").textContent="Ссылка на автомобиль должна начинаться с http:// или https://.";$("carListingUrl").focus();return}if(yearFrom&&yearTo&&Number(yearFrom)>Number(yearTo)){$("copyStatus").textContent="Год «от» не может быть больше года «до».";return}const lines=["Заявка на подбор автомобиля — PAPAUTO","Направление: "+country,"Марка: "+(make||"не указана"),"Модель: "+(model||"не указана"),"Год выпуска: "+(yearFrom||"не указан")+" — "+(yearTo||"не указан"),"Максимальный пробег: "+(mileage?new Intl.NumberFormat("ru-RU").format(Number(mileage))+" км":"не указан"),"Бюджет: "+(budget?money(Number(budget)):"не указан"),"Город получения: "+city,"Дополнительные пожелания: "+p];if(listingUrl)lines.push("Ссылка на выбранный автомобиль/лот: "+listingUrl);if(name)lines.push("Имя: "+name);lines.push("Контакт для ответа: "+contact,"Просьба: подобрать доступные варианты и подготовить предварительную смету с учётом доставки и оформления.");$("requestText").value=lines.join("\n");$("requestOutput").hidden=false;preparedLead={name,contact,country,budget:budget?Number(budget):null,city,request:lines.slice(1,listingUrl?10:9).join("\n")+(name?"\nИмя: "+name:""),consent:$("leadConsent")?.checked===true,website:$("website")?.value.trim()||""};window.dispatchEvent(new CustomEvent("papauto:lead-prepared",{detail:{...preparedLead,make,model,yearFrom,yearTo}}));$("copyStatus").textContent="";$("sendRequest").disabled=false;$("sendRequest").textContent="Отправить менеджеру ↗"});const send=$("sendRequest");if(send)send.addEventListener("click",async()=>{if(!preparedLead){$("copyStatus").textContent="Сначала заполните заявку и нажмите «Подготовить заявку».";return}if(!preparedLead.contact){$("copyStatus").textContent="Укажите телефон или Telegram для ответа."; $("contact").focus();return}if(!$("leadConsent")?.checked){$("copyStatus").textContent="Необходимо согласие на обработку данных.";return}if(!cfg.apiBaseUrl){$("copyStatus").textContent="Автоматическая отправка ещё не настроена. Скопируйте заявку.";return}send.disabled=true;send.textContent="Отправляем…";try{const response=await fetch(url(cfg.apiBaseUrl.replace(/\/$/,"")+"/api/leads"),{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(preparedLead)});let data={};try{data=await response.json()}catch{}if(!response.ok)throw new Error(data.detail||"Не удалось отправить заявку.");$("copyStatus").textContent=data.message||"Заявка отправлена менеджеру." ;send.textContent="Заявка отправлена";;window.dispatchEvent(new CustomEvent("papauto:lead-submitted",{detail:{...preparedLead,make:$("carMake").value.trim(),model:$("carModel").value.trim(),yearFrom:$("yearFrom").value.trim(),yearTo:$("yearTo").value.trim(),mileage:$("maxMileage").value.trim()}}));}catch(err){$("copyStatus").textContent=(err.message||"Ошибка отправки")+". Заявка сохранена в локальной истории; можно отправить её через Telegram вручную.";const share=document.createElement("a");share.className="button button-secondary";share.href="https://t.me/share/url?url="+encodeURIComponent("https://papauto.ru/")+"&text="+encodeURIComponent($("requestText").value);share.target="_blank";share.rel="noopener noreferrer";share.textContent="Отправить через Telegram ↗";$("copyStatus").append(document.createTextNode(" "),share);send.textContent="Повторить отправку";send.disabled=false}});document.querySelectorAll("[data-car-request]").forEach(link=>link.addEventListener("click",()=>{const prompt=$("carPrompt");if(prompt){prompt.value=link.getAttribute("data-car-request")||"";prompt.focus();}}));const cr=$("copyRequest");if(cr)cr.addEventListener("click",async()=>{try{await navigator.clipboard.writeText($("requestText").value);$("copyStatus").textContent="Заявка скопирована"}catch{$("requestText").select();$("copyStatus").textContent="Выделите текст и скопируйте вручную"}})
const auctionStatsForm=$("auctionStatsForm");
if(auctionStatsForm){
 const out=$("auctionStatsResults"),submit=$("auctionStatsSubmit"),country=$("auctionCountry"),gradeWrap=$("auctionGradeWrap");
 const fmt=(v,c)=>Number.isFinite(Number(v))?new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(Number(v))+" "+(c==="KRW"?"₩":c==="JPY"?"¥":"元"):"—";
 const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!==undefined)n.textContent=txt;return n};

 const overview=$("auctionMarketOverview");
 if(overview){
  const loadOverview=async()=>{
   const api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");
   if(!api){overview.textContent="Официальная сводка USS пока недоступна: сервер данных не настроен.";return}
   try{
    const response=await fetch(api+"/api/market-overview",{headers:{Accept:"application/json"}});
    const data=await response.json();
    if(!response.ok||!data.available||!data.metrics)throw new Error(data.message||"Официальная сводка временно недоступна.");
    const m=data.metrics,grid=el("div","uss-metric-grid");
    const moneyYen=new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(m.average_sold_price_jpy)+" ¥";
    [[ "Выставлено",new Intl.NumberFormat("ru-RU").format(m.offered) ],["Продано",new Intl.NumberFormat("ru-RU").format(m.sold)],["Доля продаж",String(m.contract_rate_percent).replace(".",",")+"%"],["Средняя цена продажи",moneyYen]].forEach(([label,value])=>{const card=el("div","uss-metric");card.append(el("small","",label),el("strong","",value));grid.append(card)});
    overview.replaceChildren();
    const head=el("div","uss-overview-head"),copy=el("div",""),eyebrow=el("span","eyebrow","ОТКРЫТЫЕ ДАННЫЕ · ЯПОНИЯ"),title=el("h3","","Последняя сводка аукционов USS"),pill=el("span","uss-live-label","Источник отвечает");
    copy.append(eyebrow,title);head.append(copy,pill);overview.append(head,grid);
    overview.append(el("p","uss-overview-note","Последний опубликованный месяц: "+m.month+". Получено "+new Date(data.retrieved_at).toLocaleString("ru-RU")+". Это общая статистика USS, а не цена конкретной модели."));
    const link=el("a","uss-source-link","Открыть первоисточник ↗");link.href=data.source_url;link.target="_blank";link.rel="noopener noreferrer";overview.append(link);
    const history=Array.isArray(data.history)?data.history:[];
    if(history.length){
     const section=el("div","uss-history"),historyTitle=el("h4","","Динамика по месяцам");
     section.append(historyTitle);
     const maxPrice=Math.max(1,...history.map(item=>Number(item.average_sold_price_jpy)||0));
     history.forEach(item=>{
      const row=el("div","uss-history-row"),month=el("span","uss-history-month",item.month);
      const track=el("div","uss-history-track"),bar=el("div","uss-history-bar");
      bar.style.width=Math.max(3,Math.round((Number(item.average_sold_price_jpy)||0)/maxPrice*100))+"%";
      track.append(bar);
      const price=new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(item.average_sold_price_jpy||0)+" ¥";
      const sold=new Intl.NumberFormat("ru-RU").format(item.sold||0);
      const meta=el("small","uss-history-meta",price+" · продано "+sold+" · доля продаж "+String(item.contract_rate_percent).replace(".",",")+"%");
      row.append(month,track,meta);section.append(row);
     });
     section.append(el("p","uss-overview-note","Средняя цена рассчитана по всем проданным автомобилям USS за месяц. Это не прогноз и не цена конкретной модели."));
     overview.append(section);
    }
    const koreaResponse=await fetch(api+"/api/korea-auction-overview",{headers:{Accept:"application/json"}});
    const koreaData=await koreaResponse.json();
    if(koreaResponse.ok&&koreaData.ok&&Array.isArray(koreaData.history)){
     const rows=koreaData.history.slice(-3).map(x=>x.month+": "+new Intl.NumberFormat("ru-RU").format(x.sold)+" продано / "+new Intl.NumberFormat("ru-RU").format(x.offered)+" выставлено ("+x.completion_rate_percent+"%)");
     overview.append(el("h3","","Южная Корея · итоги автомобильных аукционов"));
     rows.forEach(x=>overview.append(el("p","uss-overview-note",x)));
     const koreaLink=el("a","uss-source-link","Источник: ассоциация автомобильных аукционов Кореи ↗");koreaLink.href=koreaData.source_url;koreaLink.target="_blank";koreaLink.rel="noopener noreferrer";overview.append(koreaLink);
    }

   }catch(err){overview.replaceChildren(el("div","uss-overview-head", "Официальная сводка USS временно недоступна"),el("p","uss-overview-note",err.message||"Повторите позже. Значения не подменяются примерными цифрами."))}
  };loadOverview();
 }
 const renderRecord=(r,c)=>{const card=el("article","auction-stat-record");card.append(el("h4","",[r.make,r.model,r.year].filter(Boolean).join(" ")));const bits=[];if(r.mileage_km!=null)bits.push("Пробег: "+new Intl.NumberFormat("ru-RU").format(r.mileage_km)+" км");bits.push("Цена в источнике: "+fmt(r.price,c));card.append(el("p","",bits.join(" · ")));card.append(el("small","auction-record-source","Источник: "+(r.source||"источник данных")));return card};
 const sampleFilters=$("auctionSampleFilters");
 const updateMode=()=>{
  gradeWrap.hidden=country.value!=="japan";
  const isRav4=country.value==="japan"&&/rav.?4/i.test(($("auctionModel").value||"")+ " "+($("auctionMake").value||""));
  if(sampleFilters)sampleFilters.hidden=!isRav4;
 };
 country.addEventListener("change",updateMode);
 ["auctionMake","auctionModel"].forEach(id=>$(id)?.addEventListener("input",updateMode));
 updateMode();
 auctionStatsForm.addEventListener("submit",async e=>{
  e.preventDefault();const api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");
  if(!api){out.replaceChildren(el("p","auction-error","Сервер данных не настроен."));return}
  const from=Number($("auctionYearFrom").value||1990),to=Number($("auctionYearTo").value||2030);
  if(from>to){out.replaceChildren(el("p","auction-error","Год «от» не может быть больше года «до»."));return}
  const params=new URLSearchParams({country:country.value,make:$("auctionMake").value.trim(),model:$("auctionModel").value.trim(),year_from:String(from),year_to:String(to),grade:$("auctionGrade").value,limit:"20"});
  const optionalFilters=[["mileage_min","auctionMileageMin"],["mileage_max","auctionMileageMax"],["price_min_jpy","auctionPriceMin"],["price_max_jpy","auctionPriceMax"],["date_from","auctionDateFrom"],["date_to","auctionDateTo"]];
  optionalFilters.forEach(([key,id])=>{const value=$(id)?.value.trim();if(value)params.set(key,value)});
  if($("auctionIncludeUnsold")?.checked)params.set("include_unsold","true");
  submit.disabled=true;submit.textContent="Ищем…";out.replaceChildren(el("p","auction-loading","Получаем данные источника…"));
  try{
   const response=await fetch(api+"/api/auction-statistics?"+params.toString(),{headers:{Accept:"application/json"}});let data={};try{data=await response.json()}catch{}
   if(!response.ok)throw new Error(data.detail||"Не удалось загрузить статистику.");out.replaceChildren();
   if(data.data_type==="china_model_live"){
    out.append(el("span","auction-status-pill","Китай · свежие данные TTPAI"),el("h3","",data.model||"Статистика модели"),el("p","auction-sample-note","Город источника: "+(data.city||"указан в первоисточнике")+(data.transaction_count?" · записей в истории: "+data.transaction_count:"")));
    const metrics=el("div","auction-sample-metrics"),money=n=>n==null?"—":new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(Number(n))+" CNY";
    [["Средняя цена · 3 года",data.averages?.age_3_avg_cny],["Средняя цена · 5 лет",data.averages?.age_5_avg_cny],["Средняя цена · 7 лет",data.averages?.age_7_avg_cny]].forEach(([label,value])=>{const box=el("div","auction-sample-metric");box.append(el("small","",label),el("strong","",money(value)));metrics.append(box)});out.append(metrics);
    if(Array.isArray(data.recent_sales)&&data.recent_sales.length){const panel=el("section","auction-sample-panel");panel.append(el("h4","","Последние опубликованные сделки"));data.recent_sales.forEach(item=>panel.append(el("p","",item.date+" · "+item.description)));out.append(panel)}
    else out.append(el("p","auction-sample-note","TTPAI не отдал распознаваемый список последних сделок; средние цены получены отдельно."));
    if(data.retrieved_at)out.append(el("p","auction-sample-note","Получено: "+new Date(data.retrieved_at).toLocaleString("ru-RU")+"."));
    const source=document.createElement("a");source.href=data.source_url;source.target="_blank";source.rel="noopener noreferrer";source.textContent="Открыть первоисточник TTPAI ↗";out.append(source);
    out.append(el("p","auction-disclaimer",data.disclaimer||"Источник и тип данных указаны отдельно."));return;
   }
   if(data.data_type==="source_hub"){
    out.append(el("span","auction-status-pill","Проверяемые источники · без выдуманных цен"),el("h3","","Источники для "+[$("auctionMake").value.trim(),$("auctionModel").value.trim()].filter(Boolean).join(" ")),el("p","",data.message||"Выберите источник и проверьте реальные записи."));
    if(Array.isArray(data.model_search_links)&&data.model_search_links.length){
     const panel=el("section","auction-sample-panel");
     panel.append(el("div","eyebrow","ЯПОНИЯ · ПОИСК ПО ВЫБРАННОЙ МОДЕЛИ"),el("h3","","Открыть подготовленные поиски в аукционных архивах"));
     panel.append(el("p","auction-sample-note","Ссылки уже учитывают марку, модель и годы там, где источник поддерживает такие параметры. Мы не копируем закрытые базы: цены, фотографии и аукционные листы открываются у владельца источника."));
     const grid=el("div","auction-source-results");
     data.model_search_links.forEach(source=>{
      const card=el("article","auction-source-result");
      card.append(el("span","auction-source-access",source.kind||"Внешний источник"),el("h4","",source.name||"Источник"));
      if(source.access)card.append(el("p","",source.access));
      const link=document.createElement("a");link.href=String(source.url||"");link.target="_blank";link.rel="noopener noreferrer";link.textContent="Искать эту модель ↗";card.append(link);
      grid.append(card);
     });
     panel.append(grid);out.append(panel);
    }
    if(data.sample_stats&&Array.isArray(data.records)&&data.records.length){
     const sample=el("section","auction-sample-panel");
     sample.append(el("div","eyebrow","ПУБЛИЧНЫЙ ПРИМЕР · ЯПОНИЯ · TOYOTA RAV4"),el("h3","","Выборка завершённых торгов за 24–29 октября 2026"));
     const stats=data.sample_stats;
     const metrics=el("div","auction-sample-metrics");
     const metric=(label,value)=>{const box=el("div","auction-sample-metric");box.append(el("small","",label),el("strong","",value));metrics.append(box)};
     const money=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(Number(n||0))+" JPY";
     metric("Продано в выборке",String(stats.sample_count));
     metric("Средняя цена",money(stats.average_final_price_jpy));
     metric("Медиана",money(stats.median_final_price_jpy));
     metric("Минимум — максимум",money(stats.min_final_price_jpy)+" — "+money(stats.max_final_price_jpy));
     sample.append(metrics);
     const table=document.createElement("table");table.className="auction-sample-table";
     const thead=document.createElement("thead"),headRow=document.createElement("tr");
     ["Модель / комплектация","Год","Пробег","Площадка","Дата","Финальная цена"].forEach(label=>{const th=document.createElement("th");th.textContent=label;headRow.append(th)});
     thead.append(headRow);table.append(thead);
     const tbody=document.createElement("tbody");
     data.records.forEach(record=>{const tr=document.createElement("tr");const cells=[record.name||"Toyota RAV4",record.year||"—",record.mileage_km?new Intl.NumberFormat("ru-RU").format(record.mileage_km)+" км":"—",record.auction||"—",record.date||"—",money(record.final_price_jpy)];cells.forEach((value,index)=>{const td=document.createElement("td");if(index===0&&record.url){const a=document.createElement("a");a.href=record.url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=String(value);td.append(a)}else{td.textContent=String(value)}tr.append(td)});tbody.append(tr)});
     table.append(tbody);sample.append(table);
     if(Array.isArray(data.unsold_records)&&data.unsold_records.length){
      const unsold=el("section","auction-unsold-list");
      unsold.append(el("h4","","Непроданные лоты · отдельно от продаж"));
      data.unsold_records.forEach(u=>{const row=el("p","auction-sample-unsold",[u.name||"RAV4",u.date,u.mileage_km!=null?new Intl.NumberFormat("ru-RU").format(u.mileage_km)+" км":""].filter(Boolean).join(" · ")+" — последняя ставка "+money(u.last_bid_jpy)+". Не включён в среднее и медиану.");if(u.url){const a=document.createElement("a");a.href=u.url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=" Открыть лот ↗";row.append(a)}unsold.append(row)});
      sample.append(unsold);
     }
     sample.append(el("p","auction-sample-note",stats.note||"Выборка неполная и не представляет весь рынок. Дополнительные фото и полные аукционные листы доступны у первоисточника по его правилам."));
     const sourceLink=document.createElement("a");sourceLink.href=stats.source_url||"https://banzai24.com/en?source=archive";sourceLink.target="_blank";sourceLink.rel="noopener noreferrer";sourceLink.textContent="Открыть архив Banzai24 ↗";sample.append(sourceLink);
     out.append(sample);
    }
    if(Array.isArray(data.china_market_sample)&&data.china_market_sample.length){
     const panel=el("section","auction-sample-panel");
     panel.append(el("div","eyebrow","КИТАЙ · TTPAI · ИСТОРИЧЕСКИЕ СДЕЛКИ"),el("h3","","Публичные средние цены по возрасту автомобиля"));
     panel.append(el("p","auction-sample-note","Это средние цены сделок на платформе TTPAI, а не финальные цены отдельных аукционных лотов. Показанные модели — публичные примеры источника, а не результаты по выбранной вами модели."));
     const grid=el("div","auction-source-results");
     data.china_market_sample.forEach(item=>{
      const card=el("article","auction-source-result");card.append(el("span","auction-source-access","TTPAI · публичная статистика"),el("h4","",item.name||"Модель"));
      const money=n=>n==null?"—":new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(Number(n))+" CNY";
      card.append(el("p","", "Средняя цена: 3 года — "+money(item.age_3_avg_cny)+"; 5 лет — "+money(item.age_5_avg_cny)+"; 7 лет — "+money(item.age_7_avg_cny)+"."));
      if(item.recent_sales)card.append(el("p","", "Последние сделки: "+item.recent_sales));
      const link=document.createElement("a");link.href=String(item.url||"https://www.ttpai.cn/");link.target="_blank";link.rel="noopener noreferrer";link.textContent="Открыть историю модели ↗";card.append(link);if(item.photo_example_url){const photoLink=document.createElement("a");photoLink.href=String(item.photo_example_url);photoLink.target="_blank";photoLink.rel="noopener noreferrer";photoLink.textContent=item.photo_example_note||"Открыть пример с фотографиями ↗";card.append(photoLink)}grid.append(card);
     });
     panel.append(grid);out.append(panel);
    }
    if(Array.isArray(data.china_judicial_sample)&&data.china_judicial_sample.length){
     const panel=el("section","auction-sample-panel");
     panel.append(el("div","eyebrow","КИТАЙ · ПУБЛИЧНЫЕ СУДЕБНЫЕ ТОРГИ"),el("h3","","Примеры завершённых продаж автомобилей на Gongpai"));
     panel.append(el("p","auction-sample-note","Это примеры публичных судебных продаж, не результаты по выбранной вами модели. Судебная реализация имущества — не обычный дилерский аукцион; такие цены нельзя смешивать с рыночной статистикой подержанных автомобилей."));
     const table=document.createElement("table");table.className="auction-sample-table";
     const thead=document.createElement("thead"),headRow=document.createElement("tr");
     ["Автомобиль","Год","Суд / площадка","Дата","Цена продажи"].forEach(label=>{const th=document.createElement("th");th.textContent=label;headRow.append(th)});
     thead.append(headRow);table.append(thead);const tbody=document.createElement("tbody");
     data.china_judicial_sample.forEach(record=>{const tr=document.createElement("tr");const values=[record.name||"Автомобиль",record.year||"—",record.auction||"—",record.date||"—",new Intl.NumberFormat("ru-RU",{maximumFractionDigits:2}).format(Number(record.final_price_cny||0))+" ¥"];values.forEach((value,index)=>{const td=document.createElement("td");if(index===0&&record.url){const a=document.createElement("a");a.href=record.url;a.target="_blank";a.rel="noopener noreferrer";a.textContent=String(value);td.append(a)}else{td.textContent=String(value)}tr.append(td)});tbody.append(tr)});
     table.append(tbody);panel.append(table);
     panel.append(el("p","auction-sample-note","Примеры взяты из открытых карточек Gongpai; часть карточек содержит фотографии, оценочные материалы и подтверждение成交. Состав документов зависит от конкретного дела."));
     out.append(panel);
    }
    const grid=el("div","auction-source-results");
    (Array.isArray(data.sources)?data.sources:[]).forEach(source=>{
     const card=el("article","auction-source-result");
     card.append(el("span","auction-source-access",source.access||"Условия доступа уточнить"),el("h4","",source.name||"Источник"),el("p","",source.note||"Описание источника не предоставлено."));
     const kind=el("small","auction-source-kind",source.data_kind||"");card.append(kind);
     const link=document.createElement("a");link.href=String(source.url||"");link.target="_blank";link.rel="noopener noreferrer";link.textContent="Открыть первоисточник ↗";card.append(link);
     grid.append(card);
    });
    out.append(grid,el("p","auction-disclaimer",data.disclaimer||"Показываем только данные с объяснимым происхождением."));
    return;
   }
   if(data.data_type==="unavailable"){
    out.append(el("span","auction-status-pill","Источник пока не подключён"),el("h3","",data.source||"Нет подтверждённых данных"),el("p","",data.message||"Для этой страны источник статистики ещё не подключён."),el("p","auction-disclaimer",data.disclaimer||"Данные не выдумываем."));
    const request=document.createElement("button");request.type="button";request.className="button button-secondary";request.textContent="Запросить подбор этой модели";
    request.addEventListener("click",()=>{const prompt=$("carPrompt");if(prompt){prompt.value="Нужна статистика завершённых аукционов: "+country.options[country.selectedIndex].text+"; "+[$("auctionMake").value.trim(),$("auctionModel").value.trim()].filter(Boolean).join(" ")+"; годы "+from+"–"+to+". Прошу проверить реальные записи и сообщить источник.";prompt.focus();$("assistant").scrollIntoView({behavior:"smooth",block:"center"})}});out.append(request);return;
   }
   out.append(el("span","auction-status-pill",data.data_type==="current_listings"?"Цены объявлений · не результаты торгов":"Статистика торгов"),el("h3","","Найдено записей: "+(data.count||0)));
   const stats=el("div","auction-stat-metrics");[["Минимальная",data.min_price],["Медианная",data.median_price],["Максимальная",data.max_price]].forEach(([label,value])=>{const box=el("div","auction-stat-metric");box.append(el("small","",label),el("strong","",value==null?"—":fmt(value,data.currency)));stats.append(box)});out.append(stats);
   if(data.records&&data.records.length){const list=el("div","auction-stat-records");data.records.forEach(r=>list.append(renderRecord(r,data.currency)));out.append(list)}out.append(el("p","auction-disclaimer",data.disclaimer||"Источник и тип данных указаны отдельно."));
  }catch(err){out.replaceChildren(el("p","auction-error",err.message||"Ошибка поиска."))}finally{submit.disabled=false;submit.textContent="Найти статистику ↗"}
 });
}
})();