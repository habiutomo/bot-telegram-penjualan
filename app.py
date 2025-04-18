import os
import json
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime
import data
from config import ADMIN_USERNAME, ADMIN_PASSWORD, HOST, PORT

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key")

# Check if admin exists, if not create default admin
def init_admin():
    admin_path = "data/admin.json"
    if not os.path.exists(admin_path):
        admin_data = {
            "username": ADMIN_USERNAME,
            "password_hash": generate_password_hash(ADMIN_PASSWORD)
        }
        with open(admin_path, "w") as f:
            json.dump(admin_data, f)
        logger.info("Default admin account created")

# Create required data files if they don't exist
def init_data_files():
    # Ensure all data files exist
    data.get_all_products()
    data.get_all_users()
    data.get_all_orders()
    data.load_json(data.CARTS_FILE)

# Check if user is logged in
def is_logged_in():
    return session.get('logged_in', False)

# Admin login required decorator
def login_required(route_function):
    def wrapper(*args, **kwargs):
        if not is_logged_in():
            flash('Please login first', 'danger')
            return redirect(url_for('login'))
        return route_function(*args, **kwargs)
    wrapper.__name__ = route_function.__name__
    return wrapper

# Routes
@app.route('/')
def index():
    if is_logged_in():
        product_count = len(data.get_all_products())
        order_count = len(data.get_all_orders())
        user_count = len(data.get_all_users())
        
        # Get pending orders
        orders = data.get_all_orders()
        pending_orders = [order for order in orders.values() if order['status'] == 'pending']
        
        return render_template('index.html', 
                              product_count=product_count, 
                              order_count=order_count, 
                              user_count=user_count,
                              pending_orders=pending_orders,
                              now=datetime.now())
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # Load admin data
        try:
            with open("data/admin.json", "r") as f:
                admin_data = json.load(f)
        except:
            flash('Admin account not found', 'danger')
            return render_template('login.html', now=datetime.now())
        
        if username == admin_data['username'] and check_password_hash(admin_data['password_hash'], password):
            session['logged_in'] = True
            session['username'] = username
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials', 'danger')
    
    return render_template('login.html', now=datetime.now())

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/products')
@login_required
def products():
    products = data.get_all_products()
    return render_template('products.html', products=products, now=datetime.now())

@app.route('/products/add', methods=['GET', 'POST'])
@login_required
def product_add():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        image_url = request.form.get('image_url')
        
        if not name or not price or not stock:
            flash('Name, price and stock are required', 'danger')
            return render_template('product_add.html', now=datetime.now())
        
        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash('Price must be a number and stock must be an integer', 'danger')
            return render_template('product_add.html', now=datetime.now())
        
        product_data = {
            'name': name,
            'description': description,
            'price': price,
            'stock': stock,
            'image_url': image_url
        }
        
        product_id = data.add_product(product_data)
        flash(f'Product "{name}" added successfully', 'success')
        return redirect(url_for('products'))
    
    return render_template('product_add.html', now=datetime.now())

@app.route('/products/edit/<product_id>', methods=['GET', 'POST'])
@login_required
def product_edit(product_id):
    product = data.get_product(product_id)
    
    if not product:
        flash('Product not found', 'danger')
        return redirect(url_for('products'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        price = request.form.get('price')
        stock = request.form.get('stock')
        image_url = request.form.get('image_url')
        
        if not name or not price or not stock:
            flash('Name, price and stock are required', 'danger')
            return render_template('product_edit.html', product=product, now=datetime.now())
        
        try:
            price = float(price)
            stock = int(stock)
        except ValueError:
            flash('Price must be a number and stock must be an integer', 'danger')
            return render_template('product_edit.html', product=product, now=datetime.now())
        
        product_data = {
            'name': name,
            'description': description,
            'price': price,
            'stock': stock,
            'image_url': image_url
        }
        
        success = data.update_product(product_id, product_data)
        if success:
            flash(f'Product "{name}" updated successfully', 'success')
            return redirect(url_for('products'))
        else:
            flash('Failed to update product', 'danger')
    
    return render_template('product_edit.html', product=product, now=datetime.now())

@app.route('/products/delete/<product_id>')
@login_required
def product_delete(product_id):
    product = data.get_product(product_id)
    
    if not product:
        flash('Product not found', 'danger')
    else:
        success = data.delete_product(product_id)
        if success:
            flash(f'Product "{product["name"]}" deleted successfully', 'success')
        else:
            flash('Failed to delete product', 'danger')
    
    return redirect(url_for('products'))

@app.route('/orders')
@login_required
def orders():
    all_orders = data.get_all_orders()
    return render_template('orders.html', orders=all_orders)

@app.route('/orders/<order_id>')
@login_required
def order_detail(order_id):
    order = data.get_order(order_id)
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    
    return render_template('order_detail.html', order=order)

@app.route('/orders/update-status/<order_id>', methods=['POST'])
@login_required
def update_order_status(order_id):
    status = request.form.get('status')
    order = data.get_order(order_id)
    
    if not order:
        flash('Order not found', 'danger')
        return redirect(url_for('orders'))
    
    valid_statuses = ['pending', 'processing', 'shipped', 'delivered', 'cancelled']
    if status not in valid_statuses:
        flash('Invalid status', 'danger')
        return redirect(url_for('order_detail', order_id=order_id))
    
    success = data.update_order_status(order_id, status)
    if success:
        flash(f'Order status updated to {status}', 'success')
    else:
        flash('Failed to update order status', 'danger')
    
    return redirect(url_for('order_detail', order_id=order_id))

# Initialize admin and data files when app starts
init_admin()
init_data_files()

if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=True)
