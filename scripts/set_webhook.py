"""One-time setup script: registers this service's /telegram/webhook route
as the bot's Telegram webhook.

Run once, manually, after the service is deployed and reachable over HTTPS:

    BOT_TOKEN=... PUBLIC_URL=https://your-app.up.railway.app python scripts/set_webhook.py

(BOT_TOKEN can also come from a .env file in the project root - it's loaded
the same way app/config.py loads it.)
"""

import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()


async def main() -> None:
    bot_token = os.environ.get("BOT_TOKEN")
    public_url = os.environ.get("PUBLIC_URL")

    if not bot_token:
        print("Missing BOT_TOKEN", file=sys.stderr)
        sys.exit(1)
    if not public_url:
        print("Missing PUBLIC_URL (e.g. https://your-app.up.railway.app)", file=sys.stderr)
        sys.exit(1)

    from aiogram import Bot

    webhook_url = public_url.rstrip("/") + "/telegram/webhook"
    bot = Bot(token=bot_token)
    try:
        await bot.set_webhook(webhook_url)
        print(f"Webhook set to {webhook_url}")
        info = await bot.get_webhook_info()
        print(info)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
