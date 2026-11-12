(()=>{"use strict";
const grid=document.getElementById("demoAuctionGrid"),count=document.getElementById("demoAuctionCount"),country=document.getElementById("auctionCountry"),query=document.getElementById("auctionSearch");
if(!grid)return;
const countries={japan:"Япония","south-korea":"Южная Корея",china:"Китай"};
const currency={JPY:"¥",KRW:"₩",CNY:"¥"};
const number=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(n);
const rub=n=>number(n)+" ₽";
const one=(tag,txt,cls)=>{const e=document.createElement(tag);if(txt!==undefined)e.textContent=String(txt);if(cls)e.className=cls;return e};
const srcOK=s=>/^\/assets\/demo\/[a-z0-9-]+-cc0\.webp$/.test(s);
let data=[];
function render(){
 const needle=query.value.trim().toLowerCase(),c=country.value;
 const list=data.filter(v=>(!c||v.country===c)&&(!needle||[v.make,v.model,v.year,v.body,v.color].join(" ").toLowerCase().includes(needle)));
 count.textContent="Примеров расчёта для выбранных моделей: "+list.length;
 grid.replaceChildren();
 for(const v of list){
  if(!srcOK(v.image))continue;
  const card=one("article",undefined,"demo-lot");card.id=v.id;card.style.scrollMarginTop="22px";
  const picture=one("div",undefined,"demo-lot-image");
  picture.append(one("span","Аукционные фотографии — после проверки прав","demo-photo-unavailable"));card.append(picture);
  const body=one("div",undefined,"demo-lot-body");
  body.append(one("div",countries[v.country]+" · "+v.year,"demo-lot-country"),one("h3",v.make+" "+v.model));
  body.append(one("p",v.engine+" · "+v.body+" · "+(v.color==="Не уточнён"?"":v.color+" · ")+number(v.mileage_km)+" км (пример пробега)","demo-lot-specs"));
  const baseRub=Math.round(v.sale_price*v.rate_to_rub);
  const cfRub=Math.round(v.japan_cf*v.rate_to_rub);
  const exportRub=Math.round(v.export_fees*v.rate_to_rub);
  const freightRub=Math.round(v.freight*v.rate_to_rub);
  const vlad=baseRub+cfRub+exportRub+freightRub+v.duty_rub+v.util_rub+v.sbkts_rub+v.storage_rub+v.commission_rub;
  const nov=vlad+v.truck_rub;
  const price=one("div",undefined,"demo-lot-total");
  price.append(one("span","Ориентир стоимости до Новосибирска"),one("strong",rub(nov)));
  body.append(price);
  const details=one("details",undefined,"demo-lot-details");
  const summary=one("summary","Показать полный расчёт");
  details.append(summary);
  const lines=one("div",undefined,"demo-lot-lines");
  const line=(label,val,isTotal=false)=>{const row=one("div",undefined,"demo-lot-line"+(isTotal?" is-total":""));row.append(one("span",label),one("strong",val));lines.append(row)};
  const sign=currency[v.currency]||v.currency;
  line("Ориентир начальной ставки (в итог не входит)",number(v.start_price)+" "+sign);
  line("Ориентир цены покупки (не результат реальных торгов)",number(v.sale_price)+" "+sign);
  if(v.country==="japan")line("C&F, расходы Японии + фрахт",number(v.japan_cf)+" ¥");
  else{line("Расходы в стране",number(v.export_fees)+" "+sign);line("Морской фрахт",number(v.freight)+" "+sign);}
  const euro=Math.round(v.duty_rub/92.1499),usd=Math.round(euro*1.1268);
  line("Пошлина",number(euro)+" EUR, "+number(usd)+" USD, "+rub(v.duty_rub));
  line("Утилизационный сбор",rub(v.util_rub));
  line("СБКТС и оформление — единый пакет",rub(v.sbkts_rub));
  line("СВХ",rub(v.storage_rub));
  line("Комиссия PapAuto (условно)",rub(v.commission_rub));
  line("Итого во Владивостоке",rub(vlad),true);
  line("Автовоз до Новосибирска",rub(v.truck_rub));
  line("Итого до Новосибирска",rub(nov),true);
  details.append(lines);body.append(details);
  const note=one("p","Фотографии неподходящего формата сняты с публикации. Пробег и все суммы — пример расчёта, не подтверждённая продажа и не автомобиль в наличии.","demo-lot-warning");
  const link=one("a","Запросить расчёт похожего автомобиля","demo-lot-cta");
  link.href="/?view=select&similar="+encodeURIComponent(v.make+" "+v.model+" "+v.year)+"#assistant";
  body.append(note,link);card.append(body);grid.append(card);
 }
}
[country,query].forEach(el=>el.addEventListener(el===query?"input":"change",render));
fetch("/data/demo-auction-cards.json",{cache:"no-store"}).then(r=>{if(!r.ok)throw Error("demo data unavailable");return r.json()}).then(j=>{data=Array.isArray(j.lots)?j.lots:[];render();
  const target=location.hash.slice(1);
  if(target && data.some(r=>r.id===target))
    requestAnimationFrame(()=>document.getElementById(target)?.scrollIntoView({block:"start"}))}).catch(()=>{count.textContent="Карточки автомобилей временно недоступны";});
})();