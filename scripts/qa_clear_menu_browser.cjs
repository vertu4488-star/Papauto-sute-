const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const root='http://127.0.0.1:8765';
(async()=>{
const browser=await chromium.launch({headless:true});
let total=0;
try{
 for(const width of [1440,1280,900,390,320]){
  const isMobile=width<=680;
  const page=await browser.newPage({viewport:{width,height:isMobile?844:900},isMobile,hasTouch:isMobile});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(root+'/',{waitUntil:'load',timeout:45000});
  const nav=page.locator('.main-nav');
  const links=await nav.locator('a').evaluateAll(nodes=>nodes.map(a=>({name:a.textContent.trim(),href:a.getAttribute('href')})));
  const names=links.map(x=>x.name);
  assert.equal(links.length,7,'Exactly 7 intentional menu items');
  assert.deepEqual(names,["Каталог авто","Марки и модели","Статистика торгов",
   "Япония · Корея · Китай","Расчёт стоимости","Как заказать","Личный кабинет"]);
  const old=await page.locator('.main-nav').innerText();
  assert(!/100 моделей под заказ|Модели для Новосибирска/.test(old),'Outdated menu language remains');
  assert.equal(await page.locator('.header-cta').getAttribute('href'),'/podbor.html');
  if(isMobile){
    await page.locator('.menu-toggle').click();
    await nav.waitFor({state:'visible'});
    for(const name of ['Каталог авто','Марки и модели','Статистика торгов']){
      assert(await nav.getByRole('link',{name,exact:true}).isVisible(),name+' mobile menu item hidden');
    }
  }else{
    assert(await nav.getByRole('link',{name:'Каталог авто',exact:true}).isVisible(),'Desktop catalog hidden');
    assert(await nav.getByRole('link',{name:'Марки и модели',exact:true}).isVisible(),'Desktop model guide hidden');
  }
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  assert(overflow<=3,'Horizontal overflow on home '+width+'px: '+overflow);
  const items=await page.locator('.main-nav a').count();
  assert.equal(items,7);
  console.log('PAPAUTO_MENU_LAYOUT_OK',width,JSON.stringify({items,overflow,mobile:isMobile}));
  if(width===1440||width===390)await page.screenshot({path:'navigation-'+width+'.png',fullPage:false});
  await page.close();total++;
 }
 const page=await browser.newPage({viewport:{width:1280,height:900}});
 for(const [url,expected] of [
   ['/gallery.html','gallery-card'],
   ['/models-100.html','Справочник'],
   ['/?view=auctions','Статистика автомобилей'],
   ['/?view=directions','Три рынка'],
   ['/premium-japan-korea.html#import-estimate','Стоимость под ключ до Новосибирска'],
   ['/?view=about','От запроса']
 ]){
   const response=await page.goto(root+url,{waitUntil:'load',timeout:45000});
   assert.equal(response.status(),200,'Broken menu destination '+url);
   if(url.startsWith('/gallery.html')){
     assert(await page.locator('.gallery-card').count()>100,'Gallery should contain real verified cars');
   }else if(url.includes('models-100')){
     assert((await page.locator('h1').innerText()).includes('Марки и модели'),'Model guide must be honest');
   }else{
     const html=await page.content();
     assert(html.includes(expected),'Section did not exist: '+url+' expected '+expected);
   }
   console.log('PAPAUTO_MENU_DESTINATION_OK',url);
 }
 await page.close();
 console.log('PAPAUTO_MENU_ALL_CHECKS_PASSED',total);
}finally{await browser.close();}
})().catch(e=>{console.error('PAPAUTO_MENU_QA_FAILED',e.stack||e);process.exitCode=1});