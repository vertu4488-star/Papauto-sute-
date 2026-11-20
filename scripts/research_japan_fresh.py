import requests,re,json,bs4,concurrent.futures,html
from pathlib import Path
from urllib.parse import urljoin
S='https://tokidoki.su'
models='toyota/sienta toyota/aqua toyota/roomy toyota/raize toyota/corolla toyota/yaris honda/fit honda/freed honda/vezel honda/n-box nissan/note nissan/serena nissan/kicks suzuki/solio suzuki/swift suzuki/hustler suzuki/jimny daihatsu/thor mazda/demio mazda/cx-3 mazda/mazda2 subaru/impreza'.split()
def get(u):
 r=requests.get(u,timeout=15,headers={'User-Agent':'Mozilla/5.0'});r.raise_for_status();return r.text
def links(m):
 try:
  t=get(S+'/stat/'+m+'/?page=2')
  ss=set(re.findall(r'/stat/[a-z0-9-]+/[a-z0-9-]+/[0-9a-f-]{36}/',t))
  return sorted(urljoin(S,x) for x in ss)
 except Exception as e: print('listing',m,str(e)[:100]);return []
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as p: urls=sorted(set(x for l in p.map(links,models) for x in l))
print('detail URLs',len(urls))
old=[]
for path in ['research/owner-selected-japan-lots-2026-11-14.json','research/owner-approved-50-archive-2026-11-19.json','research/owner-approved-second-50-archive-2026-11-19.json','data/gallery-lots.json']:
 old.extend(json.loads(Path(path).read_text())['lots'])
used={x.get('source_listing') for x in old};urls=[x for x in urls if x not in used]
out=Path('japan-fresh');out.mkdir(exist_ok=True)
def detail(u):
 try:
  raw=get(u);s=bs4.BeautifulSoup(raw,'html.parser');t=s.get_text(' ',strip=True)
  uuid=u.rstrip('/').split('/')[-1]
  media=list(dict.fromkeys(re.findall(r'https://japan\.storage\.yandexcloud\.net/[^"\s<>\\]+?\.avif',raw)))
  media=[x for x in media if uuid in x]
  if len(media)<3:return None
  return {'source':u,'title':s.title.get_text(strip=True) if s.title else '', 'text':t[:14000], 'urls':media}
 except Exception as e: print('detail',str(e)[:80]);return None
with concurrent.futures.ThreadPoolExecutor(max_workers=12) as p: rows=[x for x in p.map(detail,urls[:180]) if x]
print('complete detail media links',len(rows))
(out/'manifest.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
if rows:print('sample',str(rows[0])[:4500])
