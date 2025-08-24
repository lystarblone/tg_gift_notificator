import asyncio
import contextlib
import logging
import sys
from typing import Optional

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode

from .config import load_config, Config
from .handlers import setup_handlers
from .notifier import notifier_loop
from .storage import JsonStateStore


async def main() -> None:
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)

    cfg: Config = load_config()
    bot = Bot(token=cfg.bot_token, parse_mode=ParseMode.HTML)
    dp = Dispatcher()

    store = JsonStateStore(cfg.state_path)
    await store.load()

    router = Router()
    setup_handlers(router, store)
    dp.include_router(router)

    stop_event = asyncio.Event()
    bg_task: Optional[asyncio.Task] = None

    async def on_startup() -> None:
        nonlocal bg_task
        bg_task = asyncio.create_task(notifier_loop(bot, cfg, store, stop_event))

    async def on_shutdown() -> None:
        stop_event.set()
        if bg_task is not None:
            bg_task.cancel()
            with contextlib.suppress(Exception):
                await bg_task
        await bot.session.close()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())