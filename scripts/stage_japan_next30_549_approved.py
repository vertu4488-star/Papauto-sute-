"""Stage exactly owner-approved 30 Japanese auction source lots for later sequential publication.

Only writes immutable media into research/ and an approval receipt. It NEVER modifies
public gallery, sitemaps, JS or currently deployed assets. Requires owner-approved 519
batch to be separately released first. Does not assert third-party commercial license.
"""
from pathlib import Path
from PIL import Image
from io import BytesIO
import json, hashlib, re

ROOT=Path(__file__).resolve().parents[1]
REVIEW=ROOT/"research/papauto-japan-next30-549-owner-review-2026-11-21.json"
PREV=ROOT/"research/papauto-japan-next30-519-owner-review-2026-11-21.json"
# Previous 519 review manifest is in another review branch until separately released.
ARCHIVES={"wave3":("14691820564","9bd14bac931dbacfb3fc2578cf52816ce9fd5a2b6c666d04eff9ec42c01ebdc2"),
          "b6":("14641252098","fe2fb3d5f95195e9fd084dc72a5ad4f349dd9f100195bf1e5c5d13bfb1c58838")}
OLD=["owner-selected-japan-lots-2026-11-14.json",
"owner-approved-50-archive-2026-11-19.json",
"owner-approved-second-50-archive-2026-11-19.json",
"owner-approved-japan-atp-30-archive-2026-11-20.json",
"owner-approved-japan-atp-second-30-archive-2026-11-20.json",
"owner-approved-japan-atp-third-30-archive-2026-11-20.json",
"owner-approved-japan-atp-fourth-30-archive-2026-11-20.json",
"owner-approved-japan-atp-fifth-30-archive-2026-11-20.json",
"owner-approved-japan-atp-sixth-30-archive-2026-11-21.json",
"owner-approved-japan-drom991-gap-17-archive-2026-11-21.json",
"owner-approved-japan-next30-2026-11-21.json",
"owner-approved-japan-followup30-2026-11-21.json"]

def read(p):return json.loads(Path(p).read_text(encoding="utf-8"))
def digest(b):return hashlib.sha256(b).hexdigest()
def norm(s):return re.sub("[^a-z0-9]","",str(s).lower())
def key(r):return "|".join((norm(r["auction"]),str(r.get("auction_date") or r.get("date") or "")[:10],str(r.get("lot") or r.get("lot_number") or "").lstrip("0")))

data=read(REVIEW)
approval=data["owner_approval"]
assert approval["approved"] and data["status"]=="OWNER_APPROVED_STAGING_PENDING_PRIOR_BATCH"
assert data["published"] is False and data["total"]==30
assert data["files"]["review_pdf"]["sha256"]=="7f1209ab57d0fa02acea28fdb33bb82d91f3c1a7027dcefb563da057265aa024"
assert data["files"]["original_media_zip"]["sha256"]=="405bb0643dc4baf67f67ff92f0e51a67e62d5b77b1e391005dbccf8e9ac33242"
assert data["files"]["full_json"]["sha256"]=="ce57eae5efc12860b259ad93bc3de15c137a91e6f2367340fb23da16e1f2f18e"
source={}
for k,(artifact_id,expected_sha) in ARCHIVES.items():
    folder=Path("/tmp/papauto-japan549-source")/artifact_id
    raw=(folder/"manifest.json").read_bytes()
    assert digest(raw)==expected_sha,("source manifest changed",k)
    source[k]=(folder,{x["index"]:x for x in json.loads(raw)})
old=[]
for name in OLD:old+=read(ROOT/"research"/name)["lots"]
assert len(old)==457
oldkeys={key(x) for x in old};oldurl={x.get("source_listing") for x in old}
oldhash={h for row in old for h in row.get("media_sha256",[])}
oldhash.update(h for row in old for h in row.get("raw_sha256",[]))
# The previous 519 batch remains a research-only review; check frozen archive row
# identifiers embedded here to ensure no archived photo or full sheet reuses.
previous_refs={("wave3",int(x)) for x in (42,64,75,35,37,66,73,71,72,70,55,52,45,7,2,54,48)}
previous_refs|={("b6",int(x)) for x in (94,22,23,83,235,80,50,221,57,34,20,208,58,96,226,241,194)}
# Read exact previous pending branch's selection when available locally;
# do not assume its approval or include its media in public output.
if PREV.is_file():
    previous_refs={(x["src"],x["index"]) for x in read(PREV)["selection"]}

selected=[];seen_keys=set();seen_refs=set();seen_urls=set();new_hash=[];new_paths=[]
out=ROOT/"research"/"japan-549-staged-media"
out.mkdir(exist_ok=True)
for i,r in enumerate(data["selection"],1):
    assert r["ordinal"]==i and (r["src"],r["index"]) not in previous_refs
    assert (r["src"],r["index"]) not in seen_refs
    folder,records=source[r["src"]]
    s=records[r["index"]]
    assert s["title"].casefold()==(r["name"]+" года").casefold(),(i,"name mismatch")
    assert key(s)==r["lot_key"],(i,"lot identity mismatch")
    assert key(s) not in oldkeys and key(s) not in seen_keys
    assert s["source"] not in oldurl and s["source"] not in seen_urls
    assert 0<s["hp"]<=160 and 0<s["cc"]<=2000 and s["km"]>0 and s["price_jpy"]>0
    assert float(s["grade"])>=3.5 and len(s["files"])==3 and len(s["raw_sha256"])==3
    assert s["source"].startswith("https://atp-auto.ru/") and all(str(u).startswith("https://7.tru.ru/imgs/") for u in s["media_urls"])
    seen_refs.add((r["src"],r["index"]));seen_keys.add(key(s));seen_urls.add(s["source"])
    names=[];hashes=[]
    for j,typ in enumerate(("front","rear","sheet")):
        original=(folder/s["files"][j]).read_bytes()
        actual=digest(original)
        # Frozen source artifact files from previous approval PDF.
        assert actual not in oldhash and actual not in new_hash
        assert original[:3]==b"\xff\xd8\xff"
        assert len(original)>3000
        with Image.open(BytesIO(original)) as im:
            assert im.format=="JPEG"
            assert min(im.size)>=(700 if typ=="sheet" else 180)
            im.verify()
        dest=out/f"japan-549-20261121-{i:02d}-{typ}.jpg"
        assert not dest.exists(),f"Cannot overwrite staged original {dest}"
        dest.write_bytes(original)
        new_hash.append(actual);hashes.append(actual);names.append(str(dest.relative_to(ROOT)))
        new_paths.append(dest)
    selected.append({
      "ordinal":i,"id":f"japan-next30-549-20261121-{i:02d}",
      "country":"japan","make":s["title"].split()[0],
      "model":" ".join(s["title"].split()[1:-2]).title(),"year":s["year"],
      "body":s["body"],"trim":s.get("trim"),
      "engine_cc":s["cc"],"power_hp":s["hp"],"mileage_km":s["km"],
      "auction":s["auction"],"auction_date":s["date"],"lot":str(s["lot"]),
      "grade":s["grade"],"reported_price":s["price_jpy"],
      "source_listing":s["source"],"source_media":s["media_urls"],
      "artifact_id":int(ARCHIVES[r["src"]][0]),"artifact_record_index":r["index"],
      "staged_photos":names[:2],"staged_auction_sheet":names[2],
      "staged_media_sha256":hashes,"raw_source_sha256":s["raw_sha256"],
      "rights_confirmed":False,"status":"reference_only","published":False
    })
assert len(selected)==30 and len(seen_keys)==30 and len(new_hash)==90 and len(set(new_hash))==90
assert digest("".join(new_hash).encode())=="14335eb0d5d9ec636a49ee0d9001f595bebf32ef18b060ebcce69a45e9e3589f","owner-reviewed original media does not match"
receipt={"owner_approval_date":"2026-11-21","owner_approved_count":30,"media_count":90,
 "status":"OWNER_APPROVED_STAGED_PENDING_519_RELEASE","published":False,
 "source_review_pdf_sha256":data["files"]["review_pdf"]["sha256"],
 "source_review_zip_sha256":data["files"]["original_media_zip"]["sha256"],
 "source_full_review_json_sha256":data["files"]["full_json"]["sha256"],
 "staged_media_aggregate_sha256":digest("".join(new_hash).encode()),
 "commercial_media_rights_confirmed":False,
 "note":"User approved exact 549 PDF, ordered publication after unapproved preceding 519 batch. This is a staged historical reference only. Nothing is added to public gallery until sequence can be honored.",
 "lots":selected}
target=ROOT/"research"/"owner-approved-japan-next30-549-staged-2026-11-21.json"
target.write_text(json.dumps(receipt,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
assert all(p.is_file() and p.stat().st_size>3000 for p in new_paths)
print("PAPAUTO_JAPAN_549_MEDIA_STAGE_OK: 30 exact-source lots, 90 verified original files, no previous IDs; public gallery unchanged")
