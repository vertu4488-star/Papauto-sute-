/* PapAuto iPhone-friendly contact entry.
   Phone input normally opens the native tel keypad. When iOS WebKit or an external
   keyboard suppresses it, the user can type with these accessible on-page buttons.
   No data is sent here; the existing lead form handles submission. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const input = $('pickerContact');
  const toggle = $('pickerOpenKeypad');
  const keypad = $('pickerKeypad');
  const done = $('pickerKeypadDone');
  const leadForm = $('pickerLeadForm');
  if (!input || !toggle || !keypad || !leadForm) return;

  let mode = 'phone';
  const values = {phone:'', telegram:''};
  const modeButtons = [...document.querySelectorAll('[data-contact-mode]')];
  const write = value => {
    input.value = value;
    values[mode] = value;
    input.dispatchEvent(new Event('input', {bubbles:true}));
  };
  const openKeypad = visible => {
    const active = Boolean(visible && mode === 'phone');
    keypad.hidden = !active;
    toggle.setAttribute('aria-expanded', String(active));
    toggle.textContent = active
      ? 'Скрыть кнопки ввода номера'
      : 'Не появилась клавиатура? Ввести номер кнопками';
    if(active) keypad.scrollIntoView({behavior:'smooth', block:'nearest'});
  };
  const setMode = next => {
    if (!['phone','telegram'].includes(next)) return;
    values[mode] = input.value;
    mode = next;
    const phone = next === 'phone';
    input.type = phone ? 'tel' : 'text';
    input.setAttribute('inputmode', phone ? 'tel' : 'text');
    input.setAttribute('autocomplete','off');
    input.setAttribute('autocorrect','off');
    input.setAttribute('spellcheck','false');
    input.placeholder = phone ? '+7 9XX XXX-XX-XX' : '@telegram_username';
    input.value = values[next];
    const label = document.querySelector('label[for="pickerContact"]');
    if(label && label.firstChild) label.firstChild.textContent = phone ? 'Телефон для ответа ' : 'Ваш Telegram ';
    modeButtons.forEach(button => {
      const selected = button.dataset.contactMode === next;
      button.classList.toggle('is-selected',selected);
      button.setAttribute('aria-pressed',String(selected));
    });
    toggle.hidden = !phone;
    openKeypad(false);
  };
  modeButtons.forEach(button => button.addEventListener('click',()=>setMode(button.dataset.contactMode)));
  input.addEventListener('input',()=>{values[mode]=input.value});
  toggle.addEventListener('click',()=>{
    const opening=keypad.hidden;
    if(opening && !input.value.trim()) write('+7 ');
    openKeypad(opening);
  });
  keypad.addEventListener('click', event => {
    const button = event.target.closest('button[data-phone-key]');
    if (!button || mode !== 'phone') return;
    const key = button.dataset.phoneKey;
    if (key === 'clear') write('');
    else if (key === 'backspace') write(input.value.slice(0,-1));
    else if (/^[0-9]$/.test(key)) {
      if (input.value.length >= 120) return;
      write(input.value+key);
    }
  });
  done?.addEventListener('click',()=>openKeypad(false));
  // Validate before the shared async submission handler, without generating
  // duplicate leads or modifying its delivery status.
  leadForm.addEventListener('submit',event=>{
    if(mode !== 'phone') return;
    const digits=input.value.replace(/\D/g,'');
    if(digits.length >= 10 && digits.length <= 15) return;
    event.preventDefault();
    event.stopImmediatePropagation();
    const status=$('pickerLeadStatus');
    if(status) status.textContent = 'Введите полный номер телефона (10–15 цифр) или выберите Telegram.';
    if(keypad.hidden) openKeypad(true);
  },true);
})();
