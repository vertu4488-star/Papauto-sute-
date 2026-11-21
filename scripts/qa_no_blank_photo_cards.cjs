/* PapAuto: never ship a vehicle card without original photograph, full sheet and genuine description. */
"use strict";
const assert=require("node:assert/strict");
const {chromium}=require("playwright");
const base=process.env.PAPAUTO_QA_URL||"http://127.0.0.1:8765";

(async()=>{
  const browser=await chromium.launch({headless:true});
  const findings=[];
  try{
    for(const width of [390,1440]){
      const page=await browser.newPage({viewport:{width,height:900}});
      const errors=[];page.on("pageerror",error=>errors.push(String(error)));
      await page.goto(base+"/catalog.html",{waitUntil:"load"});
      await page.waitForFunction(()=>document.querySelectorAll(".model-card").length>=4,
        null,{timeout:25000});
      const catalog=await page.evaluate(async()=>{
        const cards=[...document.querySelectorAll(".model-card")];
        for(const c of cards.slice(0,4)){
          for(const img of c.querySelectorAll(".catalog-verified-media img")){
            img.loading="eager";
            await Promise.race([img.decode(),new Promise((_,reject)=>setTimeout(()=>
              reject(Error("Missing source image in model card")),8000))]);
          }
        }
        return {
          count:cards.length,
          empty:cards.filter(c=>c.querySelectorAll(".catalog-verified-media img").length!==2 ||
              (c.querySelector(".catalog-lot-full-description")?.textContent.trim().length||0)<50).length,
          unverifiedTextRows:document.querySelectorAll(".catalog-model-row,.model-reference").length
        };
      });
      assert(catalog.count>=4);
      assert.equal(catalog.empty,0,"No card without full original photo+sheet+description");
      assert.equal(catalog.unverifiedTextRows,0,"Unverified models must not be listed");
      findings.push({width,page:"catalog",...catalog});
      await page.goto(base+"/popular-import-2l.html",{waitUntil:"load"});
      const popular=await page.evaluate(async()=>{
        const cards=[...document.querySelectorAll(".car-card")];
        for(const c of cards.slice(0,3)){
          for(const img of c.querySelectorAll(".verified-auction-photo img,.verified-auction-document img")){
            img.loading="eager";
            await Promise.race([img.decode(),new Promise((_,reject)=>setTimeout(()=>
              reject(Error("Popular model photo/sheet did not load")),8000))]);
          }
        }
        const data=await (await fetch("/data/gallery-lots.json")).json();
        const byId=new Map(data.lots.map(lot=>[lot.id,lot]));
        const simple=value=>String(value||"").toLowerCase().replace(/[\\s-]/g,"");
        const identityErrors=cards.filter(card=>{
          const href=card.querySelector(".verified-auction-photo a")?.getAttribute("href")||"";
          const id=decodeURIComponent(href.replace(/^\\/lots\\//,"").replace(/\\.html$/,""));
          const lot=byId.get(id);
          return !lot||simple(lot.model)!==simple(card.querySelector("h2")?.textContent)||
            lot.photos?.[0]!==card.querySelector(".verified-auction-photo img")?.getAttribute("src")||
            lot.inspection_image!==card.querySelector(".verified-auction-document img")?.getAttribute("src")||
            !lot.description||lot.description.length<50||!lot.grade||lot.mileage_km==null;
        }).map(card=>card.querySelector("h2")?.textContent);
        return {
          count:cards.length,
          bad:cards.filter(c=>c.querySelectorAll(".verified-auction-photo img,.verified-auction-document img").length!==2 ||
               (c.querySelector(".verified-lot-description")?.textContent.trim().length||0)<50).length,
          placeholders:document.querySelectorAll(".photo.auction-pending,.model-reference").length,
          identityErrors
        };
      });
      assert.equal(popular.count,34,"Exactly 34 exact-model photo+sheet+description verified popular models");
      assert.equal(popular.bad,0);
      assert.equal(popular.placeholders,0);
      assert.deepEqual(popular.identityErrors,[],"Only matching exact-model original auction photographs and sheets");
      findings.push({width,page:"popular",...popular});
      for(const [path,expected] of [["japan-compact-models.html",27],["korea-popular-models.html",0]]){
        await page.goto(base+"/"+path,{waitUntil:"load"});
        const result=await page.evaluate(async()=>{
          const cards=[...document.querySelectorAll("article.unit")];
          const data=await (await fetch("/data/gallery-lots.json")).json();
          const byId=new Map(data.lots.map(lot=>[lot.id,lot]));
          const simple=value=>String(value||"").toLowerCase().replace(/[\\s-]/g,"");
          const identityErrors=cards.filter(card=>{
            const href=card.querySelector(".media a")?.getAttribute("href")||"";
            const id=decodeURIComponent(href.replace(/^\\/lots\\//,"").replace(/\\.html$/,""));
            const lot=byId.get(id);
            const imgs=[...card.querySelectorAll(".media img")];
            return !lot||simple(lot.model)!==simple(card.querySelector("h2")?.textContent)||
              lot.photos?.[0]!==imgs[0]?.getAttribute("src")||
              lot.inspection_image!==imgs[1]?.getAttribute("src")||
              !lot.description||lot.description.length<50||!lot.grade||lot.mileage_km==null;
          }).map(card=>card.querySelector("h2")?.textContent);
          return {
            count:cards.length,
            bad:cards.filter(c=>c.querySelectorAll(".media img").length!==2 ||
              (c.querySelector(".lot-full-desc")?.textContent.trim().length||0)<50).length,
            reference:document.querySelectorAll("article.model-reference").length,
            identityErrors
          };
        });
        assert.equal(result.count,expected,path+" count");
        assert.equal(result.bad,0,path+" no unverifiable card");
        assert.equal(result.reference,0,path+" no unverified reference rows");
        assert.deepEqual(result.identityErrors,[],path+" exact model and original media validation");
        findings.push({width,page:path,...result});
      }
      assert.deepEqual(errors,[],"No browser script errors");
      await page.close();
    }
  }finally{await browser.close();}
  console.log("PAPAUTO_VERIFIED_CARDS_ONLY_QA_OK "+JSON.stringify(findings));
})().catch(error=>{console.error(error);process.exit(1);});
