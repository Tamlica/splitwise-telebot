"""POST /api/orders business logic (Task 4.2).

Called from the FastAPI route in app/main.py after the shared-secret
check has already passed.
"""

import logging

from app import db
from app.bot_instance import bot
from app.formatting import format_order_message
from app.handlers.settlement import build_settlement_keyboard

logger = logging.getLogger(__name__)


async def handle_new_order(record: dict) -> None:
    order_id = record["id"]
    group_chat_id = record["group_chat_id"]
    thread_id = record.get("telegram_thread_id")
    location = record["location"]
    order_date = record["order_date"]
    payer_id = record["payer_id"]

    items = db.get_order_items_with_members(order_id)
    payer = db.get_member(payer_id)
    payer_name = payer["name"] if payer else "Unknown"

    text = format_order_message(location, order_date, payer_name, items)
    keyboard = build_settlement_keyboard(items)

    sent = await bot.send_message(
        chat_id=group_chat_id,
        text=text,
        reply_markup=keyboard,
        message_thread_id=thread_id,
    )

    db.set_order_telegram_message_id(order_id, sent.message_id)
