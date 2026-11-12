/* Verified premium vehicle examples. Only source-backed facts are rendered. */
(() => {
  const dataPath = '/data/premium-real-examples-2026.json';
  const doc = document;
  const format = value => new Intl.NumberFormat('ru-RU').format(Number(value));
  const element = (name, cls, value) => {
    const node = doc.createElement(name);
    if (cls) node.className = cls;
    if (value !== undefined && value !== null) node.textContent = String(value);
    return node;
  };
  const dialog = element('dialog', 'lot-lightbox');
  const dialogImage = element('img', 'lot-lightbox-img');
  dialogImage.alt = 'Увеличенное фото конкретного автомобиля';
  const close = element('button', 'lot-lightbox-close', 'Закрыть ×');
  close.type = 'button';
  close.addEventListener('click', () => dialog.close());
  dialog.append(close, dialogImage);
  doc.body.append(dialog);
  dialog.addEventListener('click', event => { if (event.target === dialog) dialog.close(); });
  const openPhoto = src => {
    if (typeof dialog.showModal !== 'function') return;
    dialogImage.src = src;
    dialog.showModal();
  };
  const datum = (parent, key, value) => {
    const cell = element('div', 'lot-datum');
    cell.append(element('small', null, key), element('strong', null, value));
    parent.append(cell);
  };
  const render = record => {
    const card = doc.getElementById(record.target);
    if (!card || !card.querySelector('.car-body')) return false;
    const box = element('section', 'real-example');
    box.setAttribute('aria-label', 'Проверенный пример автомобиля');
    const head = element('div', 'real-example-top');
    head.append(element('span', 'real-example-badge', record.kind === 'sold_auction' ? 'РЕАЛЬНЫЕ ТОРГИ · ЯПОНИЯ' : 'РЕАЛЬНОЕ ОБЪЯВЛЕНИЕ · КОРЕЯ'));
    head.append(element('span', 'real-example-id', record.kind === 'sold_auction' ? 'Лот № ' + record.lot : '№ ' + record.id));
    box.append(head);
    const title = element('h3', 'real-example-title', record.trim + ' · ' + record.year);
    box.append(title);
    const metrics = element('div', 'real-example-metrics');
    datum(metrics, 'Пробег', format(record.km) + ' км');
    datum(metrics, 'Объём', format(record.cc) + ' см³');
    if (record.hp) datum(metrics, 'Мощность', format(record.hp) + ' л. с.');
    if (record.kind === 'sold_auction') {
      datum(metrics, 'Оценка', record.grade || 'Не указана');
      datum(metrics, 'Дата торгов', record.date);
      datum(metrics, 'Аукцион', record.house);
    }
    box.append(metrics);
    if (record.kind === 'sold_auction' && record.price_yen) {
      box.append(element('div', 'real-example-price', 'Продан за ' + format(record.price_yen) + ' ¥'));
    }
    const availableMedia = Array.isArray(record.media) && record.media_verified_as_specific_lot ? record.media : [];
    if (availableMedia.length) {
      const gallery = element('div', 'real-example-gallery');
      let visible=0;
      availableMedia.slice(0, 3).forEach((src, i) => {
        if (!/^https:\/\/(?:jp2\.pa-server\.ru|imagebox\.autowini\.com)\//.test(src)) return;
        const btn = element('button', 'lot-media-button');
        btn.type = 'button';
        btn.setAttribute('aria-label', 'Увеличить изображение ' + (i + 1) + ' для ' + record.title);
        const img = element('img', null);
        img.loading = 'lazy';
        img.decoding = 'async';
        img.src = src;
        img.alt = 'Исходный материал № ' + (i + 1) + ' для ' + record.title + ' — ' + record.id;
        const caption = element('span', null, 'Кадр ' + (i + 1));
        btn.append(img, caption);
        img.addEventListener('error', () => { btn.remove(); if(!gallery.querySelector('button')) gallery.remove(); });
        btn.addEventListener('click', () => openPhoto(src));
        gallery.append(btn);
        visible++;
      });
      if (visible) box.append(gallery);
    }
    const proof = element('p', 'real-example-disclosure',
      record.kind === 'sold_auction'
        ? 'Подтверждённая продажа · фото исходного лота на стороннем фотосервере. Аукционный лист требует отдельной проверки и подтверждения.'
        : 'Проверенное описание конкретной машины. Это объявление, а не японский аукцион: оригинал отчёта о состоянии не получен.'
    );
    box.append(proof);
    if (record.note) box.append(element('p', 'real-example-note', record.note));
    const actions = element('div', 'real-example-actions');
    actions.append(element('span', null, record.kind === 'sold_auction' ? 'Результат завершённых торгов' : 'Наличие нужно уточнить'));
    box.append(actions);
    const btn = card.querySelector('.car-body > .btn');
    btn ? btn.before(box) : card.querySelector('.car-body').append(box);
    card.dataset.hasExample = 'true';
    return true;
  };
  fetch(dataPath, {cache:'no-store'})
    .then(r => { if (!r.ok) throw new Error('Данные временно недоступны'); return r.json(); })
    .then(data => {
      let shown=0;
      for (const record of (data.lots || [])) if (render(record)) shown++;
      const counter=doc.getElementById('real-example-count');
      if(counter) counter.textContent = shown + ' проверенных автомобилей';
    })
    .catch(() => {
      const counter=doc.getElementById('real-example-count');
      if(counter) counter.textContent = 'Подробности по реальным лотам временно недоступны';
    });
})();
