(() => {
  "use strict";
  // Public catalog is now local-only. No remote vehicle photos or seller links.
  const $ = id => document.getElementById(id);
  const grid = $("catalogGrid"), search = $("modelQuery"), country = $("countryFilter");
  const power = $("powerFilter"), count = $("catalogCount"), empty = $("catalogEmpty"), more = $("catalogMore");
  if (!grid || !search || !country || !power) return;
  const names = {japan:"ЯПОНИЯ", "south-korea":"ЮЖНАЯ КОРЕЯ", china:"КИТАЙ"};
  const rows = Object.entries(window.PAPAUTO_CATALOG || {}).flatMap(([market, data]) =>
    (Array.isArray(data) ? data : []).map(([make, model, engine]) => ({market, make, model, engine})));
  let limit = 120;
  function render() {
    const q = search.value.trim().toLowerCase();
    const matches = rows.filter(r => (!country.value || country.value === r.market)
      && (!q || (r.make+" "+r.model+" "+r.engine).toLowerCase().includes(q))
      && (!power.value || (power.value === "ev" ? /электро|electric|EV/i.test(r.engine) : !/электро|electric|EV/i.test(r.engine))));
    grid.replaceChildren();
    for (const r of matches.slice(0, limit)) {
      const card = document.createElement("article"); card.className = "model-card";
      const market = document.createElement("div"); market.className = "country"; market.textContent = names[r.market] || r.market;
      const title = document.createElement("h2"); title.textContent = r.make + " " + r.model;
      const engine = document.createElement("div"); engine.className = "engine"; engine.textContent = r.engine || "Двигатель уточняется";
      const link = document.createElement("a"); link.className = "model-request"; link.textContent = "Подобрать похожий автомобиль →";
      link.href = "/?view=select&similar=" + encodeURIComponent(r.make+" "+r.model) + "#assistant";
      card.append(market,title,engine,link); grid.append(card);
    }
    count.textContent = "Моделей в локальном справочнике: " + matches.length + ". Аукционные фотографии добавляются только с разрешением.";
    empty.style.display = matches.length ? "none" : "block";
    if (more) more.hidden = matches.length <= limit;
  }
  [search,country,power].forEach(control => control.addEventListener(control===search?"input":"change",() => {limit=120;render()}));
  if (more) more.addEventListener("click",() => {limit+=120;render()});
  render();
})();
