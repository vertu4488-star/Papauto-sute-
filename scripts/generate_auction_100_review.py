#!/usr/bin/env python3
"""Generate a private human-review queue for 100 unapproved Japan/China auction leads.

This file lives in research/, never customer-visible, and does not fetch or
embed any remote imagery. The customer-facing gallery is NOT modified.
"""
from __future__ import annotations

from collections import Counter
from html import escape
import json
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "research" / "auction-100-japan-china-intake-2026-11-13.json"
OUTPUT = ROOT / "research" / "auction-100-japan-china-review.html"
ALLOWED_DOMAINS = {
    "japan": {"www.japanautoimport.com", "japanautoimport.com"},
    "china": {"plc.auction", "www.plc.auction"},
}

def verified_source(record: dict) -> str:
    url = record["source_url_research_only"]
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOMAINS[record["target_market"]]:
        raise ValueError(f"Unexpected source domain for {record['work_id']}: {url}")
    if parsed.username or parsed.password or parsed.port or not parsed.path.startswith("/"):
        raise ValueError("Invalid source URL")
    return url

def audited_batch(doc: dict) -> list[dict]:
    rows = doc.get("records")
    if not isinstance(rows, list) or len(rows) != 100:
        raise ValueError("The private intake must contain exactly 100 leads")
    if Counter(x.get("target_market") for x in rows) != {"japan": 90, "china": 10}:
        raise ValueError("Expected 90 Japan and 10 China source leads")
    ids = set()
    urls = set()
    for row in rows:
        ident = row["work_id"]
        if ident in ids or not ident.startswith("intake-"):
            raise ValueError("Duplicate/invalid review ID: " + str(ident))
        ids.add(ident)
        url = verified_source(row)
        if url in urls:
            raise ValueError("Duplicate source URL")
        urls.add(url)
        if (row.get("ready_for_publication") is not False
                or row.get("publication_state") != "BLOCKED_SOURCE_RESEARCH"
                or row.get("verified_original_auction_photo_files") != []
                or row.get("matching_full_original_auction_sheet_file") is not None
                or row.get("written_photo_commercial_selfhost_license") is not None
                or row.get("written_sheet_commercial_selfhost_license") is not None):
            raise ValueError("Source lead cannot be treated as approved: " + ident)
        if not isinstance(row.get("external_photo_references_research_only"), list):
            raise ValueError("Missing external photo reference field")
    return rows

def render(doc: dict) -> str:
    rows = audited_batch(doc)
    counts = Counter(x["target_market"] for x in rows)
    sections = []
    for row in rows:
        ident = escape(row["work_id"], quote=True)
        model = escape(row["make_and_model_as_listed"], quote=True)
        year = int(row["year_as_listed"])
        region = row["target_market"]
        source = escape(verified_source(row), quote=True)
        date = escape(str(row.get("date_as_listed") or "не подтверждена"))
        refs = len(row["external_photo_references_research_only"])
        photo_status = ("Только миниатюра 50 px — полноразмерное фото отсутствует"
                        if region == "japan"
                        else "5 фотоссылок агрегатора — аукционное происхождение не проверено")
        missing = [
            "Оригинальные фото именно с аукциона", "Подлинный полный аукционный лист",
            "Аукцион и номер лота", "Пробег и оценка",
            "Разрешение на коммерческое использование фото и листа",
        ]
        missing_html = "".join("<li>"+escape(text)+"</li>" for text in missing)
        sections.append(
            f'<article class="lot" id="{ident}" data-market="{region}" '
            f'data-model="{model.lower()}">'
            f'<div class="lot-top"><span class="id">{ident}</span>'
            f'<span class="country">{"Япония" if region=="japan" else "Китай"}</span></div>'
            f'<h2>{model} · {year}</h2>'
            f'<p class="meta">Дата в источнике: {date} · Ссылок на фото: {refs}</p>'
            f'<p class="warning">{escape(photo_status)}</p>'
            f'<details><summary>Что ещё необходимо подтвердить</summary>'
            f'<ul>{missing_html}</ul></details>'
            f'<a class="source" href="{source}" target="_blank" rel="noopener noreferrer">'
            f'Открыть первоисточник (только для внутренней проверки)</a>'
            f'</article>'
        )
    return """<!doctype html><html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>PapAuto — внутреннее согласование 100 аукционных кандидатов</title>
<style>
:root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;color:#1d3244;background:#f2f5f8}
*{box-sizing:border-box}body{margin:0}.top{background:#102d45;color:#fff;padding:28px max(18px,calc((100vw - 1130px)/2))}
.top h1{font-size:clamp(24px,4vw,38px);margin:0 0 8px}.top p{color:#cdddea;margin:0;line-height:1.6}
main{max-width:1150px;margin:auto;padding:22px 18px 60px}
.warn{border-left:4px solid #b56e24;background:#fff8ed;padding:15px;margin:0 0 20px;font-size:14px;line-height:1.6}
.metrics{display:flex;flex-wrap:wrap;gap:10px;margin-bottom:16px}
.metric{background:#fff;border:1px solid #dbe3ea;border-radius:12px;padding:14px 19px;flex:1;min-width:120px}
.metric strong{font-size:29px;display:block}.metric span{color:#61778b;font-size:12px}
.filters{display:flex;gap:10px;flex-wrap:wrap;margin:0 0 16px}
.filters input,.filters select{min-width:0;flex:1;border-radius:8px;padding:12px;font:inherit;border:1px solid #bcccd9;background:white}
.filters select{flex:0 0 165px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:13px}
.lot{min-width:0;background:#fff;border:1px solid #dbe3ea;border-radius:12px;padding:16px;display:flex;flex-direction:column;gap:10px}
.lot-top{display:flex;gap:8px;justify-content:space-between;color:#5c7890;font-size:11px}
.lot h2{font-size:16px;line-height:1.4;margin:0}.lot p{font-size:12px;line-height:1.5;margin:0}
.lot .warning{color:#915520}.lot details{font-size:12px;color:#4c6579}
.lot summary{font-weight:700;cursor:pointer}.lot li{margin:5px 0}
.source{color:#176197;font-size:12px;font-weight:700;margin-top:auto;overflow-wrap:anywhere}
footer{color:#667e90;font-size:12px;margin-top:19px}
@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:520px){.grid{grid-template-columns:1fr}.filters select{flex:1 1 100%}}
</style></head><body><header class="top">
<h1>100 кандидатов · Япония и Китай</h1>
<p>Закрытый исследовательский реестр PapAuto. Эти автомобили <b>не опубликованы</b> и не являются подтверждёнными аукционными лотами сайта.</p></header>
<main><p class="warn"><b>Запрещено переносить фотографии автоматически.</b>
Нет оригинальных полных аукционных листов, достоверных подтверждений фото
и разрешений на размещение. Уличные, дилерские и рекламные снимки запрещены.</p>
<div class="metrics"><div class="metric"><strong>100</strong><span>На проверке</span></div>
<div class="metric"><strong>90</strong><span>Япония</span></div>
<div class="metric"><strong>10</strong><span>Китай</span></div>
<div class="metric"><strong>0</strong><span>Готовы к публикации</span></div></div>
<div class="filters"><input id="search" type="search" placeholder="Поиск по марке, модели или ID" aria-label="Поиск по кандидату">
<select id="market" aria-label="Страна"><option value="all">Все страны</option>
<option value="japan">Япония (90)</option><option value="china">Китай (10)</option></select></div>
<p id="resultCount" aria-live="polite"></p>
<div class="grid" id="records">""" + "\n".join(sections) + """</div>
<footer>Внутренний исследовательский материал. Источники открываются только здесь, а не в клиентской галерее. Публичная галерея содержит 37 карточек.</footer>
</main><script>
(()=>{const cards=[...document.querySelectorAll(".lot")],field=document.querySelector("#search"),
market=document.querySelector("#market"),result=document.querySelector("#resultCount");
function filter(){const term=field.value.toLocaleLowerCase("ru").trim();const region=market.value;
let visible=0;for(const card of cards){const ok=(region==="all"||card.dataset.market===region)&&
(!term||(card.querySelector("h2").textContent+" "+card.id).toLocaleLowerCase("ru").includes(term));
card.hidden=!ok;if(ok)visible++}result.textContent="Показано "+visible+" из "+cards.length+" записей"; }
field.addEventListener("input",filter);market.addEventListener("change",filter);filter()})();
</script></body></html>"""

def main():
    doc = json.loads(SOURCE.read_text(encoding="utf-8"))
    page = render(doc)
    OUTPUT.write_text(page, encoding="utf-8")
    print(f"PAPAUTO_100_AUCTION_REVIEW: 100 entries; no publication, no images, no missing-source substitution")

if __name__ == "__main__":
    main()
