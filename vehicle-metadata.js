/* Explicit metadata only: an engine displacement does not establish fuel or documents. */
(()=>{"use strict";
const labels={petrol:"Бензин",diesel:"Дизель",hybrid:"Гибрид",ev:"Электромобиль",unknown:"Тип уточняется"};
function fuelTypes(value){
 const s=String(value||"").toLowerCase();const types=[];
 for(const part of s.split(/\s*[/;]\s*|\s+(?:и|или)\s+/)){
  const hybrid=/гибрид|hybrid|phev|\bhev\b|e-power|e:hev|dm-i|range extender/.test(part);
  if(hybrid)types.push("hybrid");
  if(!hybrid&&/бензин|petrol|gasoline/.test(part))types.push("petrol");
  if(!hybrid&&/дизел|diesel/.test(part))types.push("diesel");
  if(!hybrid&&/электр|electric|\bev\b|\bbev\b/.test(part))types.push("ev");
 }
 return types.length?[...new Set(types)]:["unknown"];
}
const variants={"japan|Toyota|Aqua": ["hybrid"], "japan|Toyota|Prius": ["hybrid"], "japan|Honda|Fit": ["petrol", "hybrid"], "japan|Honda|Vezel": ["petrol", "hybrid"], "south-korea|Kia|Carnival": ["diesel", "hybrid"], "china|BYD|Song Plus": ["hybrid", "ev"], "japan|Mazda|CX-5": ["petrol", "diesel", "hybrid"]};
function modelTypes(market,brand,model,engine){return variants[[market,brand,model].join("|")]||fuelTypes(engine);}
function fuelLabel(types){return types.map(t=>labels[t]||labels.unknown).join(" / ");}
function documents(row){
 const status=row&&row.document_status;
 const known={not_checked:"Документы не проверены",checking:"Документы на проверке",missing:"Документы отсутствуют",awaiting:"Ожидаем документы",epts_pending:"ЭПТС оформляется",epts_issued:"ЭПТС оформлен",pts_available:"ПТС в наличии"};
 // Positive claims require a dated, traceable verification record.
 if(["epts_issued","pts_available"].includes(status)&&!(row.document_source&&/^\d{4}-\d{2}-\d{2}$/.test(row.documents_checked_at||"")))return known.not_checked;
 return Object.prototype.hasOwnProperty.call(known,status)?known[status]:known.not_checked;
}
globalThis.PapAutoMetadata={fuelTypes,modelTypes,fuelLabel,documents,labels};
})();
