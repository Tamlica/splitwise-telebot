"""Single shared aiogram Bot instance.

Split out from telegram_bot.py so that handler modules (which need to
call the bot directly, e.g. to edit a message) don't have to import the
Dispatcher and create a circular import with telegram_bot.py, which in
turn imports the handler routers.
"""

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import settings

bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
