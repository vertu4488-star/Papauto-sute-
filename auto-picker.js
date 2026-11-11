/* PapAuto Smart Picker v1: local Tom Select + Fuse.js + own model catalogue.
   No third-party requests while searching. Actual landed cost requires verified lot,
   shipping, customs and fees; do not fabricate prices. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const form = $('carPickerForm');
  if (!form) return;
  const CATALOG = window.PAPAUTO_CATALOG || {};
  const country = $('pickerCountry'), make = $('pickerMake'), model = $('pickerModel');
  const year = $('pickerYear'), city = $('pickerCity'), budget = $('pickerBudget');
  const summary = $('pickerResult'), status = $('pickerStatus');
  const leadForm = $('pickerLeadForm'), send = $('pickerSend'), leadStatus = $('pickerLeadStatus');
  const aliases = {
    toyota: 'тойота тайота toyta toyo', honda:'хонда hoda', hyundai:'хендай хюндай хундай hundai',
    geely:'джили гили jili', kia:'киа кия', bmw:'бмв', mercedes:'мерседес',
    nissan:'ниссан нисан', mazda:'мазда', subaru:'субару', suzuki:'сузуки',
    mitsubishi:'митсубиси мицубиси', chery:'чери черри', haval:'хавал',
    volkswagen:'фольксваген', byd:'бид биуайди', lexus:'лексус'
  };
  const sorted = (values) => [...new Set(values)].sort((a,b)=>a.localeCompare(b,'ru'));
  const rows = () => Array.isArray(CATALOG[country.value]) ? CATALOG[country.value] : [];
  const options = names => sorted(names).map(value => ({
    value, label:value, alias: aliases[value.toLowerCase()] || ''
  }));
  const fuzzyScore = options => {
    let index = null, last = '';
    return function(query) {
      const term = query.trim();
      if(!term) return () => 1;
      if(!window.Fuse) return item => (item.label||'').toLocaleLowerCase('ru').includes(term.toLocaleLowerCase('ru')) ? 1 : 0;
      if(term!==last) {
        last = term;
        index = new Map();
        const fuse = new window.Fuse(options,{keys:['label','alias'],threshold:0.52,includeScore:true,ignoreLocation:true,minMatchCharLength:2});
        fuse.search(term,{limit:120}).forEach(x=>index.set(x.item.value,Math.max(.01,1-(x.score||0))));
      }
      return item => index.get(item.value) || 0;
    };
  };
  const controller = (element, items, onChange, placeholder) => {
    if(typeof window.TomSelect !== 'function') {
      const populate = opts => {
        element.replaceChildren(new Option(placeholder,''));
        opts.forEach(o=>element.add(new Option(o.label,o.value)));
      };
      populate(items);
      element.addEventListener('change',()=>onChange(element.value));
      return { setItems:populate, clear:()=>{element.value='';onChange('')}, setValue:v=>{element.value=v;onChange(v)}, enable:()=>element.disabled=false,disable:()=>element.disabled=true };
    }
    let current = items;
    const control = new window.TomSelect(element,{
      options:items,
      // Our catalogue options use {value,label,alias}; Tom Select defaults to text.
      // Without labelField it renders "undefined" on iOS Safari.
      valueField:'value',
      labelField:'label',
      create:false,
      maxItems:1,
      allowEmptyOption:true,
      placeholder,
      searchField:['label','alias'],
      score:query=>fuzzyScore(current)(query),
      onChange,
      render:{
        item:(item,escape)=>'<div>'+escape(item.label||item.value||'')+'</div>',
        option:(item,escape)=>'<div class="picker-option"><span>'+escape(item.label)+'</span></div>',
        no_results:(_data,escape)=>'<div class="no-results">Не найдено. Проверьте написание или выберите другую марку.</div>'
      }
    });
    return {
      setItems(opts){current=opts;control.clear(true);control.clearOptions();control.addOptions(opts);control.refreshOptions(false);},
      clear(){control.clear(true);onChange('')},
      setValue(v){control.setValue(v,true);onChange(v)},
      enable(){control.enable()},disable(){control.disable()}
    };
  };
  const modelsFor = name => options(rows().filter(r=>r[0]===name).map(r=>r[1]));
  let chosenMake='', chosenModel='', makeCtl, modelCtl;
  modelCtl=controller(model,[],v=>{chosenModel=v;clearResult()},'Выберите модель');
  function clearResult(){summary.hidden=true; leadStatus.textContent='';leadForm.hidden=true;send.disabled=false;send.textContent='Отправить заявку';send.dataset.locked='';}
  function onMake(v) {
    chosenMake = v;
    chosenModel = '';
    const items = modelsFor(v);
    modelCtl.setItems(items);
    if(v&&items.length)modelCtl.enable();else modelCtl.disable();
    clearResult();
    const hint = $('pickerModelHint');
    if(hint) hint.textContent = v ? 'Доступно моделей: '+items.length+' — выберите из списка' : 'Сначала выберите марку';
  }
  makeCtl=controller(make,options(rows().map(r=>r[0])),onMake,'Начните вводить марку');
  modelCtl.disable();
  country.addEventListener('change',()=>{
    chosenMake='';chosenModel='';
    makeCtl.setItems(options(rows().map(r=>r[0])));
    modelCtl.setItems([]);modelCtl.disable();
    $('pickerModelHint').textContent='Сначала выберите марку';
    clearResult();
  });
  for(const e of [year,city,budget,$('pickerEngine'),$('pickerEngineSize'),$('pickerPower'),$('pickerPurchasePrice'),$('pickerNotes')]){
    e?.addEventListener('input',()=>{if(!summary.hidden)clearResult()});
  }
  const pickSimilar=()=>{
    const term = new URLSearchParams(location.search).get('similar');
    if(!term)return;
    let found=null;
    for(const [market,entries] of Object.entries(CATALOG)){
      for(const r of entries){
        const match=(r[0]+' '+r[1]).toLocaleLowerCase('ru');
        if(match===term.toLocaleLowerCase('ru')||match.startsWith(term.toLocaleLowerCase('ru'))){found={market,make:r[0],model:r[1]};break}
      }
      if(found)break;
    }
    if(found){
      country.value=found.market;country.dispatchEvent(new Event('change',{bubbles:true}));
      makeCtl.setValue(found.make);modelCtl.setValue(found.model);
      $('pickerStatus').textContent='Модель из каталога выбрана. Укажите год для запроса расчёта.';
    }else $('pickerNotes').value='Подобрать похожий автомобиль: '+term;
  };
  pickSimilar();
  const money = n => new Intl.NumberFormat('ru-RU',{maximumFractionDigits:0}).format(n)+' ₽';
  function quoteText(){
    const details=[chosenMake,chosenModel,year.value].filter(Boolean).join(' ');
    const countryName=country.options[country.selectedIndex]?.textContent||country.value;
    return {details,countryName,city:city.value.trim()||'Новосибирск'};
  }
  async function enrichPrice() {
    const input=$('pickerPurchasePrice'),price=Number(input?.value||0),out=$('pickerPurchaseResult');
    if(!price||price<=0){out.textContent='Цена автомобиля не указана. Для точной сметы потребуется актуальный лот.';return}
    out.textContent='Проверяем актуальный курс…';
    const endpoint=String(window.PAPAUTO_CONFIG?.apiBaseUrl||'https://api.papauto.ru').replace(/\/$/,'');
    try {
      const r=await fetch(endpoint+'/api/exchange-rates',{headers:{Accept:'application/json'},signal:AbortSignal.timeout?AbortSignal.timeout(12000):undefined});
      if(!r.ok) throw new Error('rate');
      const d=await r.json();
      const prop=country.value==='japan'?'rub_per_jpy':country.value==='south-korea'?'rub_per_1000_krw':'rub_per_cny';
      const rate=Number(d[prop]),multiplier=country.value==='south-korea'?1000:1;
      if(!Number.isFinite(rate)||rate<=0)throw new Error('missing rate');
      out.textContent='Стоимость покупки по курсу: '+money(price*rate/multiplier)+' (курс '+(d.date||'без даты')+'). Доставка, таможня и услуги НЕ включены.';
    }catch{out.textContent='Курс валют сейчас недоступен. Цена указана без таможни, доставки и сборов.'}
  }
  form.addEventListener('submit',event=>{
    event.preventDefault();
    if(!chosenMake||!chosenModel){status.textContent='Выберите марку и модель из подсказок.';(!chosenMake?make:model).focus();return}
    const y=Number(year.value);
    if(!Number.isInteger(y)||y<1990||y>2026){status.textContent='Выберите корректный год выпуска.';year.focus();return}
    if(!city.value.trim()){status.textContent='Укажите город получения.';city.focus();return}
    const b=budget.value.trim();
    if(b && (!Number.isFinite(Number(b)) || Number(b)<0 || Number(b)>2000000000)){status.textContent='Проверьте бюджет либо оставьте его пустым.';budget.focus();return}
    status.textContent='';
    const v=quoteText();
    $('pickerResultTitle').textContent=v.details;
    $('pickerResultRoute').textContent=v.countryName+' → '+v.city;
    $('pickerResultBudget').textContent=b?'Бюджет до '+money(Number(b)):'Бюджет не указан — это необязательное поле';
    summary.hidden=false;
    leadForm.hidden=false;
    leadForm.dataset.prepared='yes';
    leadForm.dataset.sent='';
    send.disabled=false;send.textContent='Отправить заявку';
    leadStatus.textContent='';
    enrichPrice();
    summary.scrollIntoView({behavior:'smooth',block:'nearest'});
  });
  const requestText=()=>{
    const v=quoteText();
    const parts=['Подбор и расчёт PAPAUTO','Направление: '+v.countryName,'Марка: '+chosenMake,'Модель: '+chosenModel,'Год выпуска: '+year.value,'Доставка: '+v.city];
    if(budget.value)parts.push('Бюджет до: '+money(Number(budget.value)));
    const engine=$('pickerEngine').value;
    if(engine)parts.push('Тип двигателя: '+engine);
    const volume=$('pickerEngineSize').value;
    if(volume)parts.push('Объём двигателя, см³: '+volume);
    const power=$('pickerPower').value;
    if(power)parts.push('Мощность, л.с.: '+power);
    const price=$('pickerPurchasePrice').value;
    if(price)parts.push('Цена в валюте страны покупки: '+price);
    const notes=$('pickerNotes').value.trim();
    if(notes)parts.push('Пожелания: '+notes);
    parts.push('Просьба подтвердить наличие лота, доставку, таможню, утильсбор и итоговую цену под ключ до '+v.city+'.');
    return parts.join('\n');
  };
  leadForm.addEventListener('submit',async event=>{
    event.preventDefault();
    if(leadForm.dataset.prepared!=='yes'||leadForm.dataset.sent==='pending'||leadForm.dataset.sent==='done'||leadForm.dataset.sent==='unknown')return;
    const contact=$('pickerContact').value.trim();
    if(contact.length<3){leadStatus.textContent='Укажите контакт для ответа.';$('pickerContact').focus();return}
    if(!$('pickerConsent').checked){leadStatus.textContent='Для отправки заявки нужно согласие на обработку данных.';return}
    if($('pickerWebsite').value.trim())return;
    const endpoint=String(window.PAPAUTO_CONFIG?.apiBaseUrl||'').replace(/\/$/,'');
    if(!endpoint||!/^https:\/\//.test(endpoint)){leadStatus.textContent='API не настроен. Попробуйте связаться с нами через Telegram.';return}
    const payload={
      name:$('pickerName').value.trim(),contact,
      country:country.options[country.selectedIndex]?.textContent||country.value,
      budget:budget.value?Number(budget.value):null,
      city:city.value.trim()||'Новосибирск',request:requestText(),consent:true,website:''
    };
    leadForm.dataset.sent='pending';send.disabled=true;send.textContent='Отправляем…';leadStatus.textContent='Проверяем доставку…';
    try {
      const r=await fetch(endpoint+'/api/leads',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
      let d={};try{d=await r.json()}catch{}
      if(!r.ok){
        if([400,413,422].includes(r.status)){leadForm.dataset.sent='';send.disabled=false;send.textContent='Исправить и отправить';leadStatus.textContent=d.detail||'Проверьте данные заявки.';return}
        throw new Error('HTTP '+r.status);
      }
      leadForm.dataset.sent='done';
      send.textContent=d.notified===false?'Заявка сохранена':'Заявка отправлена';
      leadStatus.textContent=d.message||(d.notified===false?'Заявка сохранена, менеджер проверит уведомления.':'Заявка доставлена менеджеру.');
      window.dispatchEvent(new CustomEvent('papauto:lead-submitted',{detail:{...payload,make:chosenMake,model:chosenModel,yearFrom:year.value,yearTo:year.value}}));
    }catch(err){
      leadForm.dataset.sent='unknown';
      send.textContent='Статус не подтверждён';
      const httpCode = String(err?.message||'');
      const reason = /^HTTP [0-9]{3}$/.test(httpCode) ? ('Сервер ответил '+httpCode+'. ') : 'Сетевое соединение прервалось. ';
      leadStatus.textContent=reason+'Подтверждения отправки нет. Заявка могла сохраниться и прийти в Telegram. НЕ отправляйте повторно, пока менеджер не проверит.';
    }
  });
  // Improve the separate catalogue filters without changing their API or result cards.
  const vehicleCountry=$('vehicleCountry'), vehicleMake=$('vehicleMake'),vehicleModel=$('vehicleModel');
  if(vehicleCountry&&vehicleMake&&vehicleModel&&window.TomSelect){
    let catalogMakeCtl=null,catalogModelCtl=null,catalogMake='';
    const updateCatalogModels=value=>{
      catalogMake=value;
      const data=options((CATALOG[vehicleCountry.value]||[]).filter(r=>r[0]===value).map(r=>r[1]));
      catalogModelCtl.setItems(data);
      if(value&&data.length)catalogModelCtl.enable();else catalogModelCtl.disable();
    };
    catalogModelCtl=controller(vehicleModel,[],()=>{},'Модель');
    catalogMakeCtl=controller(vehicleMake,options((CATALOG[vehicleCountry.value]||[]).map(r=>r[0])),updateCatalogModels,'Марка');
    catalogModelCtl.disable();
    vehicleCountry.addEventListener('change',()=>{
      catalogMakeCtl.setItems(options((CATALOG[vehicleCountry.value]||[]).map(r=>r[0])));
      catalogModelCtl.setItems([]);catalogModelCtl.disable();
    });
  }
})();
