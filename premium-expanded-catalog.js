/* PapAuto illustrated model choices: 45 Japan, 45 Korea, 45 China.
   No unverified prices, mileages, lot IDs or seller links. */
(()=>{'use strict';
const root=document.getElementById('market-catalog');
if(!root)return;
const grid=root.querySelector('[data-selection-grid]');
const tabs=[...root.querySelectorAll('[data-selection-filter]')];
const query=root.querySelector('[data-selection-search]');
const count=root.querySelector('[data-selection-count]');
const more=root.querySelector('[data-selection-more]');
const empty=root.querySelector('[data-selection-empty]');
const FLAGS={japan:'🇯🇵 Япония',korea:'🇰🇷 Корея',china:'🇨🇳 Китай'};
const LABELS={japan:'Япония',korea:'Корея',china:'Китай'};
const valid={japan:1,korea:1,china:1};
let records=[],market='all',shown=12,visible=[],generation=0;
const el=(tag,cls,txt)=>{const e=document.createElement(tag);if(cls)e.className=cls;if(txt!==undefined)e.textContent=txt;return e;};
const norm=s=>String(s||'').toLocaleLowerCase('ru').replace(/ё/g,'е').trim();
function priorityAll(data){const groups={japan:[],korea:[],china:[]};data.forEach(x=>groups[x.market].push(x));const result=[];for(let i=0;i<45;i++)for(const k of ['china','japan','korea'])if(groups[k][i])result.push(groups[k][i]);return result;}
function makeCard(x){
 const article=el('article','selection-card');
 const photo=el('div','selection-photo');
 const img=el('img');
 img.src=x.photo;img.alt='Иллюстративное фото модели '+x.brand+' '+x.model+', не конкретный лот';
 img.loading='lazy';img.decoding='async';
 const badge=el('span','selection-market',FLAGS[x.market]);photo.append(img,badge);
 const body=el('div','selection-card-body');
 const title=el('h3','',x.model);
 const brand=el('p','selection-brand',x.brand);
 const engine=el('p','selection-engine','Версии: '+(x.engine||'уточняются'));
 const note=el('p','selection-note','Фото модели · цену и пробег уточняем');
 const cta=el('a','selection-cta','Подобрать такую модель ↗');
 cta.href='/podbor.html?similar='+encodeURIComponent(x.brand+' '+x.model+', '+LABELS[x.market]+', двигатель '+x.engine);
 body.append(title,brand,engine,note,cta);
 article.append(photo,body);
 return article;
}
function filter(){
 const q=norm(query?.value||'');
 const f=records.filter(x=>(market==='all'||market===x.market)&&(!q||norm(x.brand+' '+x.model+' '+x.engine).includes(q)));
 visible=market==='all'?priorityAll(f):f;
 render();
}
function render(){
 const slice=visible.slice(0,shown);
 grid.replaceChildren(...slice.map(makeCard));
 count.textContent='Показано '+slice.length+' из '+visible.length+' моделей для подбора';
 empty.hidden=visible.length>0;
 more.hidden=shown>=visible.length;
}
tabs.forEach(btn=>btn.addEventListener('click',()=>{
 market=btn.dataset.selectionFilter;
 tabs.forEach(x=>{const on=x===btn;x.classList.toggle('is-active',on);x.setAttribute('aria-pressed',String(on));});
 shown=12;filter();
}));
query?.addEventListener('input',()=>{shown=12;filter()});
more.addEventListener('click',()=>{shown+=12;render()});
count.textContent='Загружаем модели из Японии, Кореи и Китая…';
fetch('/data/papauto-expanded-45x3-2026.json',{credentials:'same-origin'})
.then(r=>{if(!r.ok)throw Error('Catalogue data unavailable');return r.json()})
.then(data=>{
 const list=data.items||[];
 if(list.length!==135||['japan','korea','china'].some(m=>list.filter(x=>x.market===m).length!==45))throw Error('Incorrect market counts');
 records=list.filter(x=>valid[x.market]&&/^\/assets\/demo\/[a-z0-9-]+\.webp$/.test(x.photo));
 if(records.length!==135)throw Error('Unsafe media path in model index');
 filter();
}).catch(()=>{
 count.textContent='Не удалось загрузить каталог моделей';
 empty.hidden=false;empty.textContent='Каталог временно недоступен. Все модели доступны на странице общего каталога PapAuto.';
 more.hidden=true;
});
})();
