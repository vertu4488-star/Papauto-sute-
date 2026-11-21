/* Regression: owner-approved source media is mandatory for all visual car cards.
   Non-photo model references remain navigable text rows; never blank image tiles. */
"use strict";
const assert=require("node:assert/strict");
const {chromium}=require("playwright");
const base=process.env.PAPAUTO_QA_URL||"http://127.0.0.1:8765";

(async()=>{
  const browser=await chromium.launch({headless:true});
  const findings=[];
  try{
    for(const width of [390,1440]){
      const page=await browser.newPage({viewport:{width,height:860}});
      page.on("pageerror",error=>{throw error;});
      await page.goto(base+"/catalog.html",{waitUntil:"load"});
      await page.waitForFunction(()=>{
        const cards=document.querySelectorAll(".model-card").length;
        const index=document.querySelectorAll(".catalog-model-row").length;
        return cards>=4&&cards+index===120;
      },{timeout:25000});
      const catalog=await page.evaluate(async()=>{
        const visual=[...document.querySelectorAll(".model-card")];
        const list=[...document.querySelectorAll(".catalog-model-row")];
        for(const c of visual.slice(0,5)){
          const image=c.querySelector("a.model-photo img");
          if(!image||!image.src.startsWith(location.origin+"/assets/"))throw Error("Missing verified model photo");
          await image.decode();
        }
        return {visual:visual.length,reference:list.length,images:visual.filter(c=>c.querySelector(".model-photo img")).length,
          oldPlaceholder:document.querySelectorAll(".model-photo span").length};
      });
      assert(catalog.visual>=4,"Catalog should display photo-backed approved auction examples");
      assert.equal(catalog.visual,catalog.images);
      assert.equal(catalog.visual+catalog.reference,120);
      findings.push({width,page:"catalog",...catalog});
      await page.goto(base+"/popular-import-2l.html",{waitUntil:"load"});
      await page.waitForFunction(()=>document.querySelectorAll(".car-card").length>=4,{timeout:25000});
      const popular=await page.evaluate(async()=>{
        const visual=[...document.querySelectorAll(".car-card")];
        const reference=[...document.querySelectorAll(".model-reference")];
        for(const c of visual.slice(0,5)){
          const i=c.querySelector(".verified-auction-photo img");
          if(!i)throw Error("Car visual card has no verified auction photo");
          await i.decode();
        }
        return {visual:visual.length,reference:reference.length,
          allImages:visual.every(c=>!!c.querySelector(".verified-auction-photo img")),
          blank:document.querySelectorAll(".photo.auction-pending").length};
      });
      assert(popular.visual>=4,"Popular-import page should show real auction images");
      assert.equal(popular.visual+popular.reference,78);
      assert(popular.allImages);
      assert.equal(popular.blank,0);
      findings.push({width,page:"popular",...popular});
      for(const [name,real,reference] of [["japan-compact-models.html",18,12],["korea-popular-models.html",0,30]]){
        await page.goto(base+"/"+name,{waitUntil:"load"});
        const q=await page.evaluate(()=>({
          visual:document.querySelectorAll("article.unit").length,
          ref:document.querySelectorAll("article.model-reference").length,
          emptyVisual:[...document.querySelectorAll("article.unit")].filter(c=>!c.querySelector(".media img")).length
        }));
        assert.equal(q.visual,real,name);
        assert.equal(q.ref,reference,name);
        assert.equal(q.emptyVisual,0,name);
        findings.push({width,page:name,...q});
      }
      await page.close();
    }
  }finally{await browser.close();}
  console.log("PAPAUTO_PHOTO_ONLY_CARDS_QA_OK",JSON.stringify(findings));
})().catch(err=>{console.error(err);process.exit(1)});
