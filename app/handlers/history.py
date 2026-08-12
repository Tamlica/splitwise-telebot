"""Task 4.6: /history [name]

Lists unsettled orders where the given member still owes money, i.e.
they have an unsettled order_item on that order (as the ower - being
listed as the payer of a fully-settled order isn't "outstanding" for
them, so we don't include that case), oldest first.
"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app import db
from app.formatting import format_rupiah

router = Router(name="history")


@router.message(Command("history"))
async def cmd_history(message: Message) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("Usage: /history <name>")
        return

    name = args[1].strip()
    member = db.get_member_by_name_ci(name)
    if not member:
        await message.reply(f"No member named '{name}'.")
        return

    items = db.get_unsettled_items_for_member(member["id"])
    if not items:
        await message.reply(f"{member['name']} has no outstanding orders.")
        return

    items.sort(key=lambda item: (item.get("orders") or {}).get("order_date", ""))

    lines = [f"{member['name']}'s outstanding orders:"]
    for item in items:
        order = item.get("orders") or {}
        location = order.get("location", "Unknown")
        order_date = order.get("order_date", "?")
        lines.append(f"- {order_date} · {location}: {format_rupiah(item['final_amount'])}")

    await message.reply("\n".join(lines))
