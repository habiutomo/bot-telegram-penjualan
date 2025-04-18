import logging
import html
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.ext.filters import UpdateType
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
import data
from utils import (
    paginate, create_pagination_keyboard, format_cart_message, create_cart_keyboard,
    format_product_message, create_product_keyboard, format_order_message,
    send_order_notification, send_status_update
)
from config import TOKEN

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
ADDRESS, CONFIRM_ORDER = range(2)

# Stores temporary user data during conversations
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    
    # Save or update user information
    user_info = {
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name
    }
    data.add_or_update_user(user.id, user_info)
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products_1")],
        [InlineKeyboardButton("🛒 Shopping Cart", callback_data="view_cart")],
        [InlineKeyboardButton("📦 My Orders", callback_data="my_orders_1")]
    ]
    
    await update.message.reply_markdown_v2(
        f"Welcome, {html.escape(user.first_name)}\! 👋\n\n"
        f"This is an e\-commerce bot where you can browse and purchase products\.\n\n"
        f"Use the buttons below to navigate:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    help_text = (
        "*Available Commands:*\n\n"
        "/start - Start the bot and see main menu\n"
        "/help - Show this help message\n"
        "/browse - Browse available products\n"
        "/cart - View your shopping cart\n"
        "/orders - View your orders"
    )
    await update.message.reply_markdown(help_text)

async def browse_products(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show list of products with pagination."""
    query = update.callback_query
    
    if query:
        # Extract page number from callback data
        page = int(query.data.split("_")[-1])
        await query.answer()
    else:
        # If called directly from command
        page = 1
    
    products = data.get_all_products()
    products_list = list(products.values())
    
    if not products_list:
        message = "No products available at the moment."
        if query:
            await query.edit_message_text(message)
        else:
            await update.message.reply_text(message)
        return
    
    # Paginate products
    pages = list(paginate(products_list))
    if page > len(pages):
        page = 1
    
    current_page = pages[page-1]
    
    # Create message
    message = "*Available Products:*\n\n"
    for product in current_page:
        message += f"*{html.escape(product['name'])}*\n"
        message += f"Price: ${float(product['price']):.2f}\n"
        message += f"Stock: {product['stock']}\n"
        message += "\n"
    
    # Create keyboard with product buttons and pagination
    keyboard = []
    for product in current_page:
        keyboard.append([InlineKeyboardButton(
            f"{product['name']} - ${float(product['price']):.2f}",
            callback_data=f"view_product_{product['id']}"
        )])
    
    # Add pagination buttons
    pagination = create_pagination_keyboard(page, len(pages), "browse_products")
    keyboard.extend(pagination)
    
    # Add back to main menu button
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_markdown(message, reply_markup=markup)

async def view_product(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show product details."""
    query = update.callback_query
    await query.answer()
    
    product_id = query.data.split("_")[-1]
    product = data.get_product(product_id)
    
    if not product:
        await query.edit_message_text("Product not found.")
        return
    
    message = format_product_message(product)
    markup = create_product_keyboard(product_id)
    
    await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')

async def adjust_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Adjust quantity before adding to cart."""
    query = update.callback_query
    await query.answer()
    
    action, product_id = query.data.split("_")[1:]
    product = data.get_product(product_id)
    
    if not product:
        await query.edit_message_text("Product not found.")
        return
    
    # Find the current quantity button
    current_markup = query.message.reply_markup.inline_keyboard
    qty_row = current_markup[0]
    qty_button = qty_row[1]
    current_qty = int(qty_button.text)
    
    # Adjust quantity
    if action == "increase":
        current_qty += 1
    elif action == "decrease" and current_qty > 1:
        current_qty -= 1
    
    # Update the add to cart button
    add_to_cart_row = current_markup[1]
    add_to_cart_button = add_to_cart_row[0]
    add_to_cart_button.callback_data = f"add_to_cart_{product_id}_{current_qty}"
    
    # Update the quantity button
    qty_button.text = str(current_qty)
    
    # Recreate the markup
    markup = InlineKeyboardMarkup(current_markup)
    
    await query.edit_message_reply_markup(reply_markup=markup)

async def add_to_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a product to cart."""
    query = update.callback_query
    await query.answer()
    
    _, product_id, qty = query.data.split("_")
    qty = int(qty)
    
    product = data.get_product(product_id)
    if not product:
        await query.edit_message_text("Product not found.")
        return
    
    if int(product["stock"]) < qty:
        await query.answer("Not enough stock available!", show_alert=True)
        return
    
    user_id = update.effective_user.id
    success = data.add_to_cart(user_id, product_id, qty)
    
    if success:
        await query.answer(f"Added {qty} × {product['name']} to your cart!", show_alert=True)
        
        # Show updated product view with reset quantity
        message = format_product_message(product)
        markup = create_product_keyboard(product_id)
        
        await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')
    else:
        await query.answer("Failed to add item to cart.", show_alert=True)

async def view_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the user's shopping cart."""
    user_id = update.effective_user.id
    cart = data.get_cart(user_id)
    
    message = format_cart_message(cart)
    markup = create_cart_keyboard(cart)
    
    if update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_markdown(message, reply_markup=markup)

async def update_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle cart updates (increase, decrease, remove item)."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    action, product_id = query.data.split("_")[1:]
    
    cart = data.get_cart(user_id)
    if product_id not in cart["items"]:
        await query.answer("Item not found in cart.", show_alert=True)
        return
    
    current_qty = cart["items"][product_id]["quantity"]
    
    if action == "increase":
        # Check stock before increasing
        product = data.get_product(product_id)
        if int(product["stock"]) <= current_qty:
            await query.answer("Maximum available stock reached.", show_alert=True)
            return
        data.update_cart_item(user_id, product_id, current_qty + 1)
    elif action == "decrease":
        if current_qty > 1:
            data.update_cart_item(user_id, product_id, current_qty - 1)
        else:
            data.update_cart_item(user_id, product_id, 0)  # Remove if qty would be 0
    elif action == "remove":
        data.update_cart_item(user_id, product_id, 0)  # Remove item
    
    # Refresh cart view
    cart = data.get_cart(user_id)
    message = format_cart_message(cart)
    markup = create_cart_keyboard(cart)
    
    await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')

async def clear_cart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clear the user's cart."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data.clear_cart(user_id)
    
    # Refresh cart view
    cart = data.get_cart(user_id)
    message = format_cart_message(cart)
    markup = create_cart_keyboard(cart)
    
    await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')

async def checkout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Start the checkout process."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    cart = data.get_cart(user_id)
    
    if not cart["items"]:
        await query.answer("Your cart is empty.", show_alert=True)
        return
    
    # Ask for shipping address
    await query.edit_message_text(
        "Please enter your shipping address:",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔙 Cancel", callback_data="view_cart")
        ]])
    )
    
    return ADDRESS

async def process_address(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Process the shipping address and ask for confirmation."""
    user_id = update.effective_user.id
    address = update.message.text
    cart = data.get_cart(user_id)
    
    # Store address temporarily
    user_data_store[user_id] = {"address": address}
    
    # Show order summary and ask for confirmation
    message = "*Order Summary:*\n\n"
    message += format_cart_message(cart)[len("🛒 *Your Shopping Cart*\n\n"):]  # Remove cart header
    message += f"\n\n*Shipping Address:*\n{html.escape(address)}"
    
    markup = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Confirm Order", callback_data="confirm_order")],
        [InlineKeyboardButton("🔙 Cancel", callback_data="cancel_order")]
    ])
    
    await update.message.reply_markdown(message, reply_markup=markup)
    return CONFIRM_ORDER

async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Confirm the order and create it."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    user_info = data.get_user(user_id)
    address = user_data_store.get(user_id, {}).get("address", "")
    
    # Create the order
    order_id = data.create_order(user_id, user_info, address)
    
    if order_id:
        # Clean up temporary data
        if user_id in user_data_store:
            del user_data_store[user_id]
        
        # Show success message
        order = data.get_order(order_id)
        message = "🎉 *Your order has been placed!*\n\n"
        message += format_order_message(order)
        
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]])
        
        await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')
        
        # Also notify via utils function for reference
        await send_order_notification(context, user_id, order_id, format_order_message(order))
    else:
        await query.edit_message_text(
            "Failed to create your order. Please try again.",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
            ]])
        )
    
    return ConversationHandler.END

async def cancel_order(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancel the order process."""
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    
    # Clean up temporary data
    if user_id in user_data_store:
        del user_data_store[user_id]
    
    await query.edit_message_text(
        "Order cancelled. Your cart is still available.",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🛒 View Cart", callback_data="view_cart"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]])
    )
    
    return ConversationHandler.END

async def view_orders(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show user's orders with pagination."""
    query = update.callback_query
    
    if query:
        # Extract page number from callback data
        page = int(query.data.split("_")[-1])
        await query.answer()
    else:
        # If called directly from command
        page = 1
    
    user_id = update.effective_user.id
    user_orders = data.get_user_orders(user_id)
    orders_list = list(user_orders.values())
    
    if not orders_list:
        message = "You haven't placed any orders yet."
        markup = InlineKeyboardMarkup([[
            InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products_1"),
            InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
        ]])
        
        if query:
            await query.edit_message_text(message, reply_markup=markup)
        else:
            await update.message.reply_text(message, reply_markup=markup)
        return
    
    # Sort orders by created_at (most recent first)
    orders_list.sort(key=lambda x: x.get('created_at', ''), reverse=True)
    
    # Paginate orders
    pages = list(paginate(orders_list, page_size=3))
    if page > len(pages):
        page = 1
    
    current_page = pages[page-1]
    
    # Create message
    message = "*Your Orders:*\n\n"
    for order in current_page:
        message += f"*Order #{order['id']}*\n"
        message += f"Date: {order['created_at'].split('T')[0]}\n"
        message += f"Status: {order['status'].upper()}\n"
        message += f"Total: ${order['total']:.2f}\n"
        message += f"Items: {sum(item['quantity'] for item in order['items'].values())}\n\n"
    
    # Create keyboard with order buttons and pagination
    keyboard = []
    for order in current_page:
        keyboard.append([InlineKeyboardButton(
            f"Order #{order['id']} - {order['status'].upper()}",
            callback_data=f"view_order_{order['id']}"
        )])
    
    # Add pagination buttons
    pagination = create_pagination_keyboard(page, len(pages), "my_orders")
    keyboard.extend(pagination)
    
    # Add back to main menu button
    keyboard.append([InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")])
    
    markup = InlineKeyboardMarkup(keyboard)
    
    if query:
        await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')
    else:
        await update.message.reply_markdown(message, reply_markup=markup)

async def view_order_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show details of a specific order."""
    query = update.callback_query
    await query.answer()
    
    order_id = query.data.split("_")[-1]
    order = data.get_order(order_id)
    
    if not order:
        await query.edit_message_text("Order not found.")
        return
    
    message = format_order_message(order)
    
    markup = InlineKeyboardMarkup([[
        InlineKeyboardButton("« Back to Orders", callback_data="my_orders_1"),
        InlineKeyboardButton("🏠 Main Menu", callback_data="main_menu")
    ]])
    
    await query.edit_message_text(message, reply_markup=markup, parse_mode='Markdown')

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show the main menu."""
    query = update.callback_query
    await query.answer()
    
    user = update.effective_user
    
    keyboard = [
        [InlineKeyboardButton("🛍️ Browse Products", callback_data="browse_products_1")],
        [InlineKeyboardButton("🛒 Shopping Cart", callback_data="view_cart")],
        [InlineKeyboardButton("📦 My Orders", callback_data="my_orders_1")]
    ]
    
    await query.edit_message_text(
        f"Welcome, {html.escape(user.first_name)}! 👋\n\n"
        f"This is an e-commerce bot where you can browse and purchase products.\n\n"
        f"Use the buttons below to navigate:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle callbacks that don't need to do anything (like number display)."""
    query = update.callback_query
    await query.answer()

def create_bot_application():
    """Create and configure the bot application."""
    # Create the application
    application = Application.builder().token(TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("browse", browse_products))
    application.add_handler(CommandHandler("cart", view_cart))
    application.add_handler(CommandHandler("orders", view_orders))
    
    # Add conversation handler for checkout process
    checkout_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(checkout, pattern="^cart_checkout$")],
        states={
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_address)],
            CONFIRM_ORDER: [
                CallbackQueryHandler(confirm_order, pattern="^confirm_order$"),
                CallbackQueryHandler(cancel_order, pattern="^cancel_order$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_order)],
    )
    application.add_handler(checkout_conv_handler)
    
    # Add callback query handlers
    application.add_handler(CallbackQueryHandler(browse_products, pattern="^browse_products_"))
    application.add_handler(CallbackQueryHandler(view_product, pattern="^view_product_"))
    application.add_handler(CallbackQueryHandler(adjust_quantity, pattern="^qty_"))
    application.add_handler(CallbackQueryHandler(add_to_cart, pattern="^add_to_cart_"))
    application.add_handler(CallbackQueryHandler(view_cart, pattern="^view_cart$"))
    application.add_handler(CallbackQueryHandler(update_cart, pattern="^cart_(increase|decrease|remove)_"))
    application.add_handler(CallbackQueryHandler(clear_cart, pattern="^cart_clear$"))
    application.add_handler(CallbackQueryHandler(view_orders, pattern="^my_orders_"))
    application.add_handler(CallbackQueryHandler(view_order_details, pattern="^view_order_"))
    application.add_handler(CallbackQueryHandler(main_menu, pattern="^main_menu$"))
    application.add_handler(CallbackQueryHandler(noop_callback, pattern="^noop$"))
    
    return application

if __name__ == "__main__":
    # Create the bot application
    bot_application = create_bot_application()
    
    # Run the bot
    bot_application.run_polling()
