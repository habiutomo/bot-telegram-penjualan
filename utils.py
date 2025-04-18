from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
import html
import logging

logger = logging.getLogger(__name__)

# Pagination utilities
def paginate(items, page_size=5):
    """Divide a list of items into pages."""
    for i in range(0, len(items), page_size):
        yield items[i:i + page_size]

def create_pagination_keyboard(current_page, total_pages, callback_prefix):
    """Create pagination keyboard with prev/next buttons."""
    keyboard = []
    
    # Add navigation buttons
    navigation = []
    if current_page > 1:
        navigation.append(InlineKeyboardButton("« Prev", callback_data=f"{callback_prefix}_{current_page-1}"))
    
    navigation.append(InlineKeyboardButton(f"{current_page}/{total_pages}", callback_data="noop"))
    
    if current_page < total_pages:
        navigation.append(InlineKeyboardButton("Next »", callback_data=f"{callback_prefix}_{current_page+1}"))
    
    keyboard.append(navigation)
    return keyboard

# Cart utilities
def format_cart_message(cart):
    """Format a user's cart as a message."""
    if not cart["items"]:
        return "Your cart is empty."
    
    message = "🛒 *Your Shopping Cart*\n\n"
    for product_id, item in cart["items"].items():
        subtotal = item["price"] * item["quantity"]
        message += f"*{html.escape(item['product_name'])}*\n"
        message += f"Price: ${item['price']:.2f} × {item['quantity']} = ${subtotal:.2f}\n\n"
    
    message += f"*Total: ${cart['total']:.2f}*"
    return message

def create_cart_keyboard(cart):
    """Create keyboard for cart actions."""
    keyboard = []
    
    # Add item-specific actions if cart is not empty
    if cart["items"]:
        for product_id in cart["items"]:
            keyboard.append([
                InlineKeyboardButton("➖", callback_data=f"cart_decrease_{product_id}"),
                InlineKeyboardButton("➕", callback_data=f"cart_increase_{product_id}"),
                InlineKeyboardButton("🗑 Remove", callback_data=f"cart_remove_{product_id}")
            ])
        
        # Add general cart actions
        keyboard.append([
            InlineKeyboardButton("🗑 Clear Cart", callback_data="cart_clear"),
            InlineKeyboardButton("✅ Checkout", callback_data="cart_checkout")
        ])
    else:
        # If cart is empty, add a button to browse products
        keyboard.append([InlineKeyboardButton("🔍 Browse Products", callback_data="browse_products_1")])
    
    return InlineKeyboardMarkup(keyboard)

# Product display utilities
def format_product_message(product):
    """Format a product as a message."""
    message = f"*{html.escape(product['name'])}*\n\n"
    message += f"{html.escape(product['description'])}\n\n"
    message += f"💰 Price: ${float(product['price']):.2f}\n"
    message += f"📦 Stock: {product['stock']}"
    return message

def create_product_keyboard(product_id):
    """Create keyboard for product actions."""
    keyboard = [
        [
            InlineKeyboardButton("➖", callback_data=f"qty_decrease_{product_id}"),
            InlineKeyboardButton("1", callback_data="noop"),
            InlineKeyboardButton("➕", callback_data=f"qty_increase_{product_id}")
        ],
        [InlineKeyboardButton("🛒 Add to Cart", callback_data=f"add_to_cart_{product_id}_1")],
        [InlineKeyboardButton("« Back to Products", callback_data="browse_products_1")]
    ]
    return InlineKeyboardMarkup(keyboard)

# Order utilities
def format_order_message(order):
    """Format an order as a message."""
    message = f"*Order #{order['id']}*\n"
    message += f"Status: {order['status'].upper()}\n\n"
    
    for product_id, item in order['items'].items():
        subtotal = item["price"] * item["quantity"]
        message += f"*{html.escape(item['product_name'])}*\n"
        message += f"Price: ${item['price']:.2f} × {item['quantity']} = ${subtotal:.2f}\n\n"
    
    message += f"*Total: ${order['total']:.2f}*\n\n"
    message += f"Delivery Address:\n{html.escape(order['address'])}\n"
    message += f"Order Date: {order['created_at'].split('T')[0]}"
    return message

async def send_order_notification(context: ContextTypes.DEFAULT_TYPE, user_id: int, order_id: str, order_details: str):
    """Send order notification to the user."""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🎉 Order #{order_id} has been placed!\n\n{order_details}",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send order notification: {e}")

async def send_status_update(context: ContextTypes.DEFAULT_TYPE, user_id: int, order_id: str, status: str):
    """Send order status update to the user."""
    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=f"🔔 Order #{order_id} status updated: *{status.upper()}*",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Failed to send status update: {e}")
