import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
from datetime import datetime
from gpiozero import LED, Buzzer
import time
from RPLCD.i2c import CharLCD

# RFID setup
reader = SimpleMFRC522()

# LCD setup
lcd = CharLCD(i2c_expander='PCF8574', address=0x27, port=1, cols=20, rows=4, charmap='A00')


# LED and Buzzer setup
led = LED(17)
green_led = LED(26)
buzzer = Buzzer(6)
# Database connection
conn = sqlite3.connect('barcodes.db')
c = conn.cursor()

def blink_led():
    led.on()
    buzzer.on()
    time.sleep(1)
    led.off()
    buzzer.off()

def green_blink_led():
    green_led.on()
    buzzer.on()
    time.sleep(0.5)
    green_led.off()
    buzzer.off()

try:
    lcd.clear()
    lcd.write_string("Ready to read")
    lcd.cursor_pos = (1, 0)
    lcd.write_string("RFID tag or barcode...")

    while True:
        id, text = reader.read_no_block()
        if id:
           
            c.execute("SELECT * FROM products WHERE Tag = ?", (id,))
            result = c.fetchone()
            if result:
               green_blink_led()
               product_id, product, owner, category, serial_no, barcode, Tag, details, timestamp = result
               current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
               c.execute("INSERT INTO product_movement (ProductId, status, Timestamp) VALUES (?, ?, ?)",
                  (product_id, 'exit', current_timestamp))
               conn.commit()
                
               lcd.clear()
               lcd.write_string(f"{product[:18]}")
               lcd.cursor_pos = (1, 0)
               lcd.write_string(f"{owner[:18]}")
               lcd.cursor_pos = (2, 0)
               lcd.write_string(f"{category[:18]}")
               lcd.cursor_pos = (3, 0)
               lcd.write_string(f"{serial_no[:18]}")
            else:
               c.execute("SELECT Name, Reg_no, Year FROM students WHERE Card = ?", (id,))
               student_result = c.fetchone()
               if student_result:
                   green_blink_led()
                   name, reg_no, year = student_result
                   lcd.clear()
                   lcd.write_string(f"Name:{name[:12]}")
                   lcd.cursor_pos = (1, 0)
                   lcd.write_string(f"Reg:{reg_no[:12]}")
                   lcd.cursor_pos = (2, 0)
                   lcd.write_string(f"Year:{year[:12]}")
               else:
                   blink_led()
                   lcd.clear()
                   lcd.write_string("Tag not found")
            time.sleep(2)
            lcd.clear()
            lcd.write_string("Ready to read")
            lcd.cursor_pos = (1, 0)
            lcd.write_string("RFID tag or barcode...")

except KeyboardInterrupt:
    pass
finally:
    lcd.clear()
    conn.close()
    GPIO.cleanup()
