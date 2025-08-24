from aiogram import Router, types
from aiogram.filters import CommandStart, Command
from .storage import JsonStateStore


def setup_handlers(router: Router, store: JsonStateStore) -> None:
    @router.message(CommandStart())
    async def cmd_start(message: types.Message) -> None:
        await store.add_subscriber(message.from_user.id)
        await message.answer("Вы подписаны на уведомления о новых подарках.")

    @router.message(Command(commands={"stop", "unsubscribe"}))
    async def cmd_stop(message: types.Message) -> None:
        await store.remove_subscriber(message.from_user.id)
        await message.answer("Вы отписаны от уведомлений.")

    @router.message(Command(commands={"status"}))
    async def cmd_status(message: types.Message) -> None:
        subs = await store.get_subscribers()
        await message.answer(f"Подписчиков: {len(subs)}")