"""Exact frozen 33-model owner-approved reference package, separate from auction inventory."""
import hashlib
import json
import re
import shutil
import sys
from pathlib import Path
from html import escape

ROOT = Path(__file__).resolve().parents[1]
NUMBERS = [1,2,4,5,7,8,9,10,11,12,13,14,15,16,17,18,19,20,22,23,24,29,30,31,32,34,40,41,43,44,45,46,67]
DIGEST = "42ad13579efc876452aa0456144e07f6194dec6587679e4fc421d3fc20e8d867"
ASSETS = "assets/seo-reference/atp-20261126"

def facts(root):
    doc = json.loads((root/"research/atp-seo-33-reference-facts-20261126.json").read_text(encoding="utf-8"))
    rows = doc["rows"]
    if len(rows) != 33 or len({r["model_id"] for r in rows}) != 33:
        raise RuntimeError("ATP33 unexpected reference facts")
    return list(zip(NUMBERS, rows))

def media_paths(root, number, row):
    files = root/ASSETS/row["model_id"]
    names = [f"{number:03d}-0-vehicle.jpg"]
    if number != 46:
        names.append(f"{number:03d}-1-vehicle.jpg")
    if number == 67:
        names.append(f"{number:03d}-2-sheet.jpg")
    return [files/n for n in names]

def verify(root, media_root=None):
    media_root = media_root or root
    paths = []
    lines = []
    for num,row in facts(root):
        if not re.fullmatch(r"[a-z0-9-]+",row["model_id"]):
            raise RuntimeError("ATP33 invalid model ID")
        for p in media_paths(media_root,num,row):
            if not p.is_file() or p.is_symlink() or p.stat().st_size < 500 or p.read_bytes()[:3] != b"\xff\xd8\xff":
                raise RuntimeError("ATP33 missing or invalid reviewed image "+str(p))
            paths.append(p)
            lines.append(str(p.relative_to(media_root/ASSETS))+" "+hashlib.sha256(p.read_bytes()).hexdigest())
    if len(paths)!=66 or set(paths)!=set((media_root/ASSETS).rglob("*.jpg")):
        raise RuntimeError("ATP33 unexpected media set")
    if hashlib.sha256(("\n".join(sorted(lines))+"\n").encode()).hexdigest()!=DIGEST:
        raise RuntimeError("ATP33 approved image hashes do not match")
    return paths

def install(source):
    for num,row in facts(ROOT):
        for p in media_paths(ROOT,num,row):
            match = list(source.rglob(p.name))
            if len(match)!=1:
                raise RuntimeError("ATP33 missing original "+p.name)
            p.parent.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(match[0],p)
    verify(ROOT)
    print("ATP33 verified 66 exact frozen original files")

def render(root,target,coverage):
    verify(root)
    verify(root,target)
    report = {r["model_id"]:r for r in coverage["models"]}
    for num,row in facts(root):
        ident=row["model_id"]
        rec=report[ident]
        if any(rec.get(k,0) for k in ("auction_matches","supplier_matches","related_cards")):
            raise RuntimeError("ATP33 cannot replace existing example "+ident)
        page=target/"models"/(ident+".html")
        html=page.read_text(encoding="utf-8")
        photos=media_paths(target,num,row)
        title=escape(row["title"]+" · "+str(row["year"]))
        attrs='data-model-related-reference-id' if num==67 else 'data-model-reference-id'
        media="".join('<a href="/'+escape(str(p.relative_to(target)),quote=True)+'"><img loading="lazy" decoding="async" src="/'+escape(str(p.relative_to(target)),quote=True)+'" alt="'+title+(' — аукционный лист' if p.name.endswith("-sheet.jpg") else ' — фото автомобиля')+'"></a>' for p in photos)
        label="Архивный пример Nissan Dualis, японского семейства Qashqai. Не предложение к покупке." if num==67 else "Справочный пример автомобиля из объявления. Не статистика завершённых торгов и не автомобиль в наличии PapAuto."
        card='<article class="pa-model-lot pa-model-atp-reference" '+attrs+'="'+ident+'"><div class="pa-atp-media">'+media+'</div><div class="pa-model-lot-body"><h3>'+title+'</h3><p>Пробег по данным источника: '+f'{row["mileage_km"]:,}'.replace(","," ")+' км.</p><p>'+escape(label)+'</p><p>Источник фотографий и данных: АТП.Авто, 26.11.2026.</p>'+('<p>'+escape(row["note"])+'</p>' if row.get("note") else '')+'</div></article>'
        # Replace the empty-photo sentence, not the existing model section/CTA.
        old='<p>В опубликованной базе пока нет подходящего аукционного примера этой модели из выбранной страны с оригинальным фото и полным аукционным листом. Не подставляем фото другой модели или страны.</p>'
        if html.count(old)!=1:
            raise RuntimeError("ATP33 expected empty model reference section "+ident)
        html=html.replace(old,'<p>Фотографии и характеристики конкретного автомобиля.</p><div class="pa-model-lot-grid">'+card+'</div>',1)
        html=html.replace("</head>",'<style>.pa-atp-media{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:7px}.pa-atp-media a{display:block}.pa-atp-media img{width:100%;height:auto;max-height:300px;object-fit:contain}</style></head>',1)
        page.write_text(html,encoding="utf-8")
        rec["reference_cards"]=1
        rec["reference_related"]=int(num==67)
    coverage["reference_covered"]=33
    coverage["reference_exact_covered"]=32
    coverage["photo_pages"]=sum(any(r.get(k,0) for k in ("auction_matches","supplier_matches","related_cards","reference_cards")) for r in report.values())
    coverage["no_photo_pages"]=135-coverage["photo_pages"]
    if coverage["photo_pages"]!=101:
        raise RuntimeError("ATP33 expected 101 photo-covered pages")
    (target/"data/model-statistics-coverage.json").write_text(json.dumps(coverage,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("PAPAUTO_ATP_SEO_PHOTOS_OK "+json.dumps({"reference_pages":33,"media":66,"photo_pages":101,"remaining":34,"auction_gallery_changes":0}))

if __name__=="__main__":
    install(Path(sys.argv[1]))
