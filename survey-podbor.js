/* PAPAUTO standalone car order form, built on the complete MIT SurveyJS v3.2.4 renderer.
 * Upstream source: https://github.com/surveyjs/survey-library
 * All vendor assets are locally hosted. Only the existing PapAuto API receives leads.
 */
(() => {
  'use strict';
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
          {type:'radiogroup',name:'contact_method',title:'Удобный способ связи',isRequired:true,defaultValue:'phone',
           colCount:2,choices:[{value:'phone',text:'Телефон'},{value:'telegram',text:'Telegram'}]},
          {type:'text',name:'phone',title:'Телефон для ответа',inputType:'tel',
           placeholder:'+7 900 123-45-67',visibleIf:"{contact_method} = 'phone'",isRequired:true,maxLength:30,
           validators:[{type:'regex',regex:'^\\+?[0-9() \\-]{10,25}$',text:'Введите телефон полностью или выберите Telegram.'}]},
          {type:'text',name:'telegram',title:'Ваш Telegram',inputType:'text',placeholder:'@username',
           visibleIf:"{contact_method} = 'telegram'",isRequired:true,maxLength:60,
           validators:[{type:'regex',regex:'^@?[A-Za-z0-9_]{5,32}$',text:'Введите Telegram в формате @username.'}]},
          {type:'checkbox',name:'consent',title:'Согласие на обработку персональных данных',
           isRequired:true,choices:[{value:'agree',text:'Согласен(на) на обработку данных только для ответа на заявку.'}]}
        ]
      }
    ]
  };
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
  survey.onValueChanged.add((sender,options)=>{
    if(options.name==='market')updateMakes(options.value);
    if(options.name==='make')updateModels(sender.getValue('market'),options.value);
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
  updateMakes('japan');
  const similar=new URL(location.href).searchParams.get('similar');
  if(similar && similar.length<=90){
    const query=similar.toLocaleLowerCase('ru');
    outer:for(const [market,rows] of Object.entries(catalog)){
      for(const item of rows){
        if((item[0]+' '+item[1]).toLocaleLowerCase('ru')===query){
          survey.setValue('market',market);survey.setValue('make',item[0]);survey.setValue('model',item[1]);
          break outer;
        }
      }
    }
  }
  let state='ready',savedNotification=false;
  survey.onCompleting.add(async (_, options)=>{
    if(state!=='ready'){options.allow=false;options.message='Заявка уже отправляется или её статус проверяется. Пожалуйста, не отправляйте повторно.';return}
    state='pending';
    msg.textContent='Передаём заявку менеджеру…';
    const d=survey.data;
    const contact=d.contact_method==='telegram'?String(d.telegram||'').trim():String(d.phone||'').trim();
    const request=[
      'Подбор автомобиля через PapAuto (SurveyJS)',
      'Марка: '+d.make,
      'Модель: '+d.model,
      'Год: '+d.year,
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
  survey.render(mount);
  msg.textContent='';
  } catch (error) {
    const message = document.getElementById('surveyStatus');
    if(message) message.textContent = 'Ошибка запуска формы (' + String(error?.name || 'Unknown') + '): ' + String(error?.message || 'неизвестная ошибка').slice(0,150) + ' | STACK: ' + String(error?.stack || '').split('\\n').slice(0,5).join(' | ').slice(0,650);
  }
})();