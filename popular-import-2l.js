(()=>{
  "use strict";
  const grid=document.getElementById("carGrid"),
    buttons=[...document.querySelectorAll("[data-country]")],
    search=document.getElementById("modelFilter"),
    top=document.getElementById("topOnly"),
    count=document.getElementById("resultCount"),
    empty=document.getElementById("noResults");
  if(!grid||!search||!top||!count||!empty)return;

  // Only complete owner-approved auction photo + inspection-sheet cards exist
  // in the HTML. Never render a model with missing source evidence.
  const cards=[...grid.querySelectorAll(".car-card")];
  let selected="all";
  function render(){
    const needle=search.value.normalize("NFKC").toLocaleLowerCase("ru").trim();
    let shown=0;
    for(const card of cards){
      const ok=(selected==="all"||card.dataset.market===selected) &&
        (!top.checked||card.dataset.tier==="A") &&
        (!needle||card.dataset.name.includes(needle));
      card.hidden=!ok;
      if(ok)shown++;
    }
    count.textContent="Показано "+shown+" из "+cards.length+
      " проверенных аукционных автомобилей с фотографией, листом и описанием";
    empty.hidden=shown>0;
    for(const button of buttons){
      const active=button.dataset.country===selected;
      button.classList.toggle("active",active);
      button.setAttribute("aria-pressed",String(active));
    }
  }

  for(const card of [...cards]){
    const original=card.querySelector(".verified-auction-photo img");
    const sheet=card.querySelector(".verified-auction-document img");
    const description=card.querySelector(".verified-lot-description");
    if(!original||!sheet||!description?.textContent?.trim()){
      card.remove();
      const index=cards.indexOf(card);if(index>=0)cards.splice(index,1);
      continue;
    }
    for(const image of [original,sheet]){
      image.addEventListener("error",()=>{
        card.remove();
        const index=cards.indexOf(card);if(index>=0)cards.splice(index,1);
        render();
      },{once:true});
    }
  }
  for(const button of buttons){
    button.addEventListener("click",()=>{selected=button.dataset.country;render();});
  }
  search.addEventListener("input",render);
  top.addEventListener("change",render);
  render();
})();
