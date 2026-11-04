(()=>{'use strict';
const $=id=>document.getElementById(id),names={japan:'Япония','south-korea':'Южная Корея',china:'Китай'},cache=new Map();let rows=[];
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(text!==undefined)n.textContent=text;if(cls)n.className=cls;return n};
const aliases={'приус':'prius','аква':'aqua','фит':'fit','рав4':'rav4','рав 4':'rav4','тойота':'toyota','хонда':'honda','аванте':'avante','авантэ':'avante','хендай':'hyundai','хундай':'hyundai','джили':'geely','монджаро':'monjaro'};
const norm=s=>Object.entries(aliases).reduce((t,[a,b])=>t.replaceAll(a,b),s.toLowerCase()).replace(/\s+/g,' ').trim();
const baseModel=r=>r.model.startsWith('RAV4')?'RAV4':r.model.startsWith('Prius')?'Prius':r.model.startsWith('Aqua')?'Aqua':r.model.startsWith('Fit')?'Fit':r.make==='Hyundai'?'Elantra':r.make==='Geely'?'Xingyue L':r.model;
async function illustration(r,figure){
 const modelName=r.make+' '+baseModel(r),key=modelName+' '+r.year;
 if(!cache.has(key))cache.set(key,(async()=>{try{
 const params=new URLSearchParams({action:'query',generator:'search',gsrsearch:'filetype:bitmap intitle:"'+modelName+'" '+r.year+' front -police -taxi -safari -interior -engine -Touring',gsrnamespace:'6',gsrlimit:'3',prop:'imageinfo',iiprop:'url|extmetadata',iiurlwidth:'640',format:'json',origin:'*'});
 const resp=await fetch('https://commons.wikimedia.org/w/api.php?'+params,{signal:AbortSignal.timeout(8000)});if(!resp.ok)return null;const data=await resp.json();
 for(const page of Object.values(data.query?.pages||{}).sort((a,b)=>(a.index??99)-(b.index??99))){const i=page.imageinfo?.[0],m=i?.extmetadata||{},license=m.LicenseShortName?.value||m.LicenseShortName?.Value||'';if(new RegExp('\\b'+r.year+'\\b').test(page.title)&&i?.thumburl&&/CC0|Public domain|CC BY(?:-SA)?/i.test(license))return {url:i.thumburl,page:i.descriptionurl,author:(m.Artist?.value||m.Artist?.Value||'Wikimedia Commons').replace(/<[^>]*>/g,''),license};}
 }catch{}return null;})());
 const image=await cache.get(key);if(!image||!figure.isConnected)return;
 const img=el('img');img.alt='Иллюстрация модели '+key+' — не фото лота';img.loading='lazy';img.src=image.url;
 img.onerror=()=>figure.replaceChildren(el('div','Фото лота не предоставлено','placeholder'));
 const caption=el('figcaption','Фото модели, не лота. '+image.author+' · '+image.license+' '),credit=el('a','Автор и лицензия');credit.href=image.page;credit.target='_blank';credit.rel='noopener';caption.append(credit);figure.replaceChildren(img,caption);
}
function render(){const query=norm($('q').value),list=rows.filter(r=>(!$('country').value||r.country===$('country').value)&&(!$('kind').value||($('kind').value==='sold'?r.status==='sold':r.status!=='sold'))&&(!query||query.split(' ').every(t=>norm(r.make+' '+r.model).includes(t))));$('count').textContent='Всего примеров: '+list.length+' · в базе '+rows.length+' · иллюстрации не являются фото лотов;$('examples').replaceChildren();
 for(const r of list){const card=el('article',undefined,'example'),photo=el('figure',undefined,'photo');if(Array.isArray(r.photos)&&r.photos.length){const img=el('img');img.src=r.photos[0];img.alt='Фото конкретного автомобиля '+r.make+' '+r.model;img.loading='lazy';img.onerror=()=>{photo.replaceChildren(el('div','Фото лота недоступно','placeholder'));illustration(r,photo)};photo.append(img)}else{photo.append(el('div','Подбираем иллюстрацию модели…','placeholder'))}const b=el('div',undefined,'body');b.append(el('span',names[r.country]+' · '+(r.status==='sold'?'ПРОДАН':r.status==='withdrawn'?'ОБЪЯВЛЕНИЕ СНЯТО':'ПРИМЕР ОБЪЯВЛЕНИЯ'),'badge'),el('h2',r.make+' '+r.model),el('p',r.year+' · '+r.mileage.toLocaleString('ru-RU')+' км'),el('strong',r.price?r.price.toLocaleString('ru-RU')+' '+r.currency:'Цена не опубликована'));
 b.append(el('p',r.status==='sold'?'Цена продажи · '+r.sold_date+' · '+r.auction+' · лот '+r.lot:'Цена предложения, не результат продажи'));
 if(r.grade)b.append(el('p','Аукционная оценка: '+r.grade+(r.grade==='R'?' — восстановление после повреждений':''),r.grade==='R'?'warning':''));if(r.note)b.append(el('p',r.note));b.append(el('small','Источник: '+r.source));
 const ask=el('a','Подобрать похожий','ask');ask.href='/?'+new URLSearchParams({view:'select',archive_make:r.make,archive_model:r.model,archive_year:r.year,archive_country:r.country,example_id:r.id})+'#assistant';b.append(ask);card.append(photo,b);$('examples').append(card);if(!Array.isArray(r.photos)||!r.photos.length)illustration(r,photo);
 }if(!list.length)$('examples').append(el('p','По этим параметрам записей нет.'));
}
const params=new URLSearchParams(location.search);$('q').value=[params.get('make'),params.get('model')].filter(Boolean).join(' ');if(names[params.get('country')])$('country').value=params.get('country');['q','country','kind'].forEach(id=>$(id).addEventListener('input',render));
Promise.all(['/data/sold-lots.json','/data/vehicle-examples.json'].map(async url=>{const r=await fetch(url,{signal:AbortSignal.timeout(12000)});if(!r.ok)throw Error();return r.json()})).then(([sold,listing])=>{rows=[...sold.lots,...listing.listings];render()}).catch(()=>{$('count').textContent='Не удалось загрузить примеры. Обновите страницу или перейдите к подбору автомобиля.'});
})();
