"""FastAPI app: two routes under a single uvicorn process.

- POST /api/orders        Supabase Database Webhook on INSERT into `orders`.
- POST /telegram/webhook  Telegram bot webhook.
"""

import logging
from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Request

from app.config import settings
from app.handlers.orders import handle_new_order
from app.telegram_bot import process_update

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("splitwise-telebot")

app = FastAPI(title="splitwise-telebot")


@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/api/orders")
async def orders_webhook(request: Request, x_webhook_secret: Optional[str] = Header(default=None)):
    if x_webhook_secret != settings.orders_webhook_secret:
        raise HTTPException(status_code=401, detail="invalid webhook secret")

    payload = await request.json()

    if payload.get("type") != "INSERT" or payload.get("table") != "orders":
        return {"ok": True, "skipped": True}

    record = payload.get("record")
    if not record:
        raise HTTPException(status_code=400, detail="missing record in payload")

    try:
        await handle_new_order(record)
    except Exception:
        logger.exception("Failed to process new order webhook for order_id=%s", record.get("id"))
        raise HTTPException(status_code=500, detail="failed to process order") from None

    return {"ok": True}


@app.post("/telegram/webhook")
async def telegram_webhook(request: Request):
    update_data = await request.json()
    try:
        await process_update(update_data)
    except Exception:
        # Telegram retries on non-2xx, which could cause a storm on a
        # persistent bug - log and swallow instead.
        logger.exception("Failed to process Telegram update")
    return {"ok": True}
