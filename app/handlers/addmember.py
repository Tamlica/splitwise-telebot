"""Task 4.5: /addmember <name>"""

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app import db

router = Router(name="addmember")


@router.message(Command("addmember"))
async def cmd_addmember(message: Message) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.reply("Usage: /addmember <name>")
        return

    name = args[1].strip()

    existing = db.get_member_by_name_ci(name)
    if existing:
        await message.reply(f"{existing['name']} already exists.")
        return

    try:
        member = db.create_member(name)
    except Exception as exc:
        if "duplicate" in str(exc).lower() or "unique" in str(exc).lower():
            await message.reply(f"{name} already exists.")
        else:
            await message.reply(f"Failed to add member: {exc}")
        return

    await message.reply(f"Added {member['name']} ✅")
