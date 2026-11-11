/* Safe runtime diagnostics for SurveyJS initialization: never read/store lead values. */
(() => {
  'use strict';
  let lastError = '';
  addEventListener('error', event => {
    const src = String(event.filename||'');
    const known = ['survey','vendor','vehicle-catalogue'].some(x=>src.includes(x));
    if (known) lastError = String(event.message||'JavaScript error').slice(0,180);
  });
  addEventListener('unhandledrejection', event => {
    const message = event.reason?.message;
    if (typeof message === 'string') lastError = message.slice(0,180);
  });
  addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
      const status = document.getElementById('surveyStatus');
      const root = document.getElementById('surveyContainer');
      if (!status || !root || !status.textContent.includes('Загружаем форму')) return;
      const state = {
        surveyCore: typeof window.Survey?.Model,
        renderMethod: typeof window.Survey?.Model?.prototype?.render,
        surveyUi: typeof window.SurveyUI,
        catalog: typeof window.PAPAUTO_CATALOG,
        formModule: document.querySelector('script[src*="survey-podbor.js"]')?.getAttribute('src')||'missing',
        error: lastError || 'no script error captured'
      };
      status.textContent = 'Не удалось запустить форму. Проверка загрузки: ' + JSON.stringify(state);
      status.style.color = '#ab2a3f';
    }, 8500);
  });
})();