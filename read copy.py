import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522
import sqlite3
from datetime import datetime
from gpiozero import LED
from gpiozero import Buzzer
import time




reader = SimpleMFRC522()

print("Ready to read RFID tag...")
conn = sqlite3.connect('barcodes.db')  # Establish database connection

# initianlize buzzer
buzzer = Buzzer(6)

# defibe function to activate buzzer
def buzz():
    buzzer.on()
    time.sleep(1)
    buzzer.off()

# LED setup
led = LED(17)

def blink_led():
        led.on()
        buzzer.on()

        time.sleep(1)
        led.off()

# green LED setup
gled = LED(26)

def green_blink_led():
        gled.on()
        buzzer.on()

        time.sleep(0.5)
        gled.off()

c = conn.cursor()

try:
    while True:
        id, text = reader.read_no_block()
        if id:
            c.execute("SELECT * FROM products WHERE Tag = ?", (id,))
            result = c.fetchone()
            if result:
                     green_blink_led()  # Blink green LED 3 times if product found
                     product_id, product, owner, category, serial_no, barcode, Tag, details, timestamp = result
                     current_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                     c.execute("INSERT INTO product_movement (ProductId, status, Timestamp) VALUES (?, ?, ?)",
                        (product_id, 'exit', current_timestamp))
                     conn.commit()
                     print (f"P:{product[:14]}", f"O:{owner[:14]}", f"Cat:{category[:12]}", f"SN:{serial_no[:13]}")
           
            
            else:
                blink_led()  # Blink LED 3 times if product not found
                buzz()
                print ("Product not found", "", "", "")

            print(f"ID: {id}")
            print(f"Text: {text.strip()}")
            break
finally:
    GPIO.cleanup()
