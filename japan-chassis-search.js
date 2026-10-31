(()=>{"use strict";
const $=id=>document.getElementById(id);
const input=$("japanChassisInput"),button=$("japanChassisSearch"),status=$("japanChassisStatus"),out=$("japanChassisResults");
const cfg=window.PAPAUTO_CONFIG||{};
if(!input||!button||!status||!out)return;
const el=(tag,cls,text)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(text!==undefined)node.textContent=String(text);return node};
const addMeta=(parent,label,value)=>{if(value===null||value===undefined||String(value).trim()==="")return;parent.append(el("span","",label+": "+value))};
function render(data){
 out.replaceChildren();
 if(data.test_data)out.append(el("span","japan-chassis-test","ТЕСТОВАЯ ЗАПИСЬ ИСТОЧНИКА — НЕ РЕАЛЬНЫЙ ЛОТ"));
 if(!data.found||!data.matches.length){out.append(el("p","japan-chassis-note","В архиве JP Sheet не найдено совпадений по этому номеру кузова. Это не доказывает, что автомобиль никогда не участвовал в торгах: покрытие зависит от доступных источнику архивов."));return}
 data.matches.forEach((item,index)=>{
   const card=el("article","japan-chassis-card");
   card.append(el("h4","",(item.make+" "+item.model+" "+item.year).trim()||"Аукционная запись "+(index+1)));
   const meta=el("div","japan-chassis-meta");
   addMeta(meta,"Совпадение",item.match==="exact"?"точное":item.match);
   addMeta(meta,"Объём",item.engine_cc?item.engine_cc+" см³":null);
   addMeta(meta,"Оценка",item.grade);
   addMeta(meta,"КПП",item.transmission);
   addMeta(meta,"Цвет",item.color);
   addMeta(meta,"Статус",item.result);
   addMeta(meta,"Стартовая цена",item.start_price);
   addMeta(meta,"Фото в полном отчёте",item.photos_count);
   card.append(meta);
   card.append(el("p","japan-chassis-note","Номер кузова: "+data.chassis+". Для просмотра даты торгов, номера лота, итоговой цены, аукционного листа и самих фотографий потребуется отдельный полный отчёт. Он может расходовать кредит провайдера и пока не запрашивается автоматически."));
   out.append(card);
 });
 if(data.credits_left!==null)out.append(el("p","japan-chassis-note","Остаток кредитов API: "+data.credits_left+". Проверка номера кузова бесплатна."));
}
button.addEventListener("click",async()=>{
 const chassis=input.value.trim().toUpperCase();
 const api=String(cfg.apiBaseUrl||"").replace(/\/$/,"");
 if(!/^[A-Z0-9-]{5,32}$/.test(chassis)){status.textContent="Введите номер кузова латинскими буквами и цифрами.";return}
 if(!api){status.textContent="API сайта не настроен.";return}
 button.disabled=true;status.textContent="Проверяем архив JP Sheet…";out.hidden=true;
 try{
   const response=await fetch(api+"/api/japan-auctions/chassis/search",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({chassis})});
   let data={};try{data=await response.json()}catch{}
   if(!response.ok)throw new Error(data.detail||"Не удалось проверить номер кузова.");
   render(data);out.hidden=false;
   status.textContent=data.found?"Найдены записи в архиве JP Sheet.":"Совпадений не найдено.";
 }catch(error){status.textContent=error.message||"Ошибка соединения с архивом."}
 finally{button.disabled=false}
});
input.addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();button.click()}});
})();