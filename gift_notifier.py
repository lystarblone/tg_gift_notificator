import logging
from aiogram import Bot
from config import CHAT_ID, DATA_FILEPATH
from models import StarGiftsData

logger = logging.getLogger(__name__)

def get_notify_text(gift):
    """Формирование текста уведомления"""
    is_limited = gift.get("limited", False)
    total_amount = gift.get("availability_total", 0)
    available_amount = gift.get("availability_remains", 0)
    
    available_percentage = ""
    if is_limited and total_amount > 0:
        percentage = round((available_amount / total_amount) * 100, 2)
        available_percentage = f"📊 Доступно: {available_amount} ({percentage}%)"
    
    return (
        "🔥 Появился новый лимитированный подарок\n\n"
        f"№ {gift.get('id')} ({gift.get('id')})\n"
        f"🎯 Общее количество: {total_amount if is_limited else 'N/A'}\n"
        f"💎 Цена: {gift.get('stars', 0)} ⭐️\n"
        f"♻️ Цена конвертации: {gift.get('convert_stars', 0)} ⭐️\n"
        f"{available_percentage if is_limited else ''}"
    )

async def notify_new_gift(bot: Bot, gift):
    """Отправка уведомления о новом подарке"""
    message = get_notify_text(gift)
    sticker = gift.get("sticker", {})
    file_id = sticker.get("file_id")
    
    try:
        sent_message = None
        if file_id:
            sent_message = await bot.send_photo(
                chat_id=CHAT_ID,
                photo=file_id,
                caption=message
            )
        else:
            sent_message = await bot.send_message(chat_id=CHAT_ID, text=message)
        
        logger.info(f"Отправлено уведомление о новом подарке {gift.get('id')}")
        
        star_gifts_data = StarGiftsData.load(DATA_FILEPATH)
        for stored_gift in star_gifts_data.star_gifts:
            if stored_gift.id == gift["id"]:
                stored_gift.message_id = sent_message.message_id
                break
        star_gifts_data.save()
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления: {e}")
        await bot.send_message(chat_id=CHAT_ID, text=message)