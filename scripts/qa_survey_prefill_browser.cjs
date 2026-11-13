/* Prove PapAuto auction-gallery links prefill the actual mobile SurveyJS UI.
   Read-only: no real API requests and no lead submission. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const BASE='http://127.0.0.1:8765/podbor.html';
const cases=[
 {reference:'Toyota Corolla Sport 2023 · Япония',make:'Toyota',model:'Corolla',year:'2023'},
 {reference:'BMW X1 sDrive18i 2021 · Япония',make:'BMW',model:'X1',year:'2021'},
 {reference:'BMW 118i M Sport 2019 · Япония',make:'BMW',model:'1 Series',year:'2019'},
 {reference:'BMW 218i Gran Coupe M Sport 2022 · Япония',make:'BMW',model:'2 Series',year:'2022'},
 {reference:'Mercedes-Benz A180 Sedan AMG Line 2020 · Япония',make:'Mercedes-Benz',model:'A-Class',year:'2020'},
 {reference:'Mercedes-Benz C180 Avantgarde AMG Line 2018 · Япония',make:'Mercedes-Benz',model:'C-Class',year:'2018'},
 {reference:'Hyundai Avante 2024 · Корея',make:'Hyundai',model:'Avante',year:'2024'},
 {reference:'Geely Monjaro 2025 · Китай',make:'Geely',model:'Monjaro',year:'2025'}
];
(async()=>{
 let browser;
 try {
 browser=await chromium.launch({headless:true});
 const results=[];
 for(const spec of cases){
  const page=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  const errors=[],posts=[];
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(r.method()==='POST')posts.push(r.url())});
  const link=BASE+'?similar='+encodeURIComponent(spec.reference);
  await page.goto(link,{waitUntil:'load',timeout:45000});
  await page.locator('.sd-question[data-name="make"]').waitFor({state:'visible',timeout:30000});
  const field=async name=>{
   const q=page.locator('.sd-question[data-name="'+name+'"]');
   return {text:(await q.innerText()).slice(0,450),html:(await q.evaluate(el=>el.outerHTML)).slice(0,1500)};
  };
  const make=await field('make'),model=await field('model'),year=await field('year');
  const notes=await page.locator('.sd-question[data-name="notes"] textarea').inputValue();
  assert(make.text.includes(spec.make),'Missing selected make '+spec.reference+': '+JSON.stringify(make));
  assert(model.text.includes(spec.model),'Missing selected model '+spec.reference+': '+JSON.stringify(model));
  assert(year.text.includes(spec.year),'Missing year '+spec.reference+': '+JSON.stringify(year));
  assert(notes.includes(spec.reference.split(' · ')[0]),
   'Exact lot reference lost '+spec.reference+': '+notes);
  assert.equal(errors.length,0,'Form JavaScript errors '+JSON.stringify(errors));
  assert.equal(posts.length,0,'Prefill QA must never send a live lead');
  const overflow=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  assert(overflow<=2,'Mobile form overflow '+spec.reference+': '+overflow);
  results.push({reference:spec.reference,make:true,model:true,year:true,notes:true,overflow});
  if(spec.make==='Toyota')await page.screenshot({path:'survey-prefill-mobile.png',fullPage:false});
  await page.close();
 }
 console.log('PAPAUTO_GALLERY_TO_SURVEY_PREFILL='+JSON.stringify(results));
 } finally {
   if(browser)await browser.close();
 }
})().catch(e=>{console.error('PAPAUTO_PREFILL_BROWSER_FAILED',e.stack||e);process.exitCode=1});
