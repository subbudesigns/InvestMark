import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

GROWW_API_KEY = os.getenv("GROWW_API_KEY")
GROWW_API_SECRET = os.getenv("GROWW_API_SECRET")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

PORTFOLIO_FILE = os.path.join(DATA_DIR, 'portfolio.json')
LIMITS_FILE = os.path.join(DATA_DIR, 'limits.json')
WISHLIST_FILE = os.path.join(DATA_DIR, 'wishlist.json')

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)
