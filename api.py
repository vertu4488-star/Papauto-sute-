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
    key = os.getenv("TKS_AUTO_API_KEY", "").strip()
    if not key:
        raise HTTPException(status_code=503, detail="Расчёт TKS.RU пока не активирован: в Render нужно добавить лицензионный ключ TKS_AUTO_API_KEY.")
    params = {
        "cost": req.cost, "volume": req.volume, "currency": req.currency,
        "power": req.power, "power_edizm": "ls", "engine_type": req.engine_type,
        "age": req.age, "face": req.face, "ts_type": "00_8703",
        "sequential": str(req.sequential).lower(), "chassis": "nshs",
        "forwarder": "false", "caravan": "false", "offroad": "false",
        "mdvs_gt_m30ed": "false",
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

@app.get("/api/vehicles")
async def search_vehicles(country: str = "japan", make: str = "", model: str = "",
                          year_from: int = 1990, year_to: int = 2027,
                          max_price: int = 0, limit: int = 20):
    api_url = os.getenv("AUCTIONS_API_URL", "").strip()
    api_key = os.getenv("AUCTIONS_API_KEY", "").strip()
    if not api_url or not api_key:
        raise HTTPException(status_code=503, detail="Каталог реальных автомобилей не активирован: требуется API поставщика аукционных данных и его ключ.")
    if country not in {"japan", "south-korea", "china"}:
        raise HTTPException(status_code=400, detail="Неизвестное направление поиска.")
    if year_from < 1990 or year_to > 2027 or year_from > year_to:
        raise HTTPException(status_code=400, detail="Проверьте диапазон годов выпуска.")
    params = {"country": country, "make": make, "model": model, "year_from": year_from,
              "year_to": year_to, "max_price": max_price or None, "limit": min(max(limit, 1), 50)}
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
