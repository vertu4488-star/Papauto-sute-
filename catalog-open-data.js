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
  // Locally hosted, rights-verified real CC0 model photos (not auction lot photography). Never reuse one photo for
  // another model or claim the image shows a particular sold auction vehicle.
  const photoByModel = new Map([
    ["japan|honda|freed","/assets/demo/honda-freed-hybrid-cc0.webp"],
    ["japan|toyota|prius","/assets/demo/toyota-prius-cc0.webp"],
    ["south-korea|hyundai|staria","/assets/demo/hyundai-staria-cc0.webp"],
    ["china|geely|monjaro","/assets/demo/geely-monjaro-cc0.webp"],
    ["japan|toyota|aqua","/assets/demo/toyota-aqua-cc0.webp"],
    ["japan|toyota|vitz","/assets/demo/toyota-vitz-cc0.webp"],
    ["japan|toyota|yaris","/assets/demo/toyota-yaris-cc0.webp"],
    ["japan|toyota|corolla","/assets/demo/toyota-corolla-cc0.webp"],
    ["japan|honda|vezel","/assets/demo/honda-vezel-cc0.webp"],
    ["japan|nissan|march","/assets/demo/nissan-march-cc0.webp"],
    ["south-korea|hyundai|avante / elantra","/assets/demo/hyundai-avante-cc0.webp"],
    ["south-korea|kia|k5","/assets/demo/kia-k5-cc0.webp"],
    ["south-korea|kia|sportage","/assets/demo/kia-sportage-cc0.webp"],
    ["china|byd|dolphin","/assets/demo/byd-dolphin-cc0.webp"],
    ["china|byd|qin l","/assets/demo/byd-qin-l-cc0.webp"],
    ["china|geely|coolray / binyue","/assets/demo/geely-coolray-cc0.webp"],
    ["china|changan|uni-v","/assets/demo/changan-uni-v-cc0.webp"],
    ["china|changan|uni-t","/assets/demo/changan-uni-t-cc0.webp"],
    ["china|changan|uni-z","/assets/demo/changan-uni-z-cc0.webp"],
    ["china|zeekr|007","/assets/demo/zeekr-007-cc0.webp"]
  ]);
  const photoDetail = {
    "japan|honda|freed":"demo-freed-jp",
    "japan|toyota|prius":"demo-prius-jp",
    "south-korea|hyundai|staria":"demo-staria-kr",
    "china|geely|monjaro":"demo-monjaro-cn"
  };
  const lower = value => String(value||"").normalize("NFKC").toLocaleLowerCase("ru").trim();
  const keyOf = r => [r.market,lower(r.brand),lower(r.model)].join("|");
  const isElectric = r => /электро|electric|\bev\b/i.test(r.engine);
  const label = (tag,value,css) => {
    const e=document.createElement(tag);
    if(value!==undefined)e.textContent=String(value);
    if(css)e.className=css;
    return e;
  };
  let limit = 96;

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
      (!power.value||(power.value==="ev"?isElectric(r):!isElectric(r)))
    );
    // Photograph-backed cards first, then alphabetically by brand/model.
    matched.sort((a,b)=>Number(photoByModel.has(keyOf(b)))-Number(photoByModel.has(keyOf(a)))
      ||a.brand.localeCompare(b.brand,"ru")||a.model.localeCompare(b.model,"ru"));
    grid.replaceChildren();
    for(const r of matched.slice(0,limit)){
      const card=label("article",undefined,"model-card");
      const localPhoto=photoByModel.get(keyOf(r));
      if(localPhoto){
        const frame=label("div",undefined,"model-photo");
        const img=label("img");
        img.src=localPhoto;
        img.alt=r.brand+" "+r.model+" — фотография модели, не конкретного лота";
        img.width=900; img.height=600; img.loading="lazy";img.decoding="async";
        img.addEventListener("load",()=>img.classList.add("loaded"),{once:true});
        img.addEventListener("error",()=>{frame.remove();},{once:true});
        frame.append(img,label("span","ФОТО МОДЕЛИ · CC0"));card.append(frame);
      }
      card.append(label("small",markets[r.market]||r.market,"country"),
        label("h2",r.brand+" "+r.model),
        label("div",r.engine,"engine"));
      const detailedExample=photoDetail[keyOf(r)];
      const a=label("a",detailedExample?"Фото и расчёт →":"Рассчитать подбор →","model-request");
      a.href=detailedExample?"/auction-archive.html#"+detailedExample: "/?view=select&similar="+encodeURIComponent(r.brand+" "+r.model)+"#assistant";
      card.append(a);grid.append(card);
    }
    count.textContent="Моделей в справочнике: "+matched.length+
      " · настоящих фотографий моделей: "+photoByModel.size+
      " · снимки с подтверждённой лицензией CC0";
    if(empty)empty.style.display=matched.length?"none":"block";
    if(more)more.hidden=matched.length<=limit;
  }
  country.addEventListener("change",()=>{limit=96;fillMakes();render()});
  make.addEventListener("change",()=>{limit=96;render()});
  search.addEventListener("input",()=>{limit=96;render()});
  power.addEventListener("change",()=>{limit=96;render()});
  if(more)more.addEventListener("click",()=>{limit+=96;render()});
  fillMakes();
  render();
})();