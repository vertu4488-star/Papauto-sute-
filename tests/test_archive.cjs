const assert=require('node:assert/strict');const C=require('../archive-core.js');
const base={id:'one',country:'japan',make:'Toyota',model:'Prius',year:2020,sold_date:'2026-01-02',price:100,currency:'JPY',status:'sold',source:'Test fixture',source_url:'https://example.org/lot',photos:['javascript:alert(1)','https://example.org/photo']};
const r=C.normalize([base,{...base,id:'two',price:300,mileage:10000},{...base,id:'three',country:'china',currency:'CNY',price:500}]);
assert.deepEqual(C.stats(r).find(s=>s.currency==='JPY'),{currency:'JPY',count:2,min:100,max:300,mean:200,median:200});
assert.equal(C.filter(r,{country:'japan',mileage:20000}).length,1);assert.equal(C.filter(r,{from:'2026-02-01'}).length,0);assert.equal(C.filter(r,{favorites:['three']})[0].currency,'CNY');assert.equal(r[0].photos.length,1);
assert.throws(()=>C.normalize([base,base]));assert.throws(()=>C.normalize([{...base,status:'removed'}]));assert.throws(()=>C.normalize([{...base,price:0}]));assert.throws(()=>C.normalize([{...base,sold_date:'2026-02-30'}]));assert.throws(()=>C.normalize([{...base,currency:'KRW'}]));
assert.deepEqual(C.csv('a,b\r\n"two, words","line\nnext"\r\n'),[{a:'two, words',b:'line\nnext'}]);assert.throws(()=>C.csv('a,b\n"oops'));assert.equal(C.https('https://name:password@example.org'),'');
console.log('Archive validation, filters, currencies, CSV and unsafe URL tests passed');
