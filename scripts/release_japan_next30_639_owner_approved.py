"""PapAuto: exact source-frozen 30-card Japanese gallery publication 609 -> 639.

Scope is the owner-reviewed PDF PapAuto_Japan_Another30_639_2026-11-21.pdf.
This importer intentionally handles only this batch of historical references.
Do not use it for unreviewed lots or assert a third-party commercial media license.
"""
from __future__ import annotations
from pathlib import Path
from io import BytesIO
import hashlib
import json
import re
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PREVIEW_PATH = ROOT / "research/papauto-japan-next30-639-owner-review-2026-11-21.json"
SOURCE_ROOT = Path("/tmp/papauto-japan639-source")
EXPECTED = {
  "b6": ("14641252098", "fe2fb3d5f95195e9fd084dc72a5ad4f349dd9f100195bf1e5c5d13bfb1c58838"),
  "w3": ("14691820564", "9bd14bac931dbacfb3fc2578cf52816ce9fd5a2b6c666d04eff9ec42c01ebdc2"),
}
PREVIOUS = [
 "owner-selected-japan-lots-2026-11-14.json",
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
 "owner-approved-japan-followup30-2026-11-21.json",
 "owner-approved-japan-next30-519-2026-11-21.json",
 "owner-approved-japan-next30-549-2026-11-21.json",
 "owner-approved-japan-next30-579-2026-11-21.json",
 "owner-approved-japan-next30-609-2026-11-21.json",
]
SHA_PDF = "2d814fb54e9acced643bcba53b61094bee4256eb4576c6dedd590c9ca65ddc76"
SHA_ZIP = "fa60be07638523672d19c41eb68f16fd91e3fcd1488870544b8c3b1337d20c47"
SHA_JSON = "72c556bd4a87df47926925be695777945fad8a56d9c031d7e0db1dfb8886de63"
SHA_JPEG_SEQUENCE = "fedd01f9183b25bddbd40414f9766ee273021e05b29ccb93a01b11b1fedac458"

def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def digest(data):
    return hashlib.sha256(data).hexdigest()

def norm(value):
    return re.sub("[^a-z0-9]", "", str(value or "").lower())

def lot_key(row):
    return "|".join((norm(row["auction"]),
                     str(row.get("auction_date") or row.get("date") or "")[:10],
                     str(row.get("lot") or row.get("lot_number") or "").lstrip("0")))

def replace_once(path, before, after):
    path = ROOT / path
    text = path.read_text(encoding="utf-8")
    assert text.count(before) == 1, ("expected exact unique patch anchor", path, before, text.count(before))
    path.write_text(text.replace(before, after, 1), encoding="utf-8")

review = load(PREVIEW_PATH)
assert review["status"] == "OWNER_APPROVED_FOR_EXACT_639_RELEASE"
assert review["owner_approval"]["approved"] is True
assert review["owner_approval"]["pdf_sha256"] == SHA_PDF
assert review["owner_approval"]["media_zip_sha256"] == SHA_ZIP
assert review["owner_approval"]["full_review_json_sha256"] == SHA_JSON
assert review["files"]["review_pdf"]["sha256"] == SHA_PDF
assert review["files"]["original_media_zip"]["sha256"] == SHA_ZIP
assert review["files"]["full_review_json"]["sha256"] == SHA_JSON
assert review["number_of_lots"] == 30 and review["main_gallery_count_at_review"] == 609
assert review["original_media_aggregate_sha256"] == SHA_JPEG_SEQUENCE
assert review["target_after_owner_approval"] == 639
assert len(review["selection"]) == 30
assert not review["published"]
for name,(artifact_id,expected_sha) in EXPECTED.items():
    actual = review["source_archives"][name]
    assert actual["artifact_id"] == int(artifact_id)
    assert actual["manifest_sha256"] == expected_sha

prior = []
for name in PREVIOUS:
    prior.extend(load(ROOT / "research" / name)["lots"])
assert len(prior) == 577
prior_keys = [lot_key(x) for x in prior]
assert len(prior_keys) == len(set(prior_keys)), "Prior gallery manifests have duplicate auction keys"
prior_key_set = set(prior_keys)
prior_urls = {x.get("source_listing") for x in prior}
prior_hashes = {sha for x in prior for sha in x.get("media_sha256", [])}
sources = {}
for name,(artifact_id,expected_sha) in EXPECTED.items():
    root = SOURCE_ROOT / artifact_id
    raw = (root / "manifest.json").read_bytes()
    assert digest(raw) == expected_sha, ("source archive manifest changed", name)
    records = load(root / "manifest.json")
    source_by_index = {x["index"]:x for x in records}
    assert len(source_by_index) == len(records)
    sources[name] = (root,source_by_index)

seen_keys, seen_urls, used_hashes, assembled = set(),set(),[],[]
for ordinal, selected in enumerate(review["selection"],1):
    source_type,record_number = selected["source_archive"],selected["source_index"]
    assert selected["ordinal"] == ordinal and source_type in EXPECTED
    folder,by_index = sources[source_type]
    source = by_index[record_number]
    assert source["title"].lower().removesuffix(" года") == selected["title"].lower(), (ordinal,"title mismatch")
    assert lot_key(source) == selected["lot_key"] and lot_key(source) not in prior_key_set and lot_key(source) not in seen_keys, (ordinal,"duplicate auction key")
    assert source["source"] not in prior_urls and source["source"] not in seen_urls, (ordinal,"duplicate source listing")
    assert source["source"].startswith("https://atp-auto.ru/")
    assert len(source["media_urls"]) == 3 and all(x.startswith("https://7.tru.ru/imgs/") for x in source["media_urls"])
    assert len(source["files"]) == 3 and len(source["raw_sha256"]) == 3
    assert 0 < source["cc"] <= 2000 and 0 < source["hp"] <= 160
    assert source["km"] > 0 and source["price_jpy"] > 0 and float(source["grade"]) >= 3.5
    assert source["date"].startswith("2026-")
    seen_keys.add(lot_key(source))
    seen_urls.add(source["source"])
    ident = f"japan-next30-639-20261121-{ordinal:02d}"
    img_paths,sha_list = [],[]
    for i,role in enumerate(("front","rear","sheet")):
        raw = (folder / source["files"][i]).read_bytes()
        actual_sha = digest(raw)
        assert actual_sha not in prior_hashes and actual_sha not in used_hashes, (ordinal,"duplicate JPEG")
        assert raw.startswith(b"\xff\xd8\xff") and len(raw) > 3000, (ordinal,"invalid jpeg")
        with Image.open(BytesIO(raw)) as image:
            assert image.format == "JPEG"
            assert min(image.size) >= (700 if role == "sheet" else 180)
            image.verify()
        dest = ROOT / f"assets/auction/approved/{ident}-{role}.jpg"
        assert not dest.exists(), ("cannot overwrite media",dest)
        dest.write_bytes(raw)
        img_paths.append("/" + dest.relative_to(ROOT).as_posix())
        sha_list.append(actual_sha)
        used_hashes.append(actual_sha)
    head = re.fullmatch(r"(.+?) (20\d\d) года",source["title"])
    assert head and int(head.group(2)) == source["year"],(ordinal,"model/year")
    make,model = head.group(1).split(" ",1)
    trim = str(source.get("trim") or "не указана")
    if "<" in trim or any(ord(ch) > 127 for ch in trim):
        trim = "не указана"
    desc = (f"{make} {model}, {source['year']} года, кузов {source['body']}, комплектация: {trim}. "
            f"Двигатель {source['cc']} см³, мощность {source['hp']} л.с. по данным источника. "
            f"Пробег по статистике источника (округлённый): {source['km']} км, оценка {source['grade']}, "
            f"аукцион {source['auction']}, дата {source['date']}, лот №{source['lot']}. "
            "Автомобиль не в наличии: историческая статистика аукционных продаж Японии. "
            "Цена аукциона не включает доставку, таможенные платежи и оформление.")
    assembled.append(dict(
        id=ident,country="japan",make=make,model=model,year=source["year"],
        mileage_km=source["km"],body=source["body"],grade=source["grade"],
        auction=source["auction"],lot=str(source["lot"]),auction_date=source["date"],
        description=desc,photo_context="original_auction_lot",
        sheet_type="original_auction_sheet",photos=img_paths[:2],
        auction_sheet=img_paths[2],sale_status="reference_only",
        reported_price=source["price_jpy"],media_sha256=sha_list,
        source_listing=source["source"],source_media=source["media_urls"],
        raw_sha256=source["raw_sha256"],trim=trim,engine_cc=source["cc"],
        power_hp=source["hp"],rights_confirmed=False,
        artifact_record_index=record_number,artifact_id=int(EXPECTED[source_type][0])))
assert len(assembled) == 30 and len(used_hashes) == 90
assert len(set(used_hashes)) == 90
assert digest("".join(used_hashes).encode()) == SHA_JPEG_SEQUENCE, "original JPEGs differ from owner-reviewed ZIP"

receipt_path = "research/owner-approved-japan-next30-639-2026-11-21.json"
receipt = dict(approved_count=30,approval_date="2026-11-21",rights_confirmed=False,
    owner_authorized_archival_reference_only=True, reviewed_pdf_sha256=SHA_PDF,
    reviewed_jpg_zip_sha256=SHA_ZIP,reviewed_full_manifest_sha256=SHA_JSON,
    jpg_aggregate_sha256=SHA_JPEG_SEQUENCE,lots=assembled,
    note="Owner approved exactly 30 Japanese historical auction reference examples. Not in stock; commercial re-use rights not independently verified.")
p = ROOT / receipt_path
p.write_text(json.dumps(receipt,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
blob = p.read_bytes()
gitblob = hashlib.sha1(b"blob "+str(len(blob)).encode()+b"\0"+blob).hexdigest()

append = '''        # Exact owner-approved 30 Japanese archive records: 609 -> 639.
        archive16 = json.loads((ROOT / "research/owner-approved-japan-next30-639-2026-11-21.json").read_text(encoding="utf-8"))
        archived16 = archive16["lots"]
        if (archive16.get("approved_count") != 30 or archive16.get("rights_confirmed") is not False
                or archive16.get("owner_authorized_archival_reference_only") is not True
                or archive16.get("reviewed_pdf_sha256") != "2d814fb54e9acced643bcba53b61094bee4256eb4576c6dedd590c9ca65ddc76"
                or archive16.get("reviewed_jpg_zip_sha256") != "fa60be07638523672d19c41eb68f16fd91e3fcd1488870544b8c3b1337d20c47"
                or [r["id"] for r in archived16] != [f"japan-next30-639-20261121-{i:02d}" for i in range(1,31)]
                or any(len(r["photos"]) != 2 or r.get("rights_confirmed") is not False for r in archived16)):
            raise RuntimeError("PAPAUTO_APPROVAL_REQUIRED: 639 immutable PDF/ZIP or source mismatch")
        hashes16 = [h for r in archived16 for h in r["media_sha256"]]
        if (len(hashes16) != 90 or len(set(hashes16 + hashes15 + hashes14 + hashes13 + hashes12 + hashes11 + hashes10 + hashes9 + hashes8 + hashes7 + hashes6 + hashes5 + hashes4 + hashes3 + hashes2 + hashes + media_hashes)) != 1715
                or hashlib.sha256("".join(hashes16).encode()).hexdigest() != "fedd01f9183b25bddbd40414f9766ee273021e05b29ccb93a01b11b1fedac458"):
            raise RuntimeError("PAPAUTO_POLICY: 639 image/sheet originals tampered or reused")
        for rec in archived16:
            card = prepare_approved(target, rec, owner_selected=True)
            card.update(trim=rec["trim"], engine_cc=rec["engine_cc"], power_hp=rec["power_hp"],
                        sale_label="Статистика продаж", rights_confirmed=False)
            additional.append(card)
'''

replace_once("scripts/compile_auction_gallery.py","    seen_lot_keys = {",append+"    seen_lot_keys = {")
replace_once("scripts/verify_publication_approval.py","FROZEN_SOURCE_BLOBS = {",
             'FROZEN_SOURCE_BLOBS = {\n    "'+receipt_path+'": "'+gitblob+'",')
old_list='    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"] + archive12["lots"] + archive13["lots"] + archive14["lots"] + archive15["lots"]}'
new_list='    archive16 = json.loads((ROOT / "research/owner-approved-japan-next30-639-2026-11-21.json").read_text(encoding="utf-8"))\n    approved_archive = {r["id"] for r in archive["lots"] + archive2["lots"] + archive3["lots"] + archive4["lots"] + archive5["lots"] + archive6["lots"] + archive7["lots"] + archive8["lots"] + archive9["lots"] + archive10["lots"] + archive11["lots"] + archive12["lots"] + archive13["lots"] + archive14["lots"] + archive15["lots"] + archive16["lots"]}'
replace_once("scripts/verify_publication_approval.py",old_list,new_list)
replace_once("scripts/verify_publication_approval.py",
             "len(rows) != 609 or len(approved_archive) != 477",
             "len(rows) != 639 or len(approved_archive) != 507")
replace_once("scripts/build_static_public.py",
             'gallery_result["count"] != 609 or gallery_result["new"] != 574',
             'gallery_result["count"] != 639 or gallery_result["new"] != 604')
replace_once("scripts/build_static_public.py","published_lot_count != 609","published_lot_count != 639")
index=ROOT/"scripts/publish_lot_search.py"
index_string=index.read_text(encoding="utf-8")
assert index_string.count("609") == 3, ("unexpected published index count",index_string.count("609"))
index.write_text(index_string.replace("609","639"),encoding="utf-8")
replace_once("tests/test_site_warm_theme.py",
             'self.assertEqual(lots["lot_count"],609)',
             'self.assertEqual(lots["lot_count"],639)')
replace_once("tests/test_auction_only_images_policy.py",
             'self.assertEqual(pub["lot_count"], 609)',
             'self.assertEqual(pub["lot_count"], 639)')
for file in ("AGENTS.md","docs/AUCTION_ONLY_GALLERY.md"):
    path=ROOT/file
    path.write_text(path.read_text(encoding="utf-8").rstrip()+
       "\n\nOwner expressly approved on 2026-11-21 exactly 30 full-sheet Japanese historic auction records in PapAuto_Japan_Another30_639_2026-11-21.pdf. New immutable receipt: "+receipt_path+". Exactly 90 JPEGs, 30 source auction lots; no street/dealer photos; no external card links, stock claims or third-party rights assertion. This is not blanket permission for any other batch.\n",encoding="utf-8")
print("PAPAUTO_639_RELEASE_PREPARED: 30 uniquely sourced historical lots, 90 exact reviewed JPEGs, 609 -> 639; strict release policy preserved")
