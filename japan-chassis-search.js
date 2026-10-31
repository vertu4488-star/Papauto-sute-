(()=>{"use strict";
const input=document.getElementById("japanChassisInput");
const button=document.getElementById("japanChassisSearch");
const status=document.getElementById("japanChassisStatus");
const output=document.getElementById("japanChassisResults");
if(!input||!button||!status||!output)return;
const sources=[
 ["Google · поиск по JP Sheet","jpsheet.com"],
 ["Google · архив Carvector","carvector.com"],
 ["Google · архив Aleado","aleado.com"],
 ["Google · архив Banzai24","banzai24.com"],
 ["Google · прошлые торги Auctions22","auctions22.com"]
];
const valid=value=>/^[A-Z0-9-]{5,32}$/.test(value);
button.addEventListener("click",()=>{
 const chassis=input.value.trim().toUpperCase();
 if(!valid(chassis)){status.textContent="Введите номер кузова латинскими буквами и цифрами (5–32 символа).";output.hidden=true;return;}
 output.replaceChildren();
 const note=document.createElement("p");note.className="japan-chassis-note";note.textContent="Открываются обычные поисковые страницы Google по указанному номеру кузова. Сам поиск бесплатный; сайты-источники могут ограничивать просмотр или предлагать платные отчёты — ничего покупать не нужно.";output.append(note);
 for(const [label,domain] of sources){
  const link=document.createElement("a");link.className="japan-chassis-source-link";link.href="https://www.google.com/search?q="+encodeURIComponent('site:'+domain+' "'+chassis+'"');link.target="_blank";link.rel="noopener noreferrer";link.textContent=label+" ↗";output.append(link);
 }
 output.hidden=false;
 status.textContent="Подготовлено 5 бесплатных поисковых ссылок. PAPAUTO не обращается к платным API и не списывает кредиты.";
});
input.addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();button.click();}});
})();