"use strict";
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");

function element(){
  const listeners=Object.create(null);
  return {
    value:"",children:[],textContent:"",hidden:false,style:{},id:"",className:"",
    classList:{add(){}},
    setAttribute(name,value){this[name]=String(value);},
    addEventListener(type,callback){listeners[type]=callback;},
    replaceChildren(...children){this.children=children;},
    append(...children){this.children.push(...children);},
    remove(){this.removed=true;},
    get firstChild(){return this.children[0];},
    fire(type){assert(listeners[type],"Missing listener: "+type);listeners[type]();}
  };
}
const ids=Object.fromEntries([
  "catalogGrid","modelQuery","countryFilter","makeFilter","powerFilter",
  "catalogCount","catalogEmpty","catalogMore"
].map(id=>[id,element()]));
const document={getElementById:id=>ids[id]||null,createElement:()=>element()};
const window={PAPAUTO_CATALOG:{
  japan:[["Honda","Fit","1.5 л"],["Honda","Freed","1.5 л"],["Toyota","Corolla Fielder","1.5 л"],["Nissan","Note","1.2 л"]],
  "south-korea":[["Hyundai","Avante","1.6 л"]],
  china:[["Geely","Monjaro","2.0 л"]]
}};

const sample=(id,model)=>({
  id,model,market:"japan",year:2022,auction:"JU Tokyo",lot_number:"130",
  mileage_km:36000,grade:"4.5",
  description:"Оригинальный аукционный лот с пробегом, оценкой и полным оригинальным документом конкретного автомобиля.",
  photos:["/assets/auction/approved/"+id+"-front.jpg"],
  inspection_image:"/assets/auction/approved/"+id+"-sheet.jpg"
});
const fetch=async()=>({ok:true,json:async()=>({lots:[
  sample("honda-fit","Honda Fit"),sample("honda-freed","Honda Freed"),sample("nissan-note","Nissan Note")
]})});
const texts=()=>ids.catalogGrid.children.map(c=>c.children.map(e=>String(e.textContent||"")).join(" "));
ids.countryFilter.value="japan";
const context=vm.createContext({document,window,console,fetch,Intl});
vm.runInContext(fs.readFileSync("vehicle-metadata.js","utf8"),context);
vm.runInContext(fs.readFileSync("catalog-open-data.js","utf8"),context);
(async()=>{
  await new Promise(resolve=>setImmediate(resolve));
  assert.equal(ids.catalogGrid.children.length,3,"Only 3 model entries have exact auction photo+sheet+description");
  assert(ids.catalogGrid.children.every(c=>c.children.some(v=>v.className==="catalog-verified-media")));
  assert(texts().every(text=>text.includes("Документы не проверены")));
  ids.modelQuery.value="Хо";ids.modelQuery.fire("input");
  assert.equal(ids.catalogGrid.children.length,2);
  assert(texts().every(x=>x.includes("Honda")));
  ids.modelQuery.value="Хонда Фит";ids.modelQuery.fire("input");
  assert.equal(ids.catalogGrid.children.length,1);
  assert(texts()[0].includes("Honda Fit"));
  ids.modelQuery.value="ниссан ноут";ids.modelQuery.fire("input");
  assert.equal(ids.catalogGrid.children.length,1);
  assert(texts()[0].includes("Nissan Note"));
  ids.modelQuery.value="Monjaro";ids.modelQuery.fire("input");
  assert.equal(ids.catalogGrid.children.length,0,"Never show no-photo model rows");
  ids.countryFilter.value="china";ids.countryFilter.fire("change");
  assert.equal(ids.catalogGrid.children.length,0,"No unverified China auction cards in Japan-only lot registry");
  console.log("PapAuto: Cyrillic model search and strict photo+sheet+description deletion policy OK");
})().catch(error=>{console.error(error);process.exit(1);});
