"""Task 4.4: /balance - simplified net settlements for the current chat."""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app import db
from app.debt import simplify_debts
from app.formatting import format_rupiah

router = Router(name="balance")


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    chat_id = str(message.chat.id)
    items = db.get_unsettled_items_for_chat(chat_id)

    if not items:
        await message.reply("No outstanding balances 🎉")
        return

    net: dict[str, int] = {}
    payer_name_cache: dict[str, str] = {}

    for item in items:
        member = item.get("members") or {}
        debtor_name = member.get("name", "Unknown")

        order = item.get("orders") or {}
        payer_id = order.get("payer_id")
        payer_name = payer_name_cache.get(payer_id)
        if payer_name is None:
            payer = db.get_member(payer_id) if payer_id else None
            payer_name = payer["name"] if payer else "Unknown"
            payer_name_cache[payer_id] = payer_name

        amount = item["final_amount"]
        net[debtor_name] = net.get(debtor_name, 0) - amount
        net[payer_name] = net.get(payer_name, 0) + amount

    settlements = simplify_debts(net)
    if not settlements:
        await message.reply("No outstanding balances 🎉")
        return

    lines = [f"{debtor} owes {creditor} {format_rupiah(amount)}" for debtor, creditor, amount in settlements]
    await message.reply("\n".join(lines))
