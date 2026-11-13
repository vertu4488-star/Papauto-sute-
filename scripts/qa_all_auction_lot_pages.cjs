/* Deep read-only QA: every auction detail page, original local media, and mobile rendering. */
const {chromium,request}=require('playwright');
const assert=require('node:assert/strict');
const BASE='http://127.0.0.1:8765';
(async()=>{
  const client=await request.newContext({baseURL:BASE,timeout:30000});
  let browser;
  try{
    const response=await client.get('/data/gallery-lots.json');
    assert.equal(response.status(),200,'Published gallery JSON unavailable');
    const registry=await response.json();
    const lots=registry.lots;
    assert(Array.isArray(lots)&&lots.length>=35&&lots.length<=500,'Expected 35..500 full-sheet auction lots');
    assert.equal(registry.lot_count,lots.length,'HTML/data lot count mismatch');

    const gallery=await client.get('/gallery.html');
    assert.equal(gallery.status(),200,'Gallery page missing');
    const galleryHtml=await gallery.text();
    const lotAnchors=[...galleryHtml.matchAll(/class="gallery-full" href="(\/lots\/[a-z0-9-]+\.html)"/g)].map(match=>match[1]);
    assert.equal(lotAnchors.length,lots.length,'Every auction card must link to its own detailed page');
    assert.equal(new Set(lotAnchors).size,lots.length,'Duplicate detail page links');
    const mediaStatus=new Map();
    const validLocalMedia=/^\/assets\/(?:auction\/(?:home|approved)\/|premium-auctions\/)[a-z0-9-]+\.(?:jpg|jpeg|png|webp)$/;
    const loadImage=async path=>{
      assert(validLocalMedia.test(path),'Unapproved photo path: '+path);
      if(mediaStatus.has(path))return mediaStatus.get(path);
      const image=await client.get(path);
      assert.equal(image.status(),200,'Local auction media missing: '+path);
      const data=await image.body();
      assert(data.length>100,'Empty/broken auction photo or full sheet: '+path);
      assert(/^image\//.test(image.headers()['content-type']||''),'Expected actual photo bytes: '+path);
      mediaStatus.set(path,true);
    };

    for(const lot of lots){
      const pagePath='/lots/'+lot.id+'.html';
      assert(lotAnchors.includes(pagePath),'Missing lot link '+lot.id);
      assert.equal(lot.inspection_kind,'Аукционный лист','Diagram-only lot must not be published: '+lot.id);
      const page=await client.get(pagePath);
      assert.equal(page.status(),200,'Detailed lot page missing: '+lot.id);
      const html=await page.text();
      assert(html.includes('content="noindex,follow"'),'Premature SEO publication: '+lot.id);
      assert(html.includes('class="lot-description"'),'Missing verified description: '+lot.id);
      assert(html.includes('class="lot-sheet"'),'Missing full auction sheet section: '+lot.id);
      assert(html.includes('href="/podbor.html?similar='),'Auction-to-request link missing: '+lot.id);
      assert(html.includes(lot.inspection_image),'Auction sheet mismatch: '+lot.id);
      assert(html.includes(lot.photos[0]),'Exact lot cover mismatch: '+lot.id);
      assert(!/href=["']https?:\/\//i.test(html),'External vendor link found: '+lot.id);
      assert(!/\/assets\/(?:demo|visual)\//.test(html),'Street/stock library on detail page: '+lot.id);
      const srcs=[...html.matchAll(/<img\b[^>]*\bsrc="([^"]+)"/g)].map(match=>match[1]);
      assert(srcs.includes(lot.inspection_image),'No sheet image in page: '+lot.id);
      assert(srcs.includes(lot.photos[0]),'No main photo image in page: '+lot.id);
      // Optional stale historical angles are correctly omitted; no substitution.
      for(const src of srcs)await loadImage(src);
    }

    browser=await chromium.launch({headless:true});
    const samples=[lots[0],lots[Math.floor(lots.length/2)],lots[lots.length-1]];
    const tested=[];
    for(const width of [1440,390,320]){
      const page=await browser.newPage({
        viewport:{width,height:width===1440?900:780},
        isMobile:width<500,hasTouch:width<500
      });
      const failures=[];
      page.on('pageerror',error=>failures.push(error.message));
      for(const lot of samples){
        await page.goto(BASE+'/lots/'+lot.id+'.html',{waitUntil:'load',timeout:30000});
        const image=page.locator('.lot-photo img').first();
        const sheet=page.locator('.lot-sheet img');
        await image.evaluate(img=>img.decode());
        await sheet.evaluate(img=>img.decode());
        const measurements=await page.evaluate(()=>({
          overflow:document.documentElement.scrollWidth-window.innerWidth,
          cover:getComputedStyle(document.querySelector('.lot-photo img')).objectFit,
          sheet:getComputedStyle(document.querySelector('.lot-sheet img')).objectFit
        }));
        assert(measurements.overflow<=2,'Horizontal overflow '+width+'px '+lot.id+': '+measurements.overflow);
        assert.equal(measurements.cover,'contain','Auction photograph cropped: '+lot.id);
        assert.equal(measurements.sheet,'contain','Auction sheet cropped: '+lot.id);
        assert.equal(await page.locator('a.lot-apply').count(),2,'Missing request CTA '+lot.id);
        tested.push(width+':'+lot.id);
      }
      assert.equal(failures.length,0,'Browser errors '+width+': '+failures.join('; '));
      await page.close();
    }

    console.log('PAPAUTO_ALL_AUCTION_LOT_DETAILS_QA='+JSON.stringify({
      pages_checked:lots.length,media_checked:mediaStatus.size,
      all_full_sheets:true,no_street_photos:true,no_external_sellers:true,
      noindex_until_launch:true,responsive_samples:tested
    }));
  }finally{
    if(browser)await browser.close();
    await client.dispose();
  }
})().catch(e=>{console.error('PAPAUTO_ALL_DETAILS_QA_FAILED',e.stack||e);process.exitCode=1;});
