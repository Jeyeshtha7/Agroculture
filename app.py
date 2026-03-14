
from flask import Flask, render_template, request, redirect, session, url_for
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
app.jinja_env.cache = {}
app.secret_key = 'your_secret_key'  # Change this to a secure random key in production

# MySQL Configuration
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',         # Add your MySQL password if any
    'database': 'agroculture_project'
}

# Connect to MySQL
def get_db_connection():
    return mysql.connector.connect(**db_config)

# Home Page
@app.route('/')
def index():
    return render_template('index.html')

# Signup
from flask import flash  # add this to show messages on frontend

@app.route('/signup/<role>', methods=['GET', 'POST'])
def signup(role):
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        print("Form data received:", name, email, password)

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            table = 'farmers' if role == 'farmer' else 'buyers'
            query = f"INSERT INTO {table} (name, email, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, email, password))
            conn.commit()

            cursor.close()
            conn.close()

            print("Signup success, redirecting to login.")
            return redirect(f'/login/{role}')
        except Error as e:
            print("Database Error:", e)
            return f"<h3>Database Error: {e}</h3>"

    return render_template('signup.html', role=role)


# Login
@app.route('/login/<role>', methods=['GET', 'POST'])
def login(role):
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        try:
            conn = get_db_connection()
            cursor = conn.cursor(dictionary=True)

            table = 'farmers' if role == 'farmer' else 'buyers'
            query = f"SELECT * FROM {table} WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password))
            user = cursor.fetchone()

            cursor.close()
            conn.close()

            if user:
                session['user'] = user
                session['role'] = role
                return redirect(f'/{role}/dashboard')
            else:
                return "Invalid credentials"
        except Error as e:
            return f"Error: {e}"

    return render_template('login.html', role=role)

# Farmer Dashboard
@app.route('/farmer/dashboard', methods=['GET', 'POST'])
def farmer_dashboard():
    if 'user' not in session or session.get('role') != 'farmer':
        return redirect('/login/farmer')

    user_id = session['user']['id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if request.method == 'POST':
            name = request.form['product_name']
            quantity = request.form['quantity']
            price = request.form['price']
            description = request.form['description']

            cursor.execute("""
                INSERT INTO products (name, quantity, price, description, farmer_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, quantity, price, description, user_id))
            conn.commit()

        cursor.execute("SELECT * FROM products WHERE farmer_id = %s", (user_id,))
        products = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template('farmer_dashboard.html', products=products)
    except Error as e:
        return f"Error: {e}"
    
#delete
@app.route('/farmer/delete/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    if 'user' not in session or session.get('role') != 'farmer':
        return redirect('/login/farmer')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Only allow deletion of the product by the owner farmer
        cursor.execute("DELETE FROM products WHERE id = %s AND farmer_id = %s", (product_id, session['user']['id']))
        conn.commit()

        cursor.close()
        conn.close()
        return redirect('/farmer/dashboard')
    except Error as e:
        return f"Error: {e}"

# Buyer Dashboard
@app.route('/buyer/dashboard')
def buyer_dashboard():
    if 'user' not in session or session.get('role') != 'buyer':
        return redirect('/login/buyer')

    buyer_id = session['user']['id']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    # Fetch available products
    cursor.execute("""
        SELECT p.*, f.name as farmer_name 
        FROM products p 
        JOIN farmers f ON p.farmer_id = f.id
    """)
    products = cursor.fetchall()

    # Fetch cart items from cart table
    cursor.execute("""
        SELECT c.id as cart_id, p.name as product_name, p.price, c.quantity
        FROM cart c
        JOIN products p ON c.product_id = p.id
        WHERE c.buyer_id = %s
    """, (buyer_id,))
    cart = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('buyer_dashboard.html', products=products, cart=cart)

    
#cart
# Add to Cart
@app.route('/buyer/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'user' not in session or session.get('role') != 'buyer':
        return redirect('/login/buyer')

    buyer_id = session['user']['id']
    product_id = request.form['product_id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check if product already exists in cart — if so, increase quantity
        cursor.execute("SELECT id, quantity FROM cart WHERE buyer_id = %s AND product_id = %s", (buyer_id, product_id))
        existing_item = cursor.fetchone()

        if existing_item:
            new_quantity = existing_item[1] + 1
            cursor.execute("UPDATE cart SET quantity = %s WHERE id = %s", (new_quantity, existing_item[0]))
        else:
            cursor.execute("INSERT INTO cart (buyer_id, product_id, quantity) VALUES (%s, %s, %s)", (buyer_id, product_id, 1))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect('/buyer/dashboard')
    except Error as e:
        return f"Error: {e}"
    
#remove cart
@app.route('/buyer/remove_from_cart', methods=['POST'])
def remove_from_cart():
    cart_id = request.form['cart_id']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE id = %s", (cart_id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect('/buyer/dashboard')

#order
@app.route('/buyer/order', methods=['POST'])
def order():
    if 'user' not in session or session.get('role') != 'buyer':
        return redirect('/login/buyer')

    buyer_id = session['user']['id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Remove items from cart after ordering
        cursor.execute("DELETE FROM cart WHERE buyer_id = %s", (buyer_id,))
        conn.commit()

        cursor.close()
        conn.close()

        flash('Order placed successfully!')
        return redirect('/buyer/dashboard?ordered=true')
    
    except Error as e:
        flash(f"Error: {e}")
        return redirect('/buyer/dashboard')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
