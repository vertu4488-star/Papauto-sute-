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
  // Use only photos and full sheets from already published, verified auction lots.
  // A model without one stays in the text directory, never an empty photo card.
  const photoIndex = new Map();
  const modelIndex = document.createElement("div");
  modelIndex.id = "catalogModelIndex";
  modelIndex.className = "catalog-model-index";
  modelIndex.setAttribute("role", "list");
  grid.after(modelIndex);
  const lower = value => String(value||"").normalize("NFKC").toLocaleLowerCase("ru").trim();
  // Include genuine Russian make names in the catalog search index, without
  // changing the canonical Latin make/model values used by the lead form.
  const makeAliases = {
    honda:["хонда"],toyota:["тойота"],nissan:["ниссан"],mazda:["мазда"],
    subaru:["субару"],mitsubishi:["мицубиси","митсубиси"],
    suzuki:["сузуки"],daihatsu:["дайхатсу"],lexus:["лексус"],
    hyundai:["хендай","хёндэ"],kia:["киа"],bmw:["бмв"],
    audi:["ауди"],mercedes:["мерседес"],volkswagen:["фольксваген"],
    geely:["джили"],chery:["чери"],haval:["хавал"],changan:["чанган"]
  };
  const modelAliases = {
    fit:["фит"],freed:["фрид"],"freed spike":["фрид спайк"],
    corolla:["королла"],"corolla fielder":["королла филдер"],
    note:["ноут"],"cx-5":["сх5","сх-5"],prius:["приус"],aqua:["аква"],
    vezel:["везел"],jolion:["джолион"],monjaro:["монжаро"],
    "song plus":["сонг плюс"],jimny:["джимни"]
  };
  const searchText = r => {
    const brand = lower(r.brand), model = lower(r.model);
    return [brand,model,lower(r.engine),...(makeAliases[brand]||[]),
      ...(modelAliases[model]||[]),
      ...((makeAliases[brand]||[]).flatMap(alias=>
        [alias+" "+model,...(modelAliases[model]||[]).map(m=>alias+" "+m)]))
    ].join(" ");
  };
  const keyOf = r => [r.market,lower(r.brand),lower(r.model)].join("|");
  const types = r => PapAutoMetadata.modelTypes(r.market,r.brand,r.model,r.engine);
  const label = (tag,value,css) => {
    const e=document.createElement(tag);
    if(value!==undefined)e.textContent=String(value);
    if(css)e.className=css;
    return e;
  };
  const photoKey = (market, name) =>
    market+"|"+lower(name).replace(/[^a-z0-9а-яё]/g, "");
  const photoAllowed = path =>
    typeof path==="string" &&
    ["/assets/auction/home/","/assets/auction/approved/","/assets/premium-auctions/"]
      .some(prefix=>path.startsWith(prefix)) &&
    [".jpg",".jpeg",".png",".webp"].some(suffix=>path.toLowerCase().endsWith(suffix)) &&
    !path.includes("..") && !path.includes("?");
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
  const requestUrl = r =>
    "/?view=select&similar="+encodeURIComponent(r.brand+" "+r.model)+"#assistant";

  function modelRow(r){
    const row=label("div",undefined,"catalog-model-row");
    row.setAttribute("role","listitem");
    const title=label("strong",r.brand+" "+r.model);
    const meta=label("span",(markets[r.market]||r.market)+" · "+r.engine,"catalog-model-meta");
    const request=label("a","Подобрать модель","catalog-model-request");
    request.href=requestUrl(r);
    row.append(title,meta,request);
    return row;
  }

  function photoCard(r,lot){
    const card=label("article",undefined,"model-card");
    const photo=label("a",undefined,"model-photo");
    photo.href="/lots/"+encodeURIComponent(lot.id)+".html";
    photo.setAttribute("aria-label","Открыть оригинальную фотографию и аукционный лист "+lot.model);
    const image=label("img");
    image.alt="Реальное фото аукционного лота "+lot.model+" "+lot.year;
    image.loading="lazy";
    image.decoding="async";
    image.width=460;
    image.height=330;
    image.addEventListener("load",()=>image.classList.add("loaded"),{once:true});
    image.addEventListener("error",()=>{
      // Never show an empty image box when a real asset fails.
      card.remove();
      modelIndex.append(modelRow(r));
    },{once:true});
    image.src=lot.photos[0];
    if(image.complete&&image.naturalWidth)image.classList.add("loaded");
    photo.append(image);
    const name=label("h2",r.brand+" "+r.model);
    const info=label("p","Реальный аукционный лот "+lot.year+" года · фото и полный лист","catalog-lot-source");
    const doc=label("a","Фото и аукционный лист →","model-request");
    doc.href=photo.href;
    const request=label("a","Подобрать аналог →","catalog-request-link");
    request.href=requestUrl(r);
    card.append(photo,label("small",markets[r.market]||r.market,"country"),name,
      label("div",r.engine,"engine"),info,doc,request);
    return card;
  }

  function render(){
    const q=lower(search.value);
    const selectedMake=lower(make.value);
    const matched=rows.filter(r=>
      (!country.value||country.value===r.market) &&
      (!selectedMake||selectedMake===lower(r.brand)) &&
      (!q||searchText(r).includes(q)) &&
      (!power.value||types(r).includes(power.value))
    );
    matched.sort((a,b)=>a.brand.localeCompare(b.brand,"ru")||a.model.localeCompare(b.model,"ru"));
    grid.replaceChildren();
    modelIndex.replaceChildren();
    let photoCount=0;
    for(const r of matched.slice(0,limit)){
      const lot=photoIndex.get(photoKey(r.market,r.brand+" "+r.model));
      if(lot){grid.append(photoCard(r,lot));photoCount++;}
      else modelIndex.append(modelRow(r));
    }
    const hasPhoto=matched.filter(r=>photoIndex.has(photoKey(r.market,r.brand+" "+r.model))).length;
    count.textContent="Моделей: "+matched.length+
      " · с подтверждённым фото и листом: "+hasPhoto+
      " · остальные — в справочнике без пустых фотокарточек";
    modelIndex.hidden=modelIndex.children.length===0;
    grid.hidden=grid.children.length===0;
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
  if(typeof fetch==="function")fetch("/data/gallery-lots.json",{cache:"force-cache"})
    .then(response=>{if(!response.ok)throw Error("auction media registry unavailable");return response.json();})
    .then(data=>{
      for(const lot of (data.lots||[])){
        if(lot.market!=="japan"||!lot.id||!lot.model||!lot.year||
           !photoAllowed(lot.photos?.[0])||!photoAllowed(lot.inspection_image))continue;
        const key=photoKey(lot.market,lot.model);
        if(!photoIndex.has(key))photoIndex.set(key,lot);
      }
      render();
    })
    .catch(()=>render()); // fail closed: reference text only, no stock image or blank card
})();