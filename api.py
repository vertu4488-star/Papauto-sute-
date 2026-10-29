import os
import re
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
        f"<b>Имя:</b> {lead.name or 'не указано'}\n"
        f"<b>Контакт:</b> {lead.contact}\n"
        f"<b>Направление:</b> {lead.country}\n"
        f"<b>Бюджет:</b> {f'{lead.budget:,}'.replace(',', ' ' ) + ' ₽' if lead.budget is not None else 'не указан'}\n"
        f"<b>Город:</b> {lead.city}\n"
        f"<b>Запрос:</b> {lead.request}"
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
