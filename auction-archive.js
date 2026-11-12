(()=>{"use strict";
const by=id=>document.getElementById(id);
const grid=by("auctionGrid"),status=by("auctionStatus"),count=by("auctionCount"),country=by("auctionCountry"),search=by("auctionSearch");
if(!grid||!status||!country||!search)return;
const countryNames={japan:"Япония","south-korea":"Южная Корея",china:"Китай"};
const make=(tag,value,cls)=>{const el=document.createElement(tag);if(value!==undefined)el.textContent=String(value);if(cls)el.className=cls;return el};
const securePath=p=>typeof p==="string"&&/^\/assets\/auction\/[a-z0-9._/-]+\.(jpg|jpeg|png|webp)$/i.test(p)&&!p.includes("..");
const permitted=r=>r&&r.image_rights==="approved"&&r.commercial_use_permission===true&&r.self_host_permission===true&&r.make&&r.model&&r.country in countryNames&&Number.isInteger(Number(r.year))&&Array.isArray(r.photos)&&r.photos.length>0&&r.photos.every(securePath)&&securePath(r.auction_sheet)&&r.sheet_permission===true;
const number=v=>Number.isFinite(Number(v))?Number(v).toLocaleString("ru-RU"):"";
let records=[];
const badge=(k,v)=>{const el=make("div",undefined,"lot-fact");el.append(make("small",k),make("strong",v??"Не указано"));return el};
function photoGallery(r){
  const wrap=make("div",undefined,"lot-gallery"),hero=make("div",undefined,"lot-main");
  const image=make("img");image.loading="lazy";image.decoding="async";image.alt="Аукционная фотография: "+r.make+" "+r.model+" "+r.year;image.src=r.photos[0];
  const group=make("div",undefined,"lot-thumbs");
  const available=r.photos.map((src,i)=>({src,label:"Ракурс "+(i+1)})).concat([{src:r.auction_sheet,label:"Аукционный лист",sheet:true}]);
  function select(index){
    const item=available[index];image.src=item.src;
    image.alt=(item.sheet?"Аукционный лист":"Фотография "+(index+1))+" — "+r.make+" "+r.model+" "+r.year;
    hero.classList.toggle("is-sheet",Boolean(item.sheet));
    for(const [n,el] of [...group.children].entries()){el.setAttribute("aria-pressed",String(n===index));el.classList.toggle("selected",n===index);}
    caption.textContent=item.label;
  }
  image.onerror=()=>{image.alt="Изображение временно недоступно";};
  const caption=make("p","Основное фото","lot-gallery-caption");
  hero.append(image,caption);wrap.append(hero);
  for(const [i,item] of available.entries()){
    const btn=make("button",undefined,"lot-thumb");btn.type="button";btn.setAttribute("aria-label",item.label);btn.setAttribute("aria-pressed",String(i===0));
    if(i===0)btn.classList.add("selected");
    const t=make("img");t.src=item.src;t.loading="lazy";t.alt="";t.width=96;t.height=72;
    btn.append(t);if(item.sheet)btn.append(make("span","Лист","sheet-tag"));
    btn.addEventListener("click",()=>select(i));group.append(btn);
  }
  wrap.append(group);
  return wrap;
}
function show(){
  const needle=search.value.toLocaleLowerCase("ru").trim(),locationCountry=country.value;
  const filtered=records.filter(r=>(!locationCountry||r.country===locationCountry)&&(!needle||[r.make,r.model,r.body,r.year,r.grade,r.lot].join(" ").toLocaleLowerCase("ru").includes(needle)));
  grid.replaceChildren();
  count.textContent="Подтверждённых архивных карточек: "+filtered.length;
  grid.hidden=!filtered.length;
  for(const r of filtered){
    const card=make("article",undefined,"lot");
    card.append(photoGallery(r));
    const body=make("div",undefined,"lot-body");
    body.append(make("div",countryNames[r.country],"market"),make("h2",r.make+" "+r.model+" · "+r.year));
    const facts=make("div",undefined,"lot-facts");
    facts.append(badge("Пробег",r.mileage_km==null?"Не указан":number(r.mileage_km)+" км"));
    facts.append(badge("Оценка",r.grade||"Не указана"));
    facts.append(badge("Двигатель",r.engine_cc?number(r.engine_cc)+" см³":r.engine||"Уточняется"));
    facts.append(badge("Кузов",r.body||"Уточняется"));
    facts.append(badge("Аукцион",r.auction||"Не указан"));
    facts.append(badge("Лот №",r.lot||"Не указан"));
    facts.append(badge("Дата торгов",r.auction_date||"Не указана"));
    facts.append(badge("Комплектация",r.trim||"Уточняется"));
    body.append(facts);
    if(r.sale_status==="verified_sold"&&r.currency&&Number(r.sold_price)>0){
      body.append(make("p","Цена продажи на аукционе: "+number(r.sold_price)+" "+r.currency,"price"));
    }else body.append(make("p","Цена продажи не подтверждена","price"));
    body.append(make("p","Архивный пример. Этот автомобиль не предлагается как находящийся в наличии. Доступность аналогичной машины, экспорт и стоимость до России проверяются отдельно.","note"));
    const a=make("a","Подобрать аналогичный автомобиль","cta");
    a.href="/podbor.html?similar="+encodeURIComponent(r.make+" "+r.model+" "+r.year);
    body.append(a);card.append(body);grid.append(card);
  }
  status.textContent=filtered.length?
    "Архивные примеры реальных автомобилей. Все фотографии и аукционные листы размещены на сервере PapAuto с подтверждёнными правами. Это не машины в наличии.":
    records.length?"По выбранным параметрам карточек не найдено.":
    "Архив фотографий готов к наполнению. Лоты с непроверенными правами и без аукционного листа не публикуются; для подбора автомобиля используйте заявку.";
}
country.addEventListener("change",show);search.addEventListener("input",show);
fetch("/data/approved-auction-lots.json",{cache:"no-store"}).then(resp=>{if(!resp.ok)throw Error("Failed to load");return resp.json()})
.then(data=>{records=(Array.isArray(data.lots)?data.lots:[]).filter(permitted);show()})
.catch(()=>{records=[];show();status.textContent="Проверенные карточки пока не удалось загрузить. Форма подбора доступна."});
})();