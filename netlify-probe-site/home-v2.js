(()=>{'use strict';
const $=id=>document.getElementById(id);
const models=[
 {country:'japan',make:'Toyota',model:'Corolla',details:'1,5–1,8 л · седан',photo:'/assets/demo/toyota-corolla-cc0.webp'},
 {country:'japan',make:'Honda',model:'Freed',details:'1,5 л · минивэн',photo:'/assets/demo/japan-honda-freed-cc0.webp'},
 {country:'south-korea',make:'Hyundai',model:'Avante',details:'1,6–2,0 л · седан',photo:'/assets/demo/hyundai-avante-cc0.webp'},
 {country:'china',make:'Geely',model:'Monjaro',details:'2,0 л · кроссовер',photo:'/assets/demo/geely-monjaro-cc0.webp'},
 {country:'japan',make:'Toyota',model:'Sienta',details:'1,5 л · компактвэн',photo:'/assets/demo/toyota-sienta-cc0.webp'},
 {country:'japan',make:'Honda',model:'Fit',details:'1,3–1,5 л · хэтчбек',photo:'/assets/demo/honda-fit-cc0.webp'}
];
const labels={japan:'🇯🇵 Япония','south-korea':'🇰🇷 Корея',china:'🇨🇳 Китай'};
const country=$('countryInput'),make=$('makeInput'),model=$('modelInput'),list=$('models'),chips=[...document.querySelectorAll('.chip')];
const opt=(s,v)=>new Option(s,v);
function syncOptions(){const rows=models.filter(v=>!country.value||v.country===country.value);const makes=[...new Set(rows.map(v=>v.make))].sort();const currentMake=make.value;make.replaceChildren(opt('Все марки',''),...makes.map(x=>opt(x,x)));if(makes.includes(currentMake))make.value=currentMake;const mods=[...new Set(rows.filter(v=>!make.value||v.make===make.value).map(v=>v.model))].sort();const currentModel=model.value;model.replaceChildren(opt('Все модели',''),...mods.map(x=>opt(x,x)));if(mods.includes(currentModel))model.value=currentModel;}
function imageCard(v){const card=document.createElement('article');card.className='car-card';const img=new Image();img.src=v.photo;img.width=620;img.height=410;img.loading='lazy';img.decoding='async';img.alt=v.make+' '+v.model+' — фотография модели, не конкретного лота';img.onerror=()=>{img.onerror=null;img.src='/catalog-v2-fallback.svg'};
 const pic=document.createElement('div');pic.className='car-img';pic.append(img);const countryTag=document.createElement('span');countryTag.className='car-country';countryTag.textContent=labels[v.country]||'Автомобиль';pic.append(countryTag);card.append(pic);
 const body=document.createElement('div');body.className='car-body';const h=document.createElement('h3');h.textContent=v.make+' '+v.model;body.append(h);const p=document.createElement('p');p.textContent=v.details;body.append(p);const value=document.createElement('span');value.className='price-note';value.textContent='Стоимость по запросу';body.append(value);
 const a=document.createElement('a');a.className='car-cta';a.href='/podbor.html?'+new URLSearchParams({country:v.country,make:v.make,model:v.model}).toString();a.textContent='Подобрать похожий ↗';body.append(a);card.append(body);return card;
}
function render(){const rows=models.filter(v=>!country.value||v.country===country.value);list.replaceChildren(...rows.map(imageCard));if(!rows.length){const p=document.createElement('p');p.className='no-results';p.textContent='По вашему запросу моделей не найдено.';list.append(p);}chips.forEach(chip=>{const yes=chip.dataset.country===country.value;chip.classList.toggle('active',yes);chip.setAttribute('aria-pressed',String(yes))});}
country.addEventListener('change',()=>{make.value='';model.value='';syncOptions();render()});make.addEventListener('change',syncOptions);
chips.forEach(chip=>chip.addEventListener('click',()=>{country.value=chip.dataset.country;make.value='';model.value='';syncOptions();render()}));
$('quickSearch').addEventListener('submit',e=>{e.preventDefault();const q=new URLSearchParams({section:'models'});if(country.value)q.set('country',country.value);if(make.value)q.set('make',make.value);if(model.value)q.set('search',model.value);location.assign('/catalog-v2.html?'+q.toString())});
const toggle=$('menuToggle'),nav=$('mainNav');toggle.addEventListener('click',()=>{const next=toggle.getAttribute('aria-expanded')!=='true';toggle.setAttribute('aria-expanded',String(next));nav.classList.toggle('open',next);toggle.setAttribute('aria-label',next?'Закрыть меню':'Открыть меню')});nav.addEventListener('click',e=>{if(e.target.closest('a')){nav.classList.remove('open');toggle.setAttribute('aria-expanded','false');toggle.setAttribute('aria-label','Открыть меню')}});
syncOptions();render();
})();