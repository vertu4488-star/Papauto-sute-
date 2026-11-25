/* Quick quote: reuse the calculator's tariff engines, no duplicate rate tables. */
(function(root,factory){
 if(typeof module!=="undefined"&&module.exports)module.exports=factory(require("./papauto-customs.js"),require("./papauto-japan-tariffs.js"),require("./papauto-delivery-tariffs.js"));
 else root.PapAutoQuickQuote=factory(root.PapAutoCustoms,root.PapAutoJapanTariffs,root.PapAutoDeliveryTariffs);
})(typeof window!=="undefined"?window:globalThis,function(customs,japan,delivery){
 "use strict";
 const positive=n=>Number.isFinite(n)&&n>0;
 function quote(x,fx,tariffs,options={}){
  const pending=reason=>({total:null,reason});
  if(x.market!=="japan"||x.currency!=="JPY")return pending("Для этого направления требуется отдельная смета.");
  if(x.restricted!==false)return pending("Возможность экспорта требует проверки.");
  if(!customs||!japan||!delivery)return pending("Модули расчёта недоступны.");
  if(x.type!=="ice")return pending(x.type==="hybrid"||x.type==="ev"?"Гибрид или электромобиль: отдельный таможенный расчёт.":"Уточните тип двигателя.");
  if(!Number.isInteger(Number(x.engine))||!positive(Number(x.engine))||!positive(Number(x.power)))return pending("Уточните точный объём и мощность.");
  if(!fx||fx.fallback||!fx.date||![fx.rub_per_jpy,fx.rub_per_usd,fx.rub_per_eur].every(v=>positive(Number(v))))return pending("Нет актуальных справочных курсов для полной сметы.");
  const clear=customs.parseDate(options.clearDate);
  if(!clear)return pending("Уточните дату оформления.");
  const build=customs.parseDate(x.buildDate);
  if(build&&build.getUTCFullYear()!==Number(x.year))return pending("Дата изготовления не совпадает с годом.");
  const age=build?customs.ageAt(build,clear):customs.ageByYear(Number(x.year),clear);
  if(!age)return pending("Уточните месяц изготовления для определения возрастной ставки.");
  const base=Math.round(Number(x.amount)*Number(fx.rub_per_jpy));
  if(!positive(base))return pending("Нет подтверждённой цены автомобиля.");
  const c=customs.estimate({cc:Number(x.engine),hp:Number(x.power),age,year:clear.getUTCFullYear(),eur:Number(fx.rub_per_eur),value:base,eligibility:options.eligibility||"",type:"ice"});
  if([c.duty,c.fee,c.util].some(v=>!Number.isFinite(v)))return pending(c.reason.join(" ")||"Таможенные расходы требуют уточнения.");
  const j=japan.calculate({...japan.defaults,auctionYen:Number(x.amount),jpyRate:Number(fx.rub_per_jpy),usdRate:Number(fx.rub_per_usd)});
  const kind=delivery.classify(x.name,x.bodyType);
  const truck=delivery.quote(tariffs,"Новосибирск",kind,"vlad");
  if(!truck||!Number.isFinite(truck.estimate))return pending("Уточните класс и тариф автовоза.");
  const costs={car:base,japan:j.origin,shipping:j.shipping,bank:j.bank,docs:j.docs,duty:c.duty,customsFee:c.fee,util:c.util,commission:50000,delivery:truck.estimate};
  if(Object.values(costs).some(v=>!Number.isFinite(v)||v<0))return pending("Не все стандартные расходы рассчитаны.");
  return {total:Object.values(costs).reduce((a,b)=>a+b,0),costs,reason:"",age,kind};
 }
 return {quote};
});
