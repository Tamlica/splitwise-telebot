"""Rupiah formatting and Telegram message templates.

No I/O here - pure string formatting so it stays easy to reason about
and test in isolation if needed.
"""

import html
from datetime import date


def format_rupiah(amount: int) -> str:
    """Format an integer amount of Rupiah as 'Rp 18.000' (id_ID thousands grouping)."""
    return f"Rp {amount:,}".replace(",", ".")


def _date_str(order_date) -> str:
    if isinstance(order_date, date):
        return order_date.isoformat()
    return str(order_date)


def format_order_message(location: str, order_date, payer_name: str, items: list[dict]) -> str:
    """Render the group-chat message for a new order (or a re-render after a settlement).

    `items` is the list of order_items rows, each with an embedded
    `members` dict (`{"name": ..., "telegram_username": ...}`).
    """
    lines = [
        f"🍽 <b>{html.escape(location)}</b>",
        f"📅 {html.escape(_date_str(order_date))}",
        f"💰 Paid by <b>{html.escape(payer_name)}</b>",
        "",
    ]

    total = 0
    for item in sorted(items, key=lambda it: it.get("settled", False)):
        member = item.get("members") or {}
        name = member.get("name", "Unknown")
        amount = item["final_amount"]
        total += amount
        mark = "✅" if item.get("settled") else "▫️"
        lines.append(f"{mark} {html.escape(name)}: {format_rupiah(amount)}")

    lines.append("")
    lines.append(f"<b>Total: {format_rupiah(total)}</b>")
    return "\n".join(lines)
