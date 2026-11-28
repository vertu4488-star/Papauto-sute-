"""Improve real model-name search variants without touching any lot cards."""
import html,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
BRANDS={'Honda':'Хонда','Nissan':'Ниссан','Toyota':'Тойота','Suzuki':'Сузуки','Mazda':'Мазда','Daihatsu':'Дайхатсу','Geely':'Джили','Haval':'Хавал','Changan':'Чанган','Chery':'Чери','BYD':'БИД','GAC':'ГАК','Volkswagen':'Фольксваген','Kia':'Киа','Hyundai':'Хендай','Audi':'Ауди','BMW':'БМВ','Chevrolet':'Шевроле','Genesis':'Дженезис','Mercedes-Benz':'Мерседес','Renault':'Рено','SsangYong':'СсангЙонг'}
SPECIAL={'japan-nissan-note-e-power':('Nissan Note e-POWER','Ниссан Ноут e-POWER'),'china-chery-jetour-x70':('Jetour X70','Джетур X70'),'china-chery-omoda-5':('Omoda 5','Омода 5')}
COUNTRY={'japan':'из Японии','china':'из Китая','korea':'из Южной Кореи'}
MARK='data-pa-search-wording="20261128"'
def update(path,s):
    if MARK in s:return s
    name=re.search(r'<h1\b[^>]*>(.*?) из (?:Японии|Китая|Южной Кореи)',s,re.S)
    if not name:raise ValueError('Model heading not found: '+path.name)
    official=html.unescape(name[1]).strip()
    alias=re.search(re.escape(name[1])+r'\s*\(([^<>()]*[А-Яа-яЁё][^<>()]*)\)',s)
    ru=html.unescape(alias[1]).strip() if alias else None
    if path.stem in SPECIAL:official,ru=SPECIAL[path.stem]
    # Source aliases are authoritative; do not invent obscure transliterations.
    if not ru:raise ValueError('Russian alias needs review: '+path.name)
    brand,_,model=official.partition(' ')
    ru_brand=BRANDS.get(brand,ru.split()[0])
    mixed=ru_brand+' '+model
    if brand in ('Chevrolet','Renault') and model.startswith('Korea '):
        model=model[6:];mixed=ru_brand+' '+model
    # Keep full Russian alias in original introduction; add it when absent.
    heading=re.search(r'<h2\b[^>]*>Сколько стоит[^<]*</h2>',s,re.I)
    if not heading:raise ValueError('Price section needs review: '+path.name)
    country=COUNTRY[path.stem.split('-')[0]]
    q=f'Сколько стоит {mixed} {country} с доставкой в Новосибирск?'
    # No promise of availability or export eligibility; existing answers unchanged.
    new=s[:heading.start()]+f'<h2 {MARK}>{html.escape(q)}</h2>'+s[heading.end():]
    if not alias:
        new=new.replace('</h1>','</h1><p>Название модели: '+html.escape(ru)+'.</p>',1)
    return new
def protected(s):
    return (re.findall(r'<(?:title|h1)\b[^>]*>[\s\S]*?</(?:title|h1)>|<meta\b[^>]*>|<link\b[^>]*>|<script\b[^>]*>[\s\S]*?</script>|<img\b[^>]*>|<article\b[^>]*>[\s\S]*?</article>',s,re.I),
            re.findall(r'\b(?:href|src)\s*=\s*["\x27][^"\x27]*["\x27]',s,re.I),
            re.findall(r'\d[\d \u00a0\u202f–—-]*\s*[₽¥$]',s))
def main():
    pages=sorted((ROOT/'models').glob('*.html'))
    assert len(pages)==147,len(pages)
    pending={};errors=[]
    for p in pages:
        old=p.read_text(encoding='utf-8')
        try:
            new=update(p,old)
            assert protected(new)==protected(old),'Protected content changed'
            assert update(p,new)==new,'Not idempotent'
            if new!=old:pending[p]=new
        except (ValueError,AssertionError) as e:errors.append(str(e)+' '+p.name)
    if errors:raise SystemExit('\n'.join(errors))
    if '--check' in sys.argv:assert not pending,len(pending)
    else:
        for p,s in pending.items():p.write_text(s,encoding='utf-8')
    print(f'Model pages: {len(pages)}; updated: {len(pending)}; price, URL, image and lot-card safeguards passed')
if __name__=='__main__':main()
