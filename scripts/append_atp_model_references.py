"""Publish independently worded factual model references only.

No source media, source hyperlinks, price, auction-sale claim or inventory claim.
Do not change the approved-image release contract or directory photo counts.
"""
from pathlib import Path
from html import escape
import json
import re

def append_references(root: Path, target: Path):
    doc=json.loads((root/"research/atp-seo-33-reference-facts-20261126.json").read_text(encoding="utf-8"))
    rows=doc["rows"]
    if len(rows)!=33 or len({r["model_id"] for r in rows})!=33 or doc["rights_confirmed"] is not False:
        raise RuntimeError("ATP_SEO_REFERENCE invalid approved facts")
    items={i["id"]:i for i in json.loads((target/"data/papauto-expanded-45x3-2026.json").read_text(encoding="utf-8"))["items"]}
    for r in rows:
        ident=r["model_id"]
        if ident not in items or not re.fullmatch(r"[a-z0-9-]+",ident):
            raise RuntimeError("ATP_SEO_REFERENCE invalid model: "+ident)
        if not (1900<=r["year"]<=2026 and 0<r["mileage_km"]<1000000 and str(r["source_number"]).isdigit()):
            raise RuntimeError("ATP_SEO_REFERENCE invalid facts: "+ident)
        title=escape(r["title"])
        km=f'{r["mileage_km"]:,}'.replace(","," ")
        note=('<p>'+escape(r["note"])+'</p>') if r.get("note") else ""
        section=(
            '<section id="pa-atp-reference" aria-labelledby="pa-atp-reference-title">'
            '<h2 id="pa-atp-reference-title">Пример автомобиля: '+title+'</h2>'
            '<p><strong>Год выпуска:</strong> '+str(r["year"])+' · <strong>Пробег по объявлению:</strong> '+km+' км.</p>'
            '<p>Справочные данные стороннего объявления АТП.Авто, зафиксированные 26.11.2026. '
            'Не автомобиль в наличии PapAuto, не подтверждённый результат продажи. '
            'Состояние, комплектация, фактический пробег, мощность и применимость правил ввоза требуют проверки по оригинальным документам.</p>'
            +note+'</section>')
        page=target/"models"/(ident+".html")
        html=page.read_text(encoding="utf-8")
        if 'id="pa-atp-reference"' in html:
            raise RuntimeError("ATP_SEO_REFERENCE duplicate section "+ident)
        html,count=re.subn(r'(<main\b[^>]*>[\s\S]*?</h1>)(\s*<p\b[^>]*>[\s\S]*?</p>)?',lambda m:m.group(0)+section,html,count=1,flags=re.I)
        if count!=1: raise RuntimeError("ATP_SEO_REFERENCE no main H1 "+ident)
        page.write_text(html,encoding="utf-8")
    print("PAPAUTO_ATP_SEO_FACTS_OK "+json.dumps({"pages":len(rows),"new_photos":0,"auction_gallery_changes":0}))
