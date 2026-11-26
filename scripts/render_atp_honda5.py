"""Only the five specifically approved exact archival Honda reference cards."""
import hashlib, json, re, shutil, sys
from pathlib import Path
from html import escape
ROOT=Path(__file__).resolve().parents[1]
ASSETS="assets/seo-reference/atp-honda5-20261126"
MANIFEST="research/owner-reviewed-honda-atp-5-20261126.json"
PDF_SHA="f8495bfd09098ead20988813fd91edf629484d188e79cc0e593a12205e2ca82f"
EXPECTED={("JU Gifu","2026-10-24","10062"),("JU Niigata","2026-10-23","324"),("JU Tokyo","2026-10-19","8238"),("TAA Kinki","2026-10-27","163"),("KCAA Fukuoka","2026-10-15","504")}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(root):
    d=json.loads((root/MANIFEST).read_text(encoding="utf-8"))
    rows=d["lots"]
    if d["reviewed_pdf_sha256"]!=PDF_SHA or d["rights_confirmed"] is not False or len(rows)!=5 or {(r["auction"],r["auction_date"],r["lot"]) for r in rows}!=EXPECTED:raise RuntimeError("HONDA5 owner receipt mismatch")
    if len({m["sha256"] for r in rows for m in r["media"]})!=15 or any([m["kind"] for m in r["media"]]!=["vehicle","vehicle","sheet"] for r in rows):raise RuntimeError("HONDA5 media set mismatch")
    return rows
def path_for(root,r,m):return root/ASSETS/r["model_id"]/m["file"]
def verify(root,target):
    paths=set()
    for r in load(root):
        for m in r["media"]:
            if not re.fullmatch(r"[a-zA-Z0-9]+-[0-9]{2}-(?:vehicle|sheet)\.jpg",m["file"]):raise RuntimeError("HONDA5 invalid filename")
            p=path_for(target,r,m)
            if not p.is_file() or p.is_symlink() or p.read_bytes()[:3]!=b"\xff\xd8\xff" or digest(p)!=m["sha256"]:raise RuntimeError("HONDA5 original file mismatch "+str(p))
            paths.add(p)
    if len(paths)!=15 or paths!=set((target/ASSETS).rglob("*.jpg")):raise RuntimeError("HONDA5 unexpected file")
def install(src):
    src=Path(src)
    manifest=json.loads((src/"manifest.json").read_text(encoding="utf-8"))
    for r in load(ROOT):
        matches=[x for x in manifest if x.get("url")==r["source_listing"]]
        if len(matches)!=1:raise RuntimeError("HONDA5 missing exact source")
        x=matches[0]
        if (x["Аукцион"],x["Дата аукциона"],x["Номер лота"])!=(r["auction"],r["auction_date"],r["lot"]) or x["Оценка"]!=r["grade"] or x["Цена продажи в Японии"]!=r["source_price"]:raise RuntimeError("HONDA5 source facts mismatch")
        for m in r["media"]:
            p=src/m["file"]
            if digest(p)!=m["sha256"]:raise RuntimeError("HONDA5 artifact digest mismatch")
            dst=path_for(ROOT,r,m);dst.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dst)
    verify(ROOT,ROOT)
def render(root,target,coverage,registry):
    verify(root,root);verify(root,target)
    report={r["model_id"]:r for r in coverage["models"]}
    norm=lambda x:re.sub(r"[^a-z0-9]","",str(x or "").casefold())
    existing={(norm(r.get("auction")),str(r.get("auction_date")),str(r.get("lot_number"))):r for r in registry["lots"]}
    # Also prevent duplicates with earlier frozen ATP Japan examples.
    from render_atp_japan9 import load as previous
    previous_keys={(norm(r["auction"]),str(r["auction_date"]),str(r["lot"])) for r in previous(root)}
    count=0;skips=[]
    for r in load(root):
        ident=r["model_id"];page=target/"models"/(ident+".html");html=page.read_text(encoding="utf-8")
        key=(norm(r["auction"]),r["auction_date"],r["lot"])
        if key in previous_keys:raise RuntimeError("HONDA5 duplicate prior SEO reference")
        if key in existing:
            old=existing[key]["id"]
            if ('data-model-lot-id="'+old+'"' not in html and 'href="/lots/'+old+'.html"' not in html):raise RuntimeError("HONDA5 existing lot not linked to exact model "+old)
            skips.append(r["lot"]);continue
        title=escape(r["model"]+" · "+str(r["year"]))
        media="".join('<a href="/'+escape(path_for(target,r,m).relative_to(target).as_posix(),quote=True)+'"><img loading="lazy" decoding="async" src="/'+escape(path_for(target,r,m).relative_to(target).as_posix(),quote=True)+'" alt="'+title+(' — полный аукционный лист' if m["kind"]=="sheet" else ' — фото аукциона')+'"></a>' for m in r["media"])
        facts=[("Кузов",r["body"]),("Комплектация",r["trim"]),("Пробег по данным источника",r["mileage"]),("Объём",r["engine"]),("Аукцион",r["auction"]),("Дата торгов",r["auction_date"]),("Номер лота",r["lot"]),("Оценка",r["grade"]),("Цена продажи по данным ATP",r["source_price"])]
        label="Архивный пример. Автомобиль не в наличии PapAuto. Цена торгов не включает ввоз и доставку."
        if r["export_restricted"]:label+=" Гибрид: не предложение прямого экспорта из Японии в Россию."
        card='<article class="pa-model-lot pa-model-atp-reference" data-model-reference-id="atp-honda5-'+r["lot"]+'"><div class="pa-atp-media">'+media+'</div><div class="pa-model-lot-body"><h3>'+title+'</h3><dl>'+''.join('<div><dt>'+escape(k)+'</dt><dd>'+escape(v)+'</dd></div>' for k,v in facts)+'</dl><p>'+escape(label)+'</p><p>Источник фотографий, листа и данных: АТП.Авто, архив на 26.11.2026.</p></div></article>'
        html,n=re.subn(r'(<section id="pa-model-statistics"[^>]*>[\s\S]*?)(</section>)',lambda m:m.group(1)+'<h3>Дополнительный аукционный пример</h3><div class="pa-model-lot-grid">'+card+'</div>'+m.group(2),html,count=1)
        if n!=1:raise RuntimeError("HONDA5 missing stats")
        html=html.replace("</head>",'<style>.pa-atp-media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:7px}.pa-atp-media img{width:100%;height:auto;max-height:300px;object-fit:contain}</style></head>',1)
        page.write_text(html,encoding="utf-8");report[ident]["reference_cards"]=report[ident].get("reference_cards",0)+1;count+=1
    coverage["honda5_reference_cards"]=count
    coverage["honda5_existing_lots"]=skips
    coverage["photo_pages"]=sum(any(r.get(k,0) for k in ("auction_matches","supplier_matches","related_cards","reference_cards")) for r in report.values())
    coverage["no_photo_pages"]=len(report)-coverage["photo_pages"]
    (target/"data/model-statistics-coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PAPAUTO_HONDA5_OK "+json.dumps({"new_reference_cards":count,"existing_lots_reused":skips,"model_pages":len(report),"gallery_unchanged":True}))
if __name__=="__main__":install(sys.argv[1])
