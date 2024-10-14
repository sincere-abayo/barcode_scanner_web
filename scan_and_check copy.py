import sys
import sqlite3
from datetime import datetime
import RPi.GPIO as GPIO
import RPLCD
from RPLCD.i2c import CharLCD
import time
from gpiozero import LED
from mfrc522 import SimpleMFRC522
 

 # RFID setup
reader = SimpleMFRC522()

# LCD setup using I2C
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=4, charmap='A00')

# LED setup
led = LED(17)

GPIO.setwarnings(False)

def blink_led(times):
    for _ in range(times):
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)

def check_product(conn, identifier, is_rfid=False):
    c = conn.cursor()
    if is_rfid:
        c.execute("SELECT * FROM products WHERE product_card = ?", (identifier,))
    else:
        c.execute("SELECT * FROM products WHERE barcode = ?", (identifier,))
    result = c.fetchone()
    if result:
        product_id, product, owner, category, serial_no, barcode, tag, details, timestamp, product_card = result
        current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        c.execute("INSERT INTO product_movement (ProductId, status, Timestamp) VALUES (?, ?, ?)",
                  (product_id, 'exit', current_timestamp))
        conn.commit()
        return (f"P:{product[:14]}", f"O:{owner[:14]}", f"Cat:{category[:12]}", f"SN:{serial_no[:13]}")
    else:
        blink_led(3)  # Blink LED 3 times if product not found
        return ("Product not found", "", "", "")


barcode = ""


try:
    conn = sqlite3.connect('barcodes.db')  # Establish database connection
    while True:
        lcd.clear()
        lcd.write_string("Scan barcode or")
        lcd.cursor_pos = (1, 0)
        lcd.write_string("RFID tag...")

        # Check for RFID tag
        id, text = reader.read_no_block()
        if id:
            lcd.clear()
            lcd.write_string("Checking RFID...")
            result = check_product(conn, str(id), is_rfid=True)
            lcd.clear()
            for i, line in enumerate(result):
                lcd.cursor_pos = (i, 0)
                lcd.write_string(line)
            time.sleep(5)
            continue

        # Existing barcode scanning logic
        if sys.stdin.isatty():
            char = sys.stdin.read(1)
        else:
            char = sys.stdin.buffer.read1(1).decode()
        
        if char == 'q':
            lcd.clear()
            lcd.write_string("Exiting...")
            time.sleep(2)
            break
        elif char in ('\r', '\n'):
            if barcode:
                lcd.clear()
                lcd.write_string("Checking...")
                result = check_product(conn, barcode)
                lcd.clear()
                for i, line in enumerate(result):
                    lcd.cursor_pos = (i, 0)
                    lcd.write_string(line)
                time.sleep(5)
                barcode = ""
        else:
            barcode += char
            lcd.cursor_pos = (3, 0)
            lcd.write_string(f"Barcode: {barcode[-16:]}")
except Exception as e:
    lcd.clear()
    lcd.write_string(f"Error: {str(e)[:16]}")
    time.sleep(5)
finally:
    lcd.clear()


    if 'conn' in locals() or 'conn' in globals():
        conn.close()
    GPIO.cleanup()