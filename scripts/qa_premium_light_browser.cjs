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
    const state=await page.evaluate(()=>{
      const body=document.body,stat=document.querySelector('.stats'),hero=document.querySelector('.hero');
      const sheets=[...document.querySelectorAll('.real-img-sheet')].filter(x=>getComputedStyle(x).display!=='none');
      const images=[...document.querySelectorAll('.real-card img')];
      const first=images[0];
      return {
        linkedCSS:[...document.styleSheets].some(s=>s.href?.includes('/premium-lexus-light.css')),
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
        visibleSheets:sheets.length,
        mobileMenuVisible:getComputedStyle(document.querySelector('.mobile-nav')).display!=='none'
      };
    });
    assert(state.linkedCSS,'Light premium CSS missing at '+viewport.width);
    assert.equal(state.realCards,17);
    assert.equal(state.countryCounts.japan,14);
    assert.equal(state.countryCounts.korea,3);
    assert.equal(state.models,32);
    assert(state.heroImageLoaded,'Hero photo missing');
    assert(state.firstPhotoLoaded,'Auction photo missing');
    assert(state.horizontalOverflow<=2,'Horizontal overflow '+state.horizontalOverflow+'px @'+viewport.width);
    assert(state.statsOverflow<=2,'Stats overflow '+state.statsOverflow+'px @'+viewport.width);
    if(viewport.width<=390){
      assert(state.mobileMenuVisible,'Mobile menu missing');
      assert(state.visibleSheets>0,'Original auction sheet links inaccessible on mobile');
      await page.locator('.mobile-nav summary').click();
      assert(await page.locator('.mobile-nav[open] nav a').count()>0,'Mobile menu did not open');
      await page.locator('.mobile-nav summary').click();
    }
    await page.locator('[data-real-filter=korea]').click();
    assert.equal(await page.locator('.real-card:visible').count(),3,'Korea filter invalid');
    await page.locator('[data-real-filter=japan]').click();
    assert.equal(await page.locator('.real-card:visible').count(),14,'Japan filter invalid');
    await page.locator('[data-real-filter=all]').click();
    assert.equal(await page.locator('.real-card:visible').count(),17,'All filter invalid');
    const name=viewport.width===1440?'premium-light-desktop.png':viewport.width===390?'premium-light-mobile.png':'premium-light-small.png';
    await page.screenshot({path:name,fullPage:viewport.width===1440?false:true});
    assert.equal(errors.length,0,'Browser JS errors: '+JSON.stringify(errors));
    assert.equal(failed.length,0,'Missing assets: '+JSON.stringify(failed));
    results.push({viewport,state,errors,failed});
    await page.close();
  }
  console.log('PAPAUTO_PREMIUM_VISUAL_QA='+JSON.stringify(results));
  await browser.close();
})().catch(e=>{console.error('PREMIUM_LIGHT_QA_FAILED',e.stack||e);process.exitCode=1});
