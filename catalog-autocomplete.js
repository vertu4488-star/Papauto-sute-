/* PAPAUTO: locally generated, touch-friendly model autocomplete. */
(() => {
  "use strict";
  const input = document.getElementById("modelQuery");
  const menu = document.getElementById("modelSuggestions");
  const wrapper = document.getElementById("modelSearchWrap");
  const country = document.getElementById("countryFilter");
  const make = document.getElementById("makeFilter");
  const power = document.getElementById("powerFilter");
  if (!input || !menu || !wrapper || !country || !make || !power) return;
  const marketNames = {japan:"Япония", "south-korea":"Южная Корея", china:"Китай"};
  const normalize = text => String(text || "").normalize("NFKC").toLocaleLowerCase("ru").trim();
  const raw = Object.entries(window.PAPAUTO_CATALOG || {}).flatMap(([market, list]) =>
    (Array.isArray(list) ? list : []).map(([brand, model, engine]) => ({market, brand, model, engine:engine || ""})));
  const used = new Set();
  const models = raw.filter(item => {
    const key = [item.market, normalize(item.brand), normalize(item.model)].join("|");
    if (used.has(key)) return false;
    used.add(key);
    return true;
  });
  let visible = [];
  let activeIndex = -1;

  const close = () => {
    menu.hidden = true;
    menu.replaceChildren();
    visible = [];
    activeIndex = -1;
    input.setAttribute("aria-expanded", "false");
    input.removeAttribute("aria-activedescendant");
  };

  const score = (item, query) => {
    const model = normalize(item.model);
    const full = normalize(item.brand + " " + item.model);
    const brand = normalize(item.brand);
    let value = model.startsWith(query) ? 0 : full.startsWith(query) ? 100 :
      brand.startsWith(query) ? 200 : model.includes(query) ? 300 : 400;
    if (item.market === country.value) value -= 25;
    if (item.brand === make.value) value -= 15;
    if (power.value && window.PapAutoMetadata &&
        window.PapAutoMetadata.modelTypes(item.market, item.brand, item.model, item.engine).includes(power.value)) value -= 5;
    return value;
  };

  const choose = index => {
    const item = visible[index];
    if (!item) return;
    // Selecting a model from another market adjusts the filters to show it.
    if (country.value !== item.market) {
      country.value = item.market;
      country.dispatchEvent(new Event("change", {bubbles:true}));
    }
    if (make.value !== item.brand) {
      make.value = item.brand;
      make.dispatchEvent(new Event("change", {bubbles:true}));
    }
    if (power.value && window.PapAutoMetadata &&
        !window.PapAutoMetadata.modelTypes(item.market, item.brand, item.model, item.engine).includes(power.value)) {
      power.value = "";
      power.dispatchEvent(new Event("change", {bubbles:true}));
    }
    input.value = item.brand + " " + item.model;
    input.dispatchEvent(new Event("input", {bubbles:true}));
    close();
    input.blur(); // Dismiss the iPhone keyboard after a tap.
  };

  const highlight = index => {
    activeIndex = index;
    Array.from(menu.children).forEach((node, i) => {
      node.setAttribute("aria-selected", i === index ? "true" : "false");
    });
    if (index >= 0) {
      input.setAttribute("aria-activedescendant", "model-suggestion-" + index);
      menu.children[index]?.scrollIntoView({block:"nearest"});
    } else input.removeAttribute("aria-activedescendant");
  };

  const show = () => {
    const query = normalize(input.value);
    if (!query) return close();
    visible = models.filter(item =>
      normalize(item.brand + " " + item.model + " " + item.engine).includes(query) ||
      normalize(item.model).includes(query)
    ).sort((a,b) => score(a,query) - score(b,query) ||
      a.brand.localeCompare(b.brand,"ru") || a.model.localeCompare(b.model,"ru")).slice(0,8);
    if (!visible.length) return close();
    activeIndex = -1;
    const fragment = document.createDocumentFragment();
    visible.forEach((item, index) => {
      const option = document.createElement("button");
      option.type = "button";
      option.id = "model-suggestion-" + index;
      option.className = "catalog-suggestion";
      option.setAttribute("role", "option");
      option.setAttribute("aria-selected", "false");
      const title = document.createElement("strong");
      title.textContent = item.brand + " " + item.model;
      const subtitle = document.createElement("small");
      subtitle.textContent = marketNames[item.market] || item.market;
      option.append(title, subtitle);
      option.addEventListener("click", () => choose(index));
      fragment.appendChild(option);
    });
    menu.replaceChildren(fragment);
    menu.hidden = false;
    input.setAttribute("aria-expanded", "true");
    input.removeAttribute("aria-activedescendant");
  };

  input.setAttribute("role", "combobox");
  input.setAttribute("aria-autocomplete", "list");
  input.setAttribute("aria-controls", "modelSuggestions");
  input.setAttribute("aria-expanded", "false");
  input.setAttribute("autocomplete", "off");
  input.setAttribute("autocapitalize", "off");
  input.setAttribute("spellcheck", "false");
  input.addEventListener("input", show);
  input.addEventListener("focus", show);
  input.addEventListener("keydown", event => {
    if (menu.hidden || !visible.length) return;
    if (event.key === "ArrowDown" || event.key === "ArrowUp") {
      event.preventDefault();
      highlight((activeIndex + (event.key === "ArrowDown" ? 1 : visible.length-1)) % visible.length);
    } else if (event.key === "Enter" && activeIndex >= 0) {
      event.preventDefault();
      choose(activeIndex);
    } else if (event.key === "Escape") {
      event.preventDefault();
      close();
    }
  });
  document.addEventListener("pointerdown", event => {
    if (!wrapper.contains(event.target)) close();
  });
  [country, make, power].forEach(el => el.addEventListener("change", () => {
    if (!menu.hidden) show();
  }));
})();
