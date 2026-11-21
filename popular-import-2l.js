(()=>{
  "use strict";
  const grid=document.getElementById("carGrid"),
    buttons=[...document.querySelectorAll("[data-country]")],
    search=document.getElementById("modelFilter"),
    top=document.getElementById("topOnly"),
    count=document.getElementById("resultCount"),
    empty=document.getElementById("noResults");
  if(!grid||!search||!top||!count||!empty)return;
  const cards=[...grid.querySelectorAll(".model-reference")];
  const directory=document.createElement("div");
  directory.id="popularModelDirectory";
  directory.className="popular-model-directory";
  directory.setAttribute("role","list");
  grid.after(directory);
  for(const card of cards){card.setAttribute("role","listitem");directory.append(card);}
  let selected="all";
  const key=(market,model)=>market+"|"+String(model||"").toLowerCase().normalize("NFKC").replace(/[^a-z0-9а-яё]/g,"");
  const allowed=url=>typeof url==="string"&&
    ["/assets/auction/home/","/assets/auction/approved/","/assets/premium-auctions/"]
      .some(prefix=>url.startsWith(prefix)) &&
    [".jpg",".jpeg",".png",".webp"].some(suffix=>url.toLowerCase().endsWith(suffix)) &&
    !url.includes("..") && !url.includes("?");

  function render(){
    let shown=0;
    const needle=search.value.normalize("NFKC").toLocaleLowerCase("ru").trim();
    for(const card of cards){
      const ok=(selected==="all"||card.dataset.market===selected)&&
        (!top.checked||card.dataset.tier==="A")&&
        (!needle||card.dataset.name.includes(needle));
      card.hidden=!ok;
      if(ok)shown++;
    }
    count.textContent="Показано "+shown+" из "+cards.length+
      " моделей · аукционные фото — только у подтверждённых лотов";
    empty.hidden=shown>0;
    directory.hidden=!cards.some(c=>c.classList.contains("model-reference")&&!c.hidden);
    grid.hidden=!cards.some(c=>c.classList.contains("car-card")&&!c.hidden);
    for(const button of buttons){
      const active=button.dataset.country===selected;
      button.classList.toggle("active",active);
      button.setAttribute("aria-pressed",String(active));
    }
  }

  function publishVerifiedPhoto(card,lot){
    if(!allowed(lot.photos?.[0])||!allowed(lot.inspection_image))return;
    // Preload before displaying a picture card; failed assets remain simple text rows.
    const image=new Image();
    image.alt="Оригинальное фото аукционного лота "+lot.model+" "+lot.year;
    image.decoding="async";
    image.onload=()=>{
      if(!image.naturalWidth)return;
      const photo=document.createElement("div");photo.className="photo verified-auction-photo";
      const link=document.createElement("a");
      link.href="/lots/"+encodeURIComponent(lot.id)+".html";
      link.setAttribute("aria-label","Открыть фото и аукционный лист "+lot.model);
      link.append(image);
      const tag=document.createElement("span");
      tag.textContent="Аукционный пример "+lot.year+" · не в наличии";
      photo.append(link,tag);
      card.prepend(photo);
      const source=document.createElement("a");source.className="verified-document-link";
      source.href=link.href;source.textContent="Оригинальное фото и полный аукционный лист →";
      card.querySelector(".car-info")?.append(source);
      card.classList.replace("model-reference","car-card");
      card.removeAttribute("role");
      grid.append(card);
      render();
    };
    image.onerror=()=>{}; // Keep text directory; never show an empty image box.
    image.src=lot.photos[0];
  }

  for(const button of buttons)button.addEventListener("click",()=>{
    selected=button.dataset.country;render();
  });
  search.addEventListener("input",render);
  top.addEventListener("change",render);
  render();
  fetch("/data/gallery-lots.json",{cache:"force-cache"}).then(r=>{
    if(!r.ok)throw Error("archive not available");
    return r.json();
  }).then(data=>{
    const photos=new Map();
    for(const lot of (data.lots||[])){
      if(lot.market!=="japan"||!lot.model||!lot.id||
        !allowed(lot.photos?.[0])||!allowed(lot.inspection_image))continue;
      const k=key(lot.market,lot.model);
      if(!photos.has(k))photos.set(k,lot);
    }
    for(const card of cards){
      const lot=photos.get(key(card.dataset.market,card.dataset.name));
      if(lot)publishVerifiedPhoto(card,lot);
    }
  }).catch(()=>{}); // Fail closed. Text references, not arbitrary stock photos.
})();
