/* PAPAUTO — локальная история смет. Данные остаются только в этом браузере. */
(() => {
  "use strict";
  const KEY = "papauto_estimate_history_v1";
  const fields = ["carCost","auctionFee","originDelivery","exportDocs","insurance","shipping","customs","paperwork","localDelivery","fee","otherCosts","marketReferencePrice"];
  const $ = id => document.getElementById(id);
  const form = $("calcForm");
  const panel = document.querySelector(".calc-result");
  if (!form || !panel) return;

  const read = () => {
    const values = {};
    fields.forEach(id => { const el=$(id); if(el) values[id]=el.value; });
    return {
      id: (crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + Math.random().toString(16).slice(2)),
      createdAt: new Date().toISOString(),
      country: $("calcCountry")?.value || "",
      values,
      total: $("resultTotal")?.textContent || "— ₽",
      lines: Array.from(document.querySelectorAll("#resultLines > div")).map(row => {
        const cells=row.querySelectorAll("span,b");
        return cells.length===2 ? [cells[0].textContent,cells[1].textContent] : null;
      }).filter(Boolean),
      note: $("resultNote")?.textContent || "",
      comparison: $("marketComparison")?.textContent || ""
    };
  };
  const load = () => {
    try { const data=JSON.parse(localStorage.getItem(KEY)||"[]"); return Array.isArray(data)?data:[]; }
    catch { return []; }
  };
  const save = data => { try { localStorage.setItem(KEY,JSON.stringify(data.slice(0,20))); return true; } catch { return false; } };

  const history = document.createElement("section");
  history.className="estimate-history";
  history.innerHTML='<div class="estimate-history-head"><div><h3>История смет</h3><p>До 20 последних расчётов на этом устройстве. Не отправляется на сервер.</p></div><button type="button" class="button button-secondary" data-history-export>Экспорт JSON</button></div><div class="estimate-history-list" aria-live="polite"></div>';
  panel.append(history);
  const list=history.querySelector(".estimate-history-list");

  const render = () => {
    const items=load();
    list.replaceChildren();
    if(!items.length){const empty=document.createElement("p");empty.className="estimate-history-empty";empty.textContent="Сохранённых расчётов пока нет. Нажмите «Рассчитать смету».";list.append(empty);return;}
    items.forEach(item=>{
      const card=document.createElement("article");card.className="estimate-history-item";
      const info=document.createElement("div");
      const title=document.createElement("strong");title.textContent=item.country+" · "+(item.total||"—");
      const date=document.createElement("small");date.textContent=new Date(item.createdAt).toLocaleString("ru-RU");
      info.append(title,date);
      const actions=document.createElement("div");actions.className="estimate-history-actions";
      const restore=document.createElement("button");restore.type="button";restore.textContent="Открыть";restore.addEventListener("click",()=>{
        if($("calcCountry"))$("calcCountry").value=item.country;
        fields.forEach(id=>{const el=$(id);if(el&&item.values&&Object.hasOwn(item.values,id))el.value=item.values[id]??"";});
        form.dispatchEvent(new Event("submit",{bubbles:true,cancelable:true}));
        $("calculator")?.scrollIntoView({behavior:"smooth",block:"start"});
      });
      const remove=document.createElement("button");remove.type="button";remove.textContent="Удалить";remove.addEventListener("click",()=>{save(load().filter(x=>x.id!==item.id));render();});
      actions.append(restore,remove);card.append(info,actions);list.append(card);
    });
  };
  form.addEventListener("submit",()=>{
    const result=read();
    if(!result.lines.length)return;
    const items=load().filter(x=>x.total!==result.total || x.country!==result.country || JSON.stringify(x.values)!==JSON.stringify(result.values));
    items.unshift(result);
    if(!save(items)) {
      const note=document.createElement("p");note.className="estimate-history-warning";note.textContent="Браузер запретил локальное сохранение. Скачайте CSV или распечатайте смету.";history.prepend(note);
    }
    render();
  });
  history.querySelector("[data-history-export]").addEventListener("click",()=>{
    const blob=new Blob([JSON.stringify(load(),null,2)],{type:"application/json;charset=utf-8"});
    const url=URL.createObjectURL(blob),a=document.createElement("a");
    a.href=url;a.download="papauto-estimate-history-"+new Date().toISOString().slice(0,10)+".json";
    document.body.append(a);a.click();a.remove();URL.revokeObjectURL(url);
  });
  render();
})();