import json,re,collections,pathlib
P=pathlib.Path
sample=json.loads(P('research/drom-novosibirsk-991-no-rf-2026-11-13.json').read_text())['listings_sample']
j=json.loads(P('data/gallery-lots.json').read_text())['lots']
for path in P('research').glob('owner-approved-japan*archive*.json'):
 j+=json.loads(path.read_text()).get('lots',[])
j+=json.loads(P('research/owner-approved-japan-drom991-14-2026-11-21.json').read_text())['lots']
china=[]
for path in P('research').glob('owner-approved-china-supplier-*.json'):
 china+=json.loads(path.read_text()).get('records',[])
def norm(s):return re.sub(r'[^a-z0-9]','',str(s).lower())
def ident(x):return norm(x.get('make','')+' '+x.get('model',''))
by=collections.defaultdict(list)
for x in j:by[(ident(x),int(x.get('year') or 0))].append(x)
rows=[]
for x in sample:
 key=(norm(x['model']),int(x['year']))
 matches=by.get(key,[])
 rows.append({'model':x['model'],'year':x['year'],'drom_mileage_km':x.get('mileage_km'),'papauto_same_model_year_count':len(matches),'papauto_mileages_km':[a.get('mileage_km') for a in matches],'papauto_colors':[a.get('color') for a in matches if a.get('color')],'priority':'missing' if not matches else ('single' if len(matches)==1 else 'variety')})
out=P('drom991-30x30-review');out.mkdir(exist_ok=True)
(out/'coverage.json').write_text(json.dumps({'drom_total_displayed':991,'drom_rows_actually_inspected':len(sample),'japan_lot_records_scanned':len(j),'china_supplier_records_scanned':len(china),'rows':rows},ensure_ascii=False,indent=2))
print('Drom sample:',len(sample),'Japan records:',len(j),'China records:',len(china))
print('Missing model-years:',sum(x['priority']=='missing' for x in rows),'Single:',sum(x['priority']=='single' for x in rows))
print('Top gaps:',[(x['model'],x['year']) for x in rows if x['priority']=='missing'][:30])
