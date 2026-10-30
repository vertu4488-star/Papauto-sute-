"""Public monthly auction statistics from the Korean national auction association."""
import re
from datetime import datetime, timezone
from html.parser import HTMLParser

import httpx

SOURCE_URL = "https://www.aaa-korea.com/en/data"


class _Text(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        value = " ".join((data or "").split())
        if value:
            self.parts.append(value)


def parse_korea_monthly(text):
    # The association publishes year, month, offered units, successful bids and rate.
    pattern = re.compile(
        r"(20\d{2})\s*년\s*(\d{1,2})\s*월\s*"
        r"([\d,]+)\s*([\d,]+)\s*(\d{1,3})\s*%"
    )
    rows = []
    seen = set()
    for year, month, offered, sold, rate in pattern.findall(text):
        key = (int(year), int(month))
        if key in seen or not 1 <= key[1] <= 12:
            continue
        seen.add(key)
        rows.append({
            "year": key[0],
            "month_number": key[1],
            "month": f"{key[0]}-{key[1]:02d}",
            "offered": int(offered.replace(",", "")),
            "sold": int(sold.replace(",", "")),
            "completion_rate_percent": int(rate),
        })
    rows.sort(key=lambda item: (item["year"], item["month_number"]))
    return rows


async def fetch_korea_monthly_stats():
    try:
        async with httpx.AsyncClient(timeout=18.0, follow_redirects=True) as client:
            response = await client.get(
                SOURCE_URL,
                headers={"User-Agent": "Mozilla/5.0 (compatible; PAPAUTO-Statistics/1.0; +https://papauto.ru)"},
            )
            response.raise_for_status()
        parser = _Text()
        parser.feed(response.text)
        rows = parse_korea_monthly(" ".join(parser.parts))
        if not rows:
            return {
                "ok": False, "country": "south-korea", "source": "Korea Automobile Auction Association",
                "source_url": SOURCE_URL, "message": "Страница открылась, но формат месячной таблицы изменился.",
            }
        return {
            "ok": True, "country": "south-korea", "data_type": "monthly_auction_statistics",
            "source": "Korea Automobile Auction Association",
            "source_url": SOURCE_URL, "currency": None,
            "history": rows[-6:], "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "definition": "Выставлено на автомобильные аукционы Кореи / завершённые продажи (낙찰).",
            "disclaimer": "Официальная месячная агрегированная статистика ассоциации. Это количество торговых единиц по рынку, а не карточки отдельных автомобилей и не цены конкретных лотов.",
        }
    except (httpx.HTTPError, ValueError, TypeError) as exc:
        return {
            "ok": False, "country": "south-korea", "source": "Korea Automobile Auction Association",
            "source_url": SOURCE_URL, "message": f"Не удалось обновить открытую статистику: {type(exc).__name__}.",
        }
