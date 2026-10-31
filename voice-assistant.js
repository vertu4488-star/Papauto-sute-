(()=>{"use strict";
const $=id=>document.getElementById(id);
const box=$("voiceCarAssistant"),input=$("voiceCarText"),listen=$("voiceCarListen"),apply=$("voiceCarApply"),status=$("voiceCarStatus");
const levelBox=$("voiceCarLevel"),levelFill=$("voiceCarLevelFill"),levelText=$("voiceCarLevelText");
if(!box||!input||!listen||!apply||!status)return;
const SpeechRecognition=window.SpeechRecognition||window.webkitSpeechRecognition;
let recognition=null,listening=false;
const sayStatus=(s)=>{status.textContent=s};
const countryMap=[
 {key:"japan",calc:"Япония",terms:["япони","япон","аукцион","uss"]},
 {key:"south-korea",calc:"Южная Корея",terms:["коре","корей","энкар","encar"]},
 {key:"china",calc:"Китай",terms:["китай","кита"]},
];
const makes=[
 ["Toyota",["toyota","тойота","тойоты","тойоту"]],["Honda",["honda","хонда"]],["Nissan",["nissan","ниссан"]],["Mazda",["mazda","мазда"]],["Subaru",["subaru","субару"]],["Suzuki",["suzuki","сузуки"]],["Mitsubishi",["mitsubishi","митсубиси"]],["Lexus",["lexus","лексус"]],["Daihatsu",["daihatsu","дайхатсу"]],["Isuzu",["isuzu","исузу"]],["Hyundai",["hyundai","хендай","хундай"]],["Kia",["kia","киа"]],["Genesis",["genesis","дженезис"]],["BMW",["bmw","бмв"]],["Mercedes-Benz",["mercedes","мерседес"]],["Volkswagen",["volkswagen","фольксваген"]],["Audi",["audi","ауди"]],["BYD",["byd","бид"]],["Geely",["geely","джили","джили"]],["Chery",["chery","чери"]],["Haval",["haval","хавал"]],["Zeekr",["zeekr","зикр","зикер"]],["Li Auto",["li auto","ли авто","лисян"]],["Tesla",["tesla","тесла"]],["Renault",["renault","рено"]],["Ford",["ford","форд"]],["Chevrolet",["chevrolet","шевроле"]],["Volvo",["volvo","вольво"]]
];
const models=[
 ["RAV4",["rav4","рав4","рав 4"]],["Prius",["prius","приус"]],["Aqua",["aqua","аква"]],["Corolla",["corolla","королла"]],["Camry",["camry","камри"]],["Harrier",["harrier","харриер"]],["Yaris",["yaris","ярис","витц","vitz"]],["Fit",["fit","фит"]],["Freed",["freed","фрид"]],["Vezel",["vezel","везел"]],["Noah",["noah","ноах"]],["Voxy",["voxy","вокси"]],["C-HR",["c-hr","chr","с-хр"]],["Land Cruiser",["land cruiser","ленд крузер","ланд крузер"]],["Prado",["prado","прадо"]],["Highlander",["highlander","хайлендер"]],["Crown",["crown","краун"]],["Note",["note","ноут"]],["Serena",["serena","серена"]],["X-Trail",["x-trail","икстрейл","х-трейл"]],["Leaf",["leaf","лиф"]],["CX-5",["cx-5","cx5","сх5"]],["Forester",["forester","форестер"]],["Outback",["outback","аутбек"]],["Impreza",["impreza","импреза"]],["Sportage",["sportage","спортейдж"]],["Tucson",["tucson","туссан"]],["Santa Fe",["santa fe","санта фе"]],["Sonata",["sonata","соната"]],["K5",["k5","к5"]],["Carnival",["carnival","карнивал"]],["Elantra",["elantra","элантра"]],["Staria",["staria","стария"]],["Model 3",["model 3","модель 3"]],["Model Y",["model y","модель y"]],["Tiguan",["tiguan","тигуан"]],["Touareg",["touareg","туарег"]],["X5",["x5","икс5"]],["3 Series",["3 series","3 серия"]],["RX",["rx","рх"]],["NX",["nx","нх"]],["L7",["l7","л7"]],["L9",["l9","л9"]],["Song Plus",["song plus","сонг плюс"]],["Monjaro",["monjaro","монджаро"]],["Coolray",["coolray","кулрей"]]
];
function escapeRx(s){return s.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}
function hasTerm(t,term){return new RegExp("(^|[^a-zа-я0-9])"+escapeRx(term.toLowerCase())+"([^a-zа-я0-9]|$)","i").test(t)}
function findMapped(list,t){for(const [value,aliases] of list){if(aliases.some(a=>hasTerm(t,a)))return value}return ""}
function wordsNumber(t){
 const numbers={ноль:0,один:1,одна:1,одно:1,одного:1,одну:1,двух:2,двум:2,два:2,две:2,трех:3,трёх:3,три:3,четырех:4,четырёх:4,четыре:4,пяти:5,пять:5,шести:6,шесть:6,семи:7,семь:7,восьми:8,восемь:8,девяти:9,девять:9,десяти:10,десять:10,одиннадцать:11,двенадцать:12,тринадцать:13,четырнадцать:14,пятнадцать:15,двадцать:20,тридцать:30,сорок:40,пятьдесят:50,сто:100,полтора:1.5,полутора:1.5};
 let m=t.match(/(\d[\d\s.,]*)\s*(млн|миллион(?:а|ов)?|тыс(?:яч|ячи)?|тысяч|руб(?:лей)?|₽)/i);
 if(m){let n=Number(m[1].replace(/\s/g,"").replace(",", "."));if(Number.isFinite(n)){if(/млн|миллион/i.test(m[2]))return Math.round(n*1000000);if(/тыс/i.test(m[2]))return Math.round(n*1000);return Math.round(n)}}
 m=t.match(/(полтора|полутора|один|одна|одно|одного|одну|два|две|двух|три|трех|трёх|четыре|четырех|четырёх|пять|пяти|шесть|шести|семь|семи|восемь|восьми|девять|девяти|десять|десяти|одиннадцать|двенадцать|пятнадцать|двадцать)\s+(?:миллион(?:а|ов)?|млн)/i);
 if(m)return Math.round((numbers[m[1]]||0)*1000000);
 m=t.match(/(полтора|полутора|один|одна|одно|одного|одну|два|две|двух|три|трех|трёх|четыре|четырех|четырёх|пять|пяти|шесть|шести|семь|семи|восемь|восьми|девять|девяти|десять|десяти|двадцать)\s+(?:тыс(?:яч)?|тысяч)/i);
 if(m)return Math.round((numbers[m[1]]||0)*1000);
 m=t.match(/(?:до|бюджет|стоимость|цена)\s*(?:в пределах\s*)?(\d[\d\s]{3,})/i);
 if(m){const n=Number(m[1].replace(/\s/g,""));if(n>10000)return n}
 return null;
}
function parse(text){
 const t=text.toLowerCase().replace(/ё/g,"е").replace(/\s+/g," ").trim();
 const result={raw:text};
 const cityMatch=t.match(/(?:до|в|город(?:е)?\s+получения\s+)(новосибирск(?:а|у)?|красноярск(?:а|у)?|москва|екатеринбург(?:а|е)?|иркутск(?:а|е)?|омск(?:а|е)?|кемерово|томск(?:а|е)?|барнаул(?:а|е)?)/i);
 if(cityMatch){const c=cityMatch[1].toLowerCase();result.city=/новосибирск/.test(c)?"Новосибирск":/красноярск/.test(c)?"Красноярск":/москва/.test(c)?"Москва":/екатеринбург/.test(c)?"Екатеринбург":/иркутск/.test(c)?"Иркутск":/омск/.test(c)?"Омск":/кемерово/.test(c)?"Кемерово":/томск/.test(c)?"Томск":"Барнаул"}
 const country=countryMap.find(c=>c.terms.some(term=>t.includes(term)));
 if(country){result.country=country.key;result.calcCountry=country.calc}
 const make=findMapped(makes,t);if(make)result.make=make;
 const model=findMapped(models,t);if(model)result.model=model;
 const years=[...t.matchAll(/\b(19\d{2}|20\d{2})\b/g)].map(m=>Number(m[1])).filter(y=>y>=1990&&y<=2027);
 if(years.length){result.yearFrom=Math.min(...years);result.yearTo=Math.max(...years)}
 const budget=wordsNumber(t);if(budget!==null&&budget>=50000&&budget<=200000000)result.budget=budget;
 let m=t.match(/(?:пробег(?:ом)?|до пробега|пробег до)\s*(?:до\s*)?(\d[\d\s.,]*)\s*(?:тыс(?:яч)?\s*)?км?/i);
 if(m){let n=Number(m[1].replace(/[\s,]/g,""));if(/тыс/i.test(m[0]))n*=1000;if(n>0&&n<=2000000)result.mileage=Math.round(n)}
 m=t.match(/(\d(?:[.,]\d)?)\s*(?:литр(?:а|ов)?|л\b)/i);if(m){const n=Number(m[1].replace(",","."));if(n>0&&n<=10)result.volume=Math.round(n*1000)}
 else {m=t.match(/(\d{3,4})\s*(?:см3|см³|куб(?:ов)?)/i);if(m)result.volume=Math.min(20000,Number(m[1]))}
 const bodies=[["кроссовер",["кроссовер","паркетник","suv"]],["седан",["седан"]],["хэтчбек",["хэтчбек","хэтч"]],["универсал",["универсал"]],["минивэн",["минивэн","минивен"]],["внедорожник",["внедорожник","джип"]],["купе",["купе"]]];
 const body=bodies.find(x=>x[1].some(a=>t.includes(a)));if(body)result.body=body[0];
 m=t.match(/(?:оценк(?:а|у)|аукционн(?:ая|ую) оценк(?:а|у)|grade)\s*(?:до|не ниже|не менее)?\s*(\d(?:\.\d)?)/i);if(m)result.grade=m[1];
 m=t.match(/(?:лот|номер лота)\s*#?\s*([a-z0-9-]{3,})/i);if(m)result.lot=m[1];
 return result;
}
function applyParsed(p,autoSearch){
 const set=(id,v)=>{const e=$(id);if(e&&v!==undefined&&v!==null&&v!==""){e.value=String(v);e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}))}};
 // Keep catalogue filters in sync for users who want to inspect them.
 set("vehicleCountry",p.country);set("vehicleMake",p.make);set("vehicleModel",p.model);set("vehicleYearFrom",p.yearFrom);set("vehicleYearTo",p.yearTo);set("vehicleMaxPrice",p.budget);set("vehicleMileageMax",p.mileage);set("vehicleVolumeMin",p.volume);set("vehicleVolumeMax",p.volume);set("vehicleBody",p.body);set("vehicleGrade",p.grade);set("vehicleLot",p.lot);set("calcCountry",p.calcCountry);
 // The microphone belongs to PAPAUTO SELECT: route speech to Gemini's AI selector.
 const countryLabels={japan:"Япония","south-korea":"Южная Корея",china:"Китай"};
 if(p.country)set("country",countryLabels[p.country]||"Не определился");
 set("carMake",p.make);set("carModel",p.model);set("yearFrom",p.yearFrom);set("yearTo",p.yearTo);set("budget",p.budget);set("maxMileage",p.mileage);
 if(p.city)set("city",p.city);
 if(p.raw)set("carPrompt",p.raw);
 const details=[];
 if(p.country)details.push("страна: "+(countryLabels[p.country]||p.country));if(p.city)details.push("город получения: "+p.city);
 if(p.make)details.push("марка: "+p.make);if(p.model)details.push("модель: "+p.model);
 if(p.yearFrom||p.yearTo)details.push("год: "+(p.yearFrom||"любой")+"–"+(p.yearTo||p.yearFrom));
 if(p.budget)details.push("бюджет до "+new Intl.NumberFormat("ru-RU").format(p.budget)+" ₽");
 if(p.mileage)details.push("пробег до "+new Intl.NumberFormat("ru-RU").format(p.mileage)+" км");
 if(p.volume)details.push("двигатель "+(p.volume/1000).toLocaleString("ru-RU")+" л");
 if(p.body)details.push("кузов: "+p.body);
 if(!p.raw||p.raw.trim().length<5){sayStatus("Не удалось распознать достаточно длинный запрос. Попробуйте сказать ещё раз.");return}
 if(autoSearch){
  sayStatus("Речь распознана"+(details.length?": "+details.join("; "):"")+". Выполняю бесплатный поиск по открытым источникам…");
  const selectButton=$("runAiSelect");
  const form=$("vehicleSearchForm");
  if(selectButton){setTimeout(()=>selectButton.click(),250)}
  else if(form){setTimeout(()=>form.requestSubmit(),250)}
  else sayStatus("Поля распознаны. Перейдите в каталог и нажмите «Найти автомобили».");
 }else{
  sayStatus("Распознано"+(details.length?": "+details.join("; "):"")+". Текст перенесён в форму PAPAUTO SELECT. Нажмите «Подобрать модели».");
 }
}
apply.addEventListener("click",()=>applyParsed(parse(input.value),false));
let lastSpoken="";
function speak(text){
 if(!("speechSynthesis" in window)||!text)return;
 const clean=String(text).replace(/https?:\/\/\S+/g,"").replace(/\s+/g," ").trim();
 if(!clean||clean===lastSpoken)return;
 lastSpoken=clean;
 try{window.speechSynthesis.cancel();const utterance=new SpeechSynthesisUtterance(clean);utterance.lang="ru-RU";utterance.rate=0.96;window.speechSynthesis.speak(utterance)}catch{}
}
const searchStatus=$("vehicleSearchStatus");
if(searchStatus&&"MutationObserver" in window){
 let speakTimer=null;
 new MutationObserver(()=>{const message=searchStatus.textContent.trim();if(!message||message===lastSpoken)return;clearTimeout(speakTimer);speakTimer=setTimeout(()=>speak(message),250)}).observe(searchStatus,{childList:true,subtree:true,characterData:true});
}
const searchResults=$("vehicleSearchResults");
if(searchResults&&"MutationObserver" in window){
 new MutationObserver(()=>{if(!searchResults.hidden&&searchResults.children.length){const count=searchResults.querySelectorAll(".vehicle-result-card").length;if(count)speak("Поиск завершён. Получено предложений: "+count+". Цены и наличие нужно подтвердить у продавца; доставка и оформление в России считаются отдельно.")}}).observe(searchResults,{childList:true,subtree:true,attributes:true,attributeFilter:["hidden"]});
}
const aiResults=$("aiSelectResults");
if(aiResults&&"MutationObserver" in window){
 let aiSpeakTimer=null;
 new MutationObserver(()=>{
  if(aiResults.hidden)return;
  clearTimeout(aiSpeakTimer);
  aiSpeakTimer=setTimeout(()=>{
   const summary=aiResults.querySelector(".ai-select-summary")?.textContent?.trim()||"";
   const cards=[...aiResults.querySelectorAll(".ai-select-card")].map(card=>{
    const title=card.querySelector("h3")?.textContent?.trim()||"";
    const why=card.querySelector("p")?.textContent?.trim()||"";
    return [title,why].filter(Boolean).join(". ");
   });
   const questions=aiResults.querySelector(".ai-select-questions")?.textContent?.trim()||"";
   const answer=[summary,...cards,questions].filter(Boolean).join(". ");
   if(answer)speak(answer);
  },350);
 }).observe(aiResults,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:["hidden"]});
}

const micIcon='<svg viewBox="0 0 24 24" aria-hidden="true"><rect x="9" y="2" width="6" height="12" rx="3"></rect><path d="M5 10v2a7 7 0 0 0 14 0v-2M12 19v3M8 22h8"></path></svg>';
let nativeManualStop=false,nativeGotResult=false;
function startNativeRecognition(){
 if(!SpeechRecognition)return false;
 try{
  recognition=new SpeechRecognition();
  recognition.lang="ru-RU";
  recognition.interimResults=false;
  recognition.maxAlternatives=3;
  recognition.continuous=false;
  nativeManualStop=false;
  nativeGotResult=false;
  input.value="";
  listening=true;
  listen.setAttribute("aria-pressed","true");
  listen.classList.add("is-listening");
  sayStatus("Слушаю запрос через встроенное распознавание речи…");
  recognition.onresult=event=>{
   const transcript=Array.from(event.results||[]).map(result=>result[0]?.transcript||"").join(" ").trim();
   if(!transcript)return;
   nativeGotResult=true;
   listening=false;
   resetMic();
   input.value=transcript;
   applyParsed(parse(transcript),true);
  };
  recognition.onerror=event=>{
   if(!listening)return;
   listening=false;
   resetMic();
   if(event.error==="not-allowed"||event.error==="service-not-allowed"){
    sayStatus("Браузер не разрешил распознавание речи. Проверьте разрешение микрофона и попробуйте текстовый ввод.");
    return;
   }
   sayStatus("В этом браузере нет бесплатного распознавания речи. Введите запрос текстом.");
  };
  recognition.onend=()=>{
   if(!listening)return;
   listening=false;
   resetMic();
   if(nativeManualStop){
    sayStatus(nativeGotResult?"Распознавание завершено.":"Запись остановлена. Можно попробовать ещё раз.");
    return;
   }
   if(!nativeGotResult){
    sayStatus("Браузер не вернул текст. Попробуйте ещё раз или введите запрос вручную.");
   }
  };
  recognition.start();
  return true;
 }catch(error){
  listening=false;
  resetMic();
  return false;
 }
}
listen.addEventListener("click",()=>{
 if(listening&&recognition){
  nativeManualStop=true;
  try{recognition.stop()}catch{listening=false;resetMic()}
  return;
 }
 if(!startNativeRecognition()){sayStatus("В этом браузере нет встроенного распознавания. На iPhone нажмите микрофон на клавиатуре, продиктуйте запрос в поле выше, затем нажмите «Разобрать запрос».");input.focus();}
});
})();