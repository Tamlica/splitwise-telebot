"""Task 4.3: settlement button tap, plus the shared message-refresh helper
that Task 4.3b (/paid) also reuses.
"""

import logging
from typing import Optional

from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from app import db
from app.bot_instance import bot
from app.formatting import format_order_message

logger = logging.getLogger(__name__)

router = Router(name="settlement")


def build_settlement_keyboard(items: list[dict]) -> Optional[InlineKeyboardMarkup]:
    """One '✅ {name} paid' button per still-unsettled item.

    The payer's own order_item is always inserted pre-settled, so this
    naturally excludes them without needing to special-case payer_id.
    """
    buttons = []
    for item in items:
        if item.get("settled"):
            continue
        member = item.get("members") or {}
        name = member.get("name", "?")
        buttons.append([InlineKeyboardButton(text=f"✅ {name} paid", callback_data=f"settle:{item['id']}")])
    if not buttons:
        return None
    return InlineKeyboardMarkup(inline_keyboard=buttons)


async def refresh_order_message(order_id: str) -> None:
    """Re-render an order's group-chat message in place (text + keyboard)
    after one or more of its order_items changed settled state."""
    order = db.get_order(order_id)
    if not order or not order.get("telegram_message_id"):
        return

    items = db.get_order_items_with_members(order_id)
    payer = db.get_member(order["payer_id"])
    payer_name = payer["name"] if payer else "Unknown"

    text = format_order_message(order["location"], order["order_date"], payer_name, items)
    keyboard = build_settlement_keyboard(items)

    try:
        await bot.edit_message_text(
            chat_id=order["group_chat_id"],
            message_id=order["telegram_message_id"],
            text=text,
            reply_markup=keyboard,
        )
    except Exception:
        # e.g. message content unchanged (Telegram rejects no-op edits), or
        # the message was deleted - neither should break the caller's flow.
        logger.info("Could not refresh Telegram message for order %s", order_id, exc_info=True)


@router.callback_query(F.data.startswith("settle:"))
async def on_settle(callback: CallbackQuery) -> None:
    item_id = callback.data.split(":", 1)[1]
    item = db.get_order_item(item_id)

    if not item:
        await callback.answer("This item no longer exists.", show_alert=True)
        return

    if item.get("settled"):
        await callback.answer("Already marked paid.")
        return

    member = item.get("members") or {}
    telegram_username = member.get("telegram_username")
    tapper_username = callback.from_user.username if callback.from_user else None

    if telegram_username and (not tapper_username or tapper_username.lower() != telegram_username.lower()):
        await callback.answer(f"Only {member.get('name', 'that person')} can mark this paid.", show_alert=True)
        return

    db.settle_order_item(item_id)
    await refresh_order_message(item["order_id"])
    await callback.answer("Marked as paid ✅")
