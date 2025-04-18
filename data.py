import json
import os
import logging
from datetime import datetime
from config import PRODUCTS_FILE, USERS_FILE, ORDERS_FILE, CARTS_FILE

logger = logging.getLogger(__name__)

def load_json(file_path):
    """Load data from a JSON file or return empty dict if file doesn't exist."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {file_path}")
            return {}
    else:
        # Create the file with an empty structure
        save_json(file_path, {})
        return {}

def save_json(file_path, data):
    """Save data to a JSON file."""
    with open(file_path, 'w') as f:
        json.dump(data, f, indent=4)

# Product Management
def get_all_products():
    """Get all products."""
    products = load_json(PRODUCTS_FILE)
    return products

def get_product(product_id):
    """Get a product by ID."""
    products = get_all_products()
    return products.get(product_id)

def add_product(product_data):
    """Add a new product."""
    products = get_all_products()
    product_id = str(len(products) + 1)  # Simple ID generation
    product_data['id'] = product_id
    product_data['created_at'] = datetime.now().isoformat()
    products[product_id] = product_data
    save_json(PRODUCTS_FILE, products)
    return product_id

def update_product(product_id, product_data):
    """Update an existing product."""
    products = get_all_products()
    if product_id in products:
        product_data['id'] = product_id
        product_data['updated_at'] = datetime.now().isoformat()
        products[product_id] = product_data
        save_json(PRODUCTS_FILE, products)
        return True
    return False

def delete_product(product_id):
    """Delete a product."""
    products = get_all_products()
    if product_id in products:
        del products[product_id]
        save_json(PRODUCTS_FILE, products)
        return True
    return False

# User Management
def get_all_users():
    """Get all users."""
    return load_json(USERS_FILE)

def get_user(user_id):
    """Get a user by ID."""
    users = get_all_users()
    return users.get(str(user_id))

def add_or_update_user(user_id, user_data):
    """Add or update a user."""
    users = get_all_users()
    users[str(user_id)] = user_data
    save_json(USERS_FILE, users)
    return str(user_id)

# Cart Management
def get_cart(user_id):
    """Get a user's shopping cart."""
    carts = load_json(CARTS_FILE)
    return carts.get(str(user_id), {"items": {}, "total": 0})

def add_to_cart(user_id, product_id, quantity=1):
    """Add a product to a user's cart."""
    carts = load_json(CARTS_FILE)
    user_id = str(user_id)
    product_id = str(product_id)
    
    if user_id not in carts:
        carts[user_id] = {"items": {}, "total": 0}
    
    product = get_product(product_id)
    if not product:
        return False
    
    if product_id in carts[user_id]["items"]:
        carts[user_id]["items"][product_id]["quantity"] += quantity
    else:
        carts[user_id]["items"][product_id] = {
            "product_name": product["name"],
            "price": product["price"],
            "quantity": quantity
        }
    
    # Recalculate total
    total = 0
    for item in carts[user_id]["items"].values():
        total += item["price"] * item["quantity"]
    carts[user_id]["total"] = total
    
    save_json(CARTS_FILE, carts)
    return True

def update_cart_item(user_id, product_id, quantity):
    """Update the quantity of a product in a user's cart."""
    carts = load_json(CARTS_FILE)
    user_id = str(user_id)
    product_id = str(product_id)
    
    if user_id not in carts or product_id not in carts[user_id]["items"]:
        return False
    
    if quantity <= 0:
        del carts[user_id]["items"][product_id]
    else:
        carts[user_id]["items"][product_id]["quantity"] = quantity
    
    # Recalculate total
    total = 0
    for item in carts[user_id]["items"].values():
        total += item["price"] * item["quantity"]
    carts[user_id]["total"] = total
    
    save_json(CARTS_FILE, carts)
    return True

def clear_cart(user_id):
    """Clear a user's cart."""
    carts = load_json(CARTS_FILE)
    user_id = str(user_id)
    
    if user_id in carts:
        carts[user_id] = {"items": {}, "total": 0}
        save_json(CARTS_FILE, carts)
    return True

# Order Management
def create_order(user_id, user_data, address):
    """Create a new order from a user's cart."""
    cart = get_cart(user_id)
    if not cart["items"]:
        return None
    
    orders = load_json(ORDERS_FILE)
    order_id = str(len(orders) + 1)  # Simple ID generation
    
    order = {
        "id": order_id,
        "user_id": str(user_id),
        "user_data": user_data,
        "items": cart["items"],
        "total": cart["total"],
        "address": address,
        "status": "pending",
        "created_at": datetime.now().isoformat()
    }
    
    orders[order_id] = order
    save_json(ORDERS_FILE, orders)
    
    # Clear the cart after creating the order
    clear_cart(user_id)
    
    return order_id

def get_order(order_id):
    """Get an order by ID."""
    orders = load_json(ORDERS_FILE)
    return orders.get(str(order_id))

def get_user_orders(user_id):
    """Get all orders for a user."""
    orders = load_json(ORDERS_FILE)
    user_orders = {}
    for order_id, order in orders.items():
        if order["user_id"] == str(user_id):
            user_orders[order_id] = order
    return user_orders

def get_all_orders():
    """Get all orders."""
    return load_json(ORDERS_FILE)

def update_order_status(order_id, status):
    """Update the status of an order."""
    orders = load_json(ORDERS_FILE)
    if str(order_id) in orders:
        orders[str(order_id)]["status"] = status
        orders[str(order_id)]["updated_at"] = datetime.now().isoformat()
        save_json(ORDERS_FILE, orders)
        return True
    return False
