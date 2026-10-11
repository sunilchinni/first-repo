from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
from mysql.connector import Error
import os
import uuid

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'farmer-market-secret-key')

# Database configuration
DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'db'),
    'port': int(os.environ.get('DB_PORT', 3306)),
    'user': os.environ.get('DB_USER', 'farmer_user'),
    'password': os.environ.get('DB_PASSWORD', 'farmer_pass'),
    'database': os.environ.get('DB_NAME', 'farmer_market'),
}


def get_db_connection():
    """Create and return a database connection."""
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except Error as e:
        print(f"Database connection error: {e}")
        return None


@app.before_request
def ensure_session():
    """Ensure a session ID exists for cart tracking."""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())


@app.route('/')
def index():
    """Home page - display all products."""
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT p.*, f.name AS farmer_name, f.farm_location
        FROM products p
        JOIN farmers f ON p.farmer_id = f.id
        WHERE p.quantity > 0
        ORDER BY p.created_at DESC
    """)
    products = cursor.fetchall()

    # Get cart count
    cursor.execute(
        "SELECT COALESCE(SUM(quantity), 0) AS total FROM cart WHERE session_id = %s",
        (session['session_id'],)
    )
    cart_count = cursor.fetchone()['total']

    cursor.close()
    conn.close()
    return render_template('index.html', products=products, cart_count=cart_count)


@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    """Allow farmers to add products."""
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    if request.method == 'POST':
        # Farmer details
        farmer_name = request.form['farmer_name']
        farmer_email = request.form['farmer_email']
        farmer_phone = request.form.get('farmer_phone', '')
        farm_location = request.form.get('farm_location', '')

        # Product details
        product_name = request.form['product_name']
        description = request.form.get('description', '')
        category = request.form.get('category', 'Other')
        price = float(request.form['price'])
        quantity = int(request.form['quantity'])
        unit = request.form.get('unit', 'kg')

        try:
            # Check if farmer exists
            cursor.execute("SELECT id FROM farmers WHERE email = %s", (farmer_email,))
            farmer = cursor.fetchone()

            if farmer:
                farmer_id = farmer['id']
            else:
                cursor.execute("""
                    INSERT INTO farmers (name, email, phone, farm_location)
                    VALUES (%s, %s, %s, %s)
                """, (farmer_name, farmer_email, farmer_phone, farm_location))
                farmer_id = cursor.lastrowid

            # Insert product
            cursor.execute("""
                INSERT INTO products (farmer_id, name, description, category, price, quantity, unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (farmer_id, product_name, description, category, price, quantity, unit))
            conn.commit()
            flash('Product added successfully!', 'success')
            return redirect(url_for('index'))
        except Error as e:
            conn.rollback()
            flash(f'Error adding product: {e}', 'danger')

    cursor.close()
    conn.close()
    return render_template('add_product.html')


@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    """Add a product to cart."""
    quantity = int(request.form.get('quantity', 1))
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    # Verify stock
    cursor.execute("SELECT quantity FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if not product or product['quantity'] < quantity:
        flash('Not enough stock available', 'warning')
        cursor.close()
        conn.close()
        return redirect(url_for('index'))

    # Check if already in cart
    cursor.execute("""
        SELECT id, quantity FROM cart
        WHERE session_id = %s AND product_id = %s
    """, (session['session_id'], product_id))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE cart SET quantity = quantity + %s WHERE id = %s
        """, (quantity, existing['id']))
    else:
        cursor.execute("""
            INSERT INTO cart (session_id, product_id, quantity)
            VALUES (%s, %s, %s)
        """, (session['session_id'], product_id, quantity))

    conn.commit()
    cursor.close()
    conn.close()
    flash('Added to cart!', 'success')
    return redirect(url_for('index'))


@app.route('/cart')
def view_cart():
    """Display cart contents."""
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT c.id AS cart_id, c.quantity, p.id AS product_id, p.name,
               p.price, p.unit, p.quantity AS stock, f.name AS farmer_name,
               (c.quantity * p.price) AS subtotal
        FROM cart c
        JOIN products p ON c.product_id = p.id
        JOIN farmers f ON p.farmer_id = f.id
        WHERE c.session_id = %s
    """, (session['session_id'],))
    items = cursor.fetchall()

    total = sum(item['subtotal'] for item in items) if items else 0

    cursor.close()
    conn.close()
    return render_template('cart.html', items=items, total=total)


@app.route('/remove_from_cart/<int:cart_id>', methods=['POST'])
def remove_from_cart(cart_id):
    """Remove an item from cart."""
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM cart WHERE id = %s AND session_id = %s",
        (cart_id, session['session_id'])
    )
    conn.commit()
    cursor.close()
    conn.close()
    flash('Item removed', 'info')
    return redirect(url_for('view_cart'))


@app.route('/checkout', methods=['POST'])
def checkout():
    """Process checkout."""
    customer_name = request.form['customer_name']
    customer_email = request.form['customer_email']
    customer_address = request.form['customer_address']

    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)

    # Get cart items
    cursor.execute("""
        SELECT c.quantity, p.id AS product_id, p.price, p.quantity AS stock
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.session_id = %s
    """, (session['session_id'],))
    items = cursor.fetchall()

    if not items:
        flash('Cart is empty', 'warning')
        cursor.close()
        conn.close()
        return redirect(url_for('view_cart'))

    total = sum(item['quantity'] * float(item['price']) for item in items)

    try:
        # Create order
        cursor.execute("""
            INSERT INTO orders (customer_name, customer_email, customer_address, total_amount)
            VALUES (%s, %s, %s, %s)
        """, (customer_name, customer_email, customer_address, total))
        order_id = cursor.lastrowid

        # Insert order items & update stock
        for item in items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, quantity, price)
                VALUES (%s, %s, %s, %s)
            """, (order_id, item['product_id'], item['quantity'], item['price']))

            cursor.execute("""
                UPDATE products SET quantity = quantity - %s WHERE id = %s
            """, (item['quantity'], item['product_id']))

        # Clear cart
        cursor.execute("DELETE FROM cart WHERE session_id = %s", (session['session_id'],))
        conn.commit()
        flash(f'Order #{order_id} placed successfully! Total: ${total:.2f}', 'success')
    except Error as e:
        conn.rollback()
        flash(f'Checkout failed: {e}', 'danger')

    cursor.close()
    conn.close()
    return redirect(url_for('index'))


@app.route('/orders')
def orders():
    """View all orders (admin view)."""
    conn = get_db_connection()
    if not conn:
        return "Database connection failed", 500

    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT o.*, COUNT(oi.id) AS item_count
        FROM orders o
        LEFT JOIN order_items oi ON o.id = oi.order_id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)
    all_orders = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('orders.html', orders=all_orders)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
