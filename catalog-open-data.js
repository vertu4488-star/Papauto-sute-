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
    ["china|zeekr|007","/assets/demo/zeekr-007-cc0.webp"],
    ["japan|toyota|sienta","/assets/demo/toyota-sienta-cc0.webp"],
    ["japan|honda|fit","/assets/demo/honda-fit-cc0.webp"],
    ["japan|nissan|note","/assets/demo/nissan-note-cc0.webp"],
    ["japan|nissan|serena","/assets/demo/nissan-serena-cc0.webp"],
    ["japan|mazda|cx-5","/assets/demo/mazda-cx5-cc0.webp"],
    ["south-korea|kia|seltos","/assets/demo/kia-seltos-cc0.webp"],
    ["south-korea|kia|sorento","/assets/demo/kia-sorento-cc0.webp"],
    ["china|byd|song plus","/assets/demo/byd-song-plus-cc0.webp"],
    ["china|haval|jolion","/assets/demo/haval-jolion-cc0.webp"],
    ["japan|toyota|rav4","/assets/demo/toyota-rav4-cc0.webp"],
    ["japan|toyota|noah","/assets/demo/toyota-noah-cc0.webp"],
    ["japan|toyota|alphard","/assets/demo/toyota-alphard-cc0.webp"],
    ["japan|honda|stepwgn","/assets/demo/honda-stepwgn-cc0.webp"],
    ["japan|honda|n-box","/assets/demo/honda-nbox-cc0.webp"],
    ["japan|subaru|forester","/assets/demo/subaru-forester-cc0.webp"],
    ["japan|suzuki|jimny","/assets/demo/suzuki-jimny-cc0.webp"],
    ["japan|nissan|sakura","/assets/demo/nissan-sakura-cc0.webp"],
    ["japan|honda|n-wgn","/assets/demo/honda-nwgn-cc0.webp"],
    ["japan|toyota|land cruiser","/assets/demo/toyota-land-cruiser-cc0.webp"],
    ["japan|toyota|crown","/assets/demo/toyota-crown-cc0.webp"],
    ["japan|daihatsu|tanto","/assets/demo/daihatsu-tanto-cc0.webp"],
    ["japan|nissan|dayz","/assets/demo/nissan-dayz-cc0.webp"],
    ["japan|toyota|probox","/assets/demo/toyota-probox-cc0.webp"],
    ["south-korea|hyundai|tucson","/assets/demo/hyundai-tucson-cc0.webp"],
    ["south-korea|hyundai|sonata","/assets/demo/hyundai-sonata-cc0.webp"],
    ["south-korea|hyundai|santa fe","/assets/demo/hyundai-santa-fe-cc0.webp"],
    ["south-korea|hyundai|palisade","/assets/demo/hyundai-palisade-cc0.webp"],
    ["south-korea|kia|ev6","/assets/demo/kia-ev6-cc0.webp"],
    ["south-korea|kia|carnival","/assets/demo/kia-carnival-cc0.webp"],
    ["south-korea|kia|k3 / cerato","/assets/demo/kia-cerato-cc0.webp"],
    ["china|geely|atlas / boyue","/assets/demo/geely-atlas-cc0.webp"],
    ["china|geely|emgrand","/assets/demo/geely-emgrand-cc0.webp"],
    ["china|byd|yuan plus / atto 3","/assets/demo/byd-atto3-cc0.webp"],
    ["china|zeekr|001","/assets/demo/zeekr-001-cc0.webp"],
    ["china|tank|300","/assets/demo/tank-300-cc0.webp"],
    ["china|changan|cs55 plus","/assets/demo/changan-cs55plus-cc0.webp"],
    ["china|chery|tiggo 7","/assets/demo/chery-tiggo7-cc0.webp"],
    ["china|gac|trumpchi gs8","/assets/demo/gac-gs8-cc0.webp"],
    ["japan|toyota|camry","/assets/demo/toyota-camry-cc0.webp"],
    ["japan|toyota|raize","/assets/demo/toyota-raize-cc0.webp"],
    ["japan|toyota|voxy","/assets/demo/toyota-voxy-cc0.webp"],
    ["japan|toyota|corolla cross","/assets/demo/toyota-corolla-cross-cc0.webp"],
    ["japan|toyota|c-hr","/assets/demo/toyota-chr-cc0.webp"],
    ["japan|honda|civic","/assets/demo/honda-civic-cc0.webp"],
    ["japan|honda|cr-v","/assets/demo/honda-crv-cc0.webp"],
    ["japan|honda|odyssey","/assets/demo/honda-odyssey-cc0.webp"],
    ["japan|nissan|leaf","/assets/demo/nissan-leaf-cc0.webp"],
    ["japan|nissan|x-trail","/assets/demo/nissan-xtrail-cc0.webp"],
    ["japan|suzuki|swift","/assets/demo/suzuki-swift-cc0.webp"],
    ["japan|suzuki|hustler","/assets/demo/suzuki-hustler-cc0.webp"],
    ["japan|suzuki|wagon r","/assets/demo/suzuki-wagonr-cc0.webp"],
    ["japan|subaru|impreza","/assets/demo/subaru-impreza-cc0.webp"],
    ["japan|suzuki|spacia","/assets/demo/suzuki-spacia-cc0.webp"],
    ["japan|daihatsu|taft","/assets/demo/daihatsu-taft-cc0.webp"],
    ["japan|mitsubishi|outlander","/assets/demo/mitsubishi-outlander-cc0.webp"],
    ["japan|mazda|mazda3","/assets/demo/mazda-mazda3-cc0.webp"],
    ["south-korea|hyundai|ioniq 5","/assets/demo/hyundai-ioniq5-cc0.webp"],
    ["south-korea|kia|ev9","/assets/demo/kia-ev9-cc0.webp"],
    ["south-korea|kia|soul","/assets/demo/kia-soul-cc0.webp"],
    ["south-korea|genesis|gv80","/assets/demo/genesis-gv80-cc0.webp"],
    ["south-korea|kia|stinger","/assets/demo/kia-stinger-cc0.webp"],
    ["south-korea|genesis|g80","/assets/demo/genesis-g80-cc0.webp"],
    ["south-korea|genesis|gv70","/assets/demo/genesis-gv70-cc0.webp"],
    ["south-korea|kia|niro","/assets/demo/kia-niro-cc0.webp"],
    ["china|byd|seagull","/assets/demo/byd-seagull-cc0.webp"],
    ["china|changan|cs75 plus","/assets/demo/changan-cs75-plus-cc0.webp"],
    ["china|geely|tugella","/assets/demo/geely-tugella-cc0.webp"],
    ["china|changan|uni-k","/assets/demo/changan-uni-k-cc0.webp"],
    ["china|xiaomi|su7","/assets/demo/xiaomi-su7-cc0.webp"],
    ["china|xiaomi|su7 ultra","/assets/demo/xiaomi-su7-ultra-cc0.webp"],
    ["china|geely|galaxy e5","/assets/demo/geely-galaxy-e5-cc0.webp"],
    ["china|aito|m7","/assets/demo/aito-m7-cc0.webp"],
    ["china|voyah|free","/assets/demo/voyah-free-cc0.webp"],
    ["china|gac|trumpchi m8","/assets/demo/gac-m8-cc0.webp"],
    ["china|chery|arrizo 8","/assets/demo/chery-arrizo8-cc0.webp"],
    ["china|chery|arrizo 8 pro","/assets/demo/chery-arrizo8-pro-cc0.webp"],
    ["china|byd|han ev","/assets/demo/byd-han-ev-cc0.webp"],
    ["china|chery|tiggo 8 pro","/assets/demo/chery-tiggo8-pro-cc0.webp"],
    ["china|tank|400","/assets/demo/tank-400-cc0.webp"],
    ["china|byd|seal 06","/assets/demo/byd-seal06-cc0.webp"]
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
  // Show all one hundred photo-backed model cards on initial catalog load.
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
  country.addEventListener("change",()=>{limit=pageSize;fillMakes();render()});
  make.addEventListener("change",()=>{limit=pageSize;render()});
  search.addEventListener("input",()=>{limit=pageSize;render()});
  power.addEventListener("change",()=>{limit=pageSize;render()});
  if(more)more.addEventListener("click",()=>{limit+=pageSize;render()});
  fillMakes();
  render();
})();