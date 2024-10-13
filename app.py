from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pyzbar.pyzbar import decode
import sqlite3
import time
import io
import sqlite3
from datetime import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522



app = Flask(__name__)
app.secret_key = 'abcdefghigk'  # Set a secret key for session management


def get_db_connection():
    conn = sqlite3.connect('barcodes.db')
    conn.row_factory = sqlite3.Row
    return conn



@app.route('/get_rfid_code')
def get_rfid_code():
    reader = SimpleMFRC522()
    
    try:
        for _ in range(50):  # Try for about 5 seconds
            id, text = reader.read_no_block()
            if id:
                return jsonify({"rfid_code": str(id)})
            time.sleep(0.1)
        
        return jsonify({"error": "No RFID tag detected"}), 404
    
    finally:
        GPIO.cleanup()



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

@app.route('/register_student', methods=['POST'])
def register_student():
    conn = sqlite3.connect('barcodes.db')
    c = conn.cursor()

    data = request.form

    try:
        c.execute('''INSERT INTO students 
                     (Name, Reg_no, gender, Department, Program, Year, Card) 
                     VALUES (?, ?, ?, ?, ?, ?, ?)''',
                  (data['studentName'], data['regNo'], data['gender'],
                   data['department'], data['program'], data['yearOfStudy'],
                   data['rfid']))
        conn.commit()
        return jsonify({"message": "Student registered successfully"}), 200
    except sqlite3.IntegrityError:
        return jsonify({"error": "Registration number already exists"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

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
def get_all_students():
    conn = sqlite3.connect('barcodes.db')
    c = conn.cursor()
    c.execute("SELECT Id, Name, Reg_no, Department, Program, gender as Gender, Year FROM students")
    students = [dict(zip([column[0] for column in c.description], row)) for row in c.fetchall()]
    conn.close()
    return render_template('student.html', students=students)

    
    # return jsonify([dict(zip([column[0] for column in c.description], row)) for row in students])


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
