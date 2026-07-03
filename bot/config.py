import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))
APIFY_TOKEN = os.getenv("APIFY_TOKEN", "")
ALIEXPRESS_APP_KEY = os.getenv("ALIEXPRESS_APP_KEY", "")
ALIEXPRESS_APP_SECRET = os.getenv("ALIEXPRESS_APP_SECRET", "")

DATABASE_PATH = "bot.db"
USD_TO_UZS = 12800
APIFY_ACTORS = {
    "aliexpress": "sian.agency~alibaba-1688-wholesale-scraper",
    "1688": "sian.agency~alibaba-1688-wholesale-scraper",
    "taobao": "zen-studio~taobao-search-scraper",
}
APIFY_BASE_URL = "https://api.apify.com/v2"
ALIEXPRESS_BASE_URL = "https://gw.aliexpress.com"
CATEGORIES = [
    "Elektronika",
    "Kiyim-kechak",
    "Poyabzal",
    "Sumka",
    "Uy buyumlari",
    "Sport",
    "Go'zallik",
    "Bolalar uchun",
    "Avtoulovar",
    "Boshqa",
]
