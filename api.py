import os
import logging
import html
import asyncio
import xml.etree.ElementTree as ET
from urllib.parse import quote
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("papauto.api")

app = FastAPI(title="PAPAUTO Lead API", version="1.0.0")

ALLOWED_ORIGINS = [
    "https://papauto.ru",
    "https://www.papauto.ru",
    "https://papauto-site.onrender.com",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
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
        "auction_provider_configured": bool(os.getenv("AUCTIONS_API_URL") and os.getenv("AUCTIONS_API_KEY")),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

@app.post("/api/leads")
async def create_lead(lead: Lead):
    if not lead.consent:
        raise HTTPException(status_code=400, detail="Необходимо согласие на обработку данных.")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat_id:
        raise HTTPException(status_code=503, detail="Приём заявок временно не настроен. Напишите менеджеру в Telegram.")
    text = (
        "🚘 <b>Новая заявка PAPAUTO</b>\n"
        f"<b>Время:</b> {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n"
        f"<b>Имя:</b> {html.escape(lead.name or 'не указано')}\n"
        f"<b>Контакт:</b> {html.escape(lead.contact)}\n"
        f"<b>Направление:</b> {html.escape(lead.country)}\n"
        f"<b>Бюджет:</b> {f'{lead.budget:,}'.replace(',', ' ' ) + ' ₽' if lead.budget is not None else 'не указан'}\n"
        f"<b>Город:</b> {html.escape(lead.city)}\n"
        f"<b>Запрос:</b> {html.escape(lead.request)}"
    )
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=12.0) as client:
            response = await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True})
        data = response.json()
        if response.status_code != 200 or not data.get("ok"):
            raise HTTPException(status_code=502, detail="Не удалось передать заявку менеджеру. Попробуйте позже.")
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Не удалось связаться с сервисом уведомлений. Попробуйте позже.")
    return {"ok": True, "message": "Заявка отправлена менеджеру."}


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
                params={"key": gemini_key},
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


@app.get("/api/vehicles")
async def search_vehicles(country: str = "japan", make: str = "", model: str = "",
                          year_from: int = 1990, year_to: int = 2027,
                          max_price: int = 0, mileage_max: Optional[int] = None,
                          volume_min: Optional[int] = None, volume_max: Optional[int] = None,
                          body: str = "", grade: str = "", lot_number: str = "",
                          limit: int = 20):
    """Search live Korean listings through XAPI Korea. Japan/China remain disabled until a provider is configured."""
    if country not in {"japan", "south-korea", "china"}:
        raise HTTPException(status_code=400, detail="Неизвестное направление поиска.")
    if year_from < 1990 or year_to > 2030 or year_from > year_to:
        raise HTTPException(status_code=400, detail="Проверьте диапазон годов выпуска.")
    if max_price < 0 or (mileage_max is not None and mileage_max < 0) or (volume_min is not None and volume_min < 0) or (volume_max is not None and volume_max < 0):
        raise HTTPException(status_code=400, detail="Бюджет, пробег и объём не могут быть отрицательными.")
    if volume_min is not None and volume_max is not None and volume_min > volume_max:
        raise HTTPException(status_code=400, detail="Минимальный объём двигателя не может быть больше максимального.")
    limit = min(max(limit, 1), 50)

    if country == "south-korea":
        api_key = (os.getenv("XAPIKOREA_API_KEY") or "").strip()
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
            "source": "all",
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
                raise HTTPException(status_code=503, detail="XAPI Korea отклонил ключ. Проверьте XAPIKOREA_API_KEY в Render.")
            if response.status_code == 429:
                raise HTTPException(status_code=429, detail="Достигнут лимит запросов XAPI Korea. Подождите и повторите поиск.")
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"XAPI Korea вернул ошибку поиска (HTTP {response.status_code}).")
            try:
                payload = response.json()
            except ValueError:
                raise HTTPException(status_code=502, detail="XAPI Korea вернул ответ в неизвестном формате.")
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                raise HTTPException(status_code=502, detail="Формат ответа XAPI Korea не соответствует документации.")
            results = []
            for item in payload["results"][:limit]:
                if not isinstance(item, dict):
                    continue
                price = item.get("price_krw")
                mileage = item.get("mileage_km")
                year = item.get("year") or item.get("model_year")
                listing_id = item.get("id")
                source = str(item.get("source") or "encar")
                photos = item.get("photos") if isinstance(item.get("photos"), list) else []
                if not photos:
                    thumbnail = item.get("thumbnail") or item.get("thumbnail_url") or item.get("image_url") or item.get("image")
                    if isinstance(thumbnail, str) and thumbnail.startswith("https://"):
                        photos = [thumbnail]
                results.append({
                    "id": listing_id,
                    "source": source,
                    "make": _fix_mojibake(item.get("manufacturer") or item.get("make") or ""),
                    "model": _fix_mojibake(item.get("model") or ""),
                    "year": (str(year)[:4] if year is not None and str(year).isdigit() and len(str(year)) >= 4 else year),
                    "mileage": mileage,
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
            return {
                "ok": True,
                "source": "XAPI Korea",
                "country": "south-korea",
                "total_count": payload.get("total_count", len(results)),
                "partial": bool(payload.get("partial", False)),
                "source_errors": payload.get("source_errors", []),
                "results": results,
                "disclaimer": "Цены показаны в корейских вонах и не включают доставку, таможню, оформление и доставку по России.",
            }
        except HTTPException:
            raise
        except httpx.RequestError as exc:
            logger.error("XAPI Korea connection failure: %s: %s", type(exc).__name__, str(exc))
            raise HTTPException(status_code=502, detail="Не удалось связаться с XAPI Korea. Проверьте логи сервера для определения сетевой ошибки и попробуйте позже.")

    # Japan and China are intentionally not routed to a Korean provider.
    raise HTTPException(
        status_code=503,
        detail="Для этого направления пока не подключён подтверждённый источник актуальных объявлений. Выберите Южную Корею или отправьте заявку на индивидуальный подбор."
    )



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
    if country == "south-korea":
        api_key = (os.getenv("XAPIKOREA_API_KEY") or "").strip()
        if not api_key:
            raise HTTPException(status_code=503, detail="Поиск по Южной Корее пока не активирован: в Render нужен XAPIKOREA_API_KEY.")
        params = {"brand": make or None, "model": model or None, "year_from": year_from, "year_to": year_to, "limit": limit, "page": 1, "lang": "en", "source": "all"}
        params = {k: v for k, v in params.items() if v is not None and v != ""}
        try:
            async with httpx.AsyncClient(timeout=25.0) as client:
                response = await client.get("https://api.xapikorea.com/v1/search", params=params, headers={"X-API-Key": api_key, "Accept": "application/json"})
            if response.status_code == 401:
                raise HTTPException(status_code=503, detail="XAPI Korea отклонил ключ. Проверьте XAPIKOREA_API_KEY в Render.")
            if response.status_code == 429:
                raise HTTPException(status_code=429, detail="Достигнут лимит XAPI Korea. Повторите поиск позже.")
            if response.status_code != 200:
                raise HTTPException(status_code=502, detail=f"XAPI Korea вернул ошибку HTTP {response.status_code}.")
            payload = response.json()
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                raise HTTPException(status_code=502, detail="Источник вернул неизвестный формат данных.")
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
    if country == "japan":
        detail = "Для поиска по моделям и агрегированной статистики завершённых торгов Японии нужен разрешённый доступ к историческому источнику аукционных данных. Доступный JP Sheet API ищет историю по номеру кузова, а не по марке и модели."
        source = "Исторический японский аукционный источник ещё не подключён"
    else:
        detail = "Для статистики завершённых торгов Китая нужен источник, который явно предоставляет результаты состоявшихся аукционов. Каталоги объявлений нельзя выдавать за цены продажи."
        source = "Исторический китайский аукционный источник ещё не подключён"
    return {"ok": True, "country": country, "data_type": "unavailable", "source": source, "count": 0,
        "records": [], "message": detail, "disclaimer": "Показываем только данные, происхождение которых можно объяснить и проверить."}

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
    try:
        async with httpx.AsyncClient(timeout=25.0) as client:
            response = await client.post(
                "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.8-flash:generateContent",
                params={"key": gemini_key},
                json={
                    "contents": [{"role": "user", "parts": [{"text": __import__("json").dumps({"instruction": instruction, "request": brief}, ensure_ascii=False)}]}],
                    "generationConfig": {"responseMimeType": "application/json", "temperature": 0.2}
                }
            )
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="ИИ-подбор не ответил. Проверьте ключ Gemini API и доступность модели.")
        payload = response.json()
        candidates = payload.get("candidates") or []
        parts = (candidates[0].get("content") or {}).get("parts") or [] if candidates else []
        raw = next((part.get("text", "") for part in parts if part.get("text")), "")
        if not raw:
            raise HTTPException(status_code=502, detail="ИИ-подбор вернул пустой ответ. Попробуйте уточнить запрос.")
        import json
        result = json.loads(raw)
        allowed = {(item["make"].lower(), item["model"].lower()) for item in catalogue}
        recommendations = []
        for item in result.get("recommendations", [])[:5]:
            if not isinstance(item, dict):
                continue
            key = (str(item.get("make", "")).lower(), str(item.get("model", "")).lower())
            if key in allowed:
                recommendations.append({
                    "make": item["make"], "model": item["model"],
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
    except HTTPException:
        raise
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Не удалось связаться с ИИ-помощником. Попробуйте позже.")
    except (ValueError, KeyError, IndexError, TypeError):
        raise HTTPException(status_code=502, detail="Не удалось разобрать ответ ИИ-подбора. Попробуйте сформулировать запрос иначе.")
