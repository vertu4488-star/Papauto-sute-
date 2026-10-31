(() => {
  const groups = {
    home: ['.hero', '.mobile-dashboard', '.proof-strip', '.marketplace-intro', '.budget-start'],
    catalog: ['#catalog', '#showcase', '#popular-models'],
    directions: ['#directions', '#route-planner', '#regional-delivery'],
    auctions: ['#seo-guides', '#auction-statistics', '#market-sources'],
    calculator: ['#calculator', '#currency-converter', '#logisticsBenchmarks'],
    select: ['#smart-search', '#assistant', '#account', '.account-data-section'],
    about: ['#process', '#checklist', '#auto-import-russia', '#faq', '#request']
  };
  const all = Object.values(groups).flat();
  const knownIds = new Map();
  Object.entries(groups).forEach(([view, selectors]) => selectors.forEach(selector => {
    if (selector.startsWith('#')) knownIds.set(selector.slice(1), view);
  }));
  const valid = new Set(Object.keys(groups));
  const getViewFromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    return knownIds.get(id) || null;
  };
  function apply(view, updateUrl = false) {
    if (!valid.has(view)) view = 'home';
    const nodes = new Set();
    all.forEach(selector => document.querySelectorAll(selector).forEach(node => nodes.add(node)));
    nodes.forEach(node => {
      node.hidden = true;
      node.setAttribute('aria-hidden', 'true');
    });
    groups[view].forEach(selector => document.querySelectorAll(selector).forEach(node => {
      node.hidden = false;
      node.removeAttribute('aria-hidden');
    }));
    document.querySelectorAll('[data-site-tab]').forEach(link => {
      const active = link.dataset.siteTab === view;
      link.classList.toggle('is-active', active);
      if (active) link.setAttribute('aria-current', 'page');
      else link.removeAttribute('aria-current');
    });
    document.body.dataset.siteView = view;
    if (updateUrl) {
      const url = new URL(location.href);
      url.searchParams.set('view', view);
      url.hash = '';
      history.pushState({siteView:view}, '', url);
    }
    const menu = document.querySelector('.main-nav');
    const toggle = document.querySelector('.menu-toggle');
    if (menu) menu.classList.remove('open');
    if (toggle) toggle.setAttribute('aria-expanded', 'false');
    window.scrollTo({top:0, behavior:'instant'});
  }
  const params = new URLSearchParams(location.search);
  const initial = valid.has(params.get('view')) ? params.get('view') : (getViewFromHash() || 'home');
  apply(initial);
  if (location.hash && getViewFromHash() === initial) {
    requestAnimationFrame(() => {
      const target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
      if (target) target.scrollIntoView({behavior:'instant', block:'start'});
    });
  }
  document.addEventListener('click', event => {
    const budgetShortcut = event.target.closest('[data-budget-shortcut]');
    if (budgetShortcut) {
      apply('select', true);
      requestAnimationFrame(() => document.getElementById('assistant')?.scrollIntoView({behavior:'smooth', block:'start'}));
      return;
    }
    const marketShortcut = event.target.closest('[data-market-shortcut]');
    if (marketShortcut) {
      apply('catalog', true);
      requestAnimationFrame(() => document.getElementById('catalog')?.scrollIntoView({behavior:'smooth', block:'start'}));
      return;
    }
    const tab = event.target.closest('[data-site-tab]');
    if (tab) {
      event.preventDefault();
      apply(tab.dataset.siteTab, true);
      return;
    }
    const anchor = event.target.closest('a[href^="#"]');
    if (!anchor) return;
    const id = decodeURIComponent(anchor.getAttribute('href').slice(1));
    const view = knownIds.get(id);
    if (view && view !== document.body.dataset.siteView) {
      event.preventDefault();
      apply(view, true);
      requestAnimationFrame(() => {
        const target = document.getElementById(id);
        if (target) target.scrollIntoView({behavior:'smooth', block:'start'});
      });
    }
  });
  window.addEventListener('popstate', () => {
    const p = new URLSearchParams(location.search);
    apply(valid.has(p.get('view')) ? p.get('view') : (getViewFromHash() || 'home'));
  });
  window.addEventListener('hashchange', () => {
    const view = getViewFromHash();
    if (view && view !== document.body.dataset.siteView) apply(view);
  });
})();