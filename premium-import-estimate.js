/* PapAuto estimate: verified auction-sale price only; NO invented customs rate or freight. */
(() => {
  "use strict";
  const root=document.getElementById("premiumImportCost");
  if(!root)return;
  const fields=[
    ["jpyRate","Курс покупки 1 ¥ в рублях",true],
    ["exportJpy","Экспорт, аукционные расходы и морской фрахт, ¥",true],
    ["dutyEur","Подтверждённая пошлина, EUR",true],
    ["eurRate","Курс 1 EUR в рублях на дату декларации",true],
    ["eurUsd","Курс 1 EUR в USD (для отображения, необязательно)",false],
    ["utilRub","Утилизационный сбор, ₽",true],
    ["customsRub","Сбор за таможенные операции, ₽",true],
    ["docsRub","Брокер, СБКТС, ЭПТС и оформление, ₽",true],
    ["bankRub","Банковские расходы, ₽",true],
    ["warehouseRub","СВХ и хранение, ₽",true],
    ["commissionRub","Комиссия PapAuto, ₽",true],
    ["truckRub","Автовоз Владивосток — Новосибирск, ₽",true]
  ];
  const money=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(Math.round(n));
  const box=document.createElement("div");box.className="pic-grid";
  const control=document.createElement("div");control.className="pic-controls";
  const pick=document.createElement("select");pick.id="picLot";pick.disabled=true;pick.setAttribute("aria-label","Выберите подтверждённый аукционный лот");
  const heading=document.createElement("label");heading.textContent="Лот из подтверждённых японских торгов";heading.append(pick);
  const fact=document.createElement("p");fact.className="pic-fact";
  const caution=document.createElement("p");caution.className="pic-caution";
  control.append(heading,fact,caution);
  const inputs=new Map();
  for(const [id,label,required] of fields){
    const wrap=document.createElement("label");
    wrap.textContent=label+(required?" *":"");
    const input=document.createElement("input");
    input.type="text";input.inputMode="decimal";input.autocomplete="off";
    input.placeholder="Введите значение";input.setAttribute("aria-label",label);
    wrap.append(input);control.append(wrap);inputs.set(id,input);
    input.addEventListener("input",calculate);
  }
  const result=document.createElement("aside");result.className="pic-result";result.setAttribute("aria-live","polite");
  const rows=[["car","Автомобиль, ₽"],["japan","Япония и фрахт, ₽"],["duty","Пошлина: EUR / USD / ₽"],["util","Утильсбор, ₽"],["fees","Оформление, комиссия и доставка, ₽"]];
  const outputs=new Map();
  for(const [id,label] of rows){
    const item=document.createElement("p");const name=document.createElement("span");name.textContent=label;
    const value=document.createElement("strong");value.textContent="—";
    item.append(name,value);result.append(item);outputs.set(id,value);
  }
  const total=document.createElement("p");total.className="pic-total";const totalLabel=document.createElement("span");totalLabel.textContent="Итог до Новосибирска";
  const totalValue=document.createElement("strong");totalValue.textContent="—";total.append(totalLabel,totalValue);result.append(total);
  const state=document.createElement("p");state.className="pic-state";state.textContent="Заполните подтверждённые тарифы. Нулевую услугу обозначьте цифрой 0.";result.append(state);
  const action=document.createElement("a");action.href="/podbor.html";action.textContent="Подобрать аналогичный автомобиль →";action.className="pic-action";result.append(action);
  box.append(control,result);root.append(box);
  let lots=[];
  const sale=lot=>{const n=Number(String(lot?.price_jpy||"").replace(/\D/g,""));return Number.isSafeInteger(n)&&n>0?n:null};
  const number=id=>{
    const raw=inputs.get(id).value.trim().replace(/[\s\u00a0]/g,"").replace(",",".");
    if(!raw)return null;
    const n=Number(raw);
    return Number.isFinite(n)&&n>=0&&n<=1000000000?n:null;
  };
  function calculate(){
    const lot=lots.find(l=>l.id===pick.value);
    outputs.forEach(node=>node.textContent="—");totalValue.textContent="—";
    if(!lot){state.textContent="Выберите доступный подтверждённый лот.";return;}
    const v=Object.fromEntries(fields.map(([id])=>[id,number(id)]));
    const missing=fields.filter(([id, ,required])=>required&&v[id]===null).length;
    if(missing||v.jpyRate!==null&&v.jpyRate<=0||v.eurRate!==null&&v.eurRate<=0||v.eurUsd!==null&&v.eurUsd<=0){
      state.textContent=missing?"Осталось заполнить обязательных полей: "+missing+". Не используйте неподтверждённые платежи.":"Курсы валют должны быть больше нуля.";
      return;
    }
    const car=sale(lot)*v.jpyRate, japan=v.exportJpy*v.jpyRate, duty=v.dutyEur*v.eurRate;
    const fees=["customsRub","docsRub","bankRub","warehouseRub","commissionRub","truckRub"].reduce((sum,id)=>sum+v[id],0);
    const sum=car+japan+duty+v.utilRub+fees;
    if(!Number.isFinite(sum)||sum>1e12){state.textContent="Некорректные значения — проверьте смету.";return;}
    outputs.get("car").textContent=money(car)+" ₽";
    outputs.get("japan").textContent=money(japan)+" ₽";
    outputs.get("duty").textContent=money(v.dutyEur)+" EUR · "+(v.eurUsd===null?"— USD":money(v.dutyEur*v.eurUsd)+" USD")+" · "+money(duty)+" ₽";
    outputs.get("util").textContent=money(v.utilRub)+" ₽";
    outputs.get("fees").textContent=money(fees)+" ₽";
    totalValue.textContent=money(sum)+" ₽";
    state.textContent="Предварительная смета по введённым данным, не оферта. Не учитывайте один сбор в двух строках.";
  }
  pick.addEventListener("change",()=>{
    const lot=lots.find(l=>l.id===pick.value);
    inputs.forEach(input=>input.value="");
    fact.textContent=lot?[lot.model,lot.year,lot.auction,"лот "+lot.lot_number,lot.mileage,
      "продан за "+money(sale(lot))+" ¥"].filter(Boolean).join(" · "):"";
    caution.textContent=lot?.export_restricted
      ?"Прямой экспорт этого исторического лота ограничен. Расчёт не означает, что поставка разрешена."
      :lot?.inspection_kind==="Схема повреждений"
      ?"Есть только схема повреждений, полный аукционный лист не подтверждён. Нужна проверка документов."
      :"Лот уже продан. Стоимость аналогичной машины и возможность ввоза нужно подтвердить отдельно.";
    calculate();
  });
  fetch("/data/premium-real-auction-lots.json",{credentials:"omit"})
    .then(response=>{if(!response.ok)throw Error("HTTP "+response.status);return response.json();})
    .then(data=>{
      lots=(Array.isArray(data.lots)?data.lots:[]).filter(l=>l.market==="japan"&&l.status==="sold"&&l.id&&sale(l));
      if(!lots.length)throw Error("No verified sale prices");
      for(const lot of lots){const opt=document.createElement("option");opt.value=lot.id;
        opt.textContent=lot.model+" · "+lot.year+" · "+lot.auction+" №"+lot.lot_number;pick.append(opt);}
      pick.disabled=false;pick.dispatchEvent(new Event("change"));
    }).catch(()=>{state.textContent="Аукционный реестр сейчас недоступен. Смета не показывается.";});
})();