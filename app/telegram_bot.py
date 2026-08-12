"""aiogram Dispatcher wiring: registers all command/callback routers and
exposes `process_update`, which POST /telegram/webhook feeds raw update
JSON into.
"""

from aiogram import Dispatcher
from aiogram.types import Update

from app.bot_instance import bot
from app.handlers import addmember, balance, history, paid, settlement

dp = Dispatcher()

dp.include_router(addmember.router)
dp.include_router(balance.router)
dp.include_router(history.router)
dp.include_router(paid.router)
dp.include_router(settlement.router)


async def process_update(update_data: dict) -> None:
    update = Update.model_validate(update_data)
    await dp.feed_update(bot, update)
