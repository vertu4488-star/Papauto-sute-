(() => {
  'use strict';
  const form = document.getElementById('quickSelection');
  if (form) form.addEventListener('submit', event => {
    event.preventDefault();
    const data = new FormData(form);
    for (const [id, key] of [['country','market'],['budget','budget'],['city','city']]) {
      const field = document.getElementById(id);
      if (field) { field.value = data.get(key); field.dispatchEvent(new Event('input', {bubbles:true})); }
    }
    const prompt = document.getElementById('carPrompt');
    const purpose = 'Задача: ' + data.get('purpose') + '. Нужны варианты с проверкой состояния и расчётом до города получения.';
    if (prompt) { prompt.value = prompt.value ? prompt.value + '\n' + purpose : purpose; prompt.dispatchEvent(new Event('input', {bubbles:true})); }
    const link = document.createElement('a'); link.href = '#assistant'; document.body.append(link); link.click(); link.remove();
    document.getElementById('country')?.focus({preventScroll:true});
  });
  const checklist = document.getElementById('buyerChecklist');
  if (!checklist) return;
  const key = 'papauto_buyer_checklist_v1';
  const fields = [...checklist.querySelectorAll('input[type=checkbox]')];
  const status = document.getElementById('checklistStatus');
  let storageAvailable = true;
  try {
    const saved = JSON.parse(localStorage.getItem(key) || '[]');
    if (Array.isArray(saved)) fields.forEach(input => { input.checked = saved.includes(input.value); });
  } catch { storageAvailable = false; }
  function update(save) {
    if (save) try { localStorage.setItem(key, JSON.stringify(fields.filter(x => x.checked).map(x => x.value))); }
    catch { storageAvailable = false; }
    status.textContent = 'Отмечено ' + fields.filter(x => x.checked).length + ' из ' + fields.length + (storageAvailable ? '. Сохранено в этом браузере.' : '. Сохранение недоступно — распечатайте список.');
  }
  checklist.addEventListener('change', () => update(true));
  document.getElementById('resetChecklist').addEventListener('click', () => { fields.forEach(x => { x.checked = false; }); update(true); });
  document.getElementById('printChecklist').addEventListener('click', () => window.print());
  update(false);
})();
