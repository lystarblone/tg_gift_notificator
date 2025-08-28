import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = None
CHECK_INTERVAL = 20
CHECK_UPGRADES_INTERVAL = 600
DATA_FILEPATH = Path("star_gifts.json")
DATA_SAVER_DELAY = 60
UPGRADES_CHAT_ID = None