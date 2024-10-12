import sys
import sqlite3
from datetime import datetime
import RPi.GPIO as GPIO
import RPLCD
from RPLCD.i2c import CharLCD
import time
from gpiozero import LED

# LCD setup using I2C
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=16, rows=4, charmap='A00')

# LED setup
led = LED(17)

def blink_led(times):
    for _ in range(times):
        led.on()
        time.sleep(0.5)
        led.off()
        time.sleep(0.5)

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
        return (f"P:{product[:14]}", f"O:{owner[:14]}", f"Cat:{category[:12]}", f"SN:{serial_no[:13]}")
    else:
        blink_led(3)  # Blink LED 3 times if barcode not found
        return ("Product not found", "", "", "")

conn = sqlite3.connect('barcodes1.db')
lcd.clear()
lcd.write_string("Scan barcode...")

barcode = ""

try:
    while True:
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
                result = check_barcode(conn, barcode)
                lcd.clear()
                for i, line in enumerate(result):
                    lcd.cursor_pos = (i, 0)
                    lcd.write_string(line)
                time.sleep(5)
                lcd.clear()
                lcd.write_string("Scan barcode...")
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
    conn.close()
    GPIO.cleanup()
