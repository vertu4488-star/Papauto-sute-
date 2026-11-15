/* Read-only PapAuto warm UI visual regression on real static build. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const BASE='http://127.0.0.1:8765';
const pages=[
 {url:'/',selectors:['body','.site-header','.hero','.pa-card','.button-primary']},
 {url:'/gallery.html',selectors:['body','.gallery-hero','.gallery-card','.gallery-card-head','.gallery-card-photo','.gallery-grade','.gallery-card-footer','.gallery-apply','.gallery-viewer']},
 {url:'/catalog.html',selectors:['body','.catalog-intro','.catalog-filters','.model-card']},
 {url:'/premium-japan-korea.html',selectors:['body','.hero','.real-card','.real-content']},
 {url:'/podbor.html',selectors:['body','.pa-header','.pa-card']},
 {url:'/japan.html',selectors:['body','.country-hero','.country-callout']},
 {url:'/korea.html',selectors:['body','.country-hero','.country-callout']},
 {url:'/china.html',selectors:['body','.country-hero','.country-callout']},
];
(async()=>{
 const browser=await chromium.launch({headless:true});
 try{
  for(const width of [390,1440]){
   const page=await browser.newPage({viewport:{width,height:width===390?844:900},isMobile:width===390,deviceScaleFactor:1});
   await page.route(/^https:\/\/(?:mc\.yandex\.ru|www\.googletagmanager\.com|www\.google-analytics\.com)\//,
     route=>route.fulfill({status:200,contentType:'application/javascript',body:''}));
   for(const entry of pages){
    await page.goto(BASE+entry.url,{waitUntil:'load',timeout:45000});
    await page.evaluate(()=>document.fonts.ready);
    const state=await page.evaluate((selectors)=>{
      const blue=[],sample={};
      for(const selector of selectors){
       const el=document.querySelector(selector);if(!el)continue;
       const style=getComputedStyle(el);
       const values=['backgroundColor','backgroundImage','color','borderTopColor'].map(p=>[p,style[p]]);
       sample[selector]=Object.fromEntries(values);
       for(const [prop,value] of values){
        for(const match of value.matchAll(/rgba?\((\d+),\s*(\d+),\s*(\d+)/g)){
         const [r,g,b]=[+match[1],+match[2],+match[3]];
         if(b>r+14&&b>=g-8)blue.push(selector+' '+prop+' '+match[0]);
        }
       }
      }
      return {blue,overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),
        colorScheme:getComputedStyle(document.body).colorScheme,
        finalSkin:!!document.querySelector('link[href*="papauto-warm-interior.css"]')};
    },entry.selectors);
    assert(state.finalSkin,'Warm CSS missing on '+entry.url);
    assert.equal(state.blue.length,0,'Cold UI colors on '+entry.url+': '+JSON.stringify(state.blue));
    assert(state.overflow<=2,'Horizontal overflow on '+entry.url+' at '+width+': '+state.overflow);
    if(entry.url==='/gallery.html'){
     await page.locator('.gallery-card').first().waitFor({state:'visible',timeout:10000});
     if(width===390)await page.screenshot({path:'warm-gallery-mobile.png',fullPage:false});
     if(width===1440)await page.screenshot({path:'warm-gallery-desktop.png',fullPage:false});
     const detail=await page.locator('.gallery-card a.gallery-full').first().getAttribute('href');
     assert(detail&&detail.startsWith('/lots/'),'Lot detail link unavailable');
     await page.goto(BASE+detail,{waitUntil:'load',timeout:45000});
     await page.evaluate(()=>document.fonts.ready);
     const detailState=await page.evaluate(()=>{
      const blue=[];
      for(const sel of ['body','.lot-header','.lot-information','.lot-price','.lot-photo','.lot-apply','.lot-description']){
       const el=document.querySelector(sel);if(!el)continue;
       const s=getComputedStyle(el);
       for(const prop of ['color','backgroundColor','borderTopColor']){
        const v=s[prop];const m=v.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if(m){const [r,g,b]=[+m[1],+m[2],+m[3]];if(b>r+14&&b>=g-8)blue.push([sel,prop,v]);}
       }
      }
      return {blue,overflow:Math.max(0,document.documentElement.scrollWidth-innerWidth),
       photo:document.querySelector('.lot-photo img')?.getAttribute('src'),
       sheet:document.querySelector('.lot-sheet img')?.getAttribute('src')};
     });
     assert.equal(detailState.blue.length,0,'Cool auction lot detail: '+JSON.stringify(detailState.blue));
     assert(detailState.overflow<=2,'Auction lot detail overflow');
     assert(detailState.photo&&detailState.sheet,'Original photo or auction sheet missing');
     if(width===390)await page.screenshot({path:'warm-lot-mobile.png',fullPage:false});
     if(width===1440)await page.screenshot({path:'warm-lot-desktop.png',fullPage:false});
    }
    console.log('WARM_SITE_QA='+JSON.stringify({path:entry.url,width,blue:state.blue.length,overflow:state.overflow}));
   }
   await page.close();
  }
 }finally{await browser.close()}
})().catch(e=>{console.error('WARM_SITE_FAILED',e.stack||e);process.exit(1)});
