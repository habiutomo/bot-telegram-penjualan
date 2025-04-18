import os
import logging

# Telegram bot token
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")

# Flask app settings
DEBUG = True
HOST = "0.0.0.0"
PORT = 5000

# Data file paths
DATA_DIR = "data"
PRODUCTS_FILE = os.path.join(DATA_DIR, "products.json")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
ORDERS_FILE = os.path.join(DATA_DIR, "orders.json")
CARTS_FILE = os.path.join(DATA_DIR, "carts.json")

# Admin credentials
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")

# Logging configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)
