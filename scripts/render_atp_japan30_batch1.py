"""Render exactly owner-reviewed ATP Japan batch 1; never alter gallery inventory."""
import hashlib,json,re,shutil,sys
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1]
ASSETS="assets/seo-reference/atp-japan30-batch1-20261126"
RECEIPT="research/owner-approved-atp-japan30-batch1-20261126.json"
PDF_SHA="14aa4de9c311d2dc6078e4c18604ca6df749a47aba9b64ba5ac3846b8cc19e34"
SOURCE_SHA="5017b3aa22014137d6ba6eb5ee5bc13f63a5a4f12158bc67f51ae283fd6035c3"
SELECTED_SHA="420316655dc935db404e5b09403fa9472443ea378e246a16819c13dd2fc96f19"
INDICES=[1,5,67,24,43,54,41,66,2,58,3,6,60,11,69,12,55,13,56,14,28,16,19,7,33,8,18,4,59,70]
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def norm(x):return re.sub(r"[^a-z0-9]","",str(x or "").casefold())
def key(a,d,l):return (norm(a),str(d or "")[:10],str(l or "").lstrip("0"))
def ident(r):return "japan-"+re.sub(r"[^a-z0-9]+","-",r["model"].lower()).strip("-")
def frozen_bytes(rows):return json.dumps(rows,ensure_ascii=False,indent=2).encode()
def load(root):
    data=json.loads((root/RECEIPT).read_text(encoding="utf-8"))
    rows=data["lots"]
    if data["reviewed_pdf_sha256"]!=PDF_SHA or data["rights_confirmed"] is not False or hashlib.sha256(frozen_bytes(rows)).hexdigest()!=SELECTED_SHA or [r["index"] for r in rows]!=INDICES:raise RuntimeError("ATP30 frozen review mismatch")
    if len({m["sha256"] for r in rows for m in r["media"]})!=90 or any([m["kind"] for m in r["media"]]!=["vehicle","vehicle","sheet"] for r in rows):raise RuntimeError("ATP30 media set mismatch")
    return rows
def path_for(root,r,m):return root/ASSETS/ident(r)/m["file"]
def verify(root,target):
    paths=set()
    for r in load(root):
        for m in r["media"]:
            if not re.fullmatch(r"[0-9]{3}-[0-9]+-(?:vehicle|sheet)\.jpg",m["file"]):raise RuntimeError("ATP30 invalid media path")
            p=path_for(target,r,m)
            if not p.is_file() or p.is_symlink() or p.read_bytes()[:3]!=b"\xff\xd8\xff" or digest(p)!=m["sha256"]:raise RuntimeError("ATP30 media mismatch "+str(p))
            paths.add(p)
    if len(paths)!=90 or paths!=set((target/ASSETS).rglob("*.jpg")):raise RuntimeError("ATP30 unexpected media")
def install(src):
    src=Path(src)
    if digest(src/"manifest.json")!=SOURCE_SHA:raise RuntimeError("ATP30 source manifest mismatch")
    rows=json.loads((src/"manifest.json").read_text())
    selected=[]
    for pos,i in enumerate(INDICES,1):
        r=rows[i-1]
        assert r["index"]==i
        selected.append(dict(r,review_number=pos,media=[m for m in r["media"] if m["kind"]=="vehicle"][:2]+[next(m for m in r["media"] if m["kind"]=="sheet")]))
    if hashlib.sha256(frozen_bytes(selected)).hexdigest()!=SELECTED_SHA:raise RuntimeError("ATP30 selection digest mismatch")
    (ROOT/RECEIPT).write_text(json.dumps({"reviewed_pdf":"PapAuto_Japan_ATP_30_batch1_2026-11-26.pdf","reviewed_pdf_sha256":PDF_SHA,"source_artifact_id":15115707921,"owner_approval":"Explicit request to publish exactly 30 reviewed PDF cards on 2026-11-26","rights_confirmed":False,"scope":"Historical model SEO references only, not stock","lots":selected},ensure_ascii=False,indent=2)+"\n")
    for r in load(ROOT):
        for m in r["media"]:
            p=src/m["file"];dst=path_for(ROOT,r,m)
            if digest(p)!=m["sha256"]:raise RuntimeError("ATP30 original mismatch")
            dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    verify(ROOT,ROOT)
def render(root,target,coverage,registry):
    verify(root,root);verify(root,target)
    report={r["model_id"]:r for r in coverage["models"]}
    existing={key(r.get("auction"),r.get("auction_date"),r.get("lot_number")):r for r in registry["lots"]}
    from render_atp_japan9 import load as prev9
    from render_atp_honda5 import load as prev5
    previous={key(r["auction"],r["auction_date"],r["lot"]) for r in prev9(root)+prev5(root)}
    seen=set();count=0;skips=[];pages=set()
    for r in load(root):
        model=ident(r);f=r["facts"];k=key(f["Аукцион"],f["Дата аукциона"],f["Номер лота"])
        if k in seen or k in previous:raise RuntimeError("ATP30 duplicate SEO lot")
        seen.add(k);page=target/"models"/(model+".html");html=page.read_text(encoding="utf-8")
        if k in existing:
            old=existing[k]["id"]
            if ('data-model-lot-id="'+old+'"' not in html and 'href="/lots/'+old+'.html"' not in html):raise RuntimeError("ATP30 existing lot not linked "+old)
            skips.append(r["review_number"]);continue
        title=escape(r["model"]+" · "+str(r["year"]))
        media="".join('<a href="/'+escape(path_for(target,r,m).relative_to(target).as_posix(),quote=True)+'"><img loading="lazy" decoding="async" src="/'+escape(path_for(target,r,m).relative_to(target).as_posix(),quote=True)+'" alt="'+title+(' — полный аукционный лист' if m["kind"]=="sheet" else ' — фото аукциона')+'"></a>' for m in r["media"])
        trim=f["Комплектация"].strip()
        if "&" in trim or r["index"]==5:trim="Уточнить по листу"
        facts=[("Кузов",f["Кузов"]),("Комплектация",trim or "Не указана"),("Пробег по данным источника",f["Пробег"]),("Объём",re.sub(r"\D","",f["Объем"])+" см³"),("Аукцион",f["Аукцион"]),("Дата торгов",f["Дата аукциона"]),("Номер лота",f["Номер лота"]),("Оценка",f["Оценка"]),("Цена продажи по данным ATP",f["Цена продажи в Японии"])]
        label="Архивный пример завершённых торгов. Автомобиль не в наличии PapAuto. Цена торгов без ввоза и доставки. Возможность экспорта и ввоза проверяется для конкретной версии; не предложение прямой поставки."
        card='<article class="pa-model-lot pa-model-atp-reference" data-model-reference-id="atp-japan30-b1-'+str(r["review_number"])+'"><div class="pa-atp-media">'+media+'</div><div class="pa-model-lot-body"><h3>'+title+'</h3><dl>'+''.join('<div><dt>'+escape(k)+'</dt><dd>'+escape(v)+'</dd></div>' for k,v in facts)+'</dl><p>'+escape(label)+'</p><p>Источник фотографий, листа и данных: АТП.Авто, архив на 26.11.2026.</p></div></article>'
        old_empty='<p>В опубликованной базе пока нет подходящего аукционного примера этой модели из выбранной страны с оригинальным фото и полным аукционным листом. Не подставляем фото другой модели или страны.</p>'
        html=html.replace(old_empty,'<p>Ниже — проверенный архивный пример конкретной модели.</p>',1)
        html,n=re.subn(r'(<section id="pa-model-statistics"[^>]*>[\s\S]*?)(</section>)',lambda m:m.group(1)+'<h3>Дополнительный аукционный пример</h3><div class="pa-model-lot-grid">'+card+'</div>'+m.group(2),html,count=1)
        if n!=1:raise RuntimeError("ATP30 missing model section "+model)
        if model not in pages:html=html.replace("</head>",'<style>.pa-atp-media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:7px}.pa-atp-media img{width:100%;height:auto;max-height:300px;object-fit:contain}</style></head>',1)
        page.write_text(html,encoding="utf-8");pages.add(model);report[model]["reference_cards"]=report[model].get("reference_cards",0)+1;count+=1
    coverage["japan30_batch1_reference_cards"]=count
    coverage["japan30_batch1_existing_lots"]=skips
    coverage["photo_pages"]=sum(any(r.get(k,0) for k in ("auction_matches","supplier_matches","related_cards","reference_cards")) for r in report.values())
    coverage["no_photo_pages"]=len(report)-coverage["photo_pages"]
    (target/"data/model-statistics-coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PAPAUTO_ATP_JAPAN30_BATCH1_OK "+json.dumps({"new_reference_cards":count,"existing_lots_reused":skips,"model_pages":len(report),"new_reference_model_pages":len(pages),"gallery_unchanged":True}))
if __name__=="__main__":install(sys.argv[1])
