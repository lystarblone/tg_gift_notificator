## Telegram bot: gift notifications (aiogram 3)

- Subscribes users via /start
- Checks for new gifts every second
- Notifies all subscribers when new gifts appear

### Setup

1. Create and fill .env

```
cp .env.example .env
# put your bot token into .env
```

2. Install deps (recommended Python 3.10+)

```
pip install -r requirements.txt
```

3. Run

```
python -m bot.main
```

### Configuration via env

- `BOT_TOKEN` (required): Telegram bot token
- `CHECK_INTERVAL_SECONDS` (optional, default 1)
- `GIFTS_FEED_PATH` (optional): path to JSON feed with gifts (default `data/gifts_feed.json`)
- `STATE_PATH` (optional): path to state JSON (default `data/state.json`)

### Gifts feed format (example in data/gifts_feed.json)

```json
[
  { "id": 1, "title": "Gift A", "published_at": "2025-01-01T12:00:00Z" },
  { "id": 2, "title": "Gift B", "published_at": "2025-01-01T12:01:00Z" }
]
```

Update this file externally; the bot detects new items by id and broadcasts.
