"""Bundle the complete pinned MIT SurveyJS Form Library for same-origin delivery.

The package is fetched only at build time. Browsers never load third-party code
or submit customer details to SurveyJS, unpkg, or jsDelivr.
"""
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError
import re

VERSION = "3.2.4"
ASSETS = {
    "survey.core.min.js": ("survey-core", 1_000_000),
    "survey-core.min.css": ("survey-core", 250_000),
    "survey-js-ui.min.js": ("survey-js-ui", 80_000),
    "survey.i18n.min.js": ("survey-core", 200_000),
}
MIRRORS = (
    "https://unpkg.com",
    "https://cdn.jsdelivr.net/npm",
)


def fetch_surveyjs(output: Path) -> None:
    destination = output / "vendor" / "surveyjs"
    destination.mkdir(parents=True, exist_ok=True)
    for filename, (package, minimum_size) in ASSETS.items():
        last_error = None
        for mirror in MIRRORS:
            url = f"{mirror}/{package}@{VERSION}/{filename}"
            try:
                request = Request(url, headers={"User-Agent": "PapAuto-static-build/1.0"})
                with urlopen(request, timeout=35) as response:
                    if response.status != 200:
                        raise RuntimeError(f"HTTP {response.status}")
                    data = response.read(5_000_000)
                if len(data) < minimum_size or b"surveyjs" not in data[:1000].lower():
                    raise RuntimeError("Unexpected vendor package contents")
                (destination / filename).write_bytes(data)
                print(f"Vendored SurveyJS {VERSION}: {filename} ({len(data)} bytes)")
                break
            except (URLError, TimeoutError, OSError, RuntimeError) as error:
                last_error = type(error).__name__
        else:
            raise RuntimeError(f"Failed to obtain pinned SurveyJS {filename}: {last_error}")
