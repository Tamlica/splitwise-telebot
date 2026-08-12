"""Task 4.3b: /paid <member1> to <member2>

Trust-based - any group member can run this for anyone, no identity check.
"""

import difflib
import re
from typing import Optional

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app import db
from app.formatting import format_rupiah
from app.handlers.settlement import refresh_order_message

router = Router(name="paid")

_SPLIT_TO = re.compile(r"\s+to\s+", re.IGNORECASE)


def _resolve_member_name(fragment: str, all_names: list[str]) -> tuple[Optional[str], list[str]]:
    """Case-insensitive/trimmed exact match first; otherwise fuzzy suggestions."""
    fragment = fragment.strip()
    for name in all_names:
        if name.strip().lower() == fragment.lower():
            return name, []
    suggestions = difflib.get_close_matches(fragment, all_names, n=3, cutoff=0.5)
    return None, suggestions


@router.message(Command("paid"))
async def cmd_paid(message: Message) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not _SPLIT_TO.search(args[1]):
        await message.reply("Usage: /paid <name> to <name>  (e.g. /paid tam to raihan)")
        return

    frag1, frag2 = _SPLIT_TO.split(args[1], maxsplit=1)
    frag1, frag2 = frag1.strip(), frag2.strip()
    if not frag1 or not frag2:
        await message.reply("Usage: /paid <name> to <name>  (e.g. /paid tam to raihan)")
        return

    all_names = db.get_all_member_names()
    name1, suggestions1 = _resolve_member_name(frag1, all_names)
    name2, suggestions2 = _resolve_member_name(frag2, all_names)

    if not name1 or not name2:
        bad_fragment = frag1 if not name1 else frag2
        suggestions = suggestions1 if not name1 else suggestions2
        if suggestions:
            await message.reply(f"Couldn't find '{bad_fragment}'. Did you mean: {', '.join(suggestions)}?")
        else:
            await message.reply(f"Couldn't find a member named '{bad_fragment}'.")
        return

    member1 = db.get_member_by_name_ci(name1)
    member2 = db.get_member_by_name_ci(name2)

    items = db.get_unsettled_items_between(member1["id"], member2["id"])
    if not items:
        await message.reply(f"No outstanding balance from {member1['name']} to {member2['name']}.")
        return

    total = sum(item["final_amount"] for item in items)
    item_ids = [item["id"] for item in items]
    order_ids = {item["orders"]["id"] for item in items}

    db.settle_order_items(item_ids)

    for order_id in order_ids:
        await refresh_order_message(order_id)

    await message.reply(
        f"✅ {member1['name']} → {member2['name']}: {format_rupiah(total)} across {len(items)} orders marked paid."
    )
