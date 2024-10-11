import sys
import msvcrt
import sqlite3
from datetime import datetime

def getch():
    return msvcrt.getch().decode()

def check_barcode(conn, barcode):
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE barcode = ?", (barcode,))
    result = c.fetchone()
    if result:
        product_id, product, owner, category, serial_no, barcode, tag, details, timestamp = result
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO product_movement (ProductId, status, Timestamp) VALUES (?, ?, ?)",
                  (product_id, 'exit', current_timestamp))
        conn.commit()
        return f"Product: {product}\nOwner: {owner}\nCategory: {category}\nBarcode: {barcode}\nExit Time: {current_timestamp}"
    else:
        return "Product not found"



conn = sqlite3.connect('barcodes1.db')
print("Scan a barcode to check (press 'q' to quit):")

barcode = ""
while True:
    char = getch()
    if char == 'q':
        print("\nExiting...")
        break
    elif char == '\r' or char == '\n':
        if barcode:
            print(f"\nChecking barcode: {barcode}")
            result = check_barcode(conn, barcode)
            print(result)
            barcode = ""
    else:
        barcode += char
        sys.stdout.write(char)
        sys.stdout.flush()

conn.close()
