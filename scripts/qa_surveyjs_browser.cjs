const {chromium}=require('playwright');
(async()=>{
 const browser=await chromium.launch({headless:true});
 const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
 const errors=[],posts=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('console',m=>{if(m.type()==='error')errors.push(m.text())});
 await page.route('**/*',async route=>{
   const request=route.request(),url=request.url();
   if(request.method()==='POST'){
     if(url.endsWith('/api/leads')){
       const payload=JSON.parse(request.postData()||'{}');
       posts.push({country:payload.country,city:payload.city,budget:payload.budget,request:payload.request,consent:payload.consent,contactPresent:!!payload.contact});
       return route.fulfill({status:200,contentType:'application/json',body:JSON.stringify({ok:true,stored:true,notified:true,message:'Тест API подтверждён'})});
     }
     throw new Error('Unsafe unexpected POST: '+url);
   }
   return route.continue();
 });
 await page.goto('http://127.0.0.1:8765/podbor.html',{waitUntil:'load',timeout:45000});
 await page.locator('.sd-question').first().waitFor({timeout:30000});
 const fieldSummary=await page.locator('.sd-question').evaluateAll(ns=>ns.map(n=>({id:n.id,name:n.getAttribute('data-name'),txt:(n.innerText||'').slice(0,110),inputs:[...n.querySelectorAll('input')].map(i=>({type:i.type,role:i.getAttribute('role'),placeholder:i.placeholder,readOnly:i.readOnly}))})));
 console.log('PAPAUTO_FIELDS='+JSON.stringify(fieldSummary));
 const makeQ=page.locator('.sd-question').filter({hasText:'Марка автомобиля'}).first();
 console.log('PAPAUTO_MAKE_HTML='+(await makeQ.evaluate(e=>e.outerHTML.slice(0,4500))));
 const select=makeQ.locator('input:not([type="hidden"])').first();
 await select.click();
 await select.fill('Toyota');
 await page.waitForTimeout(300);
 console.log('PAPAUTO_MAKE_OPTIONS='+JSON.stringify((await page.locator('body').innerText()).slice(-2500)));
 await page.getByText('Toyota',{exact:true}).last().click({timeout:6000});
 const modelQ=page.locator('.sd-question').filter({hasText:'Модель'}).first();
 const modelInput=modelQ.locator('input:not([type="hidden"])').first();
 await modelInput.click();
 await modelInput.fill('Corolla');
 await page.waitForTimeout(300);
 await page.getByText('Corolla',{exact:true}).last().click({timeout:6000});
 console.log('PAPAUTO_STEP1='+(await page.locator('#surveyContainer').innerText()).slice(0,1600));
 const next=page.getByRole('button',{name:/Далее|Продолжить|Next/i}).last();
 await next.click({timeout:7000});
 console.log('PAPAUTO_STEP2='+(await page.locator('#surveyContainer').innerText()).slice(0,1400));
 const phoneQ=page.locator('.sd-question').filter({hasText:'Телефон для ответа'}).first();
 const phone=phoneQ.locator('input:not([type="hidden"])').first();
 console.log('PAPAUTO_CONTACT_INPUT='+JSON.stringify({type:await phone.getAttribute('type'),inputMode:await phone.getAttribute('inputmode')}));
 await phone.fill('+79000000000');
 const consentQ=page.locator('.sd-question').filter({hasText:'Согласие на обработку'}).first();
 await consentQ.locator('input[type="checkbox"]').first().check({force:true});
 const submit=page.getByRole('button',{name:/Отправить заявку|Завершить|Complete/i}).last();
 await submit.click();
 await page.waitForTimeout(900);
 console.log('PAPAUTO_POSTS='+JSON.stringify(posts));
 console.log('PAPAUTO_DIALOG='+JSON.stringify({visible:await page.locator('#surveySuccessDialog').isVisible(),text:await page.locator('#surveySuccessDialog').innerText()}));
 console.log('PAPAUTO_ERRORS='+JSON.stringify(errors));
 await page.screenshot({path:'survey-end-to-end.png',fullPage:true});
 await browser.close();
 if(posts.length!==1 || !posts[0].consent)throw Error('Lead POST not exactly once with consent');
})().catch(e=>{console.error('PAPAUTO_BROWSER_TEST_FAILED='+e.stack);process.exit(1)});
