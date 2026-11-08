(() => {
  "use strict";
  // Demonstration copied from a user-provided screenshot as an arithmetic example,
  // NOT a published PapAuto price, live customs calculation or verified sale.
  const root = document.getElementById("importDemoCost");
  if (!root) return;
  const assumptions = Object.freeze({
    starting_jpy: 0,           // The provided screenshot did not state a starting bid.
    vehicle_rub: 187710,       // "Цена без учета пошлин и доставки".
    cf_jpy: 90000,             // C&F is one bundled line; never split or duplicate it.
    rub_per_jpy: 0.51,         // Historical rate shown in screenshot; not live FX.
    duty_rub: 441140,
    customs_rub: 2462,
    recycling_rub: 5200,
    broker_rub: 15000,
    registration_rub: 25000,  // One Price in screenshot: relabeled as illustrative documents.
    expertise_rub: 2000,
    storage_rub: 35000,
    certificate_rub: 26000,
    transfer_rub: 6000,
    commission_rub: 50000,    // Illustrated competitor amount, NOT official PapAuto tariff.
    trucking_rub: 145000      // Independent illustration; absent from screenshot.
  });
  const rows = [
    {key:"starting_jpy", label:"Стартовая ставка (на скриншоте не указана)", currency:"¥", group:"reference", excluded:true},
    {key:"vehicle_rub", label:"Цена автомобиля без пошлин и доставки", currency:"₽", group:"car"},
    {key:"cf_jpy", label:"C&F: расходы по Японии и перевозке — одной строкой", currency:"¥", group:"japan"},
    {key:"duty_rub", label:"Таможенная пошлина (пример: 1 496 см³, 3,2 €/см³)", currency:"₽", group:"customs"},
    {key:"customs_rub", label:"Таможенный сбор", currency:"₽", group:"customs"},
    {key:"recycling_rub", label:"Утилизационный сбор", currency:"₽", group:"customs"},
    {key:"broker_rub", label:"Услуги таможенного брокера", currency:"₽", group:"services"},
    {key:"registration_rub", label:"Оформление документов (в образце — One Price)", currency:"₽", group:"services"},
    {key:"expertise_rub", label:"Техническая экспертиза", currency:"₽", group:"services"},
    {key:"storage_rub", label:"СВХ — склад временного хранения", currency:"₽", group:"services"},
    {key:"certificate_rub", label:"СБКТС — документы на безопасность", currency:"₽", group:"services"},
    {key:"transfer_rub", label:"Перегон во Владивостоке", currency:"₽", group:"services"},
    {key:"commission_rub", label:"Комиссия компании (для примера, не тариф PapAuto)", currency:"₽", group:"services"},
    {key:"trucking_rub", label:"Автовоз Владивосток → Новосибирск (добавлено отдельно)", currency:"₽", group:"delivery"}
  ];
  const state = {...assumptions};
  const format = (value, currency) =>
    new Intl.NumberFormat("ru-RU", {maximumFractionDigits:currency==="₽"?0:2}).format(value)+" "+currency;
  const toRub = row => row.currency==="¥"
    ? Math.round(state[row.key]*state.rub_per_jpy)
    : Math.round(state[row.key]);
  const tr = {};
  for (const row of rows) {
    const line=document.createElement("tr");
    if(row.excluded) line.className="cost-reference";
    const name=document.createElement("th");name.scope="row";name.textContent=row.label;
    const source=document.createElement("td");source.className="cost-source";
    const converted=document.createElement("td");converted.className="cost-rubles";
    line.append(name,source,converted);
    root.querySelector("#importDemoRows").append(line);
    tr[row.key]={source,converted};
    if(row.key==="recycling_rub") {
      const sub=document.createElement("tr");sub.className="cost-subtotal";
      const label=document.createElement("th");label.scope="row";label.textContent="Итого таможенные платежи";
      const empty=document.createElement("td");empty.className="cost-source";
      const amount=document.createElement("td");amount.className="cost-rubles";amount.id="demoCustomsSubtotal";
      sub.append(label,empty,amount);root.querySelector("#importDemoRows").append(sub);
    }
  }
  function render(){
    for(const row of rows){
      const target=tr[row.key],value=state[row.key];
      target.source.textContent=row.currency==="¥" ? (row.excluded&&value===0?"Не указана":format(value,"¥")) : "—";
      target.converted.textContent=row.excluded&&value===0 ? "—" : format(toRub(row),"₽")+(row.excluded?" · не суммируется":"");
    }
    const sumGroup=group=>rows.filter(r=>r.group===group&&!r.excluded).reduce((sum,r)=>sum+toRub(r),0);
    const customs=sumGroup("customs");
    const vladivostok=sumGroup("car")+sumGroup("japan")+customs+sumGroup("services");
    const city=vladivostok+sumGroup("delivery");
    root.querySelector("#demoCustomsSubtotal").textContent=format(customs,"₽")+" · не добавлять повторно";
    root.querySelector("#demoVladivostokTotal").textContent=format(vladivostok,"₽");
    root.querySelector("#demoNovosibirskTotal").textContent=format(city,"₽");
    root.querySelector("#demoRate").textContent="Учебный курс из образца: 1 ¥ = "+new Intl.NumberFormat("ru-RU",{maximumFractionDigits:4}).format(state.rub_per_jpy)+" ₽";
    root.querySelector("#demoSourceReconcile").textContent=
      "На скриншоте итог таможни указан 450 802 ₽, но его три составляющие дают "+
      format(customs,"₽")+". Пересчёт ниже не дублирует эту разницу.";
  }
  const controls = new Map();
  function makeInput(key,label,step){
    const wrapper=document.createElement("label");wrapper.className="cost-field";
    const caption=document.createElement("span");caption.textContent=label;
    const input=document.createElement("input");input.type="number";input.min="0";
    input.max="100000000";input.step=step;input.value=assumptions[key];
    input.setAttribute("aria-label",label);
    input.addEventListener("input",()=>{
      if(input.value.trim()==="")return;
      const value=Number(input.value);
      if(Number.isFinite(value)&&value>=0&&value<=100000000){state[key]=value;render();}
    });
    controls.set(key,input);wrapper.append(caption,input);return wrapper;
  }
  for(const row of rows)root.querySelector("#importDemoFields").append(makeInput(
    row.key,row.label+" ("+row.currency+")",row.currency==="¥"?1000:100
  ));
  root.querySelector("#importDemoFields").append(makeInput("rub_per_jpy","Учебный курс: ₽ за 1 ¥",0.0001));
  root.querySelector("#importDemoReset").addEventListener("click",()=>{
    Object.assign(state,assumptions);
    controls.forEach((input,key)=>{input.value=assumptions[key];});
    render();
  });
  render();
})();