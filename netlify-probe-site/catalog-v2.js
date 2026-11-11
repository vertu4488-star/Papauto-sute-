(()=>{
'use strict';
const $=id=>document.getElementById(id);
const countries={japan:'Япония','south-korea':'Южная Корея',china:'Китай'};
const money=n=>new Intl.NumberFormat('ru-RU',{maximumFractionDigits:0}).format(n)+' ₽';
const fmt=n=>new Intl.NumberFormat('ru-RU',{maximumFractionDigits:0}).format(n);
const symbols={JPY:'¥',KRW:'₩',CNY:'¥'};
const icon='<svg aria-hidden="true" viewBox="0 0 320 155" fill="none" xmlns="http://www.w3.org/2000/svg"><path d="M28 102h22l31-45c6-8 13-12 24-12h98c12 0 22 5 28 13l33 44h27c10 0 16 9 16 18v12H14v-13c0-10 4-17 14-17Z" fill="#92A9BE" stroke="#607D98" stroke-width="5"/><path d="m100 57-23 44h156l-29-44H100Z" fill="#D5E1EA"/><circle cx="73" cy="130" r="20" fill="#355877"/><circle cx="248" cy="130" r="20" fill="#355877"/></svg>';
const params=new URLSearchParams(location.search);
const startingTab=['samples','models','archive'].includes(params.get('section'))?params.get('section'):'samples';
const state={tab:startingTab,country:params.get('country')||'',make:params.get('make')||'',search:params.get('search')||'',year:params.get('year')||'',budget:params.get('budget')||'',sort:params.get('sort')||'default',visibleModels:12};
let catalog={samples:[],models:[],approved_lots:[]};
function node(tag,cls,text){const e=document.createElement(tag);if(cls)e.className=cls;if(text!==undefined)e.textContent=String(text);return e}
function add(parent,tag,cls,text){const e=node(tag,cls,text);parent.append(e);return e}
function modelUrl(v){const q=new URLSearchParams({country:v.country,make:v.make,model:v.model});if(v.year)q.set('year',v.year);return '/podbor.html?'+q.toString()}
function numVal(v){return Number.isFinite(Number(v))?Number(v):0}
function calc(v){const rate=(n)=>Math.round(numVal(n)*numVal(v.rate_n)/numVal(v.rate_d));const lines=[];
 const purchase=rate(v.sale_price);lines.push(['Стоимость авто (учебный сценарий)',purchase]);
 if(v.country==='japan'){lines.push(['Расходы в Японии + фрахт (C&F)',rate(v.japan_cf)]);}
 else{lines.push(['Расходы в стране покупки',rate(v.export_fees)]);lines.push(['Международная перевозка',rate(v.freight)]);}
 lines.push(['Таможенная пошлина (учебная)',numVal(v.duty_rub)]);
 lines.push(['Утилизационный сбор (учебный)',numVal(v.util_rub)]);
 lines.push(['СБКТС и сопутствующее оформление (пакет)',numVal(v.sbkts_rub)]);
 lines.push(['СВХ и хранение',numVal(v.storage_rub)]);
 lines.push(['Комиссия компании (условная)',numVal(v.commission_rub)]);
 const vlad=lines.reduce((s,r)=>s+r[1],0);const truck=numVal(v.truck_rub);
 return {lines,purchase,vlad,truck,nov:vlad+truck,rate:numVal(v.rate_n)+'/'+numVal(v.rate_d)};
}
function countryFlag(code){return {japan:'🇯🇵','south-korea':'🇰🇷',china:'🇨🇳'}[code]||'•'}
function mini(label){const item=node('div','mini-item');const pic=node('img');pic.src='/catalog-v2-fallback.svg';pic.alt='';pic.loading='lazy';const txt=node('span','',label);item.append(pic,txt);return item}
function spec(parent,label,value){const row=node('div','spec-item');row.append(node('span','',label),node('b','',value));parent.append(row)}
function priceLine(parent,label,value){const r=node('div','price-line');r.append(node('span','',label),node('strong','',value));parent.append(r)}
function button(label,cl,action){const b=node('button','btn '+cl,label);b.type='button';b.addEventListener('click',action);return b}
function createSample(v){const c=calc(v);const outer=node('article','vehicle-card');outer.id=v.id;
 const main=add(outer,'div','vehicle-card-main');
 const gallery=add(main,'div','gallery');const gp=add(gallery,'div','gallery-main');
 const image=node('img');image.alt='Фотография модели '+v.make+' '+v.model+' — не фотография указанного лота';image.loading='lazy';image.decoding='async';image.src=v.image;image.onerror=()=>{image.onerror=null;image.src='/catalog-v2-fallback.svg';image.classList.add('gallery-fallback')};gp.append(image,add(gp,'span','image-label','Фото модели · CC0'));
 const minis=add(gallery,'div','gallery-mini');minis.append(mini('Салон · ожидается'),mini('Второй ракурс · ожидается'));
 const body=add(main,'div','card-body');const head=add(body,'div','card-head');const left=add(head,'div');add(left,'div','badge-flag',countryFlag(v.country)+' '+countries[v.country]+' · ПОД ЗАКАЗ');add(left,'h3','',v.make+' '+v.model);add(left,'div','card-kicker',v.engine);
 const save=node('button','save-button','☆');save.type='button';save.setAttribute('aria-label','Добавить в избранное (только в этой вкладке)');save.setAttribute('aria-pressed','false');save.addEventListener('click',()=>{const val=save.getAttribute('aria-pressed')!=='true';save.setAttribute('aria-pressed',String(val));save.textContent=val?'★':'☆'});head.append(save);
 const specs=add(body,'div','spec-table');spec(specs,'Год','пример: '+v.year);spec(specs,'Пробег','пример: '+fmt(v.mileage_km)+' км');spec(specs,'Кузов',v.body);spec(specs,'Двигатель',v.engine);spec(specs,'Страна',countries[v.country]);spec(specs,'Торги','не подтверждены');
 add(body,'p','card-footnote','Снимок относится к модели, но не подтверждает конкретный лот или его состояние. Другие ракурсы не подменяем чужими кадрами.');
 const pricing=add(main,'aside','pricebox');const priceHead=add(pricing,'div','pricehead');priceHead.append(node('span','','ДЕМОНСТРАЦИОННЫЙ РАСЧЁТ'),node('span','tag','Не цена сделки'));
 priceLine(pricing,'Начальная ставка (пример)',fmt(v.start_price)+' '+symbols[v.currency]);priceLine(pricing,'Условная цена покупки',fmt(v.sale_price)+' '+symbols[v.currency]);priceLine(pricing,'Курс для расчёта','Учебный');
 const final=add(pricing,'div','price-total');add(final,'small','Пример до Новосибирска');add(final,'strong','',money(c.nov));add(final,'em','','Не оферта · не фактическая цена продажи');
 const actions=add(pricing,'div','price-actions');let costButton;
 const open=()=>{const isOpen=outer.classList.toggle('open');costButton.setAttribute('aria-expanded',String(isOpen));costButton.textContent=isOpen?'Свернуть расходы ↑':'Все расходы ↓';if(isOpen&&window.matchMedia('(max-width:680px)').matches){setTimeout(()=>panel.scrollIntoView({block:'nearest',behavior:'smooth'}),0)}};
 costButton=button('Все расходы ↓','primary',open);costButton.setAttribute('aria-expanded','false');actions.append(costButton);
 const link=node('a','btn secondary','Подобрать похожий ↗');link.href=modelUrl(v);actions.append(link);
 const panel=add(outer,'div','cost-panel');panel.setAttribute('aria-label','Подробные расходы '+v.make+' '+v.model);const inner=add(panel,'div','cost-panel-inner');const costBody=add(inner,'div');const costHead=add(costBody,'div','cost-heading');add(costHead,'h4','','Все расходы');const close=add(costHead,'button','cost-close','×');close.type='button';close.setAttribute('aria-label','Закрыть расходы');close.addEventListener('click',open);
 add(costBody,'p','cost-sub','Образец расчёта, не подтверждённый тариф PapAuto. Суммы показаны, чтобы согласовать структуру и логику будущего калькулятора.');
 const table=add(costBody,'table','cost-table');const tb=add(table,'tbody');function tr(label,value){const row=add(tb,'tr');add(row,'th','',label);add(row,'td','',money(value))}c.lines.forEach(([l,val])=>tr(l,val));
 tr('Итого во Владивостоке',c.vlad);tr('Автовоз Владивосток → Новосибирск',c.truck);
 const side=add(inner,'aside','cost-side');add(side,'small','','Стоимость учебного сценария');const switcher=add(side,'div','city-picker');const vButton=button('Владивосток','',()=>setCity('vl'));const nButton=button('Новосибирск','',()=>setCity('nsk'));switcher.append(vButton,nButton);const label=add(side,'small','','Итого до Новосибирска');const total=add(side,'strong','',money(c.nov));add(side,'div','divider');const nrow=add(side,'div','sub-total');nrow.append(node('span','','До Владивостока'),node('b','',money(c.vlad)));const crow=add(side,'div','sub-total');crow.append(node('span','','Доставка до Новосибирска'),node('b','',money(c.truck)));
 const rate=add(side,'p','cost-note','');rate.textContent='Расчётный курс '+v.currency+': '+v.rate_n+'/'+v.rate_d+' ₽ за 1 '+v.currency+' (учебный, не текущий курс ЦБ). Таможенные суммы в примере не проверены по действующим нормам.';
 const cta=node('a','btn primary','Запросить точный расчёт ↗');cta.href=modelUrl(v);side.append(cta);
 function setCity(city){label.textContent=city==='nsk'?'Итого до Новосибирска':'Итого до Владивостока';total.textContent=money(city==='nsk'?c.nov:c.vlad);vButton.classList.toggle('active',city==='vl');nButton.classList.toggle('active',city==='nsk');vButton.setAttribute('aria-pressed',String(city==='vl'));nButton.setAttribute('aria-pressed',String(city==='nsk'))}setCity('nsk');
 return outer;
}
function createModel(v){const c=node('article','model-card');const art=add(c,'div','model-art');art.innerHTML=icon;const body=add(c,'div','model-card-body');add(body,'div','model-card-country',countryFlag(v.country)+' '+countries[v.country]);add(body,'h3','',v.make+' '+v.model);add(body,'p','',v.engine_range==='требует уточнения'?'Характеристики уточняются':'Варианты двигателя: '+v.engine_range);
 const link=node('a','btn secondary','Подобрать модель ↗');link.href=modelUrl(v);body.append(link);return c}
function safeTab(){return ['samples','models','archive'].includes(state.tab)?state.tab:'samples'}
function available(){return state.tab==='samples'?catalog.samples:state.tab==='models'?catalog.models:catalog.approved_lots}
function syncOptions(){const items=available().filter(x=>!state.country||x.country===state.country);const makes=[...new Set(items.map(x=>x.make))].sort((a,b)=>a.localeCompare(b,'ru'));const make=$('makeFilter');make.replaceChildren(new Option('Все марки',''),...makes.map(m=>new Option(m,m)));if(!makes.includes(state.make)){state.make='';}make.value=state.make;}
function visibleList(){let rows=available().filter(x=>{
 if(state.country&&x.country!==state.country)return false;
 if(state.make&&x.make!==state.make)return false;
 const phrase=[x.make,x.model,x.body,x.engine,x.engine_range].filter(Boolean).join(' ').toLocaleLowerCase('ru');if(state.search&&!phrase.includes(state.search.toLocaleLowerCase('ru')))return false;
 if(state.tab==='samples'){if(state.year&&numVal(x.year)<Number(state.year))return false;if(state.budget&&calc(x).nov>Number(state.budget))return false;}
 return true});if(state.sort==='name')rows.sort((a,b)=>(a.make+' '+a.model).localeCompare((b.make+' '+b.model),'ru'));else if(state.sort==='country')rows.sort((a,b)=>a.country.localeCompare(b.country));else if(state.sort==='price'&&state.tab==='samples')rows.sort((a,b)=>calc(a).nov-calc(b).nov);
 return rows;}
function updateUrl(){const q=new URLSearchParams();if(state.tab!=='samples')q.set('section',state.tab);for(const k of ['country','make','search','year','budget','sort']){if(state[k]&&!(k==='sort'&&state[k]==='default')&&!(state.tab!=='samples'&&(k==='year'||k==='budget')))q.set(k,state[k]);}history.replaceState(null,'',location.pathname+(q.size?'?'+q.toString():''));}
function render(){state.tab=safeTab();syncOptions();const list=visibleList();$('sampleTabCount').textContent=catalog.samples.length;$('modelTabCount').textContent=catalog.models.length;$('archiveTabCount').textContent=catalog.approved_lots.length;
 document.querySelectorAll('[role=tab]').forEach(btn=>{const yes=btn.dataset.tab===state.tab;btn.setAttribute('aria-selected',String(yes));btn.tabIndex=yes?0:-1});for(const tab of ['samples','models','archive'])$('panel-'+tab).hidden=tab!==state.tab;
 $('yearWrap').hidden=$('budgetWrap').hidden=state.tab!=='samples';$('sortFilter').querySelector('option[value=price]').hidden=state.tab!=='samples';if(state.tab!=='samples'&&state.sort==='price'){state.sort='default';$('sortFilter').value='default';}
 const titles={samples:['ПРИМЕРЫ КОНФИГУРАЦИИ','Карточки с подробной сметой','Учебные примеры на базе фотографий моделей CC0. Не результаты конкретных торгов.'],models:['МОДЕЛИ ПОД ЗАКАЗ','Подберём автомобиль под вашу задачу','Доступные направления поиска. Цена и состояние уточняются при конкретном подборе.'],archive:['ПРОВЕРЕННЫЕ АУКЦИОНЫ','Статистика завершённых торгов','Только подтверждённые продажи с исходными данными и фотографиями конкретных автомобилей.']}[state.tab];
 $('resultsEyebrow').textContent=titles[0];$('resultsHeading').textContent=titles[1];$('resultsDescription').textContent=titles[2];$('foundCount').textContent='Показано: '+list.length;
 const active=[state.country&&countries[state.country],state.make,state.search&&'Поиск: '+state.search,state.tab==='samples'&&state.year&&'С '+state.year+' г.',state.tab==='samples'&&state.budget&&'До '+money(state.budget)].filter(Boolean);$('activeFilters').textContent=active.length?active.join(' · '):'Показаны все направления';
 const empty=Boolean(state.tab!=='archive'&&!list.length);$('emptyState').hidden=!empty;
 if(state.tab==='samples'){const root=$('sampleList');root.replaceChildren(...list.map(createSample))}
 if(state.tab==='models'){const root=$('modelList');root.replaceChildren(...list.slice(0,state.visibleModels).map(createModel));$('loadMore').hidden=state.visibleModels>=list.length;$('loadMore').textContent='Показать ещё ('+(list.length-state.visibleModels)+') ↓';}
 if(state.tab==='archive'){$('archiveList').replaceChildren();$('panel-archive').querySelector('.archive-empty').hidden=catalog.approved_lots.length>0;}
 updateUrl();}
function switchTab(tab){state.tab=tab;state.country='';state.make='';state.search='';state.year='';state.budget='';state.sort='default';state.visibleModels=12;$('countryFilter').value='';$('searchFilter').value='';$('yearFilter').value='';$('budgetFilter').value='';$('sortFilter').value='default';render();}
function reset(){state.country='';state.make='';state.search='';state.year='';state.budget='';state.sort='default';state.visibleModels=12;['countryFilter','makeFilter','searchFilter','yearFilter','budgetFilter'].forEach(id=>$(id).value='');$('sortFilter').value='default';render();}
for(const tab of ['samples','models','archive'])$('tab-'+tab).addEventListener('click',()=>switchTab(tab));
$('countryFilter').addEventListener('change',e=>{state.country=e.target.value;state.make='';state.visibleModels=12;render()});
$('makeFilter').addEventListener('change',e=>{state.make=e.target.value;state.visibleModels=12;render()});
$('searchFilter').addEventListener('input',e=>{state.search=e.target.value.trim();state.visibleModels=12;render()});
for(const [k,id] of [['year','yearFilter'],['budget','budgetFilter'],['sort','sortFilter']])$(id).addEventListener('change',e=>{state[k]=e.target.value;render()});
$('resetFilters').addEventListener('click',reset);$('emptyReset').addEventListener('click',reset);
$('loadMore').addEventListener('click',()=>{state.visibleModels+=12;render()});
$('toggleFilters').addEventListener('click',()=>{const open=$('filterFields').parentElement.classList.toggle('expanded');$('toggleFilters').setAttribute('aria-expanded',String(open))});
for(const k of ['country','search','year','budget','sort']){const id=k==='country'?'countryFilter':k==='search'?'searchFilter':k==='year'?'yearFilter':k==='budget'?'budgetFilter':'sortFilter';if(state[k])$(id).value=state[k];}
fetch('/catalog-v2-data.json',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()}).then(data=>{
 catalog.samples=Array.isArray(data.samples)?data.samples.filter(v=>v.kind==='illustrative_model'):[];
 catalog.models=Array.isArray(data.models)?data.models.filter(v=>v.kind==='model_reference'):[];
 catalog.approved_lots=Array.isArray(data.approved_lots)?data.approved_lots.filter(v=>v.image_rights==='approved'&&v.sale_status==='verified_sold'&&v.proof_verified===true&&Array.isArray(v.photos)&&v.photos.length>0):[];
 render();
}).catch(e=>{$('foundCount').textContent='Каталог временно недоступен';$('resultsDescription').textContent='Не удалось загрузить данные каталога: '+String(e.message||e);});
})();