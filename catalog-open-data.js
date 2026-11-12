(() => {
  "use strict";
  // PapAuto own model index: no remote photos, no outgoing seller URLs.
  const by = id => document.getElementById(id);
  const grid = by("catalogGrid"), search = by("modelQuery"), country = by("countryFilter");
  const make = by("makeFilter"), power = by("powerFilter"), count = by("catalogCount");
  const empty = by("catalogEmpty"), more = by("catalogMore");
  if (!grid || !search || !country || !make || !power || !count) return;

  const markets = {japan:"ЯПОНИЯ", "south-korea":"ЮЖНАЯ КОРЕЯ", china:"КИТАЙ"};
  const rows = Object.entries(window.PAPAUTO_CATALOG || {}).flatMap(([market, data]) =>
    (Array.isArray(data) ? data : []).map(([brand, model, engine]) =>
      ({market,brand,model,engine:engine||"Характеристики уточняются"})));
  // Text-only model reference; auction photos are not guessed from model names.
  const photoDetail = Object.create(null);
  const lower = value => String(value||"").normalize("NFKC").toLocaleLowerCase("ru").trim();
  const keyOf = r => [r.market,lower(r.brand),lower(r.model)].join("|");
  const types = r => PapAutoMetadata.modelTypes(r.market,r.brand,r.model,r.engine);
  const label = (tag,value,css) => {
    const e=document.createElement(tag);
    if(value!==undefined)e.textContent=String(value);
    if(css)e.className=css;
    return e;
  };
  // Show text-only models, with real auction photos reserved for confirmed lots.
  const pageSize = 120;
  let limit = pageSize;

  function fillMakes(){
    const selected=make.value;
    const brands=[...new Set(rows.filter(r=>!country.value||r.market===country.value).map(r=>r.brand))]
      .sort((a,b)=>a.localeCompare(b,"ru"));
    make.replaceChildren(label("option","Все марки"));
    make.firstChild.value="";
    for(const brand of brands){
      const option=label("option",brand);option.value=brand;make.append(option);
    }
    if(brands.includes(selected))make.value=selected;
    else make.value="";
  }
  function render(){
    const q=lower(search.value);
    const selectedMake=lower(make.value);
    const matched=rows.filter(r=>
      (!country.value||country.value===r.market) &&
      (!selectedMake||selectedMake===lower(r.brand)) &&
      (!q||lower(r.brand+" "+r.model+" "+r.engine).includes(q)) &&
      (!power.value||types(r).includes(power.value))
    );
    // All model cards sorted by name, not legacy stock photograph availability.
    matched.sort((a,b)=>a.brand.localeCompare(b.brand,"ru")||a.model.localeCompare(b.model,"ru"));
    grid.replaceChildren();
    for(const r of matched.slice(0,limit)){
      const card=label("article",undefined,"model-card");
      // Прежние фотографии сняты с публикации до получения качественных аукционных кадров.
      card.append(label("small",markets[r.market]||r.market,"country"),
        label("h2",r.brand+" "+r.model),
        label("div",r.engine,"engine"),
        label("p","Варианты двигателя: "+PapAutoMetadata.fuelLabel(types(r)),"vehicle-fuel"),
        label("p","Документы: проверяются для выбранного автомобиля.","vehicle-documents"));
      const detailedExample=photoDetail[keyOf(r)];
      const a=label("a",detailedExample?"Пример расчёта →":"Рассчитать подбор →","model-request");
      a.href=detailedExample?"/auction-archive.html#"+detailedExample: "/?view=select&similar="+encodeURIComponent(r.brand+" "+r.model)+"#assistant";
      card.append(a);grid.append(card);
    }
    count.textContent="Моделей в справочнике: "+matched.length+
      " · аукционные фотографии будут добавлены после проверки прав";
    if(empty)empty.style.display=matched.length?"none":"block";
    if(more)more.hidden=matched.length<=limit;
  }
  country.addEventListener("change",()=>{limit=pageSize;fillMakes();render()});
  make.addEventListener("change",()=>{limit=pageSize;render()});
  search.addEventListener("input",()=>{limit=pageSize;render()});
  power.addEventListener("change",()=>{limit=pageSize;render()});
  if(more)more.addEventListener("click",()=>{limit+=pageSize;render()});
  fillMakes();
  render();
})();