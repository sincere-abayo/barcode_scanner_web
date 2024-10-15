from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from pyzbar.pyzbar import decode
import sqlite3
import time
import io
import sqlite3
from datetime import datetime
import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random



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
        SELECT pm.Id, p.Product, p.Owner, p.details,p.Category,  pm.status, pm.Timestamp
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

@app.route('/report', methods=['GET'])
def report():
    conn = sqlite3.connect('barcodes.db')
    cursor = conn.cursor()

    # Get entry and exit product counts
    cursor.execute("""
        SELECT status, COUNT(*) as count
        FROM product_movement
        GROUP BY status
    """)
    status_counts = dict(cursor.fetchall())

    entry_count = status_counts.get('entry', 0)
    exit_count = status_counts.get('exit', 0)

    # Get product details
    cursor.execute("""
        SELECT p.Id, p.Product, p.Owner, p.Category, p.Serial_no, p.details, pm.status, pm.Timestamp
        FROM products p
        JOIN product_movement pm ON p.Id = pm.ProductId
        ORDER BY pm.Timestamp DESC
    """)
    products = cursor.fetchall()

    conn.close()

    return render_template('report.html', entry_count=entry_count, exit_count=exit_count, products=products)


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



# profile file
@app.route('/profile', methods=['GET'])
def profile():
    return render_template('profile.html')

#forget
@app.route('/forget', methods=['GET'])
def forget():
    return render_template('forget.html')

# check if email is in db
@app.route('/check-email/<email>', methods=['GET'])
def check_email(email):
    conn = sqlite3.connect('barcodes.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE Email = ?", (email,))
    if c.fetchone():
        subject = "Password Reset Request"
        # create random 6 digit otp
        otp = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        # store otp in session
        session['otp'] = otp
        body = f"""
    <html>
    <head>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f4f4f4;
            }}
            h1 {{
                color: #0066cc;
            }}
            p {{
                margin-bottom: 15px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Password Reset OTP Confirmation</h1>
            <p>Dear User,</p>
            <p>We have received a request to reset your password for the MentalHealth project. To ensure the security of your account, we have generated a one-time password (OTP) for you.</p>
            <p>Your OTP is: <strong>{otp}</strong></p>
            <p>Please enter this OTP on the password reset page to verify your identity and proceed with resetting your password. This OTP will expire in 15 minutes for security reasons.</p>
            <p>If you did not request a password reset, please ignore this email and ensure your account is secure.</p>
            
        </div>
    </body>
    </html>
    """
        to_email = email 
        send_email( subject, body, to_email)
        return jsonify({'message': 'exists', 'email': email})
    else:
        return jsonify({'message': 'not'})
    
# check if otp is in db
@app.route('/check-otp/<otp>', methods=['GET'])
def check_otp(otp):
    # check if otp is in session
    if 'otp' in session:
        if session['otp'] == otp:
            return jsonify({'otp': 'exists', 'otp': otp})
        else:
            return jsonify({'otp': 'invalid', 'session_otp': session['otp']})
    else:
        return jsonify({'otp': 'not_found'})




#department
@app.route('/department', methods=['GET'])
def department():
    return render_template('department.html')
def department():
    return render_template('department.html')

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

# delete product based on product id
@app.route('/delete_product/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM products WHERE Id = ?", (product_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Product deleted successfully'})



# delete product based on product id
@app.route('/delete_student/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("DELETE FROM students WHERE Id = ?", (student_id,))
    conn.commit()
    conn.close()
    return jsonify({'message': 'Student deleted successfully'})


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


def send_email(subject, body, to_email):
    # Email configuration
    smtp_server = "smtp.gmail.com"
    smtp_port = 587
    sender_email = "mhpcms2024@gmail.com"
    sender_password = "qrpe sixl znov dxgj"

    # Create the email message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = to_email
    message["Subject"] = subject

    # Add body to email as HTML
    message.attach(MIMEText(body, "html"))

    # Connect to the SMTP server and send the email
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(message)
        
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
