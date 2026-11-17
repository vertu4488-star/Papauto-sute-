const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

function element() {
  const listeners = Object.create(null);
  return {
    value: '', children: [], textContent: '', hidden: false, style: {},
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

const document = {
  getElementById: id => ids[id] || null,
  createElement: () => element()
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
const cardTexts = () => ids.catalogGrid.children.map(card =>
  card.children.map(x => String(x.textContent || '')).join(' '));

ids.modelQuery.value = 'Хо';
ids.modelQuery.fire('input');
assert.equal(ids.catalogGrid.children.length, 2);
assert(cardTexts().every(x => x.includes('Honda')), cardTexts().join('; '));

ids.modelQuery.value = 'Хонда Фит';
ids.modelQuery.fire('input');
assert.equal(ids.catalogGrid.children.length, 1);
assert(cardTexts()[0].includes('Honda Fit'));

ids.modelQuery.value = 'ниссан ноут';
ids.modelQuery.fire('input');
assert.equal(ids.catalogGrid.children.length, 1);
assert(cardTexts()[0].includes('Nissan Note'));

ids.modelQuery.value = 'Monjaro';
ids.modelQuery.fire('input');
assert.equal(ids.catalogGrid.children.length, 0, 'Market filter must still apply');

ids.countryFilter.value = 'china';
ids.countryFilter.fire('change');
assert.equal(ids.catalogGrid.children.length, 1);
assert(cardTexts()[0].includes('Geely Monjaro'));

console.log('Cyrillic make/model catalog search, country filter, text-only cards: OK');
