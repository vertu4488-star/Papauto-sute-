(() => {
  "use strict";
  // Screenshot-based arithmetic demonstration, not actual PapAuto prices or a real lot.
  // The official customs processing fee is INCLUDED inside the SBKTS + services package,
  // not in addition to it. Keep the six historical components for explanation only.
  const root = document.getElementById("importDemoCost");
  if (!root) return;
  const breakdown = Object.freeze([
    ["Таможенный сбор", 2462],
    ["Услуги таможенного брокера", 15000],
    ["Оформление One Price", 25000],
    ["Техническая экспертиза", 2000],
    ["СБКТС (сертификат)", 26000],
    ["Перегон во Владивостоке", 6000]
  ]);
  const totalPackage = breakdown.reduce((s, [,price]) => s + price, 0);
  const assumptions = Object.freeze({
    starting_jpy: 0,
    vehicle_rub: 187710,
    cf_jpy: 90000,                 // C&F already combines Japan costs and freight.
    rub_per_jpy: 0.51,             // Historical rate shown in screenshot, not live FX.
    duty_rub: 441140,
    recycling_rub: 5200,
    sbkts_package_rub: totalPackage,
    storage_rub: 35000,
    commission_rub: 50000,        // Competitor screenshot example, not PapAuto tariff.
    trucking_rub: 145000         // Separate illustrative Vladivostok-Novosibirsk tariff.
  });
  const rows = [
    {key:"starting_jpy", label:"Стартовая ставка (в образце не указана)", currency:"¥", group:"reference", excluded:true},
    {key:"vehicle_rub", label:"Цена автомобиля без пошлин и доставки", currency:"₽", group:"vehicle"},
    {key:"cf_jpy", label:"C&F — доставка и расходы по Японии, вместе", currency:"¥", group:"japan"},
    {key:"duty_rub", label:"Таможенная пошлина (1 496 см³, 3,2 €/см³ в образце)", currency:"₽", group:"customs"},
    {key:"recycling_rub", label:"Утилизационный сбор", currency:"₽", group:"customs"},
    {key:"sbkts_package_rub", label:"СБКТС и оформление — единый пакет", currency:"₽", group:"services", expandable:true},
    {key:"storage_rub", label:"СВХ — склад временного хранения", currency:"₽", group:"services"},
    {key:"commission_rub", label:"Комиссия компании (условная, не тариф PapAuto)", currency:"₽", group:"services"},
    {key:"trucking_rub", label:"Автовоз Владивосток → Новосибирск", currency:"₽", group:"delivery"}
  ];
  const state = {...assumptions};
  const num = (value, currency) =>
    new Intl.NumberFormat("ru-RU", {maximumFractionDigits:currency==="₽"?0:2}).format(value)+" "+currency;
  const toRub = row => row.currency === "¥" ?
    Math.round(state[row.key]*state.rub_per_jpy) : Math.round(state[row.key]);
  const table = root.querySelector("#importDemoRows");
  const controls = new Map();
  const displayed = new Map();

  for(const row of rows) {
    const tr = document.createElement("tr");
    if(row.excluded) tr.className="cost-reference";
    if(row.expandable) tr.className="cost-package";
    const label = document.createElement("th");
    label.scope="row";
    const labelText = document.createElement("span");
    labelText.textContent=row.label;
    label.append(labelText);
    if(row.expandable) {
      const details = document.createElement("details");
      details.className="sbkts-breakdown";
      const summary = document.createElement("summary");
      summary.textContent="Показать состав пакета";
      const list = document.createElement("ul");
      for(const [name,price] of breakdown) {
        const item=document.createElement("li");
        const nameSpan=document.createElement("span");
        nameSpan.textContent=name;
        const priceSpan=document.createElement("strong");
        priceSpan.textContent=num(price,"₽");
        item.append(nameSpan,priceSpan);
        list.append(item);
      }
      const note=document.createElement("p");
      note.textContent="Это состав исходного образца на "+num(totalPackage,"₽")+
        ". Можно изменить цену единого пакета ниже. Расшифровка останется исходной, пока не пересчитаны его отдельные услуги. Таможенный сбор — государственный платёж, а не стоимость самого сертификата СБКТС.";
      details.append(summary,list,note);
      label.append(details);
    }
    const original = document.createElement("td");
    original.className="cost-source";
    const total = document.createElement("td");
    total.className="cost-rubles";
    tr.append(label,original,total);
    table.append(tr);
    displayed.set(row.key,{original,total});
  }

  function render(){
    for(const row of rows){
      const shown=displayed.get(row.key);
      const value=state[row.key];
      shown.original.textContent=row.currency==="¥" ?
        (row.excluded&&value===0 ? "Не указана" : num(value,"¥")) : "—";
      shown.total.textContent=row.excluded&&value===0 ? "—" :
        num(toRub(row),"₽")+(row.excluded?" · не суммируется":"");
    }
    const vladivostok=rows.filter(row=>!row.excluded&&row.group!=="delivery")
      .reduce((sum,row)=>sum+toRub(row),0);
    root.querySelector("#demoVladivostokTotal").textContent=num(vladivostok,"₽");
    root.querySelector("#demoNovosibirskTotal").textContent=
      num(vladivostok+state.trucking_rub,"₽");
    root.querySelector("#demoRate").textContent="Курс из образца: 1 ¥ = "+
      new Intl.NumberFormat("ru-RU",{maximumFractionDigits:4}).format(state.rub_per_jpy)+" ₽";
    const note=root.querySelector("#demoSourceReconcile");
    if(note)note.textContent="Таможенный сбор 2 462 ₽ уже включён в пакет СБКТС, поэтому отдельно не прибавляется. "+
      "По исходному скриншоту пошлина + таможенный сбор + утильсбор дают 448 802 ₽, а не 450 802 ₽, как подписано в источнике. "+
      "Общий итог примера 841 412 ₽ во Владивостоке арифметически подтверждён.";
  }

  function addInput(key,label,step){
    const holder=document.createElement("label");
    holder.className="cost-field";
    const heading=document.createElement("span");
    heading.textContent=label;
    const input=document.createElement("input");
    input.type="number";
    input.min="0";
    input.max="100000000";
    input.step=step;
    input.value=assumptions[key];
    input.setAttribute("aria-label",label);
    input.addEventListener("input",()=>{
      const value=Number(input.value);
      if(input.value.trim()!==""&&Number.isFinite(value)&&value>=0&&value<=100000000){
        state[key]=value;render();
      }
    });
    controls.set(key,input);
    holder.append(heading,input);
    root.querySelector("#importDemoFields").append(holder);
  }
  for(const row of rows){
    addInput(row.key,row.label+" ("+row.currency+")",row.currency==="¥"?1000:100);
  }
  addInput("rub_per_jpy","Курс: ₽ за 1 ¥ (учебный)",0.0001);
  root.querySelector("#importDemoReset").addEventListener("click",()=>{
    Object.assign(state,assumptions);
    controls.forEach((input,key)=>{input.value=assumptions[key];});
    render();
  });
  render();
})();