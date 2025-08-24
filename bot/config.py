import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class Config:
    bot_token: str
    check_interval_seconds: float = 1.0
    gifts_feed_path: str = "data/gifts_feed.json"
    state_path: str = "data/state.json"


def load_config() -> Config:
    load_dotenv()
    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        raise RuntimeError("BOT_TOKEN is not set. Put it into .env or environment.")

    check_interval_str = os.getenv("CHECK_INTERVAL_SECONDS", "1").strip()
    check_interval = float(check_interval_str or "1")

    gifts_feed_path = os.getenv("GIFTS_FEED_PATH", "data/gifts_feed.json").strip()
    state_path = os.getenv("STATE_PATH", "data/state.json").strip()

    return Config(
        bot_token=bot_token,
        check_interval_seconds=check_interval,
        gifts_feed_path=gifts_feed_path,
        state_path=state_path,
    )
