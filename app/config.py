"""Environment variable loading for the service.

Kept deliberately tiny: read once at import time into a module-level
Settings instance, fail fast and loudly if something required is missing.
"""

import os

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Missing required environment variable: {name}. "
            f"Copy .env.example to .env and fill it in."
        )
    return value


class Settings:
    def __init__(self) -> None:
        self.bot_token = _require("BOT_TOKEN")
        self.supabase_url = _require("SUPABASE_URL")
        self.supabase_service_role_key = _require("SUPABASE_SERVICE_ROLE_KEY")
        self.orders_webhook_secret = _require("ORDERS_WEBHOOK_SECRET")


settings = Settings()
