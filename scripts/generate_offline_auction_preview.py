"""Create one self-contained offline preview with *real* repository JPEGs.

No external HTTP requests, no placeholder images, no upload to production.
This is a review artifact, not publication approval.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "review-output" / "papauto_100_offline_auction_cards.html"
SOURCE = ROOT / "research" / "owner-selected-japan-lots-2026-11-14.json"
BASELINE = ROOT / "data" / "gallery-lots.json"
EXTRA_IDS = ("honda-stepwgn-275", "toyota-sienta-321", "toyota-corolla-fielder-111")


def encode_image(relative: str) -> str:
    assert re.fullmatch(r"/assets/auction/(?:approved|home)/[a-zA-Z0-9._/-]+\.jpg", relative), relative
    path = ROOT / relative.lstrip("/")
    assert path.is_file() and not path.is_symlink(), f"Missing JPEG {relative}"
    data = path.read_bytes()
    assert len(data) >= 3000 and data.startswith(b"\xff\xd8\xff"), f"Invalid JPEG: {relative}"
    return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")


def esc(x: object) -> str:
    return html.escape(str(x), quote=True)


def load_records() -> list[dict]:
    selected = json.loads(SOURCE.read_text(encoding="utf8"))["lots"]
    rows = []
    for r in selected:
        # Auction grades "—" and "*" are not reliable grades.
        if str(r.get("grade", "")).strip() in ("", "—", "*"):
            continue
        photo = r["photos"][0]
        sheet = r["auction_sheet"]
        rows.append({"id": r["id"], "name": r["make"] + " " + r["model"],
                     "year": r["year"], "km": r["mileage_km"], "grade": r["grade"],
                     "auction": r["auction"], "number": r["lot"],
                     "description": r["description"],
                     "photo": photo, "sheet": sheet})
    baseline = {r["id"]: r for r in json.loads(BASELINE.read_text(encoding="utf8"))["lots"]}
    for ident in EXTRA_IDS:
        r = baseline[ident]
        rows.append({"id": ident, "name": r["model"], "year": r["year"],
                     "km": r["mileage_km"], "grade": r["grade"],
                     "auction": r["auction"], "number": r["lot_number"],
                     "description": r.get("description") or "Аукционный автомобиль из Японии.",
                     "photo": r["photos"][0], "sheet": r["inspection_image"]})
    assert len(rows) == 100, f"Expected 100 records, got {len(rows)}"
    assert len({r["id"] for r in rows}) == 100
    assert all(r["photo"] != r["sheet"] and r["description"] and r["km"] >= 0 for r in rows)
    return rows


STYLE = """
:root{color-scheme:light;--sand:#f7f0e8;--paper:#fffdfa;--line:#ddc9b6;--ink:#342c25;--muted:#77675c}
*{box-sizing:border-box}html,body{margin:0;padding:0;max-width:100%;overflow-x:hidden}
body{font:15px/1.48 -apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;background:var(--sand);color:var(--ink)}
header{background:linear-gradient(135deg,#fcfaf7,#e8d7c4);border-bottom:1px solid var(--line)}
.wrap{width:min(1080px,100%);padding:0 14px;margin:auto}.head{padding:30px 3px 27px}
.brand{font-size:15px;letter-spacing:.015em;font-weight:650}.eyebrow{font-size:11px;letter-spacing:.12em;color:#9a795f;margin:17px 0 5px}
h1{font-weight:450;letter-spacing:-.045em;line-height:1.13;font-size:clamp(27px,5vw,43px);margin:3px 0 12px}
.intro{font-size:14px;line-height:1.55;color:#6e5d51;margin:0;max-width:660px}
.stats{display:flex;flex-wrap:wrap;gap:8px;margin-top:18px}.stat{background:#fff9f0;border:1px solid #dfccbb;border-radius:12px;padding:9px 13px;min-width:90px}
.stat b{font-size:21px;display:block;font-weight:550}.stat small{font-size:11px;color:#806d5d}
main{padding:20px 0 55px}.controls{display:grid;grid-template-columns:minmax(0,2fr) minmax(0,1.3fr) minmax(0,0.8fr);gap:8px;margin-bottom:14px}
.controls input,.controls select{width:100%;min-width:0;min-height:43px;padding:9px 12px;border:1px solid #d7c1ae;border-radius:11px;background:#fffdfa;color:#342c25;font:inherit}
.count{color:#7c695c;margin:4px 0 13px;font-size:12px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}
.vehicle{border:1px solid #e0cfbf;background:var(--paper);border-radius:18px;overflow:hidden;min-width:0;box-shadow:0 1px 6px #00000008}
.photos{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:5px;background:#f0e5dc;padding:7px}
.photo{position:relative;min-width:0;min-height:185px;max-height:185px;display:block;border:0;background:#eee4da;padding:0;cursor:zoom-in;border-radius:9px;overflow:hidden}
.photo img{width:100%;height:100%;object-fit:contain;display:block}.photo small{position:absolute;bottom:5px;left:5px;right:5px;background:#fff9f1ee;border-radius:6px;font-size:10px;color:#55473a;padding:4px 5px;text-align:left}
.details{padding:13px 14px 16px}.lot{font-size:11px;letter-spacing:.085em;color:#9b7d63}.details h2{font-size:20px;font-weight:500;line-height:1.2;letter-spacing:-.03em;margin:6px 0 12px}
.details h2 em{font-weight:400;color:#856d5d;font-style:normal;white-space:nowrap}.facts{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:10px}
.fact small{display:block;color:#827267;font-size:11px}.fact strong{font-size:14px;font-weight:550;overflow-wrap:anywhere}
.desc{font-size:12px;line-height:1.45;color:#6b5c4f;margin:12px 0 0}
#nothing{display:none;text-align:center;padding:24px 5px;color:#786657}.note{font-size:12px;line-height:1.6;color:#746559;margin:22px 0}
dialog{border:0;padding:10px;border-radius:12px;background:#fffdfa;max-width:96vw;max-height:96vh;box-shadow:0 15px 60px #0005}
dialog::backdrop{background:#100d09cc}.modalhead{display:flex;align-items:center;justify-content:space-between;gap:15px;margin-bottom:8px}
.modalhead span{font-size:13px}.modalhead button{border:1px solid #d2c0af;border-radius:8px;padding:9px;background:white}
dialog img{display:block;max-width:100%;max-height:79vh;object-fit:contain;margin:auto}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}}
@media(max-width:680px){.wrap{padding:0 12px}.head{padding:23px 2px}.grid{grid-template-columns:minmax(0,1fr);gap:12px}.controls{grid-template-columns:minmax(0,1fr) minmax(0,110px)}.controls input{grid-column:1/-1}.photo{min-height:170px;max-height:170px}.details h2{font-size:20px}}
@media(max-width:350px){.photo{min-height:145px;max-height:145px}.details h2{font-size:18px}.stat{padding:7px 9px}}
"""


SCRIPT = """
const cards=[...document.querySelectorAll('.vehicle')],q=document.getElementById('q'),m=document.getElementById('m'),y=document.getElementById('y'),count=document.getElementById('count');
function filter(){let n=0;for(const e of cards){let show=(!q.value||e.dataset.q.includes(q.value.trim().toLowerCase()))&&(!m.value||e.dataset.model===m.value)&&(!y.value||e.dataset.year===y.value);e.hidden=!show;if(show)n++}count.textContent='Показано '+n+' из '+cards.length;document.getElementById('nothing').style.display=n?'none':'block'}
for(const x of [q,m,y])x.addEventListener('input',filter);filter();
const dlg=document.getElementById('viewer');
document.querySelectorAll('.photo').forEach(btn=>btn.addEventListener('click',()=>{document.getElementById('large').src=btn.querySelector('img').src;document.getElementById('caption').textContent=btn.dataset.label;dlg.showModal()}));
document.getElementById('close').addEventListener('click',()=>dlg.close());
"""


def card(row: dict) -> str:
    name, year = esc(row["name"]), int(row["year"])
    photo = encode_image(row["photo"])
    sheet = encode_image(row["sheet"])
    desc = esc(row["description"])
    km = f'{int(row["km"]):,}'.replace(",", " ")
    return f'''<article class="vehicle" data-model="{name}" data-year="{year}" data-q="{esc((row["name"]+" "+str(year)+" "+row["auction"]+" "+str(row["number"])).lower())}">
<div class="photos">
<button class="photo" type="button" data-label="{name} · фото"><img loading="lazy" decoding="async" src="{photo}" alt="Фото аукционного лота {name}"><small>Фото автомобиля</small></button>
<button class="photo" type="button" data-label="{name} · аукционный лист"><img loading="lazy" decoding="async" src="{sheet}" alt="Оригинальный аукционный лист {name}"><small>Аукционный лист</small></button>
</div><div class="details"><div class="lot">ЯПОНИЯ · ЛОТ {esc(row["number"])}</div><h2>{name} <em>{year}</em></h2>
<div class="facts"><div class="fact"><small>Пробег</small><strong>{km} км</strong></div>
<div class="fact"><small>Оценка</small><strong>{esc(row["grade"])}</strong></div>
<div class="fact"><small>Аукцион</small><strong>{esc(row["auction"])}</strong></div>
<div class="fact"><small>Год</small><strong>{year}</strong></div></div>
<p class="desc">{desc}</p></div></article>'''


def main():
    rows = load_records()
    models = sorted({r["name"] for r in rows})
    years = sorted({r["year"] for r in rows}, reverse=True)
    options_m = "".join(f'<option value="{esc(v)}">{esc(v)}</option>' for v in models)
    options_y = "".join(f'<option value="{v}">{v}</option>' for v in years)
    markup = "\n".join(card(r) for r in rows)
    page = f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>PapAuto — 100 аукционных карточек — без интернета</title><style>{STYLE}</style></head><body>
<header><div class="wrap head"><div class="brand">PapAuto</div><div class="eyebrow">ВНУТРЕННИЙ ПРОСМОТР · ФОТОГРАФИИ ВСТРОЕНЫ В ФАЙЛ</div>
<h1>Аукционная статистика авто</h1><p class="intro">Фотография, соответствующий аукционный лист, пробег и оценка. Изображения сохранены внутри этого файла: доступ к papauto.ru и интернет для просмотра не нужен.</p>
<div class="stats"><div class="stat"><b>100</b><small>японских лотов</small></div><div class="stat"><b>{len(models)}</b><small>моделей</small></div><div class="stat"><b>200</b><small>встроенных изображений</small></div></div></div></header>
<main class="wrap"><div class="controls"><input id="q" placeholder="Поиск модели, номера лота…" aria-label="Поиск">
<select id="m" aria-label="Модель"><option value="">Все модели</option>{options_m}</select>
<select id="y" aria-label="Год"><option value="">Все годы</option>{options_y}</select></div>
<p class="count" id="count">Показано 100 из 100</p><section class="grid">{markup}</section><div id="nothing">Ничего не найдено</div>
<p class="note">Это просмотр уже сохранённых в GitHub лотов. Для новых китайских и японских лотов публикация будет только после отдельной проверки подлинности фотографий, листов и вашего согласия. Ссылка на стороннего продавца отсутствует.</p></main>
<dialog id="viewer"><div class="modalhead"><span id="caption">Изображение</span><button id="close" type="button">Закрыть ✕</button></div><img id="large" alt="Увеличенное изображение"></dialog><script>{SCRIPT}</script></body></html>'''
    assert page.count('src="data:image/jpeg;base64,') == 200
    assert "https://" not in page and "http://" not in page
    assert len(rows)==100
    OUTPUT.parent.mkdir(exist_ok=True)
    OUTPUT.write_text(page,encoding="utf8")
    assert OUTPUT.stat().st_size > 6_000_000, "Suspiciously small output"
    print(json.dumps({"file":str(OUTPUT),"bytes":OUTPUT.stat().st_size,
                      "cards":len(rows),"embedded_image_count":200,
                      "sha256":hashlib.sha256(OUTPUT.read_bytes()).hexdigest()}))


if __name__ == "__main__":
    main()
