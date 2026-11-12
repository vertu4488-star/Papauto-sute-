"""Import original Korean listing photos for three verified PapAuto reference cars.

Run explicitly under the GitHub workflow. Restricts sources to exact allowlisted
Autowini CDN URLs and validates that downloaded bytes are real photographs.
Provenance remains attached to the manifest; images are not auction sheets.
"""
from pathlib import Path
import io, json, urllib.request, urllib.parse
from PIL import Image, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
manifest = json.loads((ROOT/"research/premium-korea-media-sources-2026-11-12.json").read_text(encoding="utf-8"))
outputs = []
for record in manifest["records"]:
    assert record["id"] in {"bmw-x1-kr-IC5605199","bmw-x3-kr-IC5604396","audi-q3sb-kr-IC5486298"}
    assert len(record["image_urls"]) == len(record["local_paths"]) == 3
    for url, local in zip(record["image_urls"],record["local_paths"]):
        parsed = urllib.parse.urlsplit(url)
        if parsed.scheme != "https" or parsed.hostname != "imagebox.autowini.com" or not parsed.path.startswith("/upload/"):
            raise ValueError("Source is not the pre-verified Autowini image CDN: " + url)
        if not local.startswith("/assets/premium-auctions/") or not local.endswith(".webp"):
            raise ValueError("Refusing unsafe output path: "+local)
        dst = ROOT/local.lstrip("/")
        dst.parent.mkdir(parents=True,exist_ok=True)
        if dst.is_file() and dst.stat().st_size>5000:
            outputs.append(str(dst.relative_to(ROOT)))
            continue
        request=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; PapAutoMediaArchive/1.0)","Referer":"https://www.autowini.com/"})
        with urllib.request.urlopen(request,timeout=25) as resp:
            data=resp.read(8_000_001)
            if len(data)>8_000_000: raise ValueError("Too-large image: "+url)
        try:
            with Image.open(io.BytesIO(data)) as img:
                img.verify()
            with Image.open(io.BytesIO(data)) as img:
                if min(img.size)<100: raise ValueError("Unexpected image dimensions: "+url+" "+str(img.size))
                print("Validated",record["id"],img.size,url.rsplit("/",1)[-1])
                img.convert("RGB").save(dst,"WEBP",quality=82,method=5)
        except (UnidentifiedImageError,OSError) as exc:
            raise ValueError("Invalid source image "+url) from exc
        outputs.append(str(dst.relative_to(ROOT)))
print("Imported "+str(len(outputs))+" original listing photos:\n" + "\n".join(outputs))
