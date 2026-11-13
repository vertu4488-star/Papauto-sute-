/* Browser QA for PapAuto gallery. Read-only: local HTTP and no lead submissions. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const BASE='http://127.0.0.1:8765/gallery.html';
(async()=>{
 const browser=await chromium.launch({headless:true});
 const findings=[];
 for(const width of [1440,390,320]){
  const page=await browser.newPage({viewport:{width,height:width===1440?900:780},deviceScaleFactor:1,isMobile:width<500,hasTouch:width<500});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  page.on('console',m=>{if(m.type()==='error')errors.push('console: '+m.text());});
  page.on('requestfailed',r=>{if(/127\.0\.0\.1:8765/.test(r.url()))errors.push('local request: '+r.url()+' '+r.failure()?.errorText);});
  await page.goto(BASE,{waitUntil:'load',timeout:45000});
  try{
    await page.waitForFunction(()=>{const n=JSON.parse(document.querySelector('#gallery-bootstrap')?.textContent||'{}').lots?.length;return n&&document.querySelector('#gallery-count')?.textContent.includes('Найдено '+n);},{timeout:8000});
  }catch(e){
    const diagnostics=await page.evaluate(async()=>{
      let jsonReport='unknown';
      try{const r=await fetch('/data/gallery-lots.json',{cache:'no-store'});const data=await r.json();jsonReport={status:r.status,lotCount:data.lots?.length};}catch(err){jsonReport=String(err);}
      return {counter:document.querySelector('#gallery-count')?.textContent,
        grid:document.querySelector('#gallery-grid')?.textContent?.slice(0,250),
        brand:document.querySelector('#gallery-brand')?.value,
        search:document.querySelector('#gallery-search')?.value,
        scripts:[...document.scripts].map(x=>x.src).filter(Boolean),
        jsonReport};
    });
    throw new Error('Gallery did not render: '+JSON.stringify({diagnostics,errors}));
  }
  await page.waitForFunction(()=>{const img=document.querySelector('.gallery-card-photo img');return !!img?.complete&&img.naturalWidth>0;},{timeout:10000});
  const state=await page.evaluate(()=>{
   const image=document.querySelector('.gallery-card-photo img');
   return {cards:document.querySelectorAll('.gallery-card').length,
    registryIndex:document.querySelectorAll('.gallery-card[data-lot-id]').length,
    imageLoaded:image?.complete&&image.naturalWidth>0,
    fit:getComputedStyle(image).objectFit,
    pageOverflow:document.documentElement.scrollWidth-window.innerWidth,
    wholeImages:[...document.querySelectorAll('.gallery-card-photo img')].every(i=>i.src.includes('/assets/auction/home/')||i.src.includes('/assets/premium-auctions/')||i.src.includes('/assets/auction/approved/')),
    localStyles:[...document.styleSheets].some(s=>s.href?.includes('/gallery.css')),
    noStreet:[...document.images].every(i=>!/\/assets\/(demo|visual)\//.test(i.getAttribute('src')||''))};
  });
  assert.equal(state.cards,12,'Expected 12 first-page cards');
  assert.equal(state.registryIndex,12,'All 12 cards must have true lot IDs');
  assert(state.imageLoaded,'First lot photo missing at '+width);
  assert.equal(state.fit,'contain','Never crop auction photos');
  assert(state.localStyles,'Missing gallery styles');
  assert(state.wholeImages,'Non-auction gallery photo detected');
  assert(state.noStreet,'Street photo in gallery');
  assert(state.pageOverflow<=2,'Horizontal overflow at '+width+': '+state.pageOverflow);
  // Exact lot photo/auction sheet must stay in the same card.
  const card=page.locator('.gallery-card').first();
  const id=await card.getAttribute('data-lot-id');
  const before=await card.locator('.gallery-card-photo img').getAttribute('src');
  assert(/assets\/(premium-auctions|auction\/(?:home|approved))/.test(before));
  await card.locator('.gallery-thumb').last().click();
  const after=await card.locator('.gallery-card-photo img').getAttribute('src');
  assert(/(?:sheet|diagram)(?:-[a-f0-9]{12})?\.(?:webp|jpg|jpeg|png)$/.test(after),'Sheet thumb must open local document');
  await card.locator('.gallery-detail').click();
  await page.locator('#gallery-viewer[open]').waitFor({state:'visible',timeout:10000});
  const firstCaption=await page.locator('#gallery-viewer-caption').innerText();
  await page.keyboard.press('ArrowLeft');
  const secondCaption=await page.locator('#gallery-viewer-caption').innerText();
  assert.notEqual(firstCaption,secondCaption,'Keyboard must navigate gallery images');
  await page.keyboard.press('Escape');
  assert.equal(await page.locator('#gallery-viewer[open]').count(),0,'Escape must close viewer');
  await page.locator('button.gallery-tab.gallery-tab[data-gallery-category=premium]').click();
  const expectedPremium=await page.evaluate(()=>JSON.parse(document.querySelector('#gallery-bootstrap').textContent).lots.filter(l=>l.category==='premium').length);
  assert((await page.locator('#gallery-count').innerText()).includes('Найдено '+expectedPremium),'Premium grouping count mismatch');
  await page.locator('button.gallery-tab.gallery-tab[data-gallery-category=popular]').click();
  const expectedPopular=await page.evaluate(()=>JSON.parse(document.querySelector('#gallery-bootstrap').textContent).lots.filter(l=>l.category==='popular').length);
  assert((await page.locator('#gallery-count').innerText()).includes('Найдено '+expectedPopular),'Popular grouping count mismatch');
  await page.locator('button.gallery-tab.gallery-tab[data-gallery-category=all]').click();
  const availableMarkets=await page.locator('#gallery-market-filter option').allTextContents();
  assert(availableMarkets.some(x=>x.includes('Япония')),'Missing verified Japan market');
  const recordedMarkets=await page.evaluate(()=>[...new Set(JSON.parse(document.querySelector('#gallery-bootstrap').textContent).lots.map(l=>l.market))]);
  assert.equal(availableMarkets.length,recordedMarkets.length+1,'Must not advertise countries without approved photos and sheets');
  await page.locator('#gallery-market-filter').selectOption('japan');
  assert((await page.locator('#gallery-count').innerText()).includes('Найдено '+
    (await page.evaluate(()=>JSON.parse(document.querySelector('#gallery-bootstrap').textContent).lots.filter(l=>l.market==='japan').length))),
    'Country filter must show only matching auction lots');
  await page.locator('#gallery-market-filter').selectOption('all');
  await page.locator('#gallery-search').fill('Toyota');
  const hits=await page.locator('.gallery-card').count();
  assert(hits>0&&hits<=12,'Toyota search must return real filtered cars');
  for(const model of await page.locator('.gallery-card-body h3').allTextContents())assert(model.includes('Toyota'),'Wrong car in Toyota search');
  await page.locator('#gallery-search').fill('');
  const expectedAll=await page.evaluate(()=>JSON.parse(document.querySelector('#gallery-bootstrap').textContent).lots.length);
  for(let expectedVisible=24;expectedVisible<expectedAll+12;expectedVisible+=12){
    if(await page.locator('#gallery-more').isHidden())break;
    await page.locator('#gallery-more').click();
    assert.equal(await page.locator('.gallery-card').count(),Math.min(expectedVisible,expectedAll),
      'Pagination must show actual auction records without fillers');
  }
  assert.equal(await page.locator('.gallery-card').count(),expectedAll,'All approved auction cards accessible');
  assert.equal(await page.locator('#gallery-more').isHidden(),true,'No more button after last page');
  const overflowAfter=await page.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  assert(overflowAfter<=2,'Expanded gallery overflows viewport');
  assert.equal(errors.length,0,'Page errors: '+JSON.stringify(errors));
  if(width===390||width===1440){
   await page.locator('#gallery-grid').scrollIntoViewIfNeeded();
   await page.screenshot({path:width===390?'gallery-mobile.png':'gallery-desktop.png',fullPage:false});
  }
  findings.push({width,firstLot:id,firstImageLoaded:state.imageLoaded,visible:expectedAll,overflow:overflowAfter,errors});
  await page.close();
 }
 console.log('PAPAUTO_AUCTION_GALLERY_QA='+JSON.stringify(findings));
 await browser.close();
})().catch(e=>{console.error('GALLERY_QA_FAILED',e.stack||e);process.exit(1);});
