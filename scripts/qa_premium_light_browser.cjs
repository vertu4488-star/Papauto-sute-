/* Browser QA for the light premium page. All requests are local; no form submission. */
const {chromium}=require('playwright');
const assert=require('node:assert/strict');
const BASE='http://127.0.0.1:8765/premium-japan-korea.html';
(async()=>{
  const browser=await chromium.launch({headless:true});
  const results=[];
  for(const viewport of [{width:1440,height:900},{width:390,height:844},{width:320,height:720}]){
    const page=await browser.newPage({viewport,deviceScaleFactor:1,isMobile:viewport.width<=390,hasTouch:viewport.width<=390});
    const errors=[],failed=[];
    page.on('pageerror',e=>errors.push(e.message));
    page.on('response',r=>{if(r.status()>=400)failed.push(r.status()+' '+r.url())});
    await page.goto(BASE,{waitUntil:'load',timeout:45000});
    await page.locator('.real-card').first().waitFor({state:'visible',timeout:20000});
    await page.waitForTimeout(1200);
    await page.evaluate(()=>document.fonts.ready);
    const state=await page.evaluate(()=>{
      const body=document.body,stat=document.querySelector('.real-filterbar'),hero=document.querySelector('.hero');
      const sheets=[...document.querySelectorAll('.real-img-sheet')].filter(x=>getComputedStyle(x).display!=='none');
      const images=[...document.querySelectorAll('.real-card img')];
      const first=images[0];
      return {
        linkedCSS:[...document.styleSheets].some(s=>s.href?.includes('/premium-lexus-light.css')),
        manropeActivated:getComputedStyle(body).fontFamily.includes('PapAutoManrope') && document.fonts.check('300 24px PapAutoManrope','Немецкие автомобили'),
        bg:getComputedStyle(body).backgroundImage,
        headline:getComputedStyle(hero.querySelector('h1')).fontWeight,
        realCards:document.querySelectorAll('.real-card').length,
        models:document.querySelectorAll('.car').length,
        countryCounts:{
          japan:document.querySelectorAll('.real-card[data-real-market=japan]').length,
          korea:document.querySelectorAll('.real-card[data-real-market=korea]').length
        },
        horizontalOverflow:document.documentElement.scrollWidth-window.innerWidth,
        filterOverflow:stat ? stat.scrollWidth-stat.clientWidth : null,
        heroImageLoaded:(()=>{const i=document.querySelector('.hero-visual img');return !!i?.complete && i.naturalWidth>0})(),
        firstPhotoLoaded:!!first?.complete && first.naturalWidth>0,
        auctionOnly:[...document.images].every(i => !/\/assets\/(demo|visual)\//.test(i.getAttribute('src')||'')),
        visibleSheets:sheets.length,
        mobileMenuVisible:getComputedStyle(document.querySelector('.mobile-nav')).display!=='none'
      };
    });
    // No auction-like listing may exist without a photo, mileage and its own auction sheet.
    assert.equal(await page.locator('#market-catalog, [data-selection-grid], .selection-model-entry').count(),0,
      'Text-only model cards must never appear in the public premium catalog');
    assert.equal((await page.locator('#verified-lots-title').innerText()).trim(),'Аукционная статистика авто');
    const publishedCards=await page.locator('.real-card').evaluateAll(cards=>cards.map(card=>({
      photo:!!card.querySelector('.real-img-main img[src]'),
      sheet:!!card.querySelector('.real-img-sheet img[src]'),
      mileage:!![...card.querySelectorAll('.real-specs span')].find(el=>el.textContent.trim()==='Пробег'),
      description:!!card.querySelector('.real-content h3') && !!card.querySelector('.real-trim'),
      outdoor:!!card.querySelector('img[src*="/assets/demo/"],img[src*="/assets/visual/"]')
    })));
    assert(publishedCards.length>0,'No auction photo cards published');
    assert(publishedCards.every(card=>card.photo && card.sheet && card.mileage && card.description && !card.outdoor),
      'An auction card is missing its photo, description, mileage or original auction sheet');
    assert(state.linkedCSS,'Light premium CSS missing at '+viewport.width);
    assert(state.manropeActivated,'Self-hosted Manrope Cyrillic font not active at '+viewport.width);
    assert.equal(state.realCards,11,'12 frozen source cards minus the explicitly quarantined Mercedes A180');
    assert.equal(await page.locator('.real-card img[src*="mercedes-a180-2020-"]').count(),0,'Withdrawn A180 must never reappear');
    assert.equal(state.countryCounts.japan,11);
    assert.equal(state.countryCounts.korea,0);
    assert.equal(state.models,0);
    assert(state.heroImageLoaded,'Hero photo missing');
    assert(state.firstPhotoLoaded,'Auction photo missing');
    assert(state.auctionOnly,'Non-auction model photograph was displayed');
    assert(state.horizontalOverflow<=2,'Horizontal overflow '+state.horizontalOverflow+'px @'+viewport.width);
    assert(state.filterOverflow!==null && state.filterOverflow<=2,'Auction filter missing or overflowing '+state.filterOverflow+'px @'+viewport.width);
    if(viewport.width<=390){
      assert(state.mobileMenuVisible,'Mobile menu missing');
      assert(state.visibleSheets>0,'Original auction sheet links inaccessible on mobile');
      await page.locator('.mobile-nav summary').click();
      assert(await page.locator('.mobile-nav[open] nav a').count()>0,'Mobile menu did not open');
      await page.locator('.mobile-nav summary').click();
    }
    const name=viewport.width===1440?'premium-light-desktop.png':viewport.width===390?'premium-light-mobile.png':'premium-light-small.png';
    await page.evaluate(()=>window.scrollTo(0,0));
    await page.screenshot({path:name,fullPage:false});
    assert.equal(await page.locator('[data-real-filter=korea]').count(),0,'Do not advertise unverified Korean auction lots');
    assert.equal(await page.locator('.real-card[data-real-market=korea]').count(),0,'Unverified Korean auction cards returned');
    await page.locator('[data-real-filter=japan]').click();
    assert.equal(await page.locator('.real-card:visible').count(),12,'Japan filter invalid');
    await page.locator('[data-real-filter=all]').click();
    assert.equal(await page.locator('.real-card:visible').count(),12,'All auction filter invalid');
    if(viewport.width===390){
      await page.locator('#verified-lots').scrollIntoViewIfNeeded();
      await page.screenshot({path:'premium-light-mobile-catalog.png',fullPage:false});
    }
    assert.equal(errors.length,0,'Browser JS errors: '+JSON.stringify(errors));
    assert.equal(failed.length,0,'Missing assets: '+JSON.stringify(failed));
    results.push({viewport,state,errors,failed});
    await page.close();
  }
  // Links lead to the actual photo-and-sheet gallery, not a text-only directory.
  const photoGalleryLink=await browser.newPage();
  await photoGalleryLink.goto(BASE,{waitUntil:'load',timeout:45000});
  assert.equal(await photoGalleryLink.locator('a[href="/gallery.html"]').count()>0,true,
    'Premium page must link to the approved photo gallery');
  await photoGalleryLink.close();
    // Isolated noindex mobile experiment: original image and auction gallery
  // must survive the strict public build and never depend on third-party media.
  const preview=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
  const previewFailures=[];
  preview.on('pageerror',e=>previewFailures.push('JS: '+e.message));
  preview.on('response',r=>{if(r.status()>=400)previewFailures.push('HTTP '+r.status()+' '+r.url())});
  await preview.goto('http://127.0.0.1:8765/premium-mobile-photo-demo.html',{waitUntil:'load',timeout:45000});
  await preview.locator('.real-card').first().waitFor({state:'visible'});
  assert.equal(await preview.locator('#market-catalog, [data-selection-grid], .selection-model-entry').count(),0,
    'Mobile preview must never display text-only model cards');
  const previewState=await preview.evaluate(()=>{
    const image=document.querySelector('.hero-visual img');
    const main=document.querySelector('.real-card .real-img-main img');
    const sheet=document.querySelector('.real-card .real-img-sheet img');
    return {
      noindex:document.querySelector('meta[name="robots"]')?.content.includes('noindex'),
      stylesheet:[...document.styleSheets].some(s=>s.href?.includes('premium-mobile-photo-demo.css')),
      hero:!!image?.complete && image.naturalWidth>0,
      mainPhoto:!!main?.complete && main.naturalWidth>0,
      sheet:!!sheet?.complete && sheet.naturalWidth>0,
      objectFit:main?getComputedStyle(main).objectFit:'',
      pageOverflow:document.documentElement.scrollWidth-window.innerWidth,
      cards:document.querySelectorAll('.real-card').length
    };
  });
  assert(previewState.noindex,'Preview must be noindex');
  assert(previewState.stylesheet,'Missing mobile preview CSS');
  assert(previewState.hero,'Preview hero image was stripped by public-build whitelist');
  assert(previewState.mainPhoto,'Preview auction photo was stripped');
  assert(previewState.sheet,'Preview inspection sheet was stripped');
  assert.equal(previewState.cards,12,'Preview retains only 12 approved auction cards');
  assert.equal(previewState.objectFit,'contain','Preview main auction photo must be uncropped');
  assert(previewState.pageOverflow<=2,'Preview horizontal scroll '+previewState.pageOverflow+'px');
  assert.equal(previewFailures.length,0,JSON.stringify(previewFailures));
  await preview.locator('#verified-lots').scrollIntoViewIfNeeded();
  await preview.screenshot({path:'premium-mobile-photo-preview.png',fullPage:false});
  console.log('PAPAUTO_PREMIUM_MOBILE_PREVIEW_QA='+JSON.stringify(previewState));
  await preview.close();
  // Read-only cost calculator QA: prove 12 sold lots, arithmetic and currency labels.
  // All fields are local inputs; no network POST is sent to PapAuto API.
  const cost=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  await cost.goto(BASE,{waitUntil:'load',timeout:45000});
  await cost.waitForFunction(()=>document.querySelector('#picLot')?.options.length===12,{timeout:30000});
  assert.equal(await cost.locator('#pic-total').count(),0,'Unexpected duplicate older calculator');
  assert.equal(await cost.locator('.pic-total strong').innerText(),'—','No fabricated prefilled estimate permitted');
  const selected=await cost.locator('#picLot').inputValue();
  const registry=await cost.evaluate(async()=>{const r=await fetch('/data/premium-real-auction-lots.json');return r.json()});
  const lot=registry.lots.find(x=>x.id===selected);
  assert(lot && lot.status==='sold' && lot.market==='japan','Price must belong to a verified Japan sale');
  const sourceJpy=Number(String(lot.price_jpy).replace(/\D/g,''));
  const inputs=cost.locator('.pic-controls input');
  assert.equal(await inputs.count(),12,'Expected all cost fields');
  const values=['1','0','100','2','1.5','0','0','0','0','0','50000','0'];
  for(let i=0;i<values.length;i++){
    if(i===10){assert.equal(await inputs.nth(i).inputValue(),'50000','Fixed PapAuto commission');assert.equal(await inputs.nth(i).getAttribute('readonly'),'');}
    else await inputs.nth(i).fill(values[i]);
  }
  const expected=new Intl.NumberFormat('ru-RU',{maximumFractionDigits:0}).format(sourceJpy+200+50000)+' ₽';
  await cost.waitForFunction(expected=>document.querySelector('.pic-total strong')?.textContent===expected,expected,{timeout:10000});
  assert((await cost.locator('.pic-result').innerText()).includes('100 EUR · 150 USD · 200 ₽'),
    'Duty must be shown in EUR, USD and RUB on one line');
  const costOverflow=await cost.evaluate(()=>document.documentElement.scrollWidth-window.innerWidth);
  assert(costOverflow<=2,'Cost estimate overflows mobile viewport: '+costOverflow);
  console.log('PAPAUTO_COST_WORKSHEET_QA='+JSON.stringify({verifiedLots:registry.lots.length,selected,expected,overflow:costOverflow}));
  await cost.close();
  console.log('PAPAUTO_PREMIUM_VISUAL_QA='+JSON.stringify(results));
  await browser.close();
})().catch(e=>{console.error('PREMIUM_LIGHT_QA_FAILED',e.stack||e);process.exit(1)});
