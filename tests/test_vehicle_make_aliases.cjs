const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
function element() {
  const handlers = {};
  return {
    value: '', label: '', id: '', children: [], handlers, form: null,
    addEventListener(event, fn) { handlers[event] = fn; },
    replaceChildren(...items) { this.children = items; },
    setAttribute(name, value) { this[name] = value; }
  };
}
const country = element(), make = element(), model = element();
country.value = 'japan'; make.value = 'Хо';
make.form = element();
const elements = {vehicleCountry:country, vehicleMake:make, vehicleModel:model};
const document = {
  body:{append() {}},
  createElement:()=>element(),
  getElementById:id=>elements[id] || null
};
const window = {};
vm.runInNewContext(fs.readFileSync('vehicle-catalogue.js','utf8'),{window,document,console});
assert(window.PAPAUTO_CATALOG.japan.some(x=>x[0]==='Honda' && x[1]==='Fit'));
assert(make.handlers.blur, 'Make normalization blur handler is missing');
assert(make.handlers.input, 'Make input handler is missing');
const list = document.getElementById('vehicleMake');
assert(list.list==='papautoMakes');
make.handlers.blur();
assert.equal(make.value,'Honda','Russian prefix Хо should resolve to Honda on blur');
make.value='Тойота'; make.handlers.input();
assert.equal(make.value,'Toyota','Russian make must be canonicalized before form submit');
make.value='Хонда'; make.handlers.submit?.();
make.form.handlers.submit();
assert.equal(make.value,'Honda');
country.value='south-korea'; country.handlers.change();
assert.equal(make.value,'');
console.log('PapAuto Cyrillic make aliases, prefix hints, form normalization: OK');
