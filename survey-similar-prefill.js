/* Parse auction-card links into PapAuto SurveyJS make/model/year/market selections.
   No external fetches or arbitrary HTML. Unknown trim never invents a catalogue model. */
(function (root) {
  'use strict';
  const markets={japan:'Япония','south-korea':'Корея',china:'Китай'};
  const norm = value => String(value || '').normalize('NFKC').toLocaleLowerCase('ru')
    .replace(/[\u00a0\u2000-\u200b]/g,' ').replace(/\s+/g,' ').trim();
  const prefix = (full,part) => full === part || full.startsWith(part + ' ') || full.startsWith(part+'-');
  function resolve(raw,catalogue) {
    if(typeof raw!=='string'||raw.length<3||raw.length>180)return null;
    let original=raw.trim();
    if(!original)return null;
    let market=null;
    const countryPattern=/\s*[·|–—]\s*(япония|корея|южная корея|китай)\s*$/i;
    const countryMatch=original.match(countryPattern);
    if(countryMatch){
      const country=norm(countryMatch[1]);
      market=country==='япония'?'japan':country==='китай'?'china':'south-korea';
      original=original.slice(0,countryMatch.index).trim();
    }
    const ym=original.match(/\s+(19\d{2}|20\d{2})\s*$/);
    let year=null;
    if(ym){year=ym[1];original=original.slice(0,ym.index).trim();}
    if(!original)return null;
    const lookup=norm(original);
    const input=typeof catalogue==='object'&&catalogue?catalogue:{};
    const order=market?[market]:['japan','south-korea','china'];
    let best=null,matchScore=-1;
    let bestMake=null;
    for(const region of order){
      for(const r of Array.isArray(input[region])?input[region]:[]){
        const make=String(r[0]||''),model=String(r[1]||'');
        if(!make||!model)continue;
        const mk=norm(make);
        if(!prefix(lookup,mk))continue;
        if(!bestMake||mk.length>bestMake.score)bestMake={market:region,make,score:mk.length};
        // Slash-separated market variants (Avante / Elantra) are one catalogue model.
        const names=[model,...model.split(/\s*\/\s*/)].filter(Boolean);
        for(const alias of names){
          const candidate=norm(make+' '+alias);
          if(prefix(lookup,candidate)&&candidate.length>matchScore){
            matchScore=candidate.length;best={market:region,make,model};
          }
        }
      }
    }
    const selection=best||bestMake;
    return {market:selection?.market||market||null,make:selection?.make||null,
      model:best?.model||null,year,reference:original,matched:!!best};
  }
  root.PapAutoSimilarPrefill={resolve};
})(typeof window!=='undefined'?window:globalThis);
