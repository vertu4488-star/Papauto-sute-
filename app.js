(() => {
  const $ = (id) => document.getElementById(id);
  const money = (value) => new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 }).format(value) + ' ₽';
  const menu = document.querySelector('.menu-toggle');
  const nav = document.querySelector('.main-nav');
  if (menu && nav) {
    menu.addEventListener('click', () => {
      const open = nav.classList.toggle('open');
      menu.setAttribute('aria-expanded', String(open));
      menu.textContent = open ? '✕' : '☰';
    });
    nav.querySelectorAll('a').forEach((a) => a.addEventListener('click', () => {
      nav.classList.remove('open'); menu.setAttribute('aria-expanded', 'false'); menu.textContent = '☰';
    }));
  }
  if ($('year')) $('year').textContent = new Date().getFullYear();

  // Official links are configured in site-config.js once the accounts exist.
  const config = window.PAPAUTO_CONFIG || {};
  const integrations = [
    ['telegramChannelUrl', 'Telegram-канал'],
    ['vkUrl', 'ВКонтакте'],
    ['instagramUrl', 'Instagram'],
    ['youtubeUrl', 'YouTube']
  ];
  const safeUrl = (value) => {
    try {
      const url = new URL(value);
      return url.protocol === 'https:' ? url.href : '';
    } catch { return ''; }
  };
  document.querySelectorAll('[data-integration]').forEach((link) => {
    const url = safeUrl(config[link.dataset.integration] || '');
    if (url) { link.href = url; link.hidden = false; link.target = '_blank'; link.rel = 'noopener noreferrer'; }
  });
  document.querySelectorAll('[data-social-links]').forEach((container) => {
    integrations.forEach(([key, label]) => {
      const url = safeUrl(config[key] || '');
      if (!url) return;
      const a = document.createElement('a');
      a.href = url; a.textContent = label; a.target = '_blank'; a.rel = 'noopener noreferrer';
      container.appendChild(a);
    });
    if (!container.children.length) {
      const note = document.createElement('span');
      note.className = 'social-pending';
      note.textContent = 'Ссылки добавим после подключения официальных аккаунтов';
      container.appendChild(note);
    }
  });
  const socialUrls = integrations.map(([key]) => safeUrl(config[key] || '')).filter(Boolean);
  const botUrl = safeUrl(config.telegramBotUrl || '');
  if (botUrl) socialUrls.push(botUrl);
  const orgSchema = {
    '@context': 'https://schema.org', '@type': 'AutoDealer', name: 'PAPAUTO',
    url: 'https://papauto.ru/',
    description: 'Подбор и организация доставки автомобилей из Китая, Южной Кореи и Японии в Новосибирск.',
    areaServed: { '@type': 'City', name: 'Новосибирск' }
  };
  if (socialUrls.length) orgSchema.sameAs = [...new Set(socialUrls)];
  const schemaScript = document.createElement('script');
  schemaScript.type = 'application/ld+json'; schemaScript.textContent = JSON.stringify(orgSchema);
  document.head.appendChild(schemaScript);

  const calcForm = $('calcForm');
  const fields = [
    ['carCost', 'Цена автомобиля'],
    ['shipping', 'Доставка до России'],
    ['customs', 'Таможня и сборы'],
    ['paperwork', 'Оформление'],
    ['localDelivery', 'Доставка до Новосибирска'],
    ['fee', 'Услуги компании'],
    ['otherCosts', 'Другие расходы']
  ];
  let lastEstimate = '';
  if (calcForm) {
    calcForm.addEventListener('submit', (event) => {
      event.preventDefault();
      const values = fields.map(([id, label]) => ({ label, value: Math.max(0, Number($(id).value) || 0), entered: $(id).value.trim() !== '' }));
      const included = values.filter((v) => v.entered);
      const total = included.reduce((sum, item) => sum + item.value, 0);
      $('resultTotal').textContent = included.length ? money(total) : '— ₽';
      $('resultLines').innerHTML = included.length
        ? included.map((item) => `<div><span>${item.label}</span><b>${money(item.value)}</b></div>`).join('')
        : '<div><span>Добавьте известные суммы</span><b>—</b></div>';
      const missing = values.filter((v) => !v.entered).map((v) => v.label.toLowerCase());
      $('resultNote').textContent = included.length
        ? `Направление: ${$('calcCountry').value}. Учтено ${included.length} из ${fields.length} статей.${missing.length ? ' Не заполнены: ' + missing.join(', ') + '.' : ''} Это предварительная сумма, а не гарантированная цена под ключ.`
        : 'Заполните хотя бы одну известную сумму. Неизвестные статьи не учитываются.';
      lastEstimate = `PAPAUTO — предварительная смета\nНаправление: ${$('calcCountry').value}\n${included.map((item) => `${item.label}: ${money(item.value)}`).join('\n')}\nСумма заполненных расходов: ${included.length ? money(total) : 'не рассчитана'}\nНе заполнены: ${missing.length ? missing.join(', ') : 'нет'}\nВажно: предварительный расчёт; таможенные платежи и условия оформления нужно подтвердить для конкретного автомобиля.`;
    });
  }
  const copyEstimate = $('copyEstimate');
  if (copyEstimate) copyEstimate.addEventListener('click', async () => {
    if (!lastEstimate) {
      $('resultNote').textContent = 'Сначала нажмите «Рассчитать смету».';
      return;
    }
    try {
      await navigator.clipboard.writeText(lastEstimate);
      copyEstimate.textContent = 'Смета скопирована ✓';
      setTimeout(() => copyEstimate.textContent = 'Скопировать смету', 1800);
    } catch {
      $('resultNote').textContent = lastEstimate;
    }
  });

  const assistantForm = $('assistantForm');
  if (assistantForm) assistantForm.addEventListener('submit', (event) => {
    event.preventDefault();
    const description = $('carPrompt').value.trim();
    if (!description) return;
    const budget = $('budget').value.trim();
    const city = $('city').value.trim() || 'не указан';
    const contact = $('contact').value.trim() || 'не указан';
    const request = [
      'Заявка на подбор автомобиля — PAPAUTO',
      `Запрос: ${description}`,
      `Бюджет: ${budget ? money(Number(budget)) : 'не указан'}`,
      `Город получения: ${city}`,
      `Контакт: ${contact}`,
      '',
      'Просьба уточнить доступные варианты, возможность оформления и предварительную смету.'
    ].join('\n');
    $('requestText').value = request;
    $('requestOutput').hidden = false;
    $('copyStatus').textContent = '';
  });
  const copyRequest = $('copyRequest');
  if (copyRequest) copyRequest.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText($('requestText').value);
      $('copyStatus').textContent = 'Скопировано.';
    } catch {
      $('requestText').focus(); $('requestText').select();
      $('copyStatus').textContent = 'Выделите текст и скопируйте вручную.';
    }
  });
})();
