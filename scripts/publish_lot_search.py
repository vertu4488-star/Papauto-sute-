"""Expose only the final screened public lot registry to search crawlers."""
import html
import json
import xml.etree.ElementTree as ET
from pathlib import Path


def publish(target: Path):
    lots = json.loads((target / 'data/gallery-lots.json').read_text())['lots']
    esc = lambda v: html.escape(str(v), quote=True)
    rows = []
    urls = []
    for lot in lots:
        path = '/lots/' + lot['id'] + '.html'
        url = 'https://papauto.ru' + path
        file = target / path.lstrip('/')
        page = file.read_text()
        page = page.replace('content="noindex,follow"', 'content="index,follow"', 1)
        description = (f"{lot['model']} {lot['year']}: пробег {lot['mileage_km']} км, "
                       f"оценка {lot['grade']}, {lot['auction']}, {lot['auction_date']}, лот {lot['lot_number']}. "
                       'Архивный аукционный пример с фото и листом. Подбор аналога с доставкой в Новосибирск.')
        import re
        page = re.sub(r'<meta name="description" content="[^"]*">',
                      '<meta name="description" content="' + esc(description) + '">', page)
        page = page.replace('</head>', f'<link rel="canonical" href="{url}">\n<script defer src="/metrika.js"></script></head>', 1)
        page = page.replace('<nav>', '<nav><a href="/auction-lot-index.html">Все лоты по моделям</a>', 1)
        page = page.replace('</aside>', '<h2>Стоимость доставки и оформления</h2><p>Для расчёта аналога отдельно учитываем покупку, доставку до Владивостока, таможенные платежи, утильсбор и перевозку до Новосибирска. Архивная цена не является ценой под ключ.</p><p><a href="/#calculator">Калькулятор стоимости</a> · <a href="/avto-iz-yaponii-novosibirsk.html">Авто из Японии в Новосибирск</a></p></aside>', 1)
        file.write_text(page)
        urls.append(url)
        rows.append((lot['model'], f'<li><a href="{path}">{esc(lot["model"])} {lot["year"]} — {esc(lot["auction"])}, №{esc(lot["lot_number"])}</a><p>{lot["mileage_km"]:,} км · оценка {esc(lot["grade"])} · {esc(lot["auction_date"])}. Архивный пример для подбора аналога.</p></li>'))
    index = '''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="index,follow"><title>549 аукционных лота из Японии — фото и аукционные листы | PapAuto</title><meta name="description" content="Каталог архивных аукционных примеров: модели, год, пробег, оценки и оригинальные листы. Подбор аналогичного авто с доставкой в Новосибирск."><link rel="canonical" href="https://papauto.ru/auction-lot-index.html"><link rel="icon" href="/favicon.ico"><link rel="stylesheet" href="/lot-detail-photo-first.css"><script defer src="/metrika.js"></script><style>.lot-main li{padding:16px 0;border-bottom:1px solid #ccc;overflow-wrap:anywhere}.lot-main ul{padding-left:22px}.lot-main a{line-height:1.6}</style></head><body><header class="lot-header"><a class="lot-brand" href="/">PAPAUTO.</a><nav><a href="/gallery.html">Фото-галерея</a><a href="/catalog.html">Каталог моделей</a></nav></header><main class="lot-main"><h1>Аукционные лоты из Японии</h1><p>549 опубликованных примера с отдельными страницами, фотографиями и полными аукционными листами.</p><p>Это архивные примеры, а не автомобили в наличии. Цена завершённых торгов, если подтверждена, указана в карточке отдельно от доставки и оформления. Актуальность и стоимость похожего автомобиля проверяем перед заказом.</p><p><a href="/podbor.html">Подобрать автомобиль</a> · <a href="/avto-iz-yaponii-novosibirsk.html">Доставка в Новосибирск</a></p><ul>'''
    index += '\n'.join(row for _, row in sorted(rows)) + '</ul></main></body></html>'
    (target / 'auction-lot-index.html').write_text(index)
    # Keep the main sitemap focused on canonical service, model and regional pages.
    # Auction detail pages have their own dedicated sitemap, advertised in robots.txt.
    sitemap = target / 'sitemap.xml'
    tree = ET.parse(sitemap)
    ns = 'http://www.sitemaps.org/schemas/sitemap/0.9'
    ET.register_namespace('', ns)
    root = tree.getroot()
    lot_prefix = 'https://papauto.ru/lots/'
    # Idempotent: strip lots that an earlier release appended to the main map.
    for item in list(root.findall('{'+ns+'}url')):
        loc = item.findtext('{'+ns+'}loc', default='')
        if loc.startswith(lot_prefix):
            root.remove(item)
    index_url = 'https://papauto.ru/auction-lot-index.html'
    if not any(item.findtext('{'+ns+'}loc') == index_url for item in root.findall('{'+ns+'}url')):
        ET.SubElement(ET.SubElement(root, '{'+ns+'}url'), '{'+ns+'}loc').text = index_url
    tree.write(sitemap, encoding='utf-8', xml_declaration=True)
    # A dedicated sitemap makes the already approved auction detail URLs
    # independently discoverable and trackable in Search Console.
    # It is derived solely from the published, owner-reviewed registry.
    lot_map_root = ET.Element('{'+ns+'}urlset')
    for url in urls:
        ET.SubElement(ET.SubElement(lot_map_root, '{'+ns+'}url'), '{'+ns+'}loc').text = url
    ET.ElementTree(lot_map_root).write(
        target / 'sitemap-lots.xml', encoding='utf-8', xml_declaration=True)
    for name in ['catalog.html', 'auction-lots.html', 'gallery.html']:
        file = target / name
        page = file.read_text()
        page = page.replace('</main>', '<p style="padding:24px"><a href="/auction-lot-index.html">Все 549 аукционных лота: модели, пробег, оценки и листы →</a></p></main>', 1)
        file.write_text(page)
    return len(lots)
