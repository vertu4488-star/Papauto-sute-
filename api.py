import os
import base64
import logging
import html
import asyncio
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import quote
from datetime import datetime, timezone
from typing import Optional

import httpx
from china_stats import fetch_ttpai_model_stats
from korea_auction_stats import fetch_korea_monthly_stats
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("papauto.api")
logger.info("XAPI Korea key present in Render environment: %s", bool((os.getenv("XAPIKOREA_API_KEY") or "").strip()))

app = FastAPI(title="PAPAUTO Lead API", version="1.0.0")

# Public API called by the PAPAUTO website and its browser voice recorder.
# Credentials are not used, so wildcard CORS avoids Safari preflight failures
# when the site is opened through www/non-www or an alternate HTTPS entry point.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Type"],
    max_age=600,
)

@app.middleware("http")
async def ensure_json_utf8(request, call_next):
    response = await call_next(request)
    if response.headers.get("content-type", "").startswith("application/json"):
        response.headers["content-type"] = "application/json; charset=utf-8"
    return response


def _fix_mojibake(value):
    """Repair common UTF-8 text that was mistakenly decoded as Windows-1251."""
    if not isinstance(value, str):
        return value
    markers = ("Рќ", "Р°", "Рµ", "Рѕ", "Рё", "РІ", "Рї", "Р»", "РЅ", "С‚", "СЏ", "в‚", "Рє")
    if not any(marker in value for marker in markers):
        return value
    original_score = sum(value.count(marker) for marker in markers)
    for encoding in ("cp1251", "cp1252"):
        try:
            candidate = value.encode(encoding).decode("utf-8")
        except (UnicodeEncodeError, UnicodeDecodeError):
            continue
        candidate_score = sum(candidate.count(marker) for marker in markers)
        if candidate_score < original_score:
            value = candidate
            original_score = candidate_score
            if original_score == 0:
                break
    return value


def _https_photo_urls(value):
    """Keep only absolute HTTPS image URLs supplied by the upstream provider."""
    if not isinstance(value, list):
        return []
    return [url for url in value if isinstance(url, str) and url.startswith("https://") and len(url) <= 2048]


def _canonical_korea_listing_url(source, listing_id, candidate):
    """Only expose source URLs that match the marketplace; build canonical Encar URLs."""
    from urllib.parse import urlparse
    source = str(source or "encar").lower()
    if source == "encar":
        if listing_id is not None and str(listing_id).isdigit():
            return f"https://fem.encar.com/cars/detail/{listing_id}"
        candidate = candidate if isinstance(candidate, str) else ""
        parsed = urlparse(candidate)
        if parsed.scheme == "https" and parsed.hostname in {"fem.encar.com", "www.encar.com", "encar.com"}:
            return candidate
        return None
    if not isinstance(candidate, str):
        return None
    parsed = urlparse(candidate)
    if parsed.scheme != "https" or not parsed.hostname:
        return None
    host = parsed.hostname.lower()
    allowed = {
        "kbchachacha": {"kbchachacha.com", "www.kbchachacha.com"},
        "kcar": {"kcar.com", "www.kcar.com"},
    }
    domains = allowed.get(source)
    if domains and host in domains:
        return candidate
    return None


async def _xapi_photo_urls(client, listing_id, api_key):
    """Load photo URLs from the documented detail endpoint for Encar listings."""
    if listing_id is None:
        return []
    safe_id = quote(str(listing_id), safe="")
    try:
        response = await client.get(
            f"https://api.xapikorea.com/v1/cars/{safe_id}",
            params={"lang": "en"},
            headers={"X-API-Key": api_key, "Accept": "application/json"},
        )
        if response.status_code != 200:
            return []
        payload = response.json()
        if not isinstance(payload, dict):
            return []
        photos = payload.get("photos")
        if isinstance(photos, list):
            return [p for p in photos if isinstance(p, str) and p.startswith("https://")]
        single = payload.get("thumbnail") or payload.get("thumbnail_url")
        return [single] if isinstance(single, str) and single.startswith("https://") else []
    except (httpx.RequestError, ValueError, TypeError):
        return []


class Lead(BaseModel):
    name: str = Field(default="", max_length=100)
    contact: str = Field(min_length=3, max_length=120)
    country: str = Field(default="Не указано", max_length=80)
    budget: Optional[int] = Field(default=None, ge=0, le=2_000_000_000)
    city: str = Field(default="Новосибирск", max_length=80)
    request: str = Field(min_length=5, max_length=4000)
    consent: bool = True

    @field_validator("contact", "request")
    @classmethod
    def trim_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Поле не должно быть пустым")
        return value

@app.get("/")
async def root():
    return {"service": "PAPAUTO Lead API", "status": "ok"}

@app.get("/api/exchange-rates")
async def exchange_rates():
    """Return official CBR rates for KRW, JPY, CNY and USD in RUB."""
    url = "https://www.cbr.ru/scripts/XML_daily.asp"
    try:
        async with httpx.AsyncClient(timeout=8.0, follow_redirects=True) as client:
            response = await client.get(url, headers={"Accept": "application/xml"})
            response.raise_for_status()
        root = ET.fromstring(response.content)
        rates = {}
        for item in root.findall("Valute"):
            code = item.findtext("CharCode")
            try:
                nominal = float(item.findtext("Nominal", "1").replace(",", "."))
                value = float(item.findtext("Value", "0").replace(",", "."))
            except (TypeError, ValueError):
                continue
            if code in {"KRW", "JPY", "CNY", "USD"} and nominal > 0 and value > 0:
                rates[code] = value / nominal
        if any(code not in rates for code in ("KRW", "JPY", "CNY", "USD")):
            raise ValueError("CBR response is missing required currencies")
        return {
            "source": "Банк России",
            "date": root.attrib.get("Date", ""),
            "rub_per_1000_krw": round(rates["KRW"] * 1000, 6),
            "rub_per_jpy": round(rates["JPY"], 8),
            "rub_per_cny": round(rates["CNY"], 8),
            "rub_per_usd": round(rates["USD"], 6),
            "usd_per_1000_krw": round(rates["KRW"] * 1000 / rates["USD"], 8),
            "usd_per_jpy": round(rates["JPY"] / rates["USD"], 8),
            "usd_per_cny": round(rates["CNY"] / rates["USD"], 8),
            "fallback": False,
        }
    except (httpx.HTTPError, ET.ParseError, ValueError, TypeError) as exc:
        logger.warning("Could not fetch CBR exchange rates: %s", exc)
        # Saved official CBR reference values dated 29.10.2026, clearly marked as fallback.
        usd = 80.8664
        jpy = 51.2331 / 100
        cny = 12.0816
        krw1000 = 61.0635
        return {
            "source": "Банк России (последний сохранённый ориентир)",
            "date": "29.10.2026",
            "rub_per_1000_krw": krw1000,
            "rub_per_jpy": jpy,
            "rub_per_cny": cny,
            "rub_per_usd": usd,
            "usd_per_1000_krw": round(krw1000 / usd, 8),
            "usd_per_jpy": round(jpy / usd, 8),
            "usd_per_cny": round(cny / usd, 8),
            "fallback": True,
        }


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "ai_configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "tks_configured": bool(os.getenv("TKS_AUTO_API_KEY") or os.getenv("TKS_API_KEY")),
        "xapi_korea_configured": bool((os.getenv("XAPIKOREA_API_KEY") or "").strip()),
        "auction_provider_configured": bool(os.getenv("AUCTIONS_API_URL") and os.getenv("AUCTIONS_API_KEY")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/api/leads")
async def create_lead(lead: Lead):
    if not lead.consent:
        raise HTTPException(status_code=400, detail="Необходимо согласие на обработку данных.")
    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    supabase_key = (os.getenv("SUPABASE_PUBLISHABLE_KEY") or "").strip()
    if not supabase_url or not supabase_key:
        raise HTTPException(status_code=503, detail="Хранилище заявок временно не настроено.")
    record = {
        "name": lead.name,
        "contact": lead.contact,
        "country": lead.country,
        "budget": lead.budget,
        "city": lead.city,
        "request": lead.request,
        "consent": True
    }
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            stored = await client.post(
                f"{supabase_url}/rest/v1/leads",
                headers={"apikey": supabase_key, "Authorization": f"Bearer {supabase_key}", "Content-Type": "application/json", "Prefer": "return=minimal"},
                json=record
            )
        if stored.status_code not in (200, 201, 204):
            logger.error("Supabase lead insert failed: status=%s body=%s", stored.status_code, stored.text[:500])
            raise HTTPException(status_code=502, detail="Не удалось сохранить заявку. Попробуйте позже.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Не удалось связаться с базой заявок. Попробуйте позже.")

    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    notified = False
    if token and chat_id:
        message = (
            "🚘 <b>Новая заявка PAPAUTO</b>\\n"
            f"<b>Время:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\\n"
            f"<b>Имя:</b> {html.escape(lead.name or 'не указано')}\\n"
            f"<b>Контакт:</b> {html.escape(lead.contact)}\\n"
            f"<b>Направление:</b> {html.escape(lead.country)}\\n"
            f"<b>Бюджет:</b> {f'{lead.budget:,}'.replace(',', ' ' ) + ' ₽' if lead.budget is not None else 'не указан'}\\n"
            f"<b>Город:</b> {html.escape(lead.city)}\\n"
            f"<b>Запрос:</b> {html.escape(lead.request)}"
        )
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={"chat_id": chat_id, "text": message, "parse_mode": "HTML", "disable_web_page_preview": True}
                )
            data = response.json()
            notified = response.status_code == 200 and bool(data.get("ok"))
            if not notified:
                logger.error("Telegram lead notification failed: status=%s", response.status_code)
        except (httpx.RequestError, ValueError):
            logger.exception("Telegram lead notification request failed")
    return {"ok": True, "stored": True, "notified": notified, "message": "Заявка сохранена. Менеджер свяжется с вами."}


class CustomsRequest(BaseModel):
    cost: int = Field(gt=0, le=2_000_000_000)
    volume: int = Field(ge=0, le=20000)
    power: int = Field(ge=0, le=5000)
    currency: str = Field(pattern=r"^(392|410|156|643|840)$")
    engine_type: str = Field(pattern=r"^(petrol|diesel|petrol_electric|diesel_electric|electric|no_engine)$")
    age: str = Field(pattern=r"^(3|35|57|7)$")
    face: str = Field(default="nat", pattern=r"^(nat|jur)$")
    sequential: bool = False

@app.post("/api/customs/calculate")
async def calculate_customs(req: CustomsRequest):
    key = (os.getenv("TKS_AUTO_API_KEY") or os.getenv("TKS_API_KEY") or "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Расчёт TKS.RU пока не активирован: необходим действующий лицензионный ключ TKS_AUTO_API_KEY. Ключ оформляется у TKS.RU.")
    if len(key) != 32 or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789" for ch in key):
        raise HTTPException(status_code=503, detail="Ключ TKS_AUTO_API_KEY имеет неверный формат. Ожидается 32 символа a-z и 0-9.")
    params = {
        "cost": req.cost, "volume": req.volume, "currency": req.currency,
        "power": req.power, "power_edizm": "ls", "engine_type": req.engine_type,
        "age": req.age, "face": req.face, "ts_type": "00_8703",
        "sequential": str(req.sequential).lower(), "chassis": "shs",
        "country": "noru", "forwarder": "false", "caravan": "false", "offroad": "false",
        "buscap": "lt120", "mdvs_gt_m30ed": "true",
    }
    endpoint = f"https://api1.tks.ru/auto.json/json/{key}/"
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(endpoint, params=params)
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="TKS.RU не выполнил расчёт. Проверьте лицензию и параметры автомобиля.")
        try:
            data = response.json()
        except ValueError:
            raise HTTPException(status_code=502, detail="TKS.RU вернул ответ в неизвестном формате.")
        if isinstance(data, dict) and (data.get("error") or data.get("ok") is False):
            raise HTTPException(status_code=502, detail="TKS.RU отклонил расчёт. Проверьте лицензию и параметры автомобиля.")
        return {"ok": True, "source": "TKS.RU", "calculation": data, "disclaimer": "Предварительный расчёт. Итоговые платежи определяются при таможенном оформлении."}
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Не удалось связаться с TKS.RU. Попробуйте позже.")

class VehicleAssistantInput(BaseModel):
    message: str = Field(min_length=2, max_length=2000)
    known: dict = Field(default_factory=dict)

@app.post("/api/assistant/vehicle")
async def vehicle_assistant(req: VehicleAssistantInput):
    """Extract vehicle-import parameters from natural language and calculate customs when sufficient data is known."""
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not gemini_key:
        raise HTTPException(status_code=503, detail="ИИ-помощник пока не подключён: в настройках Render нужен GEMINI_API_KEY.")
    system_instruction = (
        "Ты — помощник PAPAUTO по предварительному расчёту ввоза автомобилей в Россию. "
        "Извлекай только сообщённые пользователем данные и значения, которые можно надёжно вывести из них. "
        "Не придумывай цену, объём, мощность, валюту, тип двигателя или статус импортёра. "
        "Если пользователь назвал год выпуска, оцени категорию возраста только как предварительную: "
        "3 если меньше 3 лет, 35 если от 3 до 5 лет, 57 если от 5 до 7 лет, 7 если старше 7 лет; "
        "если возрастная категория неясна, спроси год/дату производства. "
        "Поля: cost (число в валюте покупки), currency (392 JPY, 410 KRW, 156 CNY, 840 USD, 643 RUB), "
        "volume (см3), power (л.с.), engine_type (petrol, diesel, petrol_electric, diesel_electric, electric, no_engine), "
        "age (3,35,57,7), face (nat физлицо для личного ввоза, jur юрлицо/коммерческий ввоз). "
        "Если для электромобиля объём ДВС отсутствует, volume=0; power всё равно нужна. "
        "Ответь строго JSON-объектом с полями reply (краткий русский текст), "
        "fields (объект с полями cost,currency,volume,power,engine_type,age,face; неизвестные значения null), "
        "missing (массив названий недостающих обязательных полей по-русски), ready (boolean). "
        "ready=true только если все семь параметров достоверно заполнены. "
        "Не рассчитывай таможню сам и не выдавай предположительные цифры за официальный расчёт."
    )
    prompt = {
        "instruction": system_instruction,
        "known_fields": req.known,
        "user_message": req.message,
        "required_fields": ["cost", "currency", "volume", "power", "engine_type", "age", "face"]
    }
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
                headers={"x-goog-api-key": gemini_key},
                json={
                    "contents": [{"role": "user", "parts": [{"text": __import__("json").dumps(prompt, ensure_ascii=False)}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.1}
                }
            )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="ИИ не смог обработать запрос. Проверьте ключ Gemini API и доступность модели.")
        payload = response.json()
        candidates = payload.get("candidates") or []
        parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
        raw = next((part.get("text", "") for part in parts if part.get("text")), "")
        if not raw:
            raise HTTPException(status_code=502, detail="ИИ вернул пустой ответ. Попробуйте сформулировать запрос иначе.")
        import json
        parsed = json.loads(raw)
        fields = parsed.get("fields") or {}
        allowed = {"cost", "currency", "volume", "power", "engine_type", "age", "face"}
        fields = {k: fields.get(k) for k in allowed}
        # Existing user-entered values take precedence over uncertain AI extraction.
        for key, value in (req.known or {}).items():
            if key in allowed and value not in (None, ""):
                fields[key] = value
        missing_keys = [k for k in allowed if fields.get(k) in (None, "")]
        if missing_keys:
            parsed["ready"] = False
            parsed["missing"] = parsed.get("missing") or missing_keys
            return {"ok": True, "reply": parsed.get("reply") or "Уточните недостающие характеристики автомобиля.", "fields": fields, "ready": False}
        try:
            fields["cost"] = int(float(fields["cost"]))
            fields["volume"] = int(float(fields["volume"]))
            fields["power"] = int(float(fields["power"]))
            fields["currency"] = str(fields["currency"])
            fields["age"] = str(fields["age"])
            fields["face"] = str(fields["face"])
            fields["engine_type"] = str(fields["engine_type"])
            calc_req = CustomsRequest(**fields)
        except (ValueError, TypeError, Exception) as exc:
            raise HTTPException(status_code=422, detail="Проверьте цену и характеристики автомобиля: " + str(exc)[:180])
        tks_key = (os.getenv("TKS_AUTO_API_KEY") or os.getenv("TKS_API_KEY") or "").strip()
        if not tks_key or len(tks_key) != 32 or any(ch not in "abcdefghijklmnopqrstuvwxyz0123456789" for ch in tks_key):
            return {
                "ok": True, "reply": "Характеристики собраны. Для получения суммы таможенных платежей нужно активировать лицензионный ключ TKS.RU на сервере.",
                "fields": fields, "ready": True, "calculation": None,
                "calculation_status": "tks_key_missing"
            }
        params = {
            "cost": calc_req.cost, "volume": calc_req.volume, "currency": calc_req.currency,
            "power": calc_req.power, "power_edizm": "ls", "engine_type": calc_req.engine_type,
            "age": calc_req.age, "face": calc_req.face, "ts_type": "00_8703",
            "sequential": str(calc_req.sequential).lower(), "chassis": "shs",
            "country": "noru", "forwarder": "false", "caravan": "false", "offroad": "false",
            "buscap": "lt120", "mdvs_gt_m30ed": "true",
        }
        async with httpx.AsyncClient(timeout=20.0) as client:
            tks_response = await client.get(f"https://api1.tks.ru/auto.json/json/{tks_key}/", params=params)
        if tks_response.status_code != 200:
            raise HTTPException(status_code=502, detail="Данные собраны, но TKS.RU не выполнил расчёт. Проверьте лицензию.")
        calculation = tks_response.json()
        if isinstance(calculation, dict) and (calculation.get("error") or calculation.get("ok") is False):
            raise HTTPException(status_code=502, detail="Данные собраны, но TKS.RU отклонил расчёт. Проверьте лицензию и параметры.")
        return {
            "ok": True,
            "reply": "Характеристики распознаны. Получен предварительный расчёт TKS.RU; проверьте поля и итоговые статьи перед принятием решения.",
            "fields": fields,
            "ready": True,
            "calculation": calculation,
            "source": "TKS.RU",
            "disclaimer": "Предварительный расчёт. Окончательные платежи определяются при таможенном оформлении."
        }
    except HTTPException:
        raise
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Не удалось связаться с ИИ или сервисом расчёта. Попробуйте позже.")
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="Не удалось разобрать ответ ИИ. Попробуйте указать параметры автомобиля точнее.")


def _japan_model_search_links(make: str, model: str, year_from: int, year_to: int):
    """Build user-initiated model searches on public Japanese auction/statistics sites."""
    make_value = (make or "").strip()
    model_value = (model or "").strip()
    raw_make_key = "".join(ch for ch in make_value.casefold() if ch.isalnum())
    raw_model_key = "".join(ch for ch in model_value.casefold() if ch.isalnum())
    make_aliases = {
        "тойота": "toyota", "хонда": "honda", "ниссан": "nissan",
        "мазда": "mazda", "мицубиси": "mitsubishi", "субару": "subaru",
        "сузуки": "suzuki", "лексус": "lexus"
    }
    model_aliases = {
        "приус": "prius", "рав4": "rav4", "рав": "rav4",
        "прадо": "landcruiserprado", "лендкрузерпрадо": "landcruiserprado",
        "аква": "aqua", "харриер": "harrier", "витц": "vitz",
        "ярис": "yaris", "альфард": "alphard", "королла": "corolla",
        "райз": "raize", "вокси": "voxy", "веллфайр": "vellfire",
        "ярискросс": "yariscross", "фит": "fit", "везел": "vezel",
        "фрид": "freed", "икстрейл": "xtrail", "хтрейл": "xtrail",
        "сх5": "cx5"
    }
    make_key = make_aliases.get(raw_make_key, raw_make_key)
    model_key = model_aliases.get(raw_model_key, raw_model_key)
    aleado_model_map = {
        "toyota": {
            "prius": ("PRIUS", 718), "rav4": ("RAV4", 710),
            "landcruiserprado": ("LAND-CRUISER-PRADO", 751),
            "aqua": ("AQUA", 2273), "harrier": ("HARRIER", 781),
            "landcruiser": ("LAND-CRUISER", 757), "vitz": ("VITZ", 663),
            "yaris": ("YARIS", 1692), "alphard": ("ALPHARD", 2216),
            "corolla": ("COROLLA", 827), "raize": ("RAIZE", 3320),
            "voxy": ("VOXY", 661), "vellfire": ("VELLFIRE", 1682),
            "yariscross": ("YARIS-CROSS", 3351)
        },
        "honda": {
            "fit": ("FIT", 109), "vezel": ("VEZEL", 2738),
            "freed": ("FREED", 1629)
        },
        "nissan": {"xtrail": ("X-TRAIL", 415)},
        "mazda": {"cx5": ("CX-5", 2747)}
    }
    aleado_makes = {
        "toyota": ("TOYOTA", 9), "toyotamotor": ("TOYOTA", 9),
        "honda": ("HONDA", 2), "nissan": ("NISSAN", 6),
        "mazda": ("MAZDA", 4), "mitsubishi": ("MITSUBISHI", 5),
        "subaru": ("SUBARU", 7), "suzuki": ("SUZUKI", 8),
        "lexus": ("LEXUS", 59)
    }
    if not make_key:
        for candidate in ("toyota", "honda", "nissan", "mazda"):
            if model_key in aleado_model_map.get(candidate, {}):
                make_key = candidate
                break
    model_slugs = {
        "landcruiserprado": "LAND-CRUISER-PRADO", "landcruiser": "LAND-CRUISER",
        "yariscross": "YARIS-CROSS", "xtrail": "X-TRAIL", "cx5": "CX-5"
    }
    model_slug = model_slugs.get(model_key, model_key.upper() if model_key else "")
    maker_slug = aleado_makes.get(make_key, (make_key.upper(), 0))[0]
    if make_key and model_slug:
        banzai_path = f"/en/{quote(maker_slug, safe='')}/{quote(model_slug, safe='')}"
    elif make_key:
        banzai_path = f"/en/{quote(maker_slug, safe='')}"
    else:
        banzai_path = "/en"
    banzai_url = (
        "https://banzai24.com" + banzai_path
        + f"?countryISO=JP&source=archive&yearStart={int(year_from)}&yearEnd={int(year_to)}"
    )
    jp_query = quote(model_slug or maker_slug, safe="-")
    jp_sheet_url = "https://jpsheet.com/auction-price-history/" + (f"?q={jp_query}" if jp_query else "")
    links = []
    if make_key in aleado_makes and model_slug:
        carvector_make = maker_slug.lower()
        carvector_model = quote(model_slug.lower(), safe="-")
        links.append({
            "name": "Carvector — поиск проданных японских лотов",
            "url": f"https://carvector.com/stat/{carvector_make}/{carvector_model}",
            "kind": "Модельная статистика, найденные автомобили и статусы завершённых торгов",
            "access": "Публичная выдача показывает часть лотов; бесплатный аккаунт открывает больше деталей и фотографий. Дополнительные 360°/HD материалы могут требовать депозит. Сверяйте методику поля Average price."
        })
    aleado_key = make_key
    if aleado_key in aleado_model_map and model_key in aleado_model_map[aleado_key]:
        slug, name_id = aleado_model_map[aleado_key][model_key]
        company_id = aleado_makes[aleado_key][1]
        aleado_link = f"https://aleado.com/autostat/{slug}.asp?company_id={company_id}&name_id={name_id}"
    elif aleado_key in aleado_makes:
        slug, company_id = aleado_makes[aleado_key]
        aleado_link = f"https://aleado.com/autostat/{slug}.asp?company_id={company_id}"
    else:
        aleado_link = None
    if aleado_link:
        links.append({
            "name": "Aleado — статистика проданных аукционных лотов",
            "url": aleado_link,
            "kind": "По годам: количество продаж и средняя цена в тысячах иен",
            "access": "Публичные модельные страницы; расчёт основан на последних шести месяцах и исключает часть особых продаж. PAPAUTO не копирует базу."
        })
    links.append({
        "name": "Aleado — бесплатная демо-база",
        "url": "https://demo.aleado.com/auctions/?lang=ru",
        "kind": "Демонстрационный доступ к поиску по моделям и характеристикам",
        "access": "На странице Aleado опубликованы тестовые учётные данные: логин demo, пароль guest. Демо может показывать ограниченную выборку, а не всю базу."
    })
    links.extend([
        {"name": "Banzai24 — архив японских торгов", "url": banzai_url,
         "kind": "Архив закрытых торгов по марке, модели и годам",
         "access": "Публичная выдача; часть финальных цен, фотографий и листов может быть ограничена аккаунтом."},
        {"name": "JP Sheet — история цен по модели", "url": jp_sheet_url,
         "kind": "Публичная модельная статистика и недавние цены молотка",
         "access": "Открыть страницу источника. Автоматический сбор и перепубликация данных без письменного разрешения запрещены."},
        {"name": "А.М. Гамма — статистика аукционов", "url": "https://japan.amgamma.ru/car-statistics",
         "kind": "Интерактивный поиск по марке, модели, году, пробегу и оценке",
         "access": "На странице включить «Только проданные» и нажать «Найти»."},
        {"name": "ES Transit — архив продаж", "url": "https://estransit.ru/statistika/",
         "kind": "Архив по маркам, моделям, годам и аукционным площадкам",
         "access": "В выдаче цены могут быть рассчитаны до Владивостока, а не являться ценой молотка."},
        {"name": "Auctions22 — прошлые торги", "url": "https://auctions22.com/past",
         "kind": "Публичные результаты и статусы Sold / Not sold",
         "access": "Сайт заявляет бесплатную регистрацию для просмотра полных цен, характеристик и фотографий."}
    ])
    return links


@app.get("/api/vehicles")
async def search_vehicles(country: str = "japan", make: str = "", model: str = "",
                          year_from: int = 1990, year_to: int = 2027,
                          max_price: int = 0, mileage_max: Optional[int] = None,
                          volume_min: Optional[int] = None, volume_max: Optional[int] = None,
                          body: str = "", grade: str = "", lot_number: str = "",
                          limit: int = 20):
    """Search Korea live; for Japan return model-specific public source searches until a licensed feed exists."""
    if country not in {"japan", "south-korea", "china"}:
        raise HTTPException(status_code=400, detail="Неизвестное направление поиска.")
    if year_from < 1990 or year_to > 2030 or year_from > year_to:
        raise HTTPException(status_code=400, detail="Проверьте диапазон годов выпуска.")
    if max_price < 0 or (mileage_max is not None and mileage_max < 0) or (volume_min is not None and volume_min < 0) or (volume_max is not None and volume_max < 0):
        raise HTTPException(status_code=400, detail="Бюджет, пробег и объём не могут быть отрицательными.")
    if volume_min is not None and volume_max is not None and volume_min > volume_max:
        raise HTTPException(status_code=400, detail="Минимальный объём двигателя не может быть больше максимального.")
    limit = min(max(limit, 1), 50)

    if country == "china":
        live_china = await fetch_ttpai_model_stats(make, model)
        if live_china and live_china.get("ok"):
            records = [
                {
                    "make": make,
                    "model": model,
                    "date": item.get("date"),
                    "description": item.get("description"),
                    "city": live_china.get("city"),
                    "source": "TTPAI",
                    "record_type": "historical_transaction",
                    "price": None,
                    "mileage": None,
                    "photos": [],
                }
                for item in live_china.get("recent_sales", [])
            ]
            return {
                "ok": True,
                "country": "china",
                "data_type": "historical_transactions",
                "source": "TTPAI",
                "model": live_china.get("model"),
                "city": live_china.get("city"),
                "count": len(records),
                "records": records,
                "source_url": live_china.get("source_url"),
                "retrieved_at": live_china.get("retrieved_at"),
                "disclaimer": "Это история недавно завершённых сделок на китайском рынке подержанных автомобилей, а не активные объявления и не полный архив оптовых аукционов. Цена конкретной сделки и фотографии не публикуются в этом блоке.",
            }

    if country == "south-korea":
        # A configured XAPI key means the user requested a live vehicle catalogue.
        # Do not let the public monthly summary short-circuit that search.
        api_key = (os.getenv("XAPIKOREA_API_KEY") or "").strip()
        public_stats = await fetch_korea_monthly_stats() if not api_key else {"ok": False, "message": "Live catalogue configured; skip summary fallback."}
        if public_stats.get("ok"):
            monthly_lines = [
                f"{row['month']}: выставлено {row['offered']:,}, продано {row['sold']:,}, доля {row['completion_rate_percent']}%".replace(",", " ")
                for row in public_stats.get("history", [])
            ]
            return {
                "ok": True, "country": "south-korea", "data_type": "source_hub",
                "source": public_stats["source"], "count": len(public_stats.get("history", [])),
                "records": [], "model_search_links": [],
                "sources": [{
                    "name": "Национальная ассоциация автомобильных аукционов Кореи",
                    "url": public_stats["source_url"],
                    "access": "Открытая месячная статистика · без регистрации и API-ключа",
                    "data_kind": "Выставленные и проданные автомобили по месяцам",
                    "note": "Последние опубликованные месяцы: " + "; ".join(monthly_lines) + ". Это официальные агрегированные итоги аукционного рынка, не индивидуальные карточки лотов."
                }],
                "message": "Официальная месячная статистика Кореи получена напрямую с сайта отраслевой ассоциации. " + "; ".join(monthly_lines),
                "disclaimer": public_stats.get("disclaimer", "")
            }
        if not api_key:
            logger.warning("Korean public monthly auction statistics unavailable: %s", public_stats.get("message"))
        # When the live key is configured, continue directly to XAPI Korea listings.
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="Поиск автомобилей из Южной Кореи пока не активирован. Создайте бесплатный ключ XAPI Korea и добавьте его в Render как XAPIKOREA_API_KEY."
            )
        params = {
            "brand": make.strip()[:80] or None,
            "model": model.strip()[:80] or None,
            "year_from": year_from,
            "year_to": year_to,
            "mileage_max": mileage_max,
            "limit": limit,
            "page": 1,
            "lang": "en",
            "source": "encar",
            "sale_type": "normal",
        }
        # The site's budget is a Russian-ruble target, while this provider's price filter
        # is KRW/EUR. Never compare those currencies without a verified FX conversion.
        params = {key: value for key, value in params.items() if value is not None and value != ""}
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.get(
                    "https://api.xapikorea.com/v1/search",
                    params=params,
                    headers={"X-API-Key": api_key, "Accept": "application/json"},
                )
            if response.status_code == 401:
                logger.error("XAPI Korea authentication failed (401); key is present in Render but was rejected by provider")
                raise HTTPException(status_code=503, detail="XAPI Korea отклонил ключ (HTTP 401). Сам ключ не меняли; проверьте его статус в кабинете провайдера.")
            if response.status_code == 429:
                logger.warning("XAPI Korea rate limit reached (429)")
                raise HTTPException(status_code=429, detail="Достигнут лимит запросов XAPI Korea. Подождите и повторите поиск.")
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"XAPI Korea вернул ошибку поиска (HTTP {response.status_code}).")
            try:
                payload = response.json()
            except ValueError:
                raise HTTPException(status_code=502, detail="XAPI Korea вернул ответ в неизвестном формате.")
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                logger.error("XAPI Korea returned an unexpected search response shape")
                raise HTTPException(status_code=502, detail="Формат ответа XAPI Korea не соответствует документации.")
            logger.info("XAPI Korea search succeeded: results=%s total_count=%s", len(payload["results"]), payload.get("total_count"))
            results = []
            for item in payload["results"][:limit]:
                if not isinstance(item, dict):
                    continue
                price = item.get("price_krw")
                mileage = item.get("mileage_km")
                year = item.get("year") or item.get("model_year")
                volume_raw = next((item.get(key) for key in (
                    "engine_displacement_cc", "displacement_cc", "engine_volume_cc", "volume_cc"
                ) if item.get(key) not in (None, "")), None)
                try:
                    volume_cc = int(float(str(volume_raw).replace(",", "."))) if volume_raw is not None else None
                except (TypeError, ValueError):
                    volume_cc = None
                listing_id = item.get("id")
                source = str(item.get("source") or "encar")
                photos = _https_photo_urls(item.get("photos"))
                if not photos:
                    thumbnail = item.get("thumbnail") or item.get("thumbnail_url") or item.get("image_url") or item.get("image")
                    if isinstance(thumbnail, str) and thumbnail.startswith("https://") and len(thumbnail) <= 2048:
                        photos = [thumbnail]
                listing_date = item.get("listed_at") or item.get("listing_date") or item.get("created_at") or item.get("date")
                results.append({
                    "id": str(listing_id) if listing_id is not None else None,
                    "lot_number": str(listing_id) if listing_id is not None else None,
                    "record_type": "current_listing",
                    "listing_date": listing_date,
                    "source": source,
                    "make": _fix_mojibake(item.get("manufacturer") or item.get("make") or ""),
                    "model": _fix_mojibake(item.get("model") or ""),
                    "year": (str(year)[:4] if year is not None and str(year).isdigit() and len(str(year)) >= 4 else year),
                    "mileage": mileage,
                    "volume_cc": volume_cc,
                    "price": (f"{int(price):,} ₩ — цена в Корее, без доставки и оформления в РФ".replace(",", " ") if isinstance(price, (int, float)) else _fix_mojibake(item.get("price"))),
                    "price_krw": price,
                    "currency": "KRW",
                    "listing_url": _canonical_korea_listing_url(source, listing_id, item.get("encar_url") or item.get("listing_url") or item.get("url")),
                    "source_name": {"encar": "Encar", "kbchachacha": "KB ChaChaCha", "kcar": "K Car"}.get(source, _fix_mojibake(source)),
                    "body": _fix_mojibake(item.get("body_style") or item.get("body") or ""),
                    "grade": _fix_mojibake(item.get("grade") or ""),
                    "photos": photos,
                    "thumbnail": photos[0] if photos else None,
                    "data_source": "XAPI Korea",
                    "availability_note": _fix_mojibake("Наличие и цену нужно повторно подтвердить у исходной площадки."),
                })
            # Search results may omit full galleries. Fetch details only for a small
            # set of Encar listings that have no thumbnail, keeping API usage bounded.
            need_details = [
                item for item in results
                if item.get("source") == "encar" and item.get("id") and not item.get("photos")
            ][:8]
            if need_details:
                async with httpx.AsyncClient(timeout=12.0) as photo_client:
                    galleries = await asyncio.gather(*[
                        _xapi_photo_urls(photo_client, item["id"], api_key)
                        for item in need_details
                    ])
                for item, gallery in zip(need_details, galleries):
                    if gallery:
                        item["photos"] = gallery
                        item["thumbnail"] = gallery[0]
            # Apply descriptive filters locally when the provider search endpoint does not
            # expose equivalent documented query parameters. Never compare KRW with RUB.
            if body.strip():
                needle = body.strip().casefold()
                results = [item for item in results if needle in str(item.get("body") or "").casefold()]
            if grade.strip():
                wanted_grade = grade.strip().casefold()
                results = [item for item in results if str(item.get("grade") or "").strip().casefold() == wanted_grade]
            if lot_number.strip():
                wanted_lot = lot_number.strip().casefold()
                results = [
                    item for item in results
                    if wanted_lot in str(item.get("lot_number") or item.get("id") or "").casefold()
                ]
            if volume_min is not None or volume_max is not None:
                results = [
                    item for item in results
                    if item.get("volume_cc") is not None
                    and (volume_min is None or item["volume_cc"] >= volume_min)
                    and (volume_max is None or item["volume_cc"] <= volume_max)
                ]
            return {
                "ok": True,
                "source": "XAPI Korea",
                "country": "south-korea",
                "record_type": "current_listing",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "total_count": payload.get("total_count", len(results)),
                "returned_count": len(results),
                "partial": bool(payload.get("partial", False)),
                "source_errors": payload.get("source_errors", []),
                "filters_applied": {
                    "country": country, "make": make.strip(), "model": model.strip(),
                    "year_from": year_from, "year_to": year_to, "mileage_max": mileage_max,
                    "body": body.strip(), "grade": grade.strip(),
                    "lot_number": lot_number.strip(),
                    "volume_min": volume_min, "volume_max": volume_max,
                },
                "budget_rub": max_price or None,
                "budget_note": "Бюджет указан в рублях как ориентир общей стоимости. Он не используется как фильтр цены объявления, потому что цена источника в KRW не включает доставку, таможню и оформление.",
                "results": results,
                "disclaimer": "Это текущие объявления, а не результаты завершённых торгов. Цена указана в корейских вонах и не включает доставку, таможню, оформление и доставку по России. Наличие и цену нужно подтвердить у исходной площадки.",
            }
        except HTTPException:
            raise
        except httpx.RequestError as exc:
            logger.error("XAPI Korea connection failure: %s: %s", type(exc).__name__, str(exc))
            raise HTTPException(status_code=502, detail="Не удалось связаться с XAPI Korea. Проверьте логи сервера для определения сетевой ошибки и попробуйте позже.")

    if country == "japan":
        return {
            "ok": True, "country": "japan", "data_type": "external_search",
            "query": {"make": make.strip(), "model": model.strip(), "year_from": year_from, "year_to": year_to},
            "search_links": _japan_model_search_links(make, model, year_from, year_to),
            "message": "Для Японии открыты прямые поиски по архивам источников. Результаты показываются на сайтах владельцев баз; PAPAUTO не выдаёт их за собственную выгрузку и не копирует закрытые фотографии или аукционные листы."
        }
    # China has no confirmed free reusable live-lot feed configured.
    raise HTTPException(
        status_code=503,
        detail="Для Китая пока не подключён подтверждённый источник актуальных объявлений. Откройте раздел статистики и публичные источники."
    )




class _USSMonthlyTableParser(HTMLParser):
    """Extract table rows from USS's publicly published monthly auction report."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tables = []
        self.in_table = False
        self.in_row = False
        self.in_cell = False
        self.current_table = []
        self.current_row = []
        self.current_cell = []

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == "table" and not self.in_table:
            self.in_table = True
            self.current_table = []
        elif self.in_table and tag == "tr":
            self.in_row = True
            self.current_row = []
        elif self.in_table and self.in_row and tag in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data):
        if self.in_table and self.in_row and self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag):
        tag = tag.lower()
        if self.in_table and self.in_row and self.in_cell and tag in {"td", "th"}:
            self.current_row.append(" ".join(" ".join(self.current_cell).split()))
            self.current_cell = []
            self.in_cell = False
        elif self.in_table and tag == "tr":
            if self.current_row:
                self.current_table.append(self.current_row)
            self.current_row = []
            self.in_row = False
        elif tag == "table" and self.in_table:
            if self.current_table:
                self.tables.append(self.current_table)
            self.current_table = []
            self.in_table = False


def _uss_monthly_history(page: str):
    """Extract the published monthly USS aggregate series from its public HTML table."""
    parser = _USSMonthlyTableParser()
    parser.feed(page)
    month_names = {"Apr.", "May", "Jun.", "Jul.", "Aug.", "Sep.", "Oct.", "Nov.", "Dec.", "Jan.", "Feb.", "Mar.",
                   "4月", "5月", "6月", "7月", "8月", "9月", "10月", "11月", "12月", "1月", "2月", "3月"}

    def number(value):
        cleaned = value.replace(",", "").replace("千円", "").replace("台", "").replace("%", "").strip()
        try:
            return float(cleaned) if cleaned and cleaned not in {"-", "—"} else None
        except ValueError:
            return None

    for table in parser.tables:
        rows = []
        for cells in table:
            if len(cells) < 14 or cells[0].strip() not in month_names:
                continue
            offered = number(cells[3])
            sold = number(cells[6])
            rate = number(cells[9])
            average_thousand_yen = number(cells[11])
            if offered is not None and sold is not None and rate is not None and average_thousand_yen is not None:
                rows.append({
                    "month": cells[0].strip(),
                    "auctions": number(cells[1]),
                    "offered": int(offered),
                    "sold": int(sold),
                    "contract_rate_percent": round(rate, 1),
                    "average_sold_price_jpy": int(average_thousand_yen * 1000),
                })
        if rows:
            return rows
    return []


def _uss_monthly_snapshot(page: str):
    rows = _uss_monthly_history(page)
    return rows[-1] if rows else None


@app.get("/api/market-overview")
async def market_overview():
    """Fetch open, aggregate Japanese auction statistics directly from USS; no API key."""
    source_url = "https://www.ussnet.co.jp/en/ir/library/monthly/index.html"
    try:
        async with httpx.AsyncClient(timeout=12.0, follow_redirects=True) as client:
            response = await client.get(source_url, headers={"User-Agent": "PAPAUTO market statistics contact: website"})
            response.raise_for_status()
        history = _uss_monthly_history(response.text)
        snapshot = history[-1] if history else None
        if not snapshot:
            logger.warning("USS monthly page was fetched but its table format was not recognized")
            return {"ok": True, "available": False, "source": "USS Monthly Data", "source_url": source_url,
                    "message": "Официальная страница доступна, но формат таблицы изменился. Обновим разбор данных."}
        return {"ok": True, "available": True, "source": "USS Monthly Data", "source_url": source_url,
                "data_month": snapshot["month"], "retrieved_at": datetime.now(timezone.utc).isoformat(),
                "metrics": snapshot, "history": history[-6:],
                "disclaimer": "Открытая агрегированная статистика USS по всему рынку. Это не цена конкретной модели и не архив отдельных проданных лотов."}
    except (httpx.HTTPError, ValueError) as exc:
        logger.warning("USS monthly data unavailable: %s", exc)
        return {"ok": True, "available": False, "source": "USS Monthly Data", "source_url": source_url,
                "message": "Не удалось обновить открытую статистику USS. Повторите позже; значения не подменяются выдуманными цифрами."}


@app.get("/api/korea-auction-overview")
async def korea_auction_overview():
    """Free public monthly auction totals from the Korean national association."""
    return await fetch_korea_monthly_stats()


@app.get("/api/auction-statistics")
async def auction_statistics(country: str = "japan", make: str = "", model: str = "",
                             year_from: int = 1990, year_to: int = 2030,
                             grade: str = "", limit: int = 20):
    """Show source data; Korean results are current asking-price listings, not sold-auction records."""
    if country not in {"japan", "south-korea", "china"}:
        raise HTTPException(status_code=400, detail="Неизвестное направление поиска.")
    if year_from < 1990 or year_to > 2030 or year_from > year_to:
        raise HTTPException(status_code=400, detail="Проверьте диапазон годов выпуска.")
    limit = min(max(limit, 1), 30)
    make, model, grade = make.strip()[:80], model.strip()[:80], grade.strip()[:12]
    model_search_links = _japan_model_search_links(make, model, year_from, year_to) if country == "japan" else []
    if country == "china":
        live_china = await fetch_ttpai_model_stats(make, model)
        if live_china and live_china.get("ok"):
            return live_china
    if country == "south-korea":
        api_key = (os.getenv("XAPIKOREA_API_KEY") or "").strip()
        if not api_key:
            raise HTTPException(status_code=503, detail="Поиск по Южной Корее пока не активирован: в Render нужен XAPIKOREA_API_KEY.")
        params = {"brand": make or None, "model": model or None, "year_from": year_from, "year_to": year_to, "limit": limit, "page": 1, "lang": "en", "source": "encar", "sale_type": "normal"}
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.get("https://api.xapikorea.com/v1/search", params=params, headers={"X-API-Key": api_key, "Accept": "application/json"})
            if response.status_code == 401:
                logger.error("XAPI Korea statistics request rejected (401); key is present in Render but was rejected by provider")
                raise HTTPException(status_code=503, detail="XAPI Korea отклонил ключ (HTTP 401). Сам ключ не меняли; проверьте его статус в кабинете провайдера.")
            if response.status_code == 429:
                logger.warning("XAPI Korea statistics rate limit reached (429)")
                raise HTTPException(status_code=429, detail="Достигнут лимит XAPI Korea. Повторите поиск позже.")
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"XAPI Korea вернул ошибку HTTP {response.status_code}.")
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                logger.error("XAPI Korea statistics returned an unexpected response shape")
                raise HTTPException(status_code=502, detail="Источник вернул неизвестный формат данных.")
            logger.info("XAPI Korea statistics request succeeded: results=%s total_count=%s", len(payload["results"]), payload.get("total_count"))
        except HTTPException:
            raise
        except (httpx.RequestError, ValueError):
            raise HTTPException(status_code=502, detail="Не удалось получить данные из XAPI Korea.")
        records, prices = [], []
        for item in payload["results"][:limit]:
            if not isinstance(item, dict):
                continue
            price, year, mileage = item.get("price_krw"), item.get("year") or item.get("model_year"), item.get("mileage_km")
            if isinstance(price, (int, float)) and price > 0:
                prices.append(float(price))
            records.append({"make": _fix_mojibake(item.get("manufacturer") or item.get("make") or make),
                "model": _fix_mojibake(item.get("model") or model), "year": str(year)[:4] if year is not None else "",
                "mileage_km": mileage if isinstance(mileage, (int, float)) else None,
                "price": price if isinstance(price, (int, float)) else None, "currency": "KRW",
                "source": _fix_mojibake(item.get("source") or "XAPI Korea")})
        prices.sort()
        median = None
        if prices:
            mid = len(prices) // 2
            median = prices[mid] if len(prices) % 2 else (prices[mid - 1] + prices[mid]) / 2
        return {"ok": True, "country": country, "data_type": "current_listings", "source": "XAPI Korea",
            "count": len(records), "min_price": min(prices) if prices else None, "median_price": median,
            "max_price": max(prices) if prices else None, "currency": "KRW", "records": records,
            "disclaimer": "Это цены активных объявлений на корейском рынке, а не подтверждённые цены завершённых аукционов. Доставка, таможня и оформление в РФ не включены."}
    # Japan and China currently have no licensed, reusable bulk feed configured.
    sample_stats = None
    sample_records = []
    unsold_records = []
    china_judicial_sample = []
    china_market_sample = []
    # Instead of returning a dead-end error or inventing model prices, expose a ranked
    # source hub with explicit access/quality labels so users can inspect primary sources.
    if country == "japan":
        sources = [
            {"name": "Aleado — статистика проданных лотов по моделям и годам", "url": "https://aleado.com/autostat/TOYOTA.asp?company_id=9",
             "access": "Публичные модельные страницы", "data_kind": "Количество проданных лотов / средняя цена / разбивка по годам",
             "note": "Для ряда марок и моделей доступны публичные страницы с количеством проданных автомобилей и средней ценой по годам; цены в таблицах могут быть указаны в тысячах иен. Для Toyota есть отдельный каталог моделей. Используем как внешний источник, не копируем массово.",
             "priority": 1},
            {"name": "А.М. Гамма — статистика аукционов", "url": "https://japan.amgamma.ru/car-statistics",
             "access": "Открытый интерактивный поиск", "data_kind": "Архив / только проданные",
             "note": "Есть фильтры по марке, модели, кузову, оценке, объёму, году, пробегу и дате; предусмотрен переключатель «Только проданные». Это наиболее перспективный бесплатный кандидат для проверки модельных результатов. Автоматическое использование данных пока не разрешено и не подключено.",
             "priority": 1},
            {"name": "Auctions22 — прошлые торги", "url": "https://auctions22.com/past",
             "access": "Бесплатный просмотр; детали после бесплатной регистрации заявлены сайтом", "data_kind": "История / цены / фото / листы",
             "note": "Публичный архив показывает завершённые лоты и часть цен; сайт заявляет, что после бесплатного аккаунта открываются финальная цена, полный набор фото и лист. Объём публичного архива ограничен, условия повторной публикации не подтверждены.",
             "priority": 1},
            {"name": "JP Sheet — история цен по моделям", "url": "https://jpsheet.com/auction-price-history/",
             "access": "Публичные модельные сводки", "data_kind": "Модельная статистика",
             "note": "Есть публичные средние цены и число записей по моделям и годам. Это выборка сервиса, не полный рынок USS/TAA/JU; детальные проверки и API могут быть платными.",
             "priority": 1},
            {"name": "USS — официальная месячная статистика", "url": "https://www.ussnet.co.jp/en/ir/library/monthly/index.html",
             "access": "Открыто, без API-ключа", "data_kind": "Общая статистика рынка",
             "note": "Официальные месячные показатели: выставлено, продано, процент завершённых сделок и средняя цена по всей сети. Уже подключено отдельным блоком PAPAUTO; это не статистика конкретной модели.",
             "priority": 1},
            {"name": "BEX Auction", "url": "https://bexauction.com/",
             "access": "Бесплатная регистрация заявлена", "data_kind": "Лоты / рыночные записи",
             "note": "Сайт заявляет более 100 000 текущих лотов и более 2 млн записей рыночных цен. Нужно подтвердить доступ к историческим ценам, объём бесплатной квоты и право выгрузки.",
             "priority": 2},
            {"name": "ExportCar — Auto Auction Results", "url": "https://exportcar.jp/auto/",
             "access": "Публичная поисковая форма; детали проверить", "data_kind": "Мульти-аукционный каталог",
             "note": "Фильтры по десяткам залов, включая JU, USS, TAA, ARAI, MIRIVE и NAA. Требуется практическая проверка завершённых лотов и финальных цен.",
             "priority": 2},
            {"name": "JUC Inc. — Past Auctions", "url": "https://jp-auctions.com/jpauctions/index-html",
             "access": "Регистрация / вход", "data_kind": "Архив прошлых лотов",
             "note": "В интерфейсе есть фильтры Past Auctions, Last Week, Last Month и Last 3 Month; часть цен и листов закрыта для незарегистрированных пользователей.",
             "priority": 2},
            {"name": "Banzai24 — японский архив продаж", "url": "https://banzai24.com/en?source=archive",
             "access": "Публичные результаты и цены; дополнительные фото требуют входа / Premium", "data_kind": "10 000+ архивных лотов / финальные цены / модельная история",
             "note": "Публичная архивная выдача показывает завершённые лоты, статусы и финальные цены; для отдельных моделей есть диапазон цен за период. По RAV4 найден публичный срез 24–29.10.2026. Дополнительные фотографии и полный аукционный лист открываются через авторизацию и JapanStat report; их не копируем.",
             "priority": 1},
            {"name": "Auction Data Search (ADS)", "url": "https://www.auctiondatasearch.jp/",
             "access": "View Only membership; депозит/условия", "data_kind": "Статистика проданных авто за 3 месяца",
             "note": "Сайт заявляет статистику завершённых продаж за три месяца по разным аукционам Японии. Это не подтверждённый бесплатный источник: доступ View Only связан с членством.",
             "priority": 3}
        ]
        sample_stats = None
        sample_records = []
        unsold_records = []
        query_make = (make or "").strip().lower()
        query_model = (model or "").strip().lower()
        if ("rav4" in query_model or ("rav4" in query_make and not query_model)) and (not query_make or "toyota" in query_make):
            # Manually verified public sample from Banzai24 indexed lot pages, 24–29 Oct 2026.
            # Nine sold records only; unsold lots are listed separately and excluded from calculations.
            sample_stats = {
                "sample_count": 9,
                "average_final_price_jpy": 2646667,
                "median_final_price_jpy": 2554000,
                "min_final_price_jpy": 2108000,
                "max_final_price_jpy": 3500000,
                "source_model_range_min_jpy": 392000,
                "source_model_range_max_jpy": 3940000,
                "source_range_from": "2026-06-30",
                "source_range_to": "2026-10-29",
                "sample_from": "2026-10-24",
                "sample_to": "2026-10-29",
                "source_url": "https://banzai24.com/en/TOYOTA/RAV4?countryISO=JP&source=archive",
                "note": "Среднее и медиана рассчитаны PAPAUTO по 9 публично видимым проданным лотам из выборки 24–29 октября 2026 года. Это не полный массив торгов. Диапазон 392 000–3 940 000 ¥ и период 30.06–29.10.2026 показаны самим источником для модели RAV4."
            }
            sample_records = [
                {"name": "RAV4 Adventure 4WD", "year": "2024.05", "mileage_km": 35000, "auction": "TAA Hokkaido", "date": "2026-10-29", "grade": "3.5", "final_price_jpy": 2554000, "url": "https://banzai24.com/en/car/JP/01a17d51-dffa-7aed-8307-7b83e70ea004"},
                {"name": "RAV4 G 4WD", "year": "2024.08", "mileage_km": 44000, "auction": "TAA Kanto", "date": "2026-10-29", "final_price_jpy": 2497000, "url": "https://banzai24.com/en/car/JP/01a180a2-ead0-7eaa-8f90-abef31942b63"},
                {"name": "RAV4 G 4WD", "year": "2024", "mileage_km": 41000, "auction": "NAA Osaka", "date": "2026-10-29", "grade": "3.5", "final_price_jpy": 2112000, "url": "https://banzai24.com/en/car/JP/01a17d73-2cef-7370-bb54-cc7a306ffd76"},
                {"name": "RAV4 Hybrid G 4WD", "year": "2024.02", "mileage_km": 27000, "auction": "TAA Kanto", "date": "2026-10-29", "final_price_jpy": 3500000, "url": "https://banzai24.com/en/car/JP/01a17d85-9f9d-75e9-ad4d-8366bb57e34c"},
                {"name": "RAV4 Hybrid X", "year": "2019.11", "mileage_km": 39000, "auction": "TAA Yokohama", "date": "2026-10-24", "final_price_jpy": 2108000, "url": "https://banzai24.com/en/car/JP/01a151f3-a023-7f37-a4ce-3147cbaf6daa"},
                {"name": "RAV4 Hybrid G 4WD", "year": "2022.09", "mileage_km": 90000, "auction": "CAA Gifu", "date": "2026-10-27", "final_price_jpy": 2679000, "url": "https://banzai24.com/en/car/JP/01a1679c-0ec6-7827-8d74-8c658c8d10be"},
                {"name": "RAV4 Hybrid Adventure 4WD", "year": "2022.02", "mileage_km": 85000, "auction": "CAA Chubu", "date": "2026-10-28", "grade": "4.5", "final_price_jpy": 2635000, "url": "https://banzai24.com/en/car/JP/01a176e6-e09e-7eeb-af41-da3ac612d547"},
                {"name": "RAV4 G Z Package 4WD", "year": "2022.02", "mileage_km": 49000, "auction": "CAA Chubu", "date": "2026-10-28", "final_price_jpy": 2385000, "url": "https://banzai24.com/en/car/JP/01a16d32-26e4-72db-8dfd-816eefdef56b"},
                {"name": "RAV4 20S Prestige Style", "year": "2024.02", "mileage_km": 26000, "auction": "TAA Chubu", "date": "2026-10-29", "final_price_jpy": 3350000, "url": "https://banzai24.com/en/car/JP/01a17d83-dc72-7b6a-8ba3-8c4a0efa3ad8"}
            ]
            unsold_records = [
                {"name": "RAV4 G 4WD", "year": "2024.04", "mileage_km": 27751, "auction": "TAA Kanto", "date": "2026-10-29", "last_bid_jpy": 2575000, "status": "Не продан", "url": "https://banzai24.com/en/car/JP/01a17d54-9444-722d-8262-b2b0a68107bf"}
            ]
            # Apply the requested year, grade and row limit to the small manually checked
            # RAV4 sample. Never present the unfiltered sample as a model-wide search.
            def _sample_year(record):
                try:
                    return int(str(record.get("year", ""))[:4])
                except (TypeError, ValueError):
                    return None
            sample_records = [
                record for record in sample_records
                if _sample_year(record) is not None and year_from <= _sample_year(record) <= year_to
            ]
            if grade:
                wanted_grade = grade.casefold()
                sample_records = [
                    record for record in sample_records
                    if str(record.get("grade") or "").strip().casefold() == wanted_grade
                ]
            sample_records = sample_records[:limit]
            sold_prices = sorted(
                int(record["final_price_jpy"]) for record in sample_records
                if isinstance(record.get("final_price_jpy"), (int, float)) and record["final_price_jpy"] > 0
            )
            if sold_prices:
                middle = len(sold_prices) // 2
                sample_median = sold_prices[middle] if len(sold_prices) % 2 else (sold_prices[middle - 1] + sold_prices[middle]) / 2
                sample_stats = {
                    "sample_count": len(sold_prices),
                    "average_final_price_jpy": round(sum(sold_prices) / len(sold_prices)),
                    "median_final_price_jpy": round(sample_median),
                    "min_final_price_jpy": sold_prices[0],
                    "max_final_price_jpy": sold_prices[-1],
                    "source_model_range_min_jpy": 392000,
                    "source_model_range_max_jpy": 3940000,
                    "source_range_from": "2026-06-30",
                    "source_range_to": "2026-10-29",
                    "sample_from": "2026-10-24",
                    "sample_to": "2026-10-29",
                    "source_url": "https://banzai24.com/en/TOYOTA/RAV4?countryISO=JP&source=archive",
                    "note": "Небольшая вручную проверенная публичная выборка Banzai24, отфильтрованная по выбранным годам и оценке. Это не полный архив рынка и не автоматическая выгрузка."
                }
            else:
                sample_stats = None
                sample_records = []
        message = "По запросу " + " ".join(x for x in (make, model) if x) + " (" + str(year_from) + "–" + str(year_to) + ") сформированы прямые поиски по японским архивам и публичной модельной статистике. PAPAUTO пока не имеет лицензированного автоматического потока полных лотов, поэтому закрытые данные не копируются." + (" Ниже дополнительно показана небольшая проверенная выборка RAV4, отфильтрованная по вашим параметрам." if sample_stats else " Если выборка PAPAUTO отсутствует, откройте один из источников ниже — поиск уже подготовлен по вашей модели.")
    else:
        china_market_sample = [
            {"name": "Tesla Model 3 · Shanghai", "age_3_avg_cny": 120900, "age_5_avg_cny": 97500, "age_7_avg_cny": 88100,
             "recent_sales": "2026-09-21 · 2020 model · 101 000 km; 2026-09-04 · 2020 model · 9 000 km; 2026-09-03 · 2022 model · 92 000 km",
             "url": "https://www.ttpai.cn/shanghai/price/tesila-model3"},
            {"name": "Tesla Model Y · Shanghai", "age_3_avg_cny": 153100, "age_5_avg_cny": 133400, "age_7_avg_cny": None,
             "recent_sales": "2026-09-06 · 2022 model · 20 000 km; 2026-08-26 · 2024 model · 24 000 km; 2026-08-25 · 2024 model · 14 000 km",
             "url": "https://www.ttpai.cn/shanghai/price/tesila-modely"},
            {"name": "Volkswagen Polo · Shanghai", "age_3_avg_cny": 58800, "age_5_avg_cny": 45300, "age_7_avg_cny": 34700,
             "recent_sales": "2026-09-22 · 2016 model · 18 000 km; 2026-09-14 · 2012 model · 56 000 km; 2026-09-10 · 2019 model · 55 000 km",
             "url": "https://www.ttpai.cn/shanghai/price/dazhong-polo", "photo_example_url": "https://www.ttpai.cn/shanghai/98306494", "photo_example_note": "Публичная карточка проданного Polo за сентябрь 2026 года: 8 фотографий, 18 000 км; точная цена в открытом фрагменте не раскрыта."}
        ]
        china_judicial_sample = [
            {"name": "Toyota GTM6480GL · 2011", "year": "2011", "auction": "Gongpai · Xinjiang", "date": "2026-09-30", "final_price_cny": 6850, "note": "Завершённые судебные торги; пробег 225 786 км; в карточке есть описание состояния и VIN.", "url": "https://zc.gpai.net/zc/detail?id=8634855"},
            {"name": "Luxgen DYM6481ACB · 2014", "year": "2014", "auction": "Gongpai · Xinjiang", "date": "2026-09-29", "final_price_cny": 3100, "note": "Завершённая судебная продажа; карточка указывает VIN, дату регистрации и комплектацию.", "url": "https://zc.gpai.net/zc/detail?id=8626994"},
            {"name": "Nissan + Jeep · 2 автомобиля", "year": "—", "auction": "Gongpai · Xinjiang", "date": "2026-09-12", "final_price_cny": 4900, "note": "Одна завершённая продажа двух автомобилей; итоговая цена относится к лоту из двух машин.", "url": "https://zc.gpai.net/zc/detail?id=8569813"},
            {"name": "Volkswagen Passat", "year": "—", "auction": "Gongpai · Henan", "date": "2026-09-21", "final_price_cny": 4800, "note": "Завершённая продажа; карточка содержит фотографии и место хранения.", "url": "https://zc.gpai.net/zc/detail?id=8600632"},
            {"name": "Volkswagen · легковой автомобиль", "year": "—", "auction": "Gongpai · Jiangsu", "date": "2026-08-10", "final_price_cny": 7000, "note": "Завершённые торги; карточка содержит статус продажи и итоговую ставку.", "url": "https://zc.gpai.net/zc/detail?id=8367826"},
            {"name": "BYD · подержанный автомобиль", "year": "—", "auction": "Gongpai · Henan", "date": "2026-07-13", "final_price_cny": 19700, "note": "Завершённая продажа отдельного автомобиля; три ставки, карточка показывает историю торгов.", "url": "https://zc.gpai.net/zc/detail?id=8303174"},
            {"name": "Volkswagen Passat · 2008", "year": "2008", "auction": "Gongpai · Shanghai", "date": "2026-07-17", "final_price_cny": 2000, "note": "Завершённая продажа; пробег 170 373 км, VIN и фотографии доступны в карточке.", "url": "https://zc.gpai.net/zc/detail?id=8279031"},
            {"name": "Volkswagen Magotan · 2011", "year": "2011", "auction": "Gongpai · Anhui", "date": "2026-07-23", "final_price_cny": 6500, "note": "Завершённая продажа; в карточке указаны дата регистрации и пробег 236 408 км.", "url": "https://zc.gpai.net/zc/detail?id=8345496"}
        ]
        sources = [
            {"name": "天天拍车 / TTPAI — модельная статистика", "url": "https://www.ttpai.cn/shanghai/price/tesila-model3",
             "access": "Публичные модельные страницы", "data_kind": "Исторические цены / средние по возрасту / последние сделки",
             "note": "Публичные страницы показывают средние цены по возрасту автомобиля (3/5/7 лет), историю модели и последние завершённые сделки с датами, пробегом и городом. Это статистика сделок платформы, не полный экспорт аукционных лотов. В отдельных карточках проданных машин доступны фотографии; аукционные листы не заявлены.",
             "priority": 1},
            {"name": "Guazi Export", "url": "https://ru.guazi.com/",
             "access": "Ограниченный бесплатный доступ после регистрации заявлен", "data_kind": "Недавно проданные / отчёты осмотра",
             "note": "Сайт заявляет временный бесплатный доступ к недавно проданным ценам и отчётам осмотра. Нужно проверить, видны ли завершённые цены и фото без оплаты и разрешено ли сохранять данные.",
             "priority": 1},
            {"name": "汽车街 / Autostreets", "url": "https://wap.autostreets.com/view/auction",
             "access": "Публичная витрина", "data_kind": "Активные лоты / расписание торгов",
             "note": "Открытая страница показывает количество проведённых онлайн- и синхронных торгов и ближайшие автомобильные сессии. Финальные цены и полный архив лотов нужно проверить отдельно.",
             "priority": 1},
            {"name": "公拍网 / Gongpai", "url": "https://www.gpai.net/sf/",
             "access": "Публичные судебные лоты", "data_kind": "Судебные торги / фото / ставки",
             "note": "Публично отображаются карточки, стартовая цена, оценка и текущая/последняя ставка. Это судебные и принудительные продажи, не обычный дилерский рынок; анализировать отдельной выборкой.",
             "priority": 1},
            {"name": "阿里司法拍卖 / Taobao Judicial", "url": "https://sf.taobao.com/",
             "access": "Публичные карточки; часть функций требует входа", "data_kind": "Судебные торги / результаты",
             "note": "Один из официально включённых Верховным народным судом сетевых поставщиков судебных торгов. Можно искать транспорт и проверять завершённые результаты; отделяем их от рыночных дилерских аукционов.",
             "priority": 2},
            {"name": "京东司法拍卖 / JD Court Auction", "url": "https://auction.jd.com/courtProductList.html",
             "access": "Публичные карточки; часть функций требует входа", "data_kind": "Судебные торги / результаты",
             "note": "Второй официальный судебный аукционный канал. Подходит для отдельного набора судебных продаж, но не для средней цены обычного подержанного рынка.",
             "priority": 2},
            {"name": "人民法院诉讼资产网", "url": "https://www.rmfysszc.gov.cn/",
             "access": "Публичный портал; автоматический доступ ограничен", "data_kind": "Судебные активы",
             "note": "Официальный портал судебных активов. Веб-доступ для роботов ограничен; массовую выгрузку без официального разрешения не используем.",
             "priority": 2},
            {"name": "优信拍 / YouxinPai", "url": "https://www.youxinpai.com/static/about?tab=gsjj",
             "access": "B2B / регистрация участников", "data_kind": "Профессиональные автомобильные торги",
             "note": "Платформа заявляет более 20 000 сделок в месяц и предоставляет профессиональную проверку состояния. История отдельных продаж и фотографии требуют аккаунта/разрешения.",
             "priority": 2},
            {"name": "博车网 / BoCheWang", "url": "https://www.bochewang.cn/",
             "access": "Приложение / аккаунт", "data_kind": "Аварийные / страховые / обычные авто",
             "note": "Публично заявлен накопленный объём свыше миллиона продаж. Сильный источник по страховым и повреждённым машинам; без архива и доступа участников не считаем его бесплатной статистикой.",
             "priority": 2},
            {"name": "车易拍 / Cheyipai", "url": "https://www.cheyipai.com/",
             "access": "B2B-торговый зал", "data_kind": "Автомобильные торги",
             "note": "Публичная форма показывает фильтры по источнику, цене, возрасту, пробегу и состоянию; финальная цена и история требуют проверки аккаунта.",
             "priority": 2},
            {"name": "车享拍 / Chexiang Pai", "url": "https://pai.chexiang.com/main/platformr.htm",
             "access": "Публичное описание; торговый зал для участников", "data_kind": "B2B / онлайн-торги / отчёт оценки",
             "note": "Платформа группы SAIC с системой стандартизированной оценки и онлайн-торгами. Наличие открытого архива завершённых продаж не подтверждено.",
             "priority": 3},
            {"name": "中国汽车流通协会 / CADA", "url": "https://www.cada.cn/",
             "access": "Открытые отраслевые отчёты", "data_kind": "Макростатистика рынка",
             "note": "Официальные данные по рынку подержанных автомобилей в Китае; не содержит открытой базы отдельных аукционных лотов.",
             "priority": 3}
        ]
        china_month_counts = {}
        for record in china_judicial_sample:
            month_key = str(record.get("date") or "")[:7]
            if month_key:
                china_month_counts[month_key] = china_month_counts.get(month_key, 0) + 1
        china_month_summary = "; ".join(
            f"{month_key}: {count} найденных публичных карточек"
            for month_key, count in sorted(china_month_counts.items(), reverse=True)
        )
        message = "Китай: TTPAI отдаёт открытые модельные средние и последние сделки. Дополнительно собраны публичные карточки завершённых автомобильных судебных торгов Gongpai за июль–сентябрь 2026: " + china_month_summary + ". Это проверенная поисковая выборка, не полный месячный итог рынка и не дилерские оптовые торги."
    return {"ok": True, "country": country, "data_type": "source_hub", "source": "PAPAUTO source registry",
        "source_hub_version": "2026-10-30-r12", "count": len(sample_records), "records": sample_records, "sources": sources, "model_search_links": model_search_links, "sample_stats": sample_stats,
        "unsold_records": unsold_records, "china_judicial_sample": china_judicial_sample, "china_market_sample": china_market_sample, "message": message,
        "disclaimer": "Публичный пример не равен полному массиву торгов. Фотографии и аукционные листы показываем только из источников, где это разрешено; платные отчёты не копируем. Цены объявлений, стартовые ставки, судебные продажи и завершённые дилерские аукционы не смешиваются."}

@app.get("/api/logistics/benchmarks")
async def logistics_benchmarks():
    """Public reference prices; indicative only, not live quotes or a carrier booking."""
    return {
        "as_of": "2026-10-29",
        "currency_note": "Foreign-currency figures are shown in their original currency and are not converted to RUB.",
        "japan": [
            {"item": "Внутренняя доставка по Японии до порта (пример тарифа)", "amount": 65000, "currency": "JPY", "source": "VDK Logistic", "url": "https://vdklogistic.ru/costs"},
            {"item": "Морской фрахт Йокогама — Владивосток (пример тарифа)", "amount": 350, "currency": "USD", "source": "VDK Logistic", "url": "https://vdklogistic.ru/costs"}
        ],
        "vladivostok_novosibirsk": [
            {"vehicle_class": "kei", "amount_rub": 110000},
            {"vehicle_class": "sedan_hatchback", "amount_rub": 120000},
            {"vehicle_class": "wagon", "amount_rub": 125000},
            {"vehicle_class": "crossover", "amount_rub": 130000},
            {"vehicle_class": "suv_minivan", "amount_rub": 140000}
        ],
        "carrier": "STS Autovoz",
        "carrier_url": "https://ctcavtovoz.ru/",
        "carrier_note": "Публичные ориентиры, проверенные 29.10.2026; цена зависит от машины, пункта сдачи/получения, страховки и текущего рейса. Перед договором требуется индивидуальное подтверждение.",
        "disclaimer": "Это справочные тарифы, а не гарантированная текущая цена и не оферта."
    }


class VehicleSelectionInput(BaseModel):
    message: str = Field(min_length=5, max_length=3000)
    country: str = Field(default="Не определился", max_length=80)
    budget: Optional[int] = Field(default=None, ge=0, le=2_000_000_000)
    city: str = Field(default="", max_length=100)
    make: str = Field(default="", max_length=80)
    model: str = Field(default="", max_length=80)
    year_from: Optional[int] = Field(default=None, ge=1990, le=2027)
    year_to: Optional[int] = Field(default=None, ge=1990, le=2027)
    mileage_max: Optional[int] = Field(default=None, ge=0, le=2_000_000)


@app.post("/api/assistant/select")
async def assistant_select(req: VehicleSelectionInput):
    """Create a grounded shortlist and follow-up questions; never pretend recommendations are live auction lots."""
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not gemini_key:
        logger.error("Gemini API key is not configured for assistant selection")
        raise HTTPException(status_code=503, detail="ИИ-подбор пока не подключён: в Render нужен действующий ключ Gemini API.")

    catalogue = [
        {"make": "Toyota", "model": "Aqua", "fit": "компактный гибрид для города и экономии топлива", "markets": ["Япония"]},
        {"make": "Toyota", "model": "Prius", "fit": "гибрид для города и смешанных поездок", "markets": ["Япония"]},
        {"make": "Honda", "model": "Fit", "fit": "компактный городской хэтчбек", "markets": ["Япония"]},
        {"make": "Toyota", "model": "Corolla", "fit": "универсальный компактный автомобиль", "markets": ["Япония", "Китай"]},
        {"make": "Toyota", "model": "RAV4", "fit": "семейный кроссовер", "markets": ["Япония", "Китай"]},
        {"make": "Honda", "model": "Vezel", "fit": "компактный кроссовер, в том числе гибридные версии", "markets": ["Япония"]},
        {"make": "Mazda", "model": "CX-5", "fit": "семейный кроссовер", "markets": ["Япония", "Южная Корея", "Китай"]},
        {"make": "Hyundai", "model": "Tucson", "fit": "семейный кроссовер", "markets": ["Южная Корея"]},
        {"make": "Kia", "model": "Sportage", "fit": "семейный кроссовер", "markets": ["Южная Корея"]},
        {"make": "Hyundai", "model": "Avante", "fit": "седан для города и трассы", "markets": ["Южная Корея"]},
        {"make": "BYD", "model": "Song Plus", "fit": "кроссовер, встречаются гибридные и электрические версии", "markets": ["Китай"]},
        {"make": "Geely", "model": "Monjaro", "fit": "просторный кроссовер", "markets": ["Китай"]},
        {"make": "Chery", "model": "Tiggo 7", "fit": "семейный кроссовер", "markets": ["Китай"]},
        {"make": "Haval", "model": "H6", "fit": "семейный кроссовер", "markets": ["Китай"]},
    ]
    brief = {
        "country_preference": req.country,
        "total_budget_rub": req.budget,
        "delivery_city_in_Russia": req.city,
        "make": req.make,
        "model": req.model,
        "year_from": req.year_from,
        "year_to": req.year_to,
        "maximum_mileage_km": req.mileage_max,
        "additional_requirements": req.message,
        "candidate_models_reference_only": catalogue,
    }
    instruction = (
        "Ты — автомобильный консультант PAPAUTO по подбору машин из Японии, Южной Кореи и Китая для ввоза в Россию. "
        "Подготовь практичный короткий shortlist из 3–5 моделей только из переданного справочного списка. "
        "Не называй их доступными лотами, не выдумывай цены, наличие, пробеги, комплектации, ставки таможни или сроки. "
        "Если бюджет задан, оцени только общую совместимость по классу/сегменту, а не утверждай, что машина точно укладывается. "
        "Различай бюджет на автомобиль и бюджет под ключ: если неясно, явно спроси. "
        "Учитывай страну, город доставки, тип кузова, двигатель и ограничения пользователя. "
        "Если запрос противоречив или критически неполон, задай до 3 конкретных вопросов. "
        "Верни строго JSON: summary (краткий вывод на русском), recommendations (массив объектов с make,model,why,checks), "
        "questions (массив строк), caveats (массив строк). В рекомендациях только модели из списка."
    )
    request_body = {
        "contents": [{"role": "user", "parts": [{
            "text": __import__("json").dumps({"instruction": instruction, "request": brief}, ensure_ascii=False)
        }]}],
        "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
    }

    # 3.8 occasionally returns HTTP 503 during demand spikes. Fall back to 3.6
    # immediately; this keeps the voice assistant from stopping after parsing.
    response = None
    last_error = None
    for model in ("gemini-3.8-flash", "gemini-3.6-flash"):
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(20.0, connect=10.0)) as client:
                candidate = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": gemini_key},
                    json=request_body
                )
            if candidate.status_code == 200:
                response = candidate
                logger.info("Gemini assistant selection responded via %s", model)
                break
            try:
                error_payload = candidate.json()
                error_info = error_payload.get("error", {}) if isinstance(error_payload, dict) else {}
                error_message = str(error_info.get("message", ""))[:300]
                error_code = error_info.get("status") or candidate.status_code
            except ValueError:
                error_message, error_code = "non-JSON response", candidate.status_code
            last_error = (candidate.status_code, error_code, error_message)
            logger.warning(
                "Gemini assistant model %s returned HTTP %s code=%s message=%s",
                model, candidate.status_code, error_code, error_message
            )
            if candidate.status_code not in {429, 500, 502, 503, 504}:
                break
        except httpx.RequestError as exc:
            last_error = (502, "NETWORK_ERROR", type(exc).__name__)
            logger.warning("Gemini assistant model %s request failed: %s", model, type(exc).__name__)

    if response is None:
        status_code, error_code, error_message = last_error or (503, "UNAVAILABLE", "No Gemini model responded")
        logger.error(
            "Gemini assistant selection failed after fallback: http=%s code=%s message=%s",
            status_code, error_code, error_message
        )
        raise HTTPException(
            status_code=503 if status_code in (429, 503) else 502,
            detail="ИИ-подбор временно перегружен. Попробуйте ещё раз через несколько секунд."
        )

    try:
        payload = response.json()
        candidates = payload.get("candidates") or []
        parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
        raw = next((part.get("text", "") for part in parts if part.get("text")), "")
        if not raw:
            raise HTTPException(status_code=502, detail="ИИ-подбор вернул пустой ответ. Попробуйте уточнить запрос.")
        import json
        result = json.loads(raw)
    except HTTPException:
        raise
    except (ValueError, KeyError, IndexError, TypeError):
        logger.exception("Could not parse Gemini assistant selection response")
        raise HTTPException(status_code=502, detail="Не удалось разобрать ответ ИИ-подбора. Попробуйте сформулировать запрос иначе.")

    logger.info("Gemini assistant selection succeeded: response_chars=%s", len(raw))
    allowed = {(item["make"].lower(), item["model"].lower()) for item in catalogue}
    recommendations = []
    for item in result.get("recommendations", [])[:5]:
        if not isinstance(item, dict):
            continue
        key = (str(item.get("make", "")).lower(), str(item.get("model", "")).lower())
        if key in allowed:
            recommendations.append({
                "make": item["make"],
                "model": item["model"],
                "why": str(item.get("why", ""))[:600],
                "checks": str(item.get("checks", ""))[:600],
                "availability": "Модель для рассмотрения; актуальные лоты не подтверждены"
            })
    return {
        "ok": True,
        "source": "Gemini AI + справочный список моделей PAPAUTO",
        "summary": str(result.get("summary", "Подбор подготовлен."))[:1500],
        "recommendations": recommendations,
        "questions": [str(x)[:400] for x in result.get("questions", [])[:3]],
        "caveats": [str(x)[:400] for x in result.get("caveats", [])[:4]],
        "disclaimer": "Это рекомендации по моделям, а не список актуальных лотов и не коммерческое предложение. Наличие, состояние и стоимость под ключ подтверждаются отдельно."
    }


@app.post("/api/voice/transcribe")
async def voice_transcribe(request: Request):
    """Transcribe Russian voice requests with Gemini Flash in one pass."""
    audio = await request.body()
    if not audio:
        raise HTTPException(status_code=400, detail="Запись пустая. Попробуйте ещё раз.")
    if len(audio) > 8 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="Запись слишком длинная. Попробуйте короткий запрос до минуты.")
    content_type = request.headers.get("content-type", "").split(";")[0].strip().lower()
    if content_type != "audio/wav":
        raise HTTPException(status_code=415, detail="Неподдерживаемый формат аудиозаписи.")
    gemini_key = (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY") or "").strip()
    if not gemini_key:
        logger.error("Gemini API key is not configured for voice transcription")
        raise HTTPException(status_code=503, detail="Голосовой сервис пока не настроен: в Render backend нужен ключ Gemini API.")

    # The dedicated transcription endpoint repeatedly returned HTTP 200 with an
    # empty transcript in production. Call the Flash model that has actually
    # transcribed this user's WAV successfully, avoiding the wasted first request.
    payload = {
        "contents": [{
            "role": "user",
            "parts": [
                {"text": (
                    "Прослушай приложенную аудиозапись и дословно расшифруй речь "
                    "на русском языке. Верни только распознанный текст, без пояснений. "
                    "Сохраняй названия марок и моделей автомобилей, особенно Toyota RAV4. "
                    "Если речи нет, верни пустую строку."
                )},
                {"inline_data": {
                    "mime_type": "audio/wav",
                    "data": base64.b64encode(audio).decode("ascii")
                }}
            ]
        }],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": 512}
    }
    try:
        timeout = httpx.Timeout(25.0, connect=10.0)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.6-flash:generateContent",
                headers={"x-goog-api-key": gemini_key},
                json=payload
            )
        if response.status_code != 200:
            try:
                error_payload = response.json()
                error_info = error_payload.get("error", {}) if isinstance(error_payload, dict) else {}
                error_message = str(error_info.get("message", ""))[:300]
                error_code = error_info.get("status") or response.status_code
            except ValueError:
                error_message, error_code = "non-JSON response", response.status_code
            logger.error(
                "Gemini Flash voice transcription failed: http=%s code=%s message=%s",
                response.status_code, error_code, error_message
            )
            raise HTTPException(
                status_code=503 if response.status_code in (429, 503) else 502,
                detail="Сервис распознавания речи временно перегружен. Попробуйте ещё раз."
            )
        data = response.json()
        candidates = data.get("candidates") or []
        parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
        transcript = " ".join(part.get("text", "") for part in parts if part.get("text"))
        transcript = transcript.strip().strip('"«»').strip()
        if not transcript:
            logger.warning("Gemini Flash returned an empty voice transcript")
            raise HTTPException(
                status_code=422,
                detail="Не удалось разобрать запись. Проверьте, что во время записи слышна речь, и попробуйте ещё раз."
            )
        logger.info("Gemini voice transcription succeeded: transcript_chars=%s", len(transcript))
        return {"ok": True, "text": transcript}
    except HTTPException:
        raise
    except httpx.TimeoutException:
        logger.error("Gemini Flash voice transcription timed out")
        raise HTTPException(status_code=504, detail="Gemini долго обрабатывает запись. Попробуйте короткий запрос ещё раз.")
    except httpx.RequestError as exc:
        logger.error("Gemini Flash voice transcription network error: %s", type(exc).__name__)
        raise HTTPException(status_code=502, detail="Не удалось связаться с сервисом распознавания речи.")
