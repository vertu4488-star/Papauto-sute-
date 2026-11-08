(() => {
  "use strict";
  const root = document.getElementById("importDemoCost");
  if (!root) return;
  const assumptions = {
    starting_jpy: 800000,
    sale_jpy: 1000000,
    japan_jpy: 100000,
    freight_jpy: 58000,
    rub_per_jpy: 0.55,
    bank_rub: 10000,
    duty_rub: 235000,
    recycling_rub: 5200,
    customs_rub: 5000,
    vladivostok_rub: 65000,
    commission_rub: 50000,
    trucking_rub: 145000
  };
  const rows = [
    {key:"starting_jpy", label:"Стартовая цена на аукционе", currency:"¥", group:"auction", excluded:true},
    {key:"sale_jpy", label:"Цена продажи (условная)", currency:"¥", group:"auction"},
    {key:"japan_jpy", label:"Аукционный сбор, доставка и расходы по Японии", currency:"¥", group:"japan"},
    {key:"freight_jpy", label:"Морской фрахт до Владивостока", currency:"¥", group:"japan"},
    {key:"bank_rub", label:"Банковский перевод и конвертация", currency:"₽", group:"japan"},
    {key:"duty_rub", label:"Таможенная пошлина — пример", currency:"₽", group:"russia"},
    {key:"recycling_rub", label:"Утилизационный сбор — пример", currency:"₽", group:"russia"},
    {key:"customs_rub", label:"Таможенный сбор за оформление — пример", currency:"₽", group:"russia"},
    {key:"vladivostok_rub", label:"СВХ, брокер, лаборатория, СБКТС, ЭПТС и перегон", currency:"₽", group:"russia"},
    {key:"commission_rub", label:"Комиссия PapAuto — условное значение", currency:"₽", group:"russia"},
    {key:"trucking_rub", label:"Автовоз Владивосток → Новосибирск", currency:"₽", group:"city"}
  ];
  const state = {...assumptions};
  const n = (value, currency) => new Intl.NumberFormat("ru-RU", {
    maximumFractionDigits:currency==="₽" ? 0 : 2
  }).format(value) + " " + currency;
  const rub = key => key.endsWith("_jpy") ? Math.round(state[key] * state.rub_per_jpy) : state[key];
  const tr = {};
  const rowKey = key => rows.find(r => r.key === key);
  for (const r of rows) {
    const line = document.createElement("tr");
    if (r.excluded) line.className="cost-reference";
    const name=document.createElement("th"); name.scope="row"; name.textContent=r.label;
    const source=document.createElement("td"); source.className="cost-source";
    const total=document.createElement("td"); total.className="cost-rubles";
    line.append(name,source,total);
    root.querySelector("#importDemoRows").append(line);
    tr[r.key]={source,total};
  }
  const makeInput=(key,label,step)=>{
    const wrapper=document.createElement("label");wrapper.className="cost-field";
    const caption=document.createElement("span");caption.textContent=label;
    const input=document.createElement("input");input.type="number";input.min="0";input.max="100000000";input.step=step;input.value=assumptions[key];
    input.setAttribute("aria-label",label);
    input.addEventListener("input",()=>{
      const value=Number(input.value);
      if(Number.isFinite(value)&&value>=0&&value<=100000000){state[key]=value;render();}
    });
    wrapper.append(caption,input);return wrapper;
  };
  for(const row of rows){
    const postfix=row.currency==="¥"?" (¥)":" (₽)";
    root.querySelector("#importDemoFields").append(makeInput(row.key,row.label+postfix,1000));
  }
  root.querySelector("#importDemoFields").append(makeInput("rub_per_jpy","Учебный курс: ₽ за 1 ¥",0.0001));
  const update=(id,value)=>{root.querySelector("#"+id).textContent=n(value,"₽")};
  function render(){
    for(const row of rows){
      const value=state[row.key],dest=tr[row.key];
      dest.source.textContent=row.currency==="¥"?n(value,"¥"): "—";
      dest.total.textContent=n(rub(row.key),"₽")+(row.excluded?" · не суммируется":"");
    }
    const beforeCity=rows.filter(r=>!r.excluded&&r.group!=="city").reduce((s,r)=>s+rub(r.key),0);
    update("demoVladivostokTotal",beforeCity);
    update("demoNovosibirskTotal",beforeCity+state.trucking_rub);
    root.querySelector("#demoRate").textContent="1 ¥ = "+new Intl.NumberFormat("ru-RU",{maximumFractionDigits:4}).format(state.rub_per_jpy)+" ₽ (условный курс)";
  }
  const reset=root.querySelector("#importDemoReset");
  reset.addEventListener("click",()=>{Object.assign(state,assumptions);root.querySelectorAll(".cost-field input").forEach((i,index)=>{const keys=[...rows.map(r=>r.key),"rub_per_jpy"];i.value=assumptions[keys[index]]});render()});
  render();
})();