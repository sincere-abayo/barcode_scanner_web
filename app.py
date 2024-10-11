from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pyzbar.pyzbar import decode
from werkzeug.security import check_password_hash
import sqlite3
import sys
from PIL import Image
import io
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'abcdefghigk'  # Set a secret key for session management


def get_db_connection():
    conn = sqlite3.connect('barcodes1.db')
    conn.row_factory = sqlite3.Row
    return conn

# @app.route('/', methods=['GET'])
# def index():
#     return render_template('index.html')


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get total products
    cursor.execute("SELECT COUNT(*) FROM products")
    total_products = cursor.fetchone()[0]

    # Get total registered students
    cursor.execute("SELECT COUNT(*) FROM students")
    total_students = cursor.fetchone()[0]

    # Get total users
    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
     # Fetch the latest 10 movements
    cursor.execute("""
        SELECT pm.Id, p.Product, p.Owner, pm.status, pm.Timestamp
        FROM product_movement pm
        JOIN products p ON pm.ProductId = p.Id
        ORDER BY pm.Timestamp DESC
        LIMIT 10
    """)
    recent_movements = cursor.fetchall()


    conn.close()

    return render_template('dashboard.html', total_products=total_products, 
                           total_students=total_students, total_users=total_users,  recent_movements=recent_movements)


from datetime import datetime

@app.route('/register_product', methods=['POST'])
def register_product():
    data = request.form
    product = data.get('productName')
    owner = data.get('owner')
    category = data.get('productType')
    serial_no = data.get('serialNumber')
    barcode = data.get('barcode')
    tag = data.get('rfid')  # RFID as Tag
    details = data.get('description')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO products (Product, Owner, Category, Serial_no, barcode, Tag, details, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
              (product, owner, category, serial_no, barcode, tag, details, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Product registered successfully'})



# report file
@app.route('/report', methods=['GET'])
def report():
    return render_template('report.html')

# users file
@app.route('/users', methods=['GET'])
def users():
    return render_template('users.html')

# student file
@app.route('/student', methods=['GET'])
def student():
    return render_template('student.html')

@app.route('/product', methods=['GET'])
def product():
    return render_template('product.html')

@app.route('/all_products', methods=['GET'])
def get_all_products():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM products")
    products = c.fetchall()
    conn.close()

    return jsonify([dict(row) for row in products])


@app.route('/scan', methods=['POST'])
def scan():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})
    
    if file:
        image_data = file.read()
        image = Image.open(io.BytesIO(image_data))
        
        barcodes = decode(image)
        
        if barcodes:
            barcode_data = barcodes[0].data.decode('utf-8')
            conn = get_db_connection()
            c = conn.cursor()
            c.execute("SELECT * FROM scans WHERE barcode = ?", (barcode_data,))
            result = c.fetchone()
            conn.close()

            if result:
                return jsonify({
                    'barcode': result['barcode'],
                    'name': result['name'],
                    'details': result['details'],
                    'timestamp': result['timestamp']
                })
            else:
                return jsonify({'barcode': barcode_data, 'message': 'Barcode not registered'})
        else:
            return jsonify({'error': 'No barcode found'})

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    barcode = data.get('barcode')
    name = data.get('name')
    details = data.get('details')
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db_connection()
    c = conn.cursor()
    c.execute("INSERT INTO scans VALUES (?, ?, ?, ?)", (barcode, name, details, timestamp))
    conn.commit()
    conn.close()

    return jsonify({'message': 'Barcode registered successfully'})

@app.route('/all', methods=['GET'])
def get_all():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM scans")
    results = c.fetchall()
    conn.close()

    return jsonify([dict(row) for row in results])


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE Email = ?', (email,)).fetchone()
        conn.close()

        if user and (user['Password'], password):
            session['user_id'] = user['Email']
            return redirect(url_for('dashboard'))
        else:
            return render_template('index.html', error='Invalid email or password')
    
    return render_template('index.html')



@app.route('/logout')
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
