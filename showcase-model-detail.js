(()=>{
"use strict";
const names=new Map([
["hyundai-sonata","Hyundai Sonata"],
["hyundai-tucson","Hyundai Tucson"],
["kia-sportage","Kia Sportage"],
["kia-seltos","Kia Seltos"],
["hyundai-santa-fe","Hyundai Santa Fe"],
["kia-carnival","Kia Carnival"],
["geely-coolray","Geely Coolray"],
["geely-emgrand","Geely Emgrand"],
["byd-song-plus","BYD Song Plus"],
["byd-dolphin","BYD Dolphin"],
["changan-uni-v","Changan UNI-V"],
["changan-cs55-plus","Changan CS55 Plus"],
["haval-jolion","Haval Jolion"]
]);
const el=id=>document.getElementById(id);
const slug=new URLSearchParams(location.search).get("model")||"";
const name=names.get(slug);
function unavailable(){el("detail").hidden=true;el("notFound").hidden=false;}
if(!name){unavailable();return;}
fetch("/index.html",{cache:"no-store"}).then(r=>{
 if(!r.ok)throw Error("Homepage model data unavailable");
 return r.text();
}).then(html=>{
 const doc=new DOMParser().parseFromString(html,"text/html");
 const cards=[...doc.querySelectorAll("article.pa-car-card")];
 const card=cards.find(x=>x.querySelector("h3")?.textContent.trim()===name);
 if(!card)throw Error("Model is missing from the live showroom");
 const price=card.querySelector(".pa-car-price strong")?.textContent.trim()||"";
 const spec=card.querySelector(".pa-car-meta")?.textContent.trim()||"";
 const detail=card.querySelector(".pa-car-price small")?.textContent.trim()||"";
 const country=card.querySelector(".pa-car-type")?.textContent.trim()||"";
 const note=card.querySelector(".pa-car-note")?.textContent.trim()||"";
 el("name").textContent=name;el("crumb").textContent=name;el("country").textContent=country;
 el("spec").textContent=spec;el("price").textContent=price;el("priceDetail").textContent=detail;el("note").textContent=note;
 el("quote").href="/?view=select&similar="+encodeURIComponent(name)+"#assistant";
 document.title=name+" — характеристики и подбор автомобиля | PAPAUTO";
 el("detail").hidden=false;
}).catch(unavailable);
})();
