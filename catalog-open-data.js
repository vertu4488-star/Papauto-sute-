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
  // Owner's publication rule: no real photograph + original full sheet +
  // substantive verified description = no card, no public text listing.
  const photoIndex=new Map();
  const invalidLotIds=new Set();
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
    const brands=[...new Set(rows.filter(r=>photoIndex.has(photoKey(r.market,r.brand+" "+r.model))&&
      (!country.value||r.market===country.value)).map(r=>r.brand))]
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

  const provenLot = lot => !!lot && !invalidLotIds.has(lot.id) &&
    photoAllowed(lot.photos?.[0]) && photoAllowed(lot.inspection_image) &&
    typeof lot.description==="string" && lot.description.trim().length>=50 &&
    lot.year && lot.auction && lot.lot_number &&
    lot.mileage_km!=null && lot.grade!=null;

  function photoCard(r,lot){
    const url="/lots/"+encodeURIComponent(lot.id)+".html";
    const card=label("article",undefined,"model-card");
    const group=label("div",undefined,"catalog-verified-media");
    const imglink=label("a",undefined,"model-photo");
    imglink.href=url;
    imglink.setAttribute("aria-label","Открыть оригинальное фото "+lot.model);
    const image=label("img");
    image.alt="Оригинальная фотография "+lot.model+" "+lot.year+" · лот №"+lot.lot_number;
    image.decoding="async";
    image.loading="lazy";
    image.width=450;image.height=337;
    image.addEventListener("load",()=>image.classList.add("loaded"),{once:true});
    const failed=()=>{
      invalidLotIds.add(lot.id);
      card.remove();
      render();
    };
    image.addEventListener("error",failed,{once:true});
    image.src=lot.photos[0];
    if(image.complete&&image.naturalWidth)image.classList.add("loaded");
    imglink.append(image);
    const sheetlink=label("a",undefined,"catalog-sheet-photo");
    sheetlink.href=url;
    sheetlink.setAttribute("aria-label","Открыть полный аукционный лист "+lot.model);
    const sheet=label("img");
    sheet.alt="Аукционный лист "+lot.model+" · №"+lot.lot_number;
    sheet.loading="lazy";sheet.decoding="async";
    sheet.addEventListener("error",failed,{once:true});
    sheet.src=lot.inspection_image;sheetlink.append(sheet);
    group.append(imglink,sheetlink);

    const title=label("h2",r.brand+" "+r.model);
    const details=label("p",lot.description,"catalog-lot-full-description");
    const facts=label("p",lot.auction+" · лот №"+lot.lot_number+" · "+
      new Intl.NumberFormat("ru-RU").format(lot.mileage_km)+" км · оценка "+lot.grade,
      "catalog-lot-facts");
    const doc=label("a","Оригинальное фото и полный аукционный лист →","model-request");
    doc.href=url;
    const request=label("a","Подобрать аналог →","catalog-request-link");
    request.href=requestUrl(r);
    card.append(group,label("small",markets[r.market]||r.market,"country"),title,
      label("div",r.engine,"engine"),facts,details,doc,request);
    return card;
  }

  function render(){
    const q=lower(search.value),selectedMake=lower(make.value);
    const matched=rows.filter(r=>{
      const lot=photoIndex.get(photoKey(r.market,r.brand+" "+r.model));
      return provenLot(lot) &&
        (!country.value||country.value===r.market) &&
        (!selectedMake||selectedMake===lower(r.brand)) &&
        (!q||searchText(r).includes(q)) &&
        (!power.value||types(r).includes(power.value));
    });
    matched.sort((a,b)=>a.brand.localeCompare(b.brand,"ru")||a.model.localeCompare(b.model,"ru"));
    grid.replaceChildren();
    for(const r of matched.slice(0,limit)){
      const lot=photoIndex.get(photoKey(r.market,r.brand+" "+r.model));
      grid.append(photoCard(r,lot));
    }
    count.textContent="Проверенных моделей с оригинальными фотографиями, полными листами и описанием: "+matched.length;
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
        if(lot.market!=="japan"||!lot.id||!lot.model||!provenLot(lot))continue;
        const key=photoKey(lot.market,lot.model);
        if(!photoIndex.has(key))photoIndex.set(key,lot);
      }
      fillMakes();
      render();
    })
    .catch(()=>render()); // fail closed: publish no cards when verified evidence cannot be loaded
})();