/* PapAuto: TEXT-ONLY 45x3 model reference list. Never render unsourced photographs. */
(()=>{'use strict';
const root=document.getElementById('market-catalog');if(!root)return;
const grid=root.querySelector('[data-selection-grid]');
const tabs=[...root.querySelectorAll('[data-selection-filter]')];
const query=root.querySelector('[data-selection-search]');
const count=root.querySelector('[data-selection-count]');
const more=root.querySelector('[data-selection-more]');
const empty=root.querySelector('[data-selection-empty]');
const FLAGS={japan:'🇯🇵 Япония',korea:'🇰🇷 Корея',china:'🇨🇳 Китай'};
const LABELS={japan:'Япония',korea:'Корея',china:'Китай'};
const initial=new URLSearchParams(window.location.search).get('market');
let records=[],market=['japan','korea','china'].includes(initial)?initial:'all',shown=12,visible=[];
const el=(tag,cls,txt)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(txt!=null)n.textContent=txt;return n};
const norm=s=>String(s||'').toLocaleLowerCase('ru').replace(/ё/g,'е').trim();
function priorityAll(data){const groups={japan:[],korea:[],china:[]};for(const x of data)groups[x.market].push(x);const out=[];for(let i=0;i<45;i++)for(const k of ['china','japan','korea'])if(groups[k][i])out.push(groups[k][i]);return out}
function row(x){
 const article=el('article','selection-model-entry');
 article.append(el('small','selection-market-text',FLAGS[x.market]),el('h3','selection-model-name',x.brand+' '+x.model),el('p','selection-engine','Двигатель: '+(x.engine||'уточняется')));
 const a=el('a','selection-cta','Найти аукционный лот ↗');
 a.href='/podbor.html?similar='+encodeURIComponent(x.brand+' '+x.model+', '+LABELS[x.market]);
 article.append(a);return article;
}
function render(){
 const list=visible.slice(0,shown);grid.replaceChildren(...list.map(row));
 count.textContent='Показано '+list.length+' из '+visible.length+' моделей (без фотографий)';
 empty.hidden=visible.length!==0;more.hidden=shown>=visible.length;
}
function filter(){
 const q=norm(query?.value);const filtered=records.filter(x=>(market==='all'||market===x.market)&&(!q||norm(x.brand+' '+x.model+' '+x.engine).includes(q)));
 visible=market==='all'?priorityAll(filtered):filtered;render();
}
tabs.forEach(b=>{
 const active=b.dataset.selectionFilter===market;b.classList.toggle('is-active',active);b.setAttribute('aria-pressed',String(active));
 b.addEventListener('click',()=>{market=b.dataset.selectionFilter;tabs.forEach(t=>{const yes=t===b;t.classList.toggle('is-active',yes);t.setAttribute('aria-pressed',String(yes))});shown=12;filter()});
});
query?.addEventListener('input',()=>{shown=12;filter()});more?.addEventListener('click',()=>{shown+=12;render()});
count.textContent='Загружаем список моделей…';
fetch('/data/papauto-expanded-45x3-2026.json',{credentials:'same-origin'}).then(r=>{if(!r.ok)throw Error('Catalog unavailable');return r.json()}).then(d=>{
 if(!Array.isArray(d.items)||d.items.length!==135||['japan','korea','china'].some(m=>d.items.filter(x=>x.market===m).length!==45))throw Error('Wrong country counts');
 if(d.items.some(x=>Object.keys(x).some(k=>/photo|image|source|url/i.test(k))))throw Error('Non-auction photo source in model directory');
 records=d.items;filter();
}).catch(()=>{count.textContent='Справочник временно недоступен';empty.hidden=false;more.hidden=true});
})();