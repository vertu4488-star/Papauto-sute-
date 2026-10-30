"""On-demand parser for publicly displayed TTPAI used-car transaction summaries.

These are marketplace transactions by city, not wholesale auction-lot results.
"""
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
import httpx


class _VisibleText(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []

    def handle_data(self, data):
        value = " ".join((data or "").split())
        if value:
            self.parts.append(value)


# Only pages whose URLs and displayed transaction summaries have been checked.
_MODELS = {
    ("tesla", "model 3"): ("Tesla Model 3", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-model3"),
    ("tesla", "model3"): ("Tesla Model 3", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-model3"),
    ("tesla", "model y"): ("Tesla Model Y", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-modely"),
    ("tesla", "modely"): ("Tesla Model Y", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-modely"),
    ("tesla", "model x"): ("Tesla Model X", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-modelx"),
    ("tesla", "modelx"): ("Tesla Model X", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-modelx"),
    ("tesla", "model s"): ("Tesla Model S", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-models"),
    ("tesla", "models"): ("Tesla Model S", "Shanghai", "https://www.ttpai.cn/shanghai/price/tesila-models"),
    ("volkswagen", "polo"): ("Volkswagen Polo", "Shanghai", "https://www.ttpai.cn/shanghai/price/dazhong-polo"),
    ("vw", "polo"): ("Volkswagen Polo", "Shanghai", "https://www.ttpai.cn/shanghai/price/dazhong-polo"),
    ("大众", "polo"): ("Volkswagen Polo", "Shanghai", "https://www.ttpai.cn/shanghai/price/dazhong-polo"),
    ("фольксваген", "поло"): ("Volkswagen Polo", "Shanghai", "https://www.ttpai.cn/shanghai/price/dazhong-polo"),
    ("byd", "song plus"): ("BYD Song Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-songplusxinnengyuan"),
    ("byd", "songplus"): ("BYD Song Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-songplusxinnengyuan"),
    ("byd", "song plus new energy"): ("BYD Song Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-songplusxinnengyuan"),
    ("比亚迪", "宋plus"): ("BYD Song Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-songplusxinnengyuan"),
    ("byd", "qin plus"): ("BYD Qin Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-qinplus"),
    ("byd", "qinplus"): ("BYD Qin Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-qinplus"),
    ("比亚迪", "秦plus"): ("BYD Qin Plus", "Shenzhen", "https://www.ttpai.cn/shenzhen/price/biyadi-qinplus"),
    ("zeekr", "x"): ("Zeekr X", "Shanghai", "https://www.ttpai.cn/shanghai/price/jike-jikex"),
    ("极氪", "x"): ("Zeekr X", "Shanghai", "https://www.ttpai.cn/shanghai/price/jike-jikex"),
}


def _norm(value):
    return re.sub(r"\\s+", " ", (value or "").strip().casefold())


async def fetch_ttpai_model_stats(make, model):
    info = _MODELS.get((_norm(make), _norm(model)))
    if not info:
        return None
    display_name, city, url = info
    try:
        async with httpx.AsyncClient(timeout=18.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    "User-Agent": "Mozilla/5.0 (compatible; PAPAUTO-Statistics/1.0; +https://papauto.ru)",
                    "Accept": "text/html,application/xhtml+xml",
                    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.7",
                },
            )
        response.raise_for_status()
        parser = _VisibleText()
        parser.feed(response.text)
        page_text = re.sub(r"\\s+", " ", " ".join(parser.parts))

        averages = {}
        for age in (3, 5, 7):
            match = re.search(
                rf"{age}\\s*年车龄\\s*市场均价\\s*([0-9]+(?:\\.[0-9]+)?)\\s*万",
                page_text,
            )
            averages[f"age_{age}_avg_cny"] = round(float(match.group(1)) * 10000) if match else None

        recent_sales = []
        for match in re.finditer(
            r"最新成交\\s*(.{0,220}?)\\s*(20\\d{2}\\.\\d{2}\\.\\d{2})成交",
            page_text,
        ):
            recent_sales.append({
                "description": re.sub(r"\\s+", " ", match.group(1)).strip(" /／·")[:220],
                "date": match.group(2),
            })
            if len(recent_sales) >= 8:
                break

        count_match = re.search(r"已找到\\s*(\\d+)\\s*条历史成交", page_text)
        transaction_count = int(count_match.group(1)) if count_match else None
        if not any(value is not None for value in averages.values()) and not recent_sales and transaction_count is None:
            return {
                "ok": False,
                "source": "TTPAI",
                "source_url": url,
                "message": "Страница TTPAI открылась, но распознаваемые показатели сделок не найдены.",
            }

        return {
            "ok": True,
            "country": "china",
            "data_type": "china_model_live",
            "source": "TTPAI · история сделок подержанных автомобилей",
            "model": display_name,
            "city": city,
            "currency": "CNY",
            "averages": averages,
            "recent_sales": recent_sales,
            "transaction_count": transaction_count,
            "source_url": url,
            "retrieved_at": datetime.now(timezone.utc).isoformat(),
            "disclaimer": (
                f"Данные TTPAI по городу {city}: история сделок на китайском рынке подержанных автомобилей, "
                "не полный архив оптовых аукционов. Средние по возрасту — ориентир сервиса, а не цена конкретного лота. "
                "Доставка, экспорт, таможня и оформление в РФ не включены."
            ),
        }
    except (httpx.HTTPError, ValueError, TypeError):
        return {
            "ok": False,
            "source": "TTPAI",
            "source_url": url,
            "message": "Не удалось обновить открытую статистику TTPAI. Старые примеры не подставляются вместо свежих данных.",
        }
