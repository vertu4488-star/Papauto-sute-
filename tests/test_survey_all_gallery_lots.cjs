/* Read every real, published PapAuto auction lot and require a real catalogue
 * preselection for its model, year and country. No street/stock/AI images; no leads.
 * Uses the ACTUAL photo-backed 37-lot gallery and ACTUAL site catalogue. */
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const ctx={window:{},document:{getElementById:()=>null}};
vm.runInNewContext(fs.readFileSync('vehicle-catalogue.js','utf8'),ctx);
vm.runInNewContext(fs.readFileSync('survey-similar-prefill.js','utf8'),ctx);
const catalogue=ctx.window.PAPAUTO_CATALOG;
const resolve=ctx.window.PapAutoSimilarPrefill.resolve;
const gallery=JSON.parse(fs.readFileSync('data/gallery-lots.json','utf8'));
assert.equal(gallery.lots.length,37,'37 published exact-photo full-sheet lots');
const marketName={japan:'Япония','south-korea':'Корея',china:'Китай'};
let checked=0;
for(const lot of gallery.lots){
 assert.equal(lot.inspection_kind,'Аукционный лист','Never use diagram-only lots');
 const make=lot.model.startsWith('Mercedes-Benz')?'Mercedes-Benz':lot.model.split(' ')[0];
 const url=lot.model+' '+lot.year+' · '+marketName[lot.market];
 const selection=resolve(url,catalogue);
 assert.equal(selection?.market,lot.market,'market mismatch '+lot.id);
 assert.equal(selection?.make,make,'make mismatch '+lot.id+' '+JSON.stringify(selection));
 assert.equal(selection?.year,String(lot.year),'year mismatch '+lot.id);
 assert(selection?.matched,'model not selected for '+lot.id+': '+JSON.stringify(selection));
 assert(selection?.model,'Missing catalogue model for '+lot.id);
 assert(catalogue[lot.market].some(([m,n])=>m===selection.make&&n===selection.model),
        'Selected non-existent model '+lot.id);
 assert.equal(selection.reference,lot.model+' '+String(lot.year));
 checked++;
}
console.log('PAPAUTO_AUCTION_LEAD_FULL_COVERAGE='+JSON.stringify({checked,lots:gallery.lots.length,complete_sheets:true}));
