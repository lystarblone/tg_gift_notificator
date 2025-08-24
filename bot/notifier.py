import asyncio
from typing import Set
from aiogram import Bot
from .config import Config
from .storage import JsonStateStore
from .gifts_source import get_new_gifts


async def notifier_loop(bot: Bot, cfg: Config, store: JsonStateStore, stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        try:
            last_seen = await store.get_last_seen_id()
            new_gifts = await get_new_gifts(cfg.gifts_feed_path, last_seen)
            if new_gifts:
                subscribers: Set[int] = await store.get_subscribers()
                for gift in new_gifts:
                    text = f"Новый подарок: {gift['title']} (id: {gift['id']})"
                    for chat_id in list(subscribers):
                        try:
                            await bot.send_message(chat_id, text)
                        except Exception:
                            pass
                await store.set_last_seen_id(max(g["id"] for g in new_gifts))
        except asyncio.CancelledError:
            break
        except Exception:
            pass
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=cfg.check_interval_seconds)
        except asyncio.TimeoutError:
            pass