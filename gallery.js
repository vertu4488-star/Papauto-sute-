/* PapAuto unified auction gallery: 25 genuine home lots + 14 premium examples.
   No exterior photos, third-party outgoing links or synthesized prices. */
(() => {
 "use strict";
 const d=document,grid=d.getElementById("gallery-grid");
 if(!grid)return;
 const count=d.getElementById("gallery-count"),search=d.getElementById("gallery-search"),
  brand=d.getElementById("gallery-brand"),sort=d.getElementById("gallery-sort"),
  more=d.getElementById("gallery-more"),empty=d.getElementById("gallery-empty"),
  tabs=[...d.querySelectorAll("[data-gallery-category]")],
  viewer=d.getElementById("gallery-viewer"),viewerImage=d.getElementById("gallery-viewer-image"),
  viewerTitle=d.getElementById("gallery-viewer-title"),viewerCaption=d.getElementById("gallery-viewer-caption"),
  viewerThumbs=d.getElementById("gallery-viewer-thumbs");
 const mediaPath=/^\/assets\/(?:auction\/home|premium-auctions)\/[a-z0-9-]+\.(?:jpg|webp)$/;
 const rub=n=>new Intl.NumberFormat("ru-RU",{maximumFractionDigits:0}).format(n);
 const normal=s=>String(s||"").toLocaleLowerCase("ru");
 const validImg=s=>typeof s==="string"&&mediaPath.test(s)?s:null;
 const img=(src,alt,eager=false)=>{
   const i=d.createElement("img");i.src=src;i.alt=alt;i.decoding="async";i.loading=eager?"eager":"lazy";
   return i;
 };
 const element=(tag,cls,content)=>{
   const el=d.createElement(tag);if(cls)el.className=cls;if(content!==undefined)el.textContent=content;
   return el;
 };
 const MAX=12;
 let all=[],filtered=[],shown=MAX,category="all",view={items:[],index:0,lot:null},previousFocus=null;
 const brandName=lot=>lot.model.split(" ")[0];
 const mediaItems=lot=>[
   ...lot.photos.filter(validImg).map((url,index)=>({url,label:"Ракурс "+(index+1),kind:"photo"})),
   ...(validImg(lot.inspection_image)?[{url:lot.inspection_image,label:lot.inspection_kind==="Схема повреждений"?"Схема повреждений":"Аукционный лист",kind:"sheet"}]:[])
 ];
 const legibility=lot=>lot.status==="sold"?"Продан на аукционе":lot.sale_label;
 function setThumb(card,lot,index){
   const arr=mediaItems(lot),selected=arr[index];if(!selected)return;
   const picture=card.querySelector(".gallery-card-photo img"),bubble=card.querySelector(".gallery-photo-indicator");
   picture.src=selected.url;picture.alt=lot.model+" · "+selected.label+" · лот №"+lot.lot_number;
   bubble.textContent=selected.label;
   card.dataset.photoIndex=String(index);
   for(const b of card.querySelectorAll(".gallery-thumb"))b.setAttribute("aria-pressed",String(Number(b.dataset.index)===index));
 }
 function card(lot,i){
   const item=element("article","gallery-card");item.id="gallery-lot-"+lot.id;
   item.dataset.model=normal(lot.model);item.dataset.market=lot.market;item.dataset.galleryCategory=lot.category;
   item.dataset.lotId=lot.id;item.dataset.photoIndex="0";
   const head=element("div","gallery-card-head");
   head.append(element("span","gallery-market","🇯🇵 ЯПОНИЯ · АУКЦИОН"));
   head.append(element("span","gallery-grade","Оценка "+lot.grade));
   item.append(head);
   const photo=element("button","gallery-card-photo");photo.type="button";photo.dataset.action="view";
   photo.setAttribute("aria-label","Увеличить фотографии "+lot.model+" ("+lot.year+")");
   const cover=validImg(lot.photos[0]);if(cover)photo.append(img(cover,lot.model+" — аукционная фотография лота №"+lot.lot_number,i<3));
   photo.append(element("span","gallery-photo-indicator","Ракурс 1"));
   item.append(photo);
   const thumbs=element("div","gallery-thumbnails");
   const items=mediaItems(lot);
   items.forEach((entry,index)=>{
     const b=element("button","gallery-thumb");b.type="button";b.dataset.action="thumb";b.dataset.index=String(index);
     b.setAttribute("aria-label",lot.model+": "+entry.label);b.setAttribute("aria-pressed",String(index===0));
     const i=img(entry.url,entry.label+" "+lot.model);
     // Optional second/third angle may not exist in this build; don't leave a broken thumbnail.
     i.addEventListener("error",()=>{if(entry.kind==="photo"&&index>0)b.remove();else b.classList.add("gallery-missing-media");},{once:true});
     b.append(i);thumbs.append(b);
   });
   item.append(thumbs);
   const body=element("div","gallery-card-body");
   body.append(element("h3","",lot.model+" · "+lot.year));
   body.append(element("p","gallery-variant",legibility(lot)));
   const facts=element("div","gallery-facts");
   const fact=(label,value)=>{
     const row=element("div","gallery-fact");row.append(element("span","",label),element("strong","",value||"Не указано"));facts.append(row);
   };
   fact("Пробег",lot.mileage_km?rub(lot.mileage_km)+" км":"—");
   fact("Аукцион",lot.auction);
   fact("Кузов",lot.body||"—");
   fact("Лот · дата", "№ "+lot.lot_number+" · "+(lot.auction_date?lot.auction_date.split("-").reverse().join("."):"—"));
   body.append(facts);
   if(lot.export_restricted)body.append(element("p","gallery-card-warning","Ограничение прямого экспорта в РФ. Не предложение к поставке."));
   if(lot.inspection_kind==="Схема повреждений")body.append(element("p","gallery-card-warning","Вместо полного аукционного листа доступна только схема повреждений."));
   const price=element("div","gallery-price");price.append(element("span","","Цена торгов, без ввоза"),element("strong","",rub(lot.price_jpy)+" ¥"));
   body.append(price);item.append(body);
   const footer=element("div","gallery-card-footer");
   const details=element("button","gallery-detail","Фото и лист");details.type="button";details.dataset.action="view";
   const apply=element("a","gallery-apply","Подобрать аналог");apply.href="/podbor.html?similar="+encodeURIComponent(lot.model+" "+lot.year+" · Япония");
   footer.append(details,apply);item.append(footer);
   return item;
 }
 function draw(){
   const term=normal((search.value||"").trim());
   const mark=brand.value||"all";
   const activeCategory=["all","premium","popular"].includes(category)?category:"all";
   filtered=all.filter(lot=>(activeCategory==="all"||lot.category===activeCategory)&&
      (mark==="all"||brandName(lot)===mark)&&
      (!term||normal(lot.model+" "+lot.year+" "+lot.auction+" "+lot.lot_number).includes(term)));
   // Browser form-state restoration must never hide the complete gallery on first load.
   // When the UI says "Все", no search/brand constraints are permitted.
   if(activeCategory==="all"&&mark==="all"&&!term&&filtered.length!==all.length)filtered=all.slice();
   if(sort.value==="recommended")filtered.sort((a,b)=>(b.category==="premium")-(a.category==="premium") || b.year-a.year || b.price_jpy-a.price_jpy);
   else if(sort.value==="year")filtered.sort((a,b)=>b.year-a.year || b.price_jpy-a.price_jpy);
   else if(sort.value==="price-low")filtered.sort((a,b)=>a.price_jpy-b.price_jpy);
   else if(sort.value==="price-high")filtered.sort((a,b)=>b.price_jpy-a.price_jpy);
   const fragment=d.createDocumentFragment();
   filtered.slice(0,shown).forEach((lot,i)=>fragment.append(card(lot,i)));
   grid.replaceChildren(fragment);
   count.textContent="Найдено "+filtered.length+" автомобилей · показано "+Math.min(filtered.length,shown);
   empty.hidden=filtered.length!==0;
   more.hidden=filtered.length<=shown;more.textContent="Показать ещё "+Math.min(MAX,filtered.length-shown)+" автомобилей ↓";
 }
 function resetPage(){shown=MAX;draw();}
 function updateBrands(){
   const chosen=brand.value;
   const marks=[...new Set(all.filter(lot=>category==="all"||lot.category===category).map(brandName))].sort((a,b)=>a.localeCompare(b,"ru"));
   brand.replaceChildren(new Option("Все марки","all"),...marks.map(m=>new Option(m,m)));
   brand.value=marks.includes(chosen)?chosen:"all";
 }
 tabs.forEach(tab=>tab.addEventListener("click",()=>{
   category=tab.dataset.galleryCategory;
   tabs.forEach(t=>{const selected=t===tab;t.classList.toggle("is-active",selected);t.setAttribute("aria-pressed",String(selected));});
   updateBrands();resetPage();
 }));
 search.addEventListener("input",resetPage);brand.addEventListener("change",resetPage);sort.addEventListener("change",resetPage);
 more.addEventListener("click",()=>{shown+=MAX;draw();});
 function viewAt(index){
   if(!view.items.length)return;
   view.index=(index+view.items.length)%view.items.length;
   const entry=view.items[view.index];
   viewerImage.src=entry.url;viewerImage.alt=view.lot.model+": "+entry.label;
   viewerCaption.textContent=(view.index+1)+" / "+view.items.length+" · "+entry.label+" · "+view.lot.auction+" · лот №"+view.lot.lot_number;
   const t=d.createDocumentFragment();
   view.items.forEach((media,i)=>{
     const b=element("button","");b.type="button";b.setAttribute("aria-label",media.label);b.setAttribute("aria-pressed",String(i===view.index));
     const pic=img(media.url,media.label);b.append(pic);b.addEventListener("click",()=>viewAt(i));t.append(b);
   });
   viewerThumbs.replaceChildren(t);
 }
 function openViewer(lot,idx){
   previousFocus=d.activeElement;
   view={lot,items:mediaItems(lot),index:0};
   viewerTitle.textContent=lot.model+" · "+lot.year+" · "+lot.auction;
   viewAt(idx);
   viewer.showModal();
   d.getElementById("gallery-viewer-close").focus();
 }
 grid.addEventListener("click",event=>{
   const pressed=event.target.closest("button[data-action]");
   if(!pressed)return;
   const parent=pressed.closest(".gallery-card");
   const lot=all.find(l=>l.id===parent?.dataset.lotId);
   if(!lot)return;
   if(pressed.dataset.action==="thumb")setThumb(parent,lot,Number(pressed.dataset.index));
   else openViewer(lot,Number(parent.dataset.photoIndex)||0);
 });
 d.getElementById("gallery-viewer-close").addEventListener("click",()=>viewer.close());
 d.getElementById("gallery-viewer-prev").addEventListener("click",()=>viewAt(view.index-1));
 d.getElementById("gallery-viewer-next").addEventListener("click",()=>viewAt(view.index+1));
 viewer.addEventListener("click",event=>{if(event.target===viewer)viewer.close();});
 viewer.addEventListener("close",()=>{if(previousFocus?.isConnected)previousFocus.focus();});
 viewer.addEventListener("keydown",event=>{
   if(event.key==="ArrowLeft"){event.preventDefault();viewAt(view.index-1);}
   if(event.key==="ArrowRight"){event.preventDefault();viewAt(view.index+1);}
 });
 let touchX=null;
 viewerImage.addEventListener("touchstart",e=>{if(e.touches.length===1)touchX=e.touches[0].clientX;},{passive:true});
 viewerImage.addEventListener("touchend",e=>{if(touchX===null)return;const delta=e.changedTouches[0].clientX-touchX;touchX=null;if(Math.abs(delta)>50)viewAt(view.index+(delta<0?1:-1));},{passive:true});

 // The gallery is self-contained: no fetch race, CDN JSON failure or network dependency.
 // 39 static <article> cards remain visible if JS is unavailable or the bootstrap is bad.
 try{
   const bootstrap=d.getElementById("gallery-bootstrap");
   if(!bootstrap)throw Error("Missing static auction data");
   const data=JSON.parse(bootstrap.textContent);
   if(!Array.isArray(data.lots)||data.lots.length!==39)throw Error("Incomplete auction data");
   all=data.lots.filter(l=>l.market==="japan"&&validImg(l.photos?.[0])&&validImg(l.inspection_image)&&l.price_jpy>0);
   if(all.length!==39)throw Error("Auction-photo provenance mismatch");
   category="all";
   tabs.forEach(tab=>{
     const selected=tab.dataset.galleryCategory==="all";
     tab.classList.toggle("is-active",selected);
     tab.setAttribute("aria-pressed",String(selected));
     tab.disabled=false;
   });
   search.value="";search.disabled=false;
   sort.value="recommended";sort.disabled=false;
   updateBrands();brand.value="all";brand.disabled=false;
   draw();
 }catch(error){
   // Fail open to the factual static cards, never replace them with an empty grid.
   count.textContent="39 аукционных автомобилей · статическая галерея";
   more.hidden=true;
   console.warn("PAPAUTO_GALLERY_STATIC_FALLBACK",error.message);
 }
})();
