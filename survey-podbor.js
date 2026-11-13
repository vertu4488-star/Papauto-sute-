/* PAPAUTO standalone car order form, built on the complete MIT SurveyJS v3.2.4 renderer.
 * Upstream source: https://github.com/surveyjs/survey-library
 * All vendor assets are locally hosted. Only the existing PapAuto API receives leads.
 */
(() => {
  'use strict';
  let startupStage = 'initialization';
  try {
  const mount = document.getElementById('surveyContainer');
  const msg = document.getElementById('surveyStatus');
  const dialog = document.getElementById('surveySuccessDialog');
  const head = document.getElementById('surveySuccessTitle');
  const note = document.getElementById('surveySuccessText');
  const catalog = window.PAPAUTO_CATALOG || {};
  const markets = {'japan':'Япония','south-korea':'Южная Корея','china':'Китай'};
  if(!mount) return;
  if(!window.Survey || typeof window.Survey.Model !== 'function') {
    msg.textContent = 'Форма временно недоступна. Попробуйте открыть страницу ещё раз.';
    return;
  }
  const sortRU = values => [...new Set(values)].sort((a,b)=>a.localeCompare(b,'ru'));
  const getRows = market => Array.isArray(catalog[market]) ? catalog[market] : [];
  const getMakes = market => sortRU(getRows(market).map(row=>row[0]));
  const getModels = (market,make) => sortRU(getRows(market).filter(row=>row[0]===make).map(row=>row[1]));
  const aliases = {
    toyota:['toyta','тойота','тайота'], honda:['хонда','hoda'],
    hyundai:['хендай','хюндай','hundai'], geely:['джили'],
    kia:['киа'], nissan:['ниссан'], mazda:['мазда'], subaru:['субару'],
    suzuki:['сузуки'], mitsubishi:['мицубиси','митсубиси'],
    chery:['чери'], haval:['хавал'], bmw:['бмв']
  };
  const distance = (a,b) => {
    const row=Array.from({length:b.length+1},(_,i)=>i);
    for(let i=1;i<=a.length;i++){
      let prev=row[0];row[0]=i;
      for(let j=1;j<=b.length;j++){
        const old=row[j];
        row[j]=Math.min(row[j]+1,row[j-1]+1,prev+(a[i-1]===b[j-1]?0:1));
        prev=old;
      }
    }
    return row[b.length];
  };
  const yearChoices = Array.from({length:37},(_,i)=>String(2026-i));
  const schema = {
    title:'',locale:'ru',
    showQuestionNumbers:'off',
    showProgressBar:'top',
    progressBarType:'pages',
    firstPageIsStarted:false,
    goNextPageAutomatic:false,
    completeText:'Отправить заявку',
    nextText:'Продолжить',
    prevText:'Назад',
    completedHtml:'<h2>Заявка принята</h2><p>Результат подтверждён сервером PapAuto.</p>',
    clearInvisibleValues:'onComplete',
    // Commit native phone and Telegram input on each keystroke; onBlur can
    // race the final iOS tap and trigger a false required-field error.
    textUpdateMode:'onTyping',
    pages:[
      {
        name:'car',title:'1. Выберите автомобиль',
        description:'Три страны, марка и модель. Бюджет указывать необязательно.',
        elements:[
          {type:'radiogroup',name:'market',title:'Откуда автомобиль?',isRequired:true,
           defaultValue:'japan',colCount:3,choices:[
             {value:'japan',text:'Япония'},{value:'south-korea',text:'Корея'},{value:'china',text:'Китай'}]},
          {type:'dropdown',name:'make',title:'Марка автомобиля',isRequired:true,
           placeholder:'Выберите марку',searchEnabled:true,allowClear:true,choices:[]},
          {type:'dropdown',name:'model',title:'Модель',isRequired:true,
           placeholder:'Выберите модель',searchEnabled:true,allowClear:true,choices:[]},
          {type:'dropdown',name:'year',title:'Год выпуска',isRequired:true,
           defaultValue:'2022',choices:yearChoices},
          {type:'text',name:'city',title:'Город получения',isRequired:true,defaultValue:'Новосибирск',maxLength:80},
          {type:'text',name:'budget',title:'Ваш бюджет, ₽ (необязательно)',inputType:'number',
           description:'Можно оставить пустым. Итоговую стоимость под ключ менеджер уточнит после проверки лота.',
           validators:[{type:'numeric',minValue:1,maxValue:2000000000}]},
          {type:'comment',name:'notes',title:'Пожелания (необязательно)',maxLength:1000,
           placeholder:'Цвет, пробег, комплектация...'}
        ]
      },
      {
        name:'contact',title:'2. Куда отправить варианты?',
        description:'Контакт нужен только для ответа на вашу заявку. Регистрация не требуется.',
        elements:[
          {type:'text',name:'name',title:'Как к вам обращаться? (необязательно)',maxLength:100},
          {type:'radiogroup',name:'contact_method',title:'Как удобнее связаться?',isRequired:true,defaultValue:'phone',
           colCount:2,choices:[{value:'phone',text:'Позвонить'},{value:'telegram',text:'Telegram по номеру'}]},
          {type:'text',name:'phone',title:'Номер телефона для связи',inputType:'tel',
           placeholder:'+7 900 123-45-67',isRequired:true,maxLength:25,
           description:'Номер для звонка или Telegram. Если клавиатура не появляется, используйте кнопки ниже.',
           validators:[{type:'regex',regex:'^[0-9+ ()-]{10,25}$',text:'Введите полный номер телефона.'}]},
          {type:'checkbox',name:'consent',title:'Согласие на обработку персональных данных',
           isRequired:true,choices:[{value:'agree',text:'Согласен(на) на обработку данных только для ответа на заявку.'}]}
        ]
      }
    ]
  };
  startupStage = 'construct Model';
  const survey = new window.Survey.Model(schema);
  const updateMakes = market => {
    const q=survey.getQuestionByName('make');
    const next=getMakes(market);
    q.choices=next.map(value=>({value,text:value}));
    if(!next.includes(survey.getValue('make')))survey.setValue('make',undefined);
    updateModels(market,survey.getValue('make'));
  };
  const updateModels = (market,make) => {
    const q=survey.getQuestionByName('model');
    const options=getModels(market,make);
    q.choices=options.map(value=>({value,text:value}));
    if(!options.includes(survey.getValue('model')))survey.setValue('model',undefined);
    // SurveyJS 3 exposes isReadOnly as a getter; the empty choices list suffices.
  };
  // Physical keyboards and embedded iOS browsers can suppress the native
  // software keyboard. Always render a touch-operated dialpad with this field.
  survey.onValidateQuestion.add((_sender, options)=>{
    if(options.question?.name!=='phone' || !options.value)return;
    const digits=String(options.value).replace(/\D/g,'');
    if(digits.length<10 || digits.length>15){
      options.error='Введите полный номер: от 10 до 15 цифр.';
    }
  });
  survey.onAfterRenderQuestion.add((_sender, options)=>{
    if(options.question?.name!=='phone')return;
    const host=options.htmlElement?.querySelector('.sd-question__content')||options.htmlElement;
    if(!host||host.querySelector('.pa-phonepad'))return;
    const pad=document.createElement('div');
    pad.className='pa-phonepad';
    pad.setAttribute('role','group');
    pad.setAttribute('aria-label','Цифровой набор номера');
    const label=document.createElement('p');
    label.className='pa-phonepad-title';
    label.textContent='Наберите номер кнопками';
    pad.appendChild(label);
    const grid=document.createElement('div');
    grid.className='pa-phonepad-grid';
    for(const key of ['1','2','3','4','5','6','7','8','9','+','0','⌫']){
      const button=document.createElement('button');
      button.type='button';
      button.className='pa-phonepad-key';
      button.textContent=key;
      button.setAttribute('aria-label',key==='⌫'?'Удалить последнюю цифру':key==='+'?'Плюс':key);
      button.addEventListener('click',event=>{
        event.preventDefault();
        const prior=String(survey.getValue('phone')||'');
        let next=prior;
        if(key==='⌫') next=prior.slice(0,-1);
        else if(key==='+'){if(!prior)next='+';}
        else if(prior.length<25)next=prior+key;
        survey.setValue('phone',next);
      });
      grid.appendChild(button);
    }
    pad.appendChild(grid);
    const actions=document.createElement('div');
    actions.className='pa-phonepad-actions';
    const prefix=document.createElement('button');
    prefix.type='button';
    prefix.className='pa-phonepad-prefix';
    prefix.textContent='+7';
    prefix.setAttribute('aria-label','Начать номер с плюс семь');
    prefix.addEventListener('click',event=>{
      event.preventDefault();
      const prior=String(survey.getValue('phone')||'');
      const digits=prior.replace(/\D/g,'');
      survey.setValue('phone',prior?'+7'+digits.replace(/^[78]/,''):'+7');
    });
    const clear=document.createElement('button');
    clear.type='button';
    clear.className='pa-phonepad-clear';
    clear.textContent='Очистить';
    clear.addEventListener('click',event=>{
      event.preventDefault();
      survey.setValue('phone','');
    });
    actions.append(prefix,clear);
    pad.appendChild(actions);
    host.appendChild(pad);
  });
  startupStage = 'attach event listeners';
  survey.onValueChanged.add((sender,options)=>{
    if(options.name==='market')updateMakes(options.value);
    if(options.name==='make')updateModels(sender.getValue('market'),options.value);
    if(options.name==='contact_method'){
      const phone=sender.getQuestionByName('phone');
      if(phone)phone.description=options.value==='telegram'
        ? 'Введите телефон, к которому привязан Telegram. Связь по номеру зависит от настроек конфиденциальности Telegram.'
        : 'Введите номер для звонка или воспользуйтесь кнопками ниже.';
    }
  });
  survey.onChoicesSearch.add((sender,options)=>{
    if(options.question?.name!=='make' && options.question?.name!=='model')return;
    const key=(options.filter||'').trim().toLocaleLowerCase('ru');
    if(!key)return;
    const fuzzy = (options.choices||[]).map(item=>{
      const value=String(item.value||'');
      const word=value.toLocaleLowerCase('ru');
      const possibilities=[word,...(aliases[word]||[])];
      const best=Math.min(...possibilities.map(w=>w.includes(key)?0:distance(w,key)));
      return {item,best};
    }).filter(x=>x.best<=Math.max(1,Math.floor(key.length/3))).sort((a,b)=>a.best-b.best).slice(0,80);
    if(fuzzy.length)options.filteredChoices=fuzzy.map(x=>x.item);
  });
  startupStage = 'populate dropdowns';
  updateMakes('japan');
  // Internal gallery CTAs include trim, year and country:
  // e.g. "Toyota Corolla Sport 2023 · Япония", not a bare catalogue label.
  // Restore a matching base model but always preserve the exact auction trim
  // in notes; if the model is unknown, do NOT choose a misleading substitute.
  const similar=new URL(location.href).searchParams.get('similar');
  const ref=window.PapAutoSimilarPrefill?.resolve(similar,catalog);
  if(ref){
    if(ref.market&&markets[ref.market]){
      survey.setValue('market',ref.market);
      updateMakes(ref.market);
    }
    if(ref.make){
      survey.setValue('make',ref.make);
      updateModels(ref.market||'japan',ref.make);
    }
    if(ref.model)survey.setValue('model',ref.model);
    if(ref.year&&yearChoices.includes(ref.year))survey.setValue('year',ref.year);
    survey.setValue('notes','Интересует аналог аукционного лота: '+ref.reference+
      (ref.year?' '+ref.year:'')+'. Уточнить комплектацию, цену и доступность.');
  }
  let state='ready',savedNotification=false;
  survey.onCompleting.add(async (_, options)=>{
    if(state!=='ready'){options.allow=false;options.message='Заявка уже отправляется или её статус проверяется. Пожалуйста, не отправляйте повторно.';return}
    state='pending';
    msg.textContent='Передаём заявку менеджеру…';
    const d=survey.data;
    const contact=String(d.phone||'').trim();
    const request=[
      'Подбор автомобиля через PapAuto (SurveyJS)',
      'Марка: '+d.make,
      'Модель: '+d.model,
      'Год: '+d.year,
      'Предпочитаемый способ связи: '+(d.contact_method==='telegram'?'Telegram по номеру (если разрешено настройками приватности)':'Телефонный звонок'),
      d.budget?'Бюджет: '+d.budget+' ₽':'Бюджет не указан',
      d.notes?'Пожелания: '+d.notes:'',
      'Нужна подтверждённая цена под ключ, включая таможню, утильсбор и доставку.'
    ].filter(Boolean).join('\n');
    const payload={
      name:String(d.name||'').trim(),contact,
      country:markets[d.market]||d.market,
      city:String(d.city||'Новосибирск').trim(),
      budget:d.budget?Number(d.budget):null,
      request,consent:Array.isArray(d.consent)&&d.consent.includes('agree'),website:''
    };
    const endpoint=location.hostname==='ru-preview.papauto.ru'
      ? location.origin : String(window.PAPAUTO_CONFIG?.apiBaseUrl||'https://api.papauto.ru').replace(/\/$/,'');
    try{
      const response=await fetch(endpoint+'/api/leads',{
        method:'POST',
        headers:{'Content-Type':'application/json','Accept':'application/json'},
        credentials:'omit',body:JSON.stringify(payload)
      });
      let data={};try{data=await response.json()}catch{}
      if(data.ok===true && data.stored===true && response.ok){
        state='done';savedNotification=data.notified===true;
        msg.textContent=savedNotification?'Заявка доставлена менеджеру.':'Заявка сохранена. Доставка уведомления проверяется.';
        options.allow=true;
      }else{
        state='unknown';
        options.allow=false;
        options.message='Статус заявки не подтверждён. Проверьте Telegram перед повторной отправкой.';
        msg.textContent='Ошибка '+response.status+'. Заявка могла сохраниться. Не отправляйте повторно до проверки.';
      }
    }catch{
      state='unknown';options.allow=false;
      options.message='Не удалось получить подтверждение сервера. Не отправляйте заявку повторно.';
      msg.textContent='Сбой сети. Статус заявки неизвестен, проверьте Telegram.';
    }
  });
  survey.onComplete.add(()=>{
    if(state!=='done')return;
    head.textContent=savedNotification?'Ваша заявка отправлена!':'Ваша заявка сохранена!';
    note.textContent=savedNotification
      ? 'Заявка сохранена в PapAuto и передана менеджеру через Telegram. Мы свяжемся с вами.'
      : 'Заявка сохранена, но Telegram пока не подтвердил доставку. Повторно отправлять не нужно.';
    if(typeof dialog?.showModal==='function')dialog.showModal();
    else if(dialog)dialog.setAttribute('open','');
  });
  document.getElementById('surveySuccessClose')?.addEventListener('click',()=>{
    if(typeof dialog?.close==='function')dialog.close();
    else dialog?.removeAttribute('open');
  });
  startupStage = 'render form';
  survey.render(mount);
  msg.textContent='';
  } catch (error) {
    const message = document.getElementById('surveyStatus');
    if(message) message.textContent = 'Ошибка на этапе [' + startupStage + '] (' + String(error?.name || 'Unknown') + '): ' + String(error?.message || 'неизвестная ошибка').slice(0,150) + ' | STACK: ' + String(error?.stack || '').split('\\n').slice(0,5).join(' | ').slice(0,650);
  }
})();