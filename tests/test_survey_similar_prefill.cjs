const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const ctx={};
vm.runInNewContext(fs.readFileSync('survey-similar-prefill.js','utf8'),ctx);
const resolve=ctx.PapAutoSimilarPrefill.resolve;
const catalogue={
  japan:[['Toyota','Corolla'],['Toyota','Corolla Fielder'],['Toyota','Corolla Axio'],
         ['BMW','X1'],['BMW','1 Series'],['Audi','Q3'],['Mercedes-Benz','GLA']],
  'south-korea':[['Hyundai','Avante / Elantra'],['Kia','K5'],['BMW','X3']],
  china:[['Geely','Monjaro'],['BYD','Song Plus']]
};
function pick(input,expected){
  const got=resolve(input,catalogue);
  for(const key of Object.keys(expected))assert.equal(got?.[key],expected[key],input+' '+key);
}
pick('Toyota Corolla Sport 2023 · Япония',{market:'japan',make:'Toyota',model:'Corolla',year:'2023',matched:true});
pick('Toyota Corolla Fielder 2022 · Япония',{market:'japan',make:'Toyota',model:'Corolla Fielder',year:'2022'});
pick('BMW X1 sDrive18i 2021 · Япония',{market:'japan',make:'BMW',model:'X1',year:'2021'});
pick('BMW 118i M Sport 2019 · Япония',{market:'japan',make:'BMW',model:null,year:'2019',matched:false});
pick('Mercedes-Benz GLA 180 AMG 2025 · Япония',{market:'japan',make:'Mercedes-Benz',model:'GLA'});
pick('Hyundai Avante 2024 · Корея',{market:'south-korea',make:'Hyundai',model:'Avante / Elantra'});
pick('Kia K5 2021 · Южная Корея',{market:'south-korea',make:'Kia',model:'K5'});
pick('Geely Monjaro 2024 · Китай',{market:'china',make:'Geely',model:'Monjaro'});
pick('Toyota Corolla',{market:'japan',make:'Toyota',model:'Corolla',year:null});
pick('Unknown Auto 2024 · Китай',{market:'china',make:null,model:null,matched:false});
// Our Japan catalogue must actually contain the photographed premium models.
const vmCatalog={window:{},document:{getElementById:()=>null}};
vm.runInNewContext(fs.readFileSync('vehicle-catalogue.js','utf8'),vmCatalog);
const japan=vmCatalog.window.PAPAUTO_CATALOG.japan;
for(const [make,model] of [['BMW','X1'],['BMW','X2'],['BMW','1 Series'],['Mercedes-Benz','GLA'],['Mercedes-Benz','GLB'],['Audi','Q2'],['Audi','Q3']]){
 assert(japan.some(([m,x])=>m===make&&x===model),'Missing model in Japan form: '+make+' '+model);
}
const applied=resolve('BMW X1 sDrive18i 2021 · Япония',vmCatalog.window.PAPAUTO_CATALOG);
assert.equal(applied.market,'japan');
assert.equal(applied.make,'BMW');
assert.equal(applied.model,'X1');
assert.equal(resolve('',catalogue),null);
assert.equal(resolve('x'.repeat(181),catalogue),null);
const page=fs.readFileSync('podbor.html','utf8');
assert(page.indexOf('/survey-similar-prefill.js')<page.indexOf('/survey-podbor.js'));
const script=fs.readFileSync('survey-podbor.js','utf8');
assert(script.includes('PapAutoSimilarPrefill?.resolve'));
assert(script.includes("survey.setValue('notes','Интересует аналог аукционного лота:"));
console.log('PAPAUTO_SURVEY_AUCTION_PREFILL: 11 tests passed');
