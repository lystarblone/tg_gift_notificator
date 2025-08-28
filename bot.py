import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, types
from aiogram.filters import Command
from config import BOT_TOKEN, CHAT_ID, CHECK_INTERVAL
from gift_checker import check_new_gifts, process_update_gifts, check_upgrades

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

running = False

@router.message(Command("start"))
async def start(message: types.Message):
    """Обработчик команды /start"""
    global CHAT_ID, running
    CHAT_ID = message.chat.id
    running = True
    await message.answer("Бот запущен! Вы будете получать уведомления о новых подарках и апгрейдах.")
    logger.info(f"Зарегистрирован CHAT_ID: {CHAT_ID}")
    asyncio.create_task(schedule_gift_checks())
    asyncio.create_task(process_update_gifts(bot))
    asyncio.create_task(check_upgrades(bot))

@router.message(Command("stop"))
async def stop(message: types.Message):
    """Обработчик команды /stop"""
    global running
    running = False
    await message.answer("Уведомления остановлены. Используйте /start для возобновления.")
    logger.info("Уведомления остановлены пользователем")

async def schedule_gift_checks():
    """Периодическая проверка новых подарков"""
    while running:
        await check_new_gifts(bot)
        await asyncio.sleep(CHECK_INTERVAL)

async def main():
    """Запуск бота"""
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())