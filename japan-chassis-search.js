(()=>{"use strict";
const input=document.getElementById("japanChassisInput");
const button=document.getElementById("japanChassisSearch");
const status=document.getElementById("japanChassisStatus");
const output=document.getElementById("japanChassisResults");
if(!input||!button||!status||!output)return;
const valid=value=>/^[A-Z0-9-]{5,32}$/.test(value);
button.addEventListener("click",()=>{
 const chassis=input.value.trim().toUpperCase();
 if(!valid(chassis)){
  status.textContent="Введите номер кузова латинскими буквами и цифрами (5–32 символа).";
  output.hidden=true;
  return;
 }
 output.replaceChildren();
 const title=document.createElement("strong");title.textContent="Номер кузова: "+chassis;
 const p=document.createElement("p");p.className="japan-chassis-note";
 p.textContent="Поиск и проверка источников выполняются специалистом PAPAUTO. Мы не отправляем вас к сторонним продавцам. При обращении укажите этот номер кузова.";
 const link=document.createElement("a");link.className="japan-chassis-source-link";
 link.href="/?view=select&japan_chassis="+encodeURIComponent(chassis)+"#assistant";
 link.textContent="Запросить проверку в PAPAUTO";
 output.append(title,p,link);
 output.hidden=false;
 status.textContent="Подготовлен запрос на проверку кузова через PAPAUTO; внешних переходов нет.";
});
input.addEventListener("keydown",event=>{
 if(event.key==="Enter"){event.preventDefault();button.click();}
});
})();
