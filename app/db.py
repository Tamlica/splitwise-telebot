"""Supabase client singleton plus small typed query helpers.

supabase-py's client is synchronous. Given the low volume this bot
handles (a handful of lunch orders a day in a couple of group chats),
calling it directly from async handlers is an acceptable simplification
rather than reaching for a task queue or a thread pool - see README.
"""

from datetime import datetime, timezone
from typing import Optional

from supabase import Client, create_client

from app.config import settings

_client: Optional[Client] = None


def get_client() -> Client:
    global _client
    if _client is None:
        _client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    return _client


# --- members -----------------------------------------------------------


def get_member(member_id: str) -> Optional[dict]:
    res = get_client().table("members").select("*").eq("id", member_id).limit(1).execute()
    return res.data[0] if res.data else None


def get_member_by_name_ci(name: str) -> Optional[dict]:
    """Case-insensitive, trimmed exact match on members.name."""
    res = get_client().table("members").select("*").ilike("name", name.strip()).limit(1).execute()
    return res.data[0] if res.data else None


def get_all_member_names() -> list[str]:
    res = get_client().table("members").select("name").execute()
    return [row["name"] for row in res.data]


def create_member(name: str) -> dict:
    res = get_client().table("members").insert({"name": name}).execute()
    return res.data[0]


# --- orders / order_items ----------------------------------------------


def get_order(order_id: str) -> Optional[dict]:
    res = get_client().table("orders").select("*").eq("id", order_id).limit(1).execute()
    return res.data[0] if res.data else None


def set_order_telegram_message_id(order_id: str, message_id: int) -> None:
    get_client().table("orders").update({"telegram_message_id": message_id}).eq("id", order_id).execute()


def get_order_items_with_members(order_id: str) -> list[dict]:
    res = (
        get_client()
        .table("order_items")
        .select("*, members(name, telegram_username)")
        .eq("order_id", order_id)
        .execute()
    )
    return res.data


def get_order_item(item_id: str) -> Optional[dict]:
    res = (
        get_client()
        .table("order_items")
        .select("*, members(name, telegram_username)")
        .eq("id", item_id)
        .limit(1)
        .execute()
    )
    return res.data[0] if res.data else None


def settle_order_item(item_id: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    get_client().table("order_items").update({"settled": True, "settled_at": now}).eq("id", item_id).execute()


def settle_order_items(item_ids: list[str]) -> None:
    if not item_ids:
        return
    now = datetime.now(timezone.utc).isoformat()
    get_client().table("order_items").update({"settled": True, "settled_at": now}).in_("id", item_ids).execute()


def get_unsettled_items_between(debtor_id: str, creditor_id: str) -> list[dict]:
    """order_items where member_id = debtor_id, settled = false, and the
    parent order's payer_id = creditor_id (i.e. debtor owes creditor)."""
    res = (
        get_client()
        .table("order_items")
        .select("*, orders!inner(id, payer_id, telegram_message_id, location, order_date, group_chat_id)")
        .eq("member_id", debtor_id)
        .eq("settled", False)
        .eq("orders.payer_id", creditor_id)
        .execute()
    )
    return res.data


def get_unsettled_items_for_chat(group_chat_id: str) -> list[dict]:
    res = (
        get_client()
        .table("order_items")
        .select("*, orders!inner(id, payer_id, group_chat_id), members(name)")
        .eq("settled", False)
        .eq("orders.group_chat_id", group_chat_id)
        .execute()
    )
    return res.data


def get_unsettled_items_for_member(member_id: str) -> list[dict]:
    res = (
        get_client()
        .table("order_items")
        .select("*, orders!inner(id, location, order_date, payer_id)")
        .eq("member_id", member_id)
        .eq("settled", False)
        .execute()
    )
    return res.data
