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
      const body=document.body,stat=document.querySelector('.stats'),hero=document.querySelector('.hero');
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
        statsOverflow:stat.scrollWidth-stat.clientWidth,
        heroImageLoaded:(()=>{const i=document.querySelector('.hero-visual img');return !!i?.complete && i.naturalWidth>0})(),
        firstPhotoLoaded:!!first?.complete && first.naturalWidth>0,
        auctionOnly:[...document.images].every(i => !/\/assets\/(demo|visual)\//.test(i.getAttribute('src')||'')),
        visibleSheets:sheets.length,
        mobileMenuVisible:getComputedStyle(document.querySelector('.mobile-nav')).display!=='none'
      };
    });
    // The expanded selection is separate from the 17 real historical lots.
    await page.locator('[data-selection-grid] .selection-model-entry').first().waitFor({state:'visible',timeout:20000});
    const expanded=await page.evaluate(()=>({
      css:[...document.styleSheets].some(s=>s.href?.includes('premium-expanded-catalog.css')),
      all:document.querySelector('[data-selection-count]')?.textContent,
      count:document.querySelectorAll('[data-selection-grid] .selection-model-entry').length,
      chinaTab:!!document.querySelector('[data-selection-filter="china"]'),
      photo:document.querySelector('[data-selection-grid] img')?.getAttribute('src')
    }));
    assert(expanded.css,'Expanded catalogue CSS missing at '+viewport.width);
    assert(expanded.chinaTab,'China market tab not present');
    assert(expanded.all.includes('из 135'),'Expected 135 models in catalogue, got '+expanded.all);
    assert.equal(expanded.count,12,'Expected 12 text-only model rows');
    assert(!expanded.photo,'Model references must NOT publish street photos');
    await page.locator('[data-selection-filter="china"]').click();
    assert((await page.locator('[data-selection-count]').textContent()).includes('из 45'),'China should offer 45 reference models');
    assert((await page.locator('[data-selection-grid] .selection-model-entry').first().innerText()).includes('Geely'),'China starts with priority Geely model');
    await page.locator('[data-selection-more]').click();
    assert.equal(await page.locator('[data-selection-grid] .selection-model-entry').count(),24,'Show more should append twelve');
    await page.locator('[data-selection-filter="korea"]').click();
    assert((await page.locator('[data-selection-count]').textContent()).includes('из 45'),'Korea should offer 45 reference models');
    await page.locator('[data-selection-filter="japan"]').click();
    assert((await page.locator('[data-selection-count]').textContent()).includes('из 45'),'Japan should offer 45 reference models');
    await page.locator('[data-selection-filter="all"]').click();
    assert(state.linkedCSS,'Light premium CSS missing at '+viewport.width);
    assert(state.manropeActivated,'Self-hosted Manrope Cyrillic font not active at '+viewport.width);
    assert.equal(state.realCards,14);
    assert.equal(state.countryCounts.japan,14);
    assert.equal(state.countryCounts.korea,0);
    assert.equal(state.models,0);
    assert.equal(await page.locator('[data-selection-grid] img').count(),0,'Non-auction model gallery has returned');
    assert(state.heroImageLoaded,'Hero photo missing');
    assert(state.firstPhotoLoaded,'Auction photo missing');
    assert(state.auctionOnly,'Non-auction model photograph was displayed');
    assert(state.horizontalOverflow<=2,'Horizontal overflow '+state.horizontalOverflow+'px @'+viewport.width);
    assert(state.statsOverflow<=2,'Stats overflow '+state.statsOverflow+'px @'+viewport.width);
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
    await page.locator('[data-real-filter=korea]').click();
    assert.equal(await page.locator('.real-card:visible').count(),3,'Korea filter invalid');
    await page.locator('[data-real-filter=japan]').click();
    assert.equal(await page.locator('.real-card:visible').count(),14,'Japan filter invalid');
    await page.locator('[data-real-filter=all]').click();
    assert.equal(await page.locator('.real-card:visible').count(),14,'All auction filter invalid');
    if(viewport.width===390){
      await page.locator('#verified-lots').scrollIntoViewIfNeeded();
      await page.screenshot({path:'premium-light-mobile-catalog.png',fullPage:false});
    }
    assert.equal(errors.length,0,'Browser JS errors: '+JSON.stringify(errors));
    assert.equal(failed.length,0,'Missing assets: '+JSON.stringify(failed));
    results.push({viewport,state,errors,failed});
    await page.close();
  }
  // Deep link from China country page must preselect its 45 card examples.
  const cnLink=await browser.newPage({viewport:{width:390,height:844},isMobile:true,hasTouch:true});
  await cnLink.goto(BASE+'?market=china#market-catalog',{waitUntil:'load',timeout:45000});
  await cnLink.locator('.selection-model-entry').first().waitFor({state:'visible',timeout:20000});
  assert((await cnLink.locator('[data-selection-count]').textContent()).includes('из 45'),'China deep-link should contain 45 models');
  assert.equal(await cnLink.locator('[data-selection-filter=china]').getAttribute('aria-pressed'),'true','China tab should activate via URL');
  await cnLink.close();
  // Isolated noindex mobile experiment: original image and auction gallery
  // must survive the strict public build and never depend on third-party media.
  const preview=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:1,isMobile:true,hasTouch:true});
  const previewFailures=[];
  preview.on('pageerror',e=>previewFailures.push('JS: '+e.message));
  preview.on('response',r=>{if(r.status()>=400)previewFailures.push('HTTP '+r.status()+' '+r.url())});
  await preview.goto('http://127.0.0.1:8765/premium-mobile-photo-demo.html',{waitUntil:'load',timeout:45000});
  await preview.locator('.real-card').first().waitFor({state:'visible'});
  await preview.locator('[data-selection-grid] .selection-model-entry').first().waitFor({state:'visible',timeout:20000});
  assert((await preview.locator('[data-selection-count]').textContent()).includes('из 135'),'Preview should have 135 models');
  await preview.locator('[data-selection-filter="china"]').click();
  assert((await preview.locator('[data-selection-count]').textContent()).includes('из 45'),'China should be selectable in mobile preview');
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
  assert.equal(previewState.cards,14,'Preview should retain 14 real auction cards');
  assert.equal(previewState.objectFit,'contain','Preview main auction photo must be uncropped');
  assert(previewState.pageOverflow<=2,'Preview horizontal scroll '+previewState.pageOverflow+'px');
  assert.equal(previewFailures.length,0,JSON.stringify(previewFailures));
  await preview.locator('#verified-lots').scrollIntoViewIfNeeded();
  await preview.screenshot({path:'premium-mobile-photo-preview.png',fullPage:false});
  console.log('PAPAUTO_PREMIUM_MOBILE_PREVIEW_QA='+JSON.stringify(previewState));
  await preview.close();
  console.log('PAPAUTO_PREMIUM_VISUAL_QA='+JSON.stringify(results));
  await browser.close();
})().catch(e=>{console.error('PREMIUM_LIGHT_QA_FAILED',e.stack||e);process.exitCode=1});
