"""Frozen visually reviewed nine ATP auction references, separate from 666-lot gallery."""
import hashlib,json,re,shutil,sys
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1]
ASSETS="assets/seo-reference/atp-japan9-20261126"
MANIFEST="research/atp-japan13-frozen-manifest-20261126.json"
DIGEST="857fb42c8b651403ad44a11e0bcd459caf790a4c20d734e4b82d714d2962630d"
MEDIA_DIGEST="6b93251c7a443cc64ea8eaae56c838aabde2823afcac9f08ccebdc0a5a3b11b5"
MODELS={"1":"japan-toyota-vitz","2":"japan-toyota-noah","3":"japan-toyota-voxy","7":"japan-nissan-nv200","8":"japan-suzuki-jimny","10":"japan-suzuki-solio","11":"japan-suzuki-hustler","12":"japan-mazda-mazda3","13":"japan-mazda-cx-3"}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(root):
    path=root/MANIFEST
    if digest(path)!=DIGEST:raise RuntimeError("ATP9 frozen source manifest mismatch")
    rows=[r for r in json.loads(path.read_text(encoding="utf-8")) if str(r["number"]) in MODELS]
    if len(rows)!=9:raise RuntimeError("ATP9 expected nine reviewed records")
    if any([m["kind"] for m in r["media"]]!=["vehicle","vehicle","sheet"] for r in rows):raise RuntimeError("ATP9 incomplete reviewed record")
    return rows
def path_for(root,r,m):return root/ASSETS/MODELS[str(r["number"])]/m["file"]
def verify(root,target=None):
    target=target or root
    paths=set();lines=[]
    for r in load(root):
        for m in r["media"]:
            p=path_for(target,r,m)
            if not p.is_file() or p.is_symlink() or p.read_bytes()[:3]!=b"\xff\xd8\xff" or digest(p)!=m["sha256"]:raise RuntimeError("ATP9 invalid frozen media "+str(p))
            paths.add(p);lines.append(m["file"]+" "+digest(p))
    if len(paths)!=27 or paths!=set((target/ASSETS).rglob("*.jpg")) or hashlib.sha256(("\n".join(sorted(lines))+"\n").encode()).hexdigest()!=MEDIA_DIGEST:raise RuntimeError("ATP9 media set mismatch")
def install(src):
    src=Path(src)
    if digest(src/"manifest.json")!=DIGEST:raise RuntimeError("ATP9 original artifact mismatch")
    shutil.copyfile(src/"manifest.json",ROOT/MANIFEST)
    for r in load(ROOT):
        for m in r["media"]:
            p=path_for(ROOT,r,m);p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src/m["file"],p)
    verify(ROOT)
def render(root,target,coverage,registry):
    verify(root);verify(root,target)
    report={r["model_id"]:r for r in coverage["models"]}
    norm=lambda x:re.sub(r"\s+","",str(x or "").casefold())
    existing={(norm(r.get("auction")),str(r.get("auction_date")),str(r.get("lot_number"))):r for r in registry["lots"]}
    count=0;skips=[]
    for r in load(root):
        ident=MODELS[str(r["number"])]
        page=target/"models"/(ident+".html")
        html=page.read_text(encoding="utf-8")
        key=(norm(r["auction"]),str(r["auction_date"]),str(r["lot"]))
        old=existing.get(key)
        if old:
            # The exact lot may already be listed among the additional archive
            # links beyond the ten inline cards. Reuse rather than duplicate it.
            if ('data-model-lot-id="'+old["id"]+'"' in html or
                    'href="/lots/'+old["id"]+'.html"' in html):
                skips.append(ident);continue
            raise RuntimeError("ATP9 lot already published but not linked "+ident+" "+old["id"])
        title=escape(r["model"]+" · "+str(r["year"]))
        media="".join('<a href="/'+escape(path_for(target,r,m).relative_to(target).as_posix(),quote=True)+'"><img loading="lazy" decoding="async" src="/'+escape(path_for(target,r,m).relative_to(target).as_posix(),quote=True)+'" alt="'+title+(' — полный аукционный лист' if m["kind"]=="sheet" else ' — фото аукциона')+'"></a>' for m in r["media"])
        facts=[("Пробег по данным источника",r["mileage"]),("Объём двигателя",r["engine"].replace(" cм"," см³")),("Аукцион",r["auction"]),("Дата торгов",r["auction_date"]),("Номер лота",r["lot"]),("Оценка",r["grade"]),("Цена продажи по данным ATP",r["source_price"])]
        label="Архивный пример. Автомобиль не в наличии PapAuto. Цена торгов не включает ввоз и доставку."
        if r["number"] in (2,3,10,11):label+=" Данная версия может подпадать под экспортные ограничения. Не предложение прямой поставки."
        card='<article class="pa-model-lot pa-model-atp-reference" data-model-reference-id="atp-japan9-'+str(r["number"])+'"><div class="pa-atp-media">'+media+'</div><div class="pa-model-lot-body"><h3>'+title+'</h3><dl>'+''.join('<div><dt>'+escape(k)+'</dt><dd>'+escape(v)+'</dd></div>' for k,v in facts)+'</dl><p>'+escape(label)+'</p><p>Источник фотографий, листа и данных: АТП.Авто, архив на 26.11.2026.</p></div></article>'
        old_empty='<p>В опубликованной базе пока нет подходящего аукционного примера этой модели из выбранной страны с оригинальным фото и полным аукционным листом. Не подставляем фото другой модели или страны.</p>'
        if old_empty in html:html=html.replace(old_empty,'<p>Ниже — проверенный архивный пример конкретной модели.</p>',1)
        html,n=re.subn(r'(<section id="pa-model-statistics"[^>]*>[\s\S]*?)(</section>)',lambda m:m.group(1)+'<h3>Дополнительный аукционный пример</h3><div class="pa-model-lot-grid">'+card+'</div>'+m.group(2),html,count=1)
        if n!=1:raise RuntimeError("ATP9 missing stats section "+ident)
        html=html.replace("</head>",'<style>.pa-atp-media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:7px}.pa-atp-media img{width:100%;height:auto;max-height:300px;object-fit:contain}</style></head>',1)
        page.write_text(html,encoding="utf-8")
        report[ident]["reference_cards"]=report[ident].get("reference_cards",0)+1;count+=1
    coverage["japan9_reference_cards"]=count
    coverage["japan9_existing_lots"]=skips
    coverage["photo_pages"]=sum(any(r.get(k,0) for k in ("auction_matches","supplier_matches","related_cards","reference_cards")) for r in report.values())
    coverage["no_photo_pages"]=len(report)-coverage["photo_pages"]
    (target/"data/model-statistics-coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PAPAUTO_ATP_JAPAN9_OK "+json.dumps({"new_reference_cards":count,"existing_lots_reused":skips,"model_pages":len(report),"photo_pages":coverage["photo_pages"],"gallery_unchanged":True}))
if __name__=="__main__":install(sys.argv[1])
