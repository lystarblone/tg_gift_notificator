import asyncio
import logging
import requests
from aiogram import Bot
from config import BOT_TOKEN, CHAT_ID, DATA_FILEPATH, DATA_SAVER_DELAY, CHECK_UPGRADES_INTERVAL, UPGRADES_CHAT_ID
from gift_notifier import notify_new_gift, get_notify_text
from models import StarGiftsData, StarGiftData

logger = logging.getLogger(__name__)

previous_gifts = set()
update_gifts_queue = asyncio.Queue()

async def get_star_gifts():
    """Получение списка подарков через Telegram API"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getStarGifts"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if data.get("ok"):
            return data.get("result", {}).get("gifts", [])
        else:
            logger.error(f"Ошибка API: {data}")
            return []
    except Exception as e:
        logger.error(f"Ошибка при получении подарков: {e}")
        return []

async def check_is_star_gift_upgradable(bot: Bot, gift_id: int) -> bool:
    """Проверка, можно ли апгрейдить подарок"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/getStarGiftUpgradePreview?gift_id={gift_id}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get("ok", False)
    except Exception:
        logger.debug(f"Подарок {gift_id} пока не доступен для апгрейда")
        return False

async def check_new_gifts(bot: Bot):
    """Проверка новых подарков и отправка уведомлений"""
    global previous_gifts
    gifts = await get_star_gifts()
    current_gift_ids = {gift["id"] for gift in gifts}

    star_gifts_data = StarGiftsData.load(DATA_FILEPATH)
    old_gifts_dict = {g.id: g for g in star_gifts_data.star_gifts}

    new_gifts = current_gift_ids - previous_gifts

    for gift_id in new_gifts:
        gift = next((g for g in gifts if g["id"] == gift_id), None)
        if gift and CHAT_ID:
            await notify_new_gift(bot, gift)
    
    for gift_id in old_gifts_dict:
        new_gift = next((g for g in gifts if g["id"] == gift_id), None)
        if new_gift and old_gifts_dict[gift_id].available_amount != new_gift.get("availability_remains", 0):
            await update_gifts_queue.put((old_gifts_dict[gift_id], new_gift))
    
    previous_gifts.update(new_gifts)

    star_gifts_data.star_gifts = [
        StarGiftData(
            id=gift["id"],
            number=idx + 1,
            sticker_file_id=gift.get("sticker", {}).get("file_id", ""),
            sticker_file_name=f"{gift['id']}.tgs",
            price=gift.get("stars", 0),
            convert_price=gift.get("convert_stars", 0),
            available_amount=gift.get("availability_remains", 0),
            total_amount=gift.get("availability_total", 0),
            require_premium=gift.get("require_premium", False),
            user_limited=gift.get("per_user_total", None),
            is_limited=gift.get("limited", False),
            first_appearance_timestamp=gift.get("first_sale_date", None),
            last_sale_timestamp=gift.get("last_sale_date", None),
            is_upgradable=old_gifts_dict.get(gift["id"], StarGiftData(id=gift["id"], number=idx+1, sticker_file_id="", sticker_file_name=f"{gift['id']}.tgs", price=0, convert_price=0, available_amount=0, total_amount=0, is_limited=False)).is_upgradable,
            message_id=old_gifts_dict.get(gift["id"], StarGiftData(id=gift["id"], number=idx+1, sticker_file_id="", sticker_file_name=f"{gift['id']}.tgs", price=0, convert_price=0, available_amount=0, total_amount=0, is_limited=False)).message_id
        ) for idx, gift in enumerate(gifts)
    ]
    await star_gifts_data_saver(star_gifts_data)

async def process_update_gifts(bot: Bot):
    """Обработка обновлений количества доступных подарков"""
    while True:
        try:
            old_gift, new_gift = await update_gifts_queue.get()
            if old_gift.message_id is None:
                logger.warning(f"Не могу обновить подарок {old_gift.id}: отсутствует message_id")
                continue
            
            try:
                await bot.edit_message_caption(
                    chat_id=CHAT_ID,
                    message_id=old_gift.message_id,
                    caption=get_notify_text(new_gift)
                )
                logger.info(f"Обновлено сообщение для подарка {old_gift.id}: доступно {new_gift.get('availability_remains')}")
                
                star_gifts_data = StarGiftsData.load(DATA_FILEPATH)
                for stored_gift in star_gifts_data.star_gifts:
                    if stored_gift.id == new_gift["id"]:
                        stored_gift.available_amount = new_gift.get("availability_remains", 0)
                        break
                await star_gifts_data_saver(star_gifts_data)
                
            except Exception as e:
                logger.error(f"Ошибка при обновлении сообщения для подарка {old_gift.id}: {e}")
            
            update_gifts_queue.task_done()
        
        except asyncio.QueueEmpty:
            await asyncio.sleep(0.1)

async def check_upgrades(bot: Bot):
    """Проверка апгрейдов подарков"""
    while True:
        star_gifts_data = StarGiftsData.load(DATA_FILEPATH)
        gifts_to_check = [g for g in star_gifts_data.star_gifts if not g.is_upgradable]
        
        if not gifts_to_check:
            logger.debug("Нет подарков для проверки апгрейдов")
            await asyncio.sleep(CHECK_UPGRADES_INTERVAL)
            continue
        
        for gift in gifts_to_check:
            logger.debug(f"Проверка апгрейда для подарка {gift.id}")
            if await check_is_star_gift_upgradable(bot, gift.id):
                logger.info(f"Подарок {gift.id} теперь доступен для апгрейда")
                chat_id = UPGRADES_CHAT_ID or CHAT_ID
                if not chat_id:
                    logger.warning("Не указан chat_id для уведомлений об апгрейдах")
                    continue
                
                try:
                    message = f"🎉 Подарок {gift.id} теперь можно апгрейдить!"
                    await bot.send_message(chat_id=chat_id, text=message)
                    
                    for stored_gift in star_gifts_data.star_gifts:
                        if stored_gift.id == gift.id:
                            stored_gift.is_upgradable = True
                            break
                    await star_gifts_data_saver(star_gifts_data)
                    
                except Exception as e:
                    logger.error(f"Ошибка при отправке уведомления об апгрейде для подарка {gift.id}: {e}")
        
        await asyncio.sleep(CHECK_UPGRADES_INTERVAL)

async def star_gifts_data_saver(star_gifts_data):
    """Сохранение данных о подарках с задержкой"""
    global last_star_gifts_data_saved_time
    last_star_gifts_data_saved_time = getattr(globals().get('last_star_gifts_data_saved_time', 0), 0)
    
    current_time = int(asyncio.get_event_loop().time())
    if current_time - last_star_gifts_data_saved_time >= DATA_SAVER_DELAY:
        star_gifts_data.save()
        last_star_gifts_data_saved_time = current_time
        logger.debug("Сохранены данные о подарках.")
    else:
        logger.debug(f"Пропуск сохранения. Следующее сохранение через {DATA_SAVER_DELAY - (current_time - last_star_gifts_data_saved_time)} секунд.")