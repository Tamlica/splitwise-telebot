# splitwise-telebot

Telegram bot half of the lunch-bill-splitting system. The companion React
app (`splitwise`) writes rows directly into a shared Supabase Postgres
database when someone saves a bill split; this service reacts to that via
a Supabase Database Webhook, and lets the group settle up via Telegram
buttons and slash commands.

## Stack

- Python, FastAPI (single uvicorn process, two HTTP routes)
- aiogram v3 (async), run in **webhook** mode - updates are fed into the
  aiogram `Dispatcher` from a FastAPI route rather than aiogram polling or
  running its own web server
- `supabase-py`, initialized with the **service-role key** (bypasses RLS -
  keep it server-side only)

## Layout

```
app/
  main.py            FastAPI app, POST /api/orders and POST /telegram/webhook
  config.py          env var loading
  bot_instance.py    shared aiogram Bot instance
  db.py              supabase client singleton + query helpers
  telegram_bot.py    aiogram Dispatcher wiring (routers) + webhook update feed
  formatting.py      Rupiah formatting, message templates
  debt.py            pure debt-simplification algorithm (unit tested)
  handlers/
    orders.py        POST /api/orders logic - post new-order message + buttons
    settlement.py     settle-button callback + shared message-refresh helper
    paid.py           /paid <name> to <name>
    balance.py        /balance
    addmember.py      /addmember <name>
    history.py        /history <name>
tests/
  test_debt.py        unit tests for debt.py
scripts/
  set_webhook.py       one-time: registers the Telegram webhook URL
```

## Endpoints

- `POST /api/orders` - hit by a Supabase Database Webhook on `INSERT` into
  `orders`. Requires header `X-Webhook-Secret: <ORDERS_WEBHOOK_SECRET>` or
  it returns 401. Formats and sends the order summary + settle buttons to
  `orders.group_chat_id`, then writes the resulting message id back onto
  `orders.telegram_message_id`.
- `POST /telegram/webhook` - standard Telegram webhook receiver; hands the
  raw update to the aiogram `Dispatcher`.

## Known simplifications

- `supabase-py`'s client is synchronous. Given this bot's volume (a handful
  of lunch orders a day, small group chats), calling it directly from async
  handlers - rather than a thread pool or task queue - is an intentional
  simplification, not an oversight.
- The settle-button identity check is soft, per spec: if a member has no
  `telegram_username` on file, anyone can tap their button, matching the
  trust-based nature of `/paid`, `/addmember`, etc.

## Requirements

**Python >= 3.10.** aiogram auto-installs `uvloop` as the asyncio event loop
policy at import time when it's available. On Python 3.9, `asyncio.Lock()`
(used internally by aiogram's `Dispatcher`) eagerly calls `get_event_loop()`
in its constructor, and uvloop's `get_event_loop()` raises instead of
creating one outside a running loop - so `Dispatcher()` crashes at import on
3.9. Python 3.10+ removed that eager loop lookup, so this is a non-issue
there. A `.python-version` file pins `3.11` for Railway/nixpacks; use the
same locally (`brew install python@3.11` on macOS if your default `python3`
is older).

## Local setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in BOT_TOKEN, SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY, ORDERS_WEBHOOK_SECRET
uvicorn app.main:app --reload
```

Run tests:

```bash
pip install pytest
pytest
```

## Manual deploy steps (not done by this repo's code)

1. **Register the bot with @BotFather** and grab `BOT_TOKEN`.
2. **Create a Railway project** for this repo. Railway auto-detects Python
   via nixpacks and uses the `Procfile`. Set the environment variables from
   `.env.example` (`BOT_TOKEN`, `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`,
   `ORDERS_WEBHOOK_SECRET`) in the Railway project settings.
3. **After deploy**, register the Telegram webhook once:
   ```bash
   BOT_TOKEN=... PUBLIC_URL=https://your-app.up.railway.app python scripts/set_webhook.py
   ```
4. **Configure the Supabase Database Webhook**: on `INSERT` into `orders`,
   POST to `https://your-app.up.railway.app/api/orders` with header
   `X-Webhook-Secret: <same value as ORDERS_WEBHOOK_SECRET>`.

## Commands

- `/addmember <name>` - add a member.
- `/balance` - simplified net settlements for the current chat.
- `/paid <name> to <name>` - mark all outstanding balances from one member
  to another as settled (e.g. `/paid tam to raihan`).
- `/history <name>` - list a member's outstanding (unsettled) orders.
- Tapping a "✅ {name} paid" button under an order message settles that
  person's line for that order.
