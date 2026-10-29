import os
import html
from datetime import datetime, timezone
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator

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

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "telegram_configured": bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID")),
        "ai_configured": bool(os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_AI_API_KEY") or os.getenv("GOOGLE_API_KEY")),
        "tks_configured": bool(os.getenv("TKS_AUTO_API_KEY") or os.getenv("TKS_API_KEY")),
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
    api_url = os.getenv("AUCTIONS_API_URL", "").strip()
    api_key = os.getenv("AUCTIONS_API_KEY", "").strip()
    if not api_url or not api_key:
        raise HTTPException(status_code=503, detail="Каталог реальных автомобилей не активирован: требуется API поставщика аукционных данных и его ключ.")
    if country not in {"japan", "south-korea", "china"}:
        raise HTTPException(status_code=400, detail="Неизвестное направление поиска.")
    if year_from < 1990 or year_to > 2027 or year_from > year_to:
        raise HTTPException(status_code=400, detail="Проверьте диапазон годов выпуска.")
    if max_price < 0 or (mileage_max is not None and mileage_max < 0) or (volume_min is not None and volume_min < 0) or (volume_max is not None and volume_max < 0):
        raise HTTPException(status_code=400, detail="Бюджет, пробег и объём не могут быть отрицательными.")
    if volume_min is not None and volume_max is not None and volume_min > volume_max:
        raise HTTPException(status_code=400, detail="Минимальный объём двигателя не может быть больше максимального.")
    params = {"country": country, "make": make.strip()[:80], "model": model.strip()[:80], "year_from": year_from,
              "year_to": year_to, "max_price": max_price or None, "mileage_max": mileage_max,
              "volume_min": volume_min, "volume_max": volume_max, "body": body.strip()[:60],
              "grade": grade.strip()[:10], "lot_number": lot_number.strip()[:40],
              "limit": min(max(limit, 1), 50)}
    params = {key: value for key, value in params.items() if value is not None and value != ""}
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.get(api_url, params=params,
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"})
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Поставщик аукционных данных не выполнил поиск.")
        try:
            data = response.json()
        except ValueError:
            raise HTTPException(status_code=502, detail="Поставщик аукционных данных вернул неизвестный формат.")
        return {"ok": True, "source": "configured_auction_provider", "results": data}
    except httpx.RequestError:
        raise HTTPException(status_code=502, detail="Не удалось связаться с поставщиком аукционных данных.")


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
