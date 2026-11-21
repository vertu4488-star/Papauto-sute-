const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function element() {
  const listeners = Object.create(null);
  return {
    value: '', children: [], textContent: '', hidden: false, style: {}, id: '', className: '',
    setAttribute(name,value) { this[name]=String(value); },
    after(next) { this.nextSibling=next; },
    remove() { this.removed=true; },
    addEventListener(type, callback) { listeners[type] = callback; },
    replaceChildren(...children) { this.children = children; },
    append(...children) { this.children.push(...children); },
    get firstChild() { return this.children[0]; },
    fire(type) { assert(listeners[type], 'Missing listener: ' + type); listeners[type](); }
  };
}

const ids = Object.fromEntries([
  'catalogGrid','modelQuery','countryFilter','makeFilter','powerFilter',
  'catalogCount','catalogEmpty','catalogMore'
].map(id => [id, element()]));

const created = [];
const document = {
  getElementById: id => ids[id] || null,
  createElement: () => {const el=element();created.push(el);return el;}
};
const catalog = {
  japan: [
    ['Honda','Fit','1.5 л'],
    ['Honda','Freed','1.5 л'],
    ['Toyota','Corolla Fielder','1.5 л'],
    ['Nissan','Note','1.2 л']
  ],
  'south-korea': [['Hyundai','Avante','1.6 л']],
  china: [['Geely','Monjaro','2.0 л']]
};
const window = {PAPAUTO_CATALOG: catalog};
const PapAutoMetadata = {
  modelTypes: () => ['petrol'],
  fuelLabel: () => 'Бензин'
};

ids.countryFilter.value = 'japan';
vm.runInNewContext(fs.readFileSync('catalog-open-data.js', 'utf8'), {
  window, document, PapAutoMetadata, console
});
const references=()=>created.find(el=>el.id==='catalogModelIndex');
const cardTexts = () => references().children.map(row =>
  row.children.map(x => String(x.textContent || '')).join(' '));
assert.equal(ids.catalogGrid.children.length,0,'No empty photo cards in offline model directory');

ids.modelQuery.value = 'Хо';
ids.modelQuery.fire('input');
assert.equal(references().children.length, 2);
assert(cardTexts().every(x => x.includes('Honda')), cardTexts().join('; '));

ids.modelQuery.value = 'Хонда Фит';
ids.modelQuery.fire('input');
assert.equal(references().children.length, 1);
assert(cardTexts()[0].includes('Honda Fit'));

ids.modelQuery.value = 'ниссан ноут';
ids.modelQuery.fire('input');
assert.equal(references().children.length, 1);
assert(cardTexts()[0].includes('Nissan Note'));

ids.modelQuery.value = 'Monjaro';
ids.modelQuery.fire('input');
assert.equal(references().children.length, 0, 'Market filter must still apply');

ids.countryFilter.value = 'china';
ids.countryFilter.fire('change');
assert.equal(references().children.length, 1);
assert(cardTexts()[0].includes('Geely Monjaro'));

assert(references().children.every(x=>x.className==='catalog-model-row'));
assert.equal(ids.catalogGrid.children.length,0,'Photo cards require a real published matching lot');
console.log('Cyrillic make/model catalog search, country filter, photo-only visual cards: OK');
