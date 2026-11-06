"""Build public buyer pages from content/buyer-pages.json (standard library only)."""
import json,re
from pathlib import Path
from html import escape
from xml.etree import ElementTree as ET
ROOT=Path(__file__).resolve().parents[1]
BASE='https://papauto.ru'
def e(value): return escape(str(value),quote=True)
def link(url):
    if not url.startswith('/') or url.startswith('//'): raise ValueError('Only internal links are allowed')
    return e(url)
def build():
    pages=json.loads((ROOT/'content/buyer-pages.json').read_text())
    used=set()
    for p in pages:
        slug=p['slug']
        if not re.fullmatch('[a-z][a-z0-9-]+',slug) or slug in used: raise ValueError('Invalid or duplicate page slug')
        used.add(slug)
        url=f'{BASE}/{slug}.html'
        sections=''
        for s in p['sections']:
            cta=f'<a href="{link(s["link"])}">{e(s["label"])} →</a>' if s.get('link') else ''
            sections+=f'<section class="buyer-block"><h2>{e(s["heading"])}</h2><p>{e(s["text"])}</p>{cta}</section>'
        checklist=''
        if p.get('checklist'):
            items=''.join(f'<label><input type="checkbox" value="{i}"><span>{e(text)}</span></label>' for i,text in enumerate(p['checklist']))
            checklist=f'<div id="buyerChecklist" class="buyer-checklist">{items}</div><p id="checklistStatus" role="status"></p><div class="buyer-tools-actions"><button id="printChecklist" type="button" class="button button-secondary">Распечатать</button><button id="resetChecklist" type="button" class="button button-secondary">Сбросить отметки</button></div>'
        crumbs={'@context':'https://schema.org','@type':'BreadcrumbList','itemListElement':[{'@type':'ListItem','position':1,'name':'Главная','item':BASE+'/'},{'@type':'ListItem','position':2,'name':p['heading'],'item':url}]}
        structured=json.dumps(crumbs,ensure_ascii=False).replace('<','\\u003c')
        nav='<nav class="buyer-links" aria-label="Помощь покупателю">'+''.join(f'<a href="/{x["slug"]}.html"'+(' aria-current="page"' if x['slug']==slug else '')+f'>{e(x["heading"])}</a>' for x in pages)+'</nav>'
        html=f'''<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{e(p['title'])}</title><meta name="description" content="{e(p['description'])}"><meta name="robots" content="index,follow,max-image-preview:large"><link rel="canonical" href="{url}"><meta property="og:type" content="website"><meta property="og:site_name" content="PAPAUTO"><meta property="og:title" content="{e(p['title'])}"><meta property="og:description" content="{e(p['description'])}"><meta property="og:url" content="{url}"><link rel="icon" href="/assets/favicon.svg"><link rel="stylesheet" href="/styles.css"><link rel="stylesheet" href="/buyer-tools.css"><script type="application/ld+json">{structured}</script></head><body><header class="site-header"><a class="brand" href="/">PAPAUTO</a><a class="header-cta" href="/?view=select#assistant">Подобрать автомобиль →</a></header><main class="buyer-page"><a href="/">Главная</a> / Помощь покупателю<h1>{e(p['heading'])}</h1><p>{e(p['intro'])}</p>{checklist}{sections}{nav}</main><footer class="site-footer"><a href="/catalog.html">Каталог моделей</a><a href="/privacy.html">Конфиденциальность</a></footer><script src="/buyer-tools.js" defer></script></body></html>'''
        (ROOT/f'{slug}.html').write_text(html+'\n')
    # Discover public pages, keeping each canonical route exactly once.
    urls=[]
    for path in sorted(ROOT.glob('*.html')):
        text=path.read_text()
        if re.search(r'<meta[^>]+content="[^"]*noindex',text): continue
        m=re.search(r'<link rel="canonical" href="([^"]+)"',text)
        if m and m[1].startswith(BASE+'/'): urls.append(m[1])
    (ROOT/'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'+''.join(f'  <url><loc>{e(url)}</loc></url>\n' for url in sorted(set(urls)))+'</urlset>\n')
    print(f'Built {len(pages)} pages; sitemap contains {len(set(urls))} URLs')
if __name__=='__main__': build()
