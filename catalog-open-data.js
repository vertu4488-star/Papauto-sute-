(() => {
  "use strict";
  const SOURCE = "https://cdn.jsdelivr.net/gh/gor3a/vehicle-makes-models@main/data/json/all.json";
  const LABELS = { japan: "ЯПОНИЯ", "south-korea": "ЮЖНАЯ КОРЕЯ", china: "КИТАЙ" };
  const MAKES = {
    japan: ["Toyota","Lexus","Honda","Nissan","Mazda","Suzuki","Subaru","Mitsubishi","Daihatsu","Isuzu","Hino","Acura","Infiniti","Mitsuoka","光岡","Autozam","Eunos","Scion"],
    "south-korea": ["Hyundai","Kia","Genesis","SsangYong","KG Mobility","Daewoo","Renault Samsung","Samsung","GM Korea","Chevrolet Korea"],
    china: ["BYD","Geely","Chery","Changan","Haval","Great Wall","GWM","GAC","Hongqi","FAW","Dongfeng","Wuling","Baojun","NIO","Nio","Xpeng","XPeng","Li Auto","Li Xiang","Leapmotor","Zeekr","Lynk & Co","JAC","Jetour","Exeed","Omoda","Jaecoo","Tank","Aito","Seres","Foton","Roewe","MG","Maxus","SAIC","BAIC","JMC","Avatr","Deepal","Denza","Yangwang","Fangchengbao","Chery Exeed","Soueast","Kaiyi","Cowin","Karry","Venucia","Qoros","Hozon","Neta","Aiways","HiPhi","Voyah","M-Hero","Mengshi","Forthing","Fengon","DFSK","Landian","Bestune","Besturn","Hongqi","Jetta","Jiyue","Rox","Polestones","Onvo","Firefly","Arcfox","BAW","Borgward","Changhe","Dayun","Enovate","Everus","Gonow","Haima","Hanteng","Hawtai","Hengchi","Hengrun","Huanghai","Jinbei","King Long","Lifan","Lingbox","Nanjing","Noble","Qiantu","Ranz","Shuanghuan","Soueast","Weichai","Yema","Yudo","Zotye","ZX Auto","Zhidou","Zinoro","Zedriv","Skywell","Skyworth","Leapmotor","Polestar China","Rising Auto","Feifan","IM Motors","Jidu","Deepal","Aion","Trumpchi","Hyptec","Eon","GAC Aion","GAC Trumpchi","GAC Hyptec","BAIC BJEV","Beijing","Foton","Faw","FAW Bestune","Jiefang","Sinotruk","Higer","Yutong"]
  };
  const $ = id => document.getElementById(id);
  const grid=$("catalogGrid"), q=$("modelQuery"), country=$("countryFilter"), power=$("powerFilter"), count=$("catalogCount"), empty=$("catalogEmpty");
  if (!grid || !q || !country || !power) return;
  let rows=[], loaded=false, visibleLimit=120;
  const imageCache=new Map(), imagePending=new Set();
  let imageQueue=[], imageWorkers=0;
  const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
  function marketFor(make) {
    const name=String(make||"").toLocaleLowerCase("en");
    for (const [market,names] of Object.entries(MAKES)) if(names.some(x=>x.toLocaleLowerCase("en")===name)) return market;
    return "";
  }
  function flatten(data) {
    const out=[];
    const groups=Array.isArray(data)?data:(data?.makes||[]);
    for(const group of groups) {
      const makes=group?.makes || (group?.name && group?.models ? [group] : []);
      for(const mk of makes) {
        const make=mk.name || group.name || "";
        const market=marketFor(make); if(!market) continue;
        for(const model of (mk.models||[])) {
          for(const gen of (model.generations||[])) {
            for(const engine of (gen.engines||[])) {
              const cc=Number(engine.displacementCc);
              const electric=/electric/i.test(engine.fuelType||"") || /kwh/i.test(engine.label||"");
              if(!electric && !String(engine.label||"").trim() && (!Number.isFinite(cc) || cc<=0)) continue;
              out.push({market,make,model:model.name||"",generation:gen.name||"",year:gen.yearStart||model.yearStart||"",engine:engine.label||"Параметры не указаны",fuel:engine.fuelType||"",cc:electric?0:(Number.isFinite(cc)&&cc>0?cc:null),hp:engine.powerHp||"",transmission:engine.transmission||"",drive:engine.drivetrain||"",electric});
            }
          }
        }
      }
    }
    return out;
  }
  function render() {
    const term=q.value.trim().toLocaleLowerCase("ru");
    const filtered=rows.filter(x=>(!country.value||x.market===country.value)&&(!term||[x.make,x.model,x.generation,x.engine,x.fuel].join(" ").toLocaleLowerCase("ru").includes(term))&&(!power.value||(power.value==="ev"?x.electric:!x.electric)));
    count.textContent=loaded ? "Найдено модификаций: "+filtered.length.toLocaleString("ru-RU")+" · всего в выбранном справочнике: "+rows.length.toLocaleString("ru-RU") : "Загружаем открытую базу поколений и двигателей…";
    grid.innerHTML=filtered.slice(0,visibleLimit).map(x=>'<article class="model-card"><div class="model-photo"><img loading="lazy" alt="'+esc(x.make+' '+x.model)+'" data-model-image="'+esc(x.make+' '+x.model)+'"><span>ФОТО МОДЕЛИ</span><a class="photo-credit" target="_blank" rel="noopener" hidden></a></div><div class="country">'+LABELS[x.market]+'</div><h2>'+esc(x.make)+' '+esc(x.model)+'</h2><div class="make">'+esc(x.generation)+(x.year?' · с '+esc(x.year):'')+'</div><div class="engine">'+esc(x.engine)+'</div><div class="market">'+(x.electric?'ЭЛЕКТРОМОБИЛЬ':(x.cc?((x.cc/1000).toFixed(1)+' Л · '):'Объём не указан · ')+esc(x.fuel||'ДВС'))+'</div><div class="make">'+(x.hp?esc(x.hp)+' л.с.':'')+(x.transmission?' · '+esc(x.transmission):'')+'</div></article>').join("");
    loadModelImages();
    empty.style.display=filtered.length?"none":"block";
    empty.textContent="По выбранным параметрам модификаций не найдено.";
    const more=$("catalogMore");
    if(more){more.hidden=filtered.length<=visibleLimit;more.textContent="Показать ещё · осталось "+Math.max(0,filtered.length-visibleLimit).toLocaleString("ru-RU");}
  }
  function loadModelImages(){
    grid.querySelectorAll("img[data-model-image]").forEach(img=>{
      const key=img.dataset.modelImage;
      if(imageCache.has(key)){applyImage(img,imageCache.get(key));return;}
      if(imagePending.has(key))return;
      imagePending.add(key);img.dataset.queued="1";imageQueue.push({img,key});
    });
    pumpImages();
  }
  function applyImage(img,data){
    if(!img.isConnected||!data)return;
    img.src=data.thumb;
    img.onload=()=>{img.classList.add("loaded");const credit=img.parentElement.querySelector(".photo-credit");if(credit){credit.href=data.page;credit.textContent="Источник: Wikimedia Commons";credit.hidden=false;}};
    img.onerror=()=>img.removeAttribute("src");
  }
  function pumpImages(){
    while(imageWorkers<3&&imageQueue.length){
      const job=imageQueue.shift();imageWorkers++;
      const api="https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch="+encodeURIComponent('filetype:bitmap "'+job.key+'" car')+"&gsrnamespace=6&gsrlimit=1&prop=imageinfo&iiprop=url&iiurlwidth=720&format=json&origin=*";
      fetch(api).then(r=>{if(!r.ok)throw Error("Commons "+r.status);return r.json();}).then(data=>{
        const p=Object.values(data.query?.pages||{})[0],info=p?.imageinfo?.[0];
        const item=info?.thumburl?{thumb:info.thumburl,page:"https://commons.wikimedia.org/wiki/"+encodeURIComponent(p.title.replace(/ /g,"_"))}:null;
        imageCache.set(job.key,item);applyImage(job.img,item);
      }).catch(()=>imageCache.set(job.key,null)).finally(()=>{imagePending.delete(job.key);imageWorkers--;pumpImages();});
    }
  }
  [q,country,power].forEach(el=>el.addEventListener(el===q?"input":"change",()=>{visibleLimit=120;render();}));
  const moreButton=$("catalogMore"); if(moreButton)moreButton.addEventListener("click",()=>{visibleLimit+=120;render();});
  fetch(SOURCE).then(r=>{if(!r.ok)throw new Error("HTTP "+r.status);return r.json();}).then(data=>{const seen=new Set();rows=flatten(data).filter(x=>{const key=[x.market,x.make,x.model,x.generation,x.engine,x.fuel].join("|").toLocaleLowerCase("en");if(seen.has(key))return false;seen.add(key);return true;});loaded=true;render();}).catch(err=>{console.error("PAPAUTO open vehicle database:",err);const fallback=window.PAPAUTO_CATALOG||{};rows=[];Object.entries(fallback).forEach(([market,items])=>items.forEach(([make,model,engine])=>{const nums=[...engine.matchAll(/\d+(?:[.,]\d+)?/g)].map(v=>Number(v[0].replace(",",".")));if(/электро|EV/i.test(engine)||nums.some(n=>n<=2))rows.push({market,make,model,generation:"",year:"",engine,fuel:"",cc:0,electric:/электро|EV/i.test(engine)});}));loaded=true;count.textContent="Внешняя база временно недоступна; показан локальный справочник ("+rows.length+" записей).";render();});
  render();
})();