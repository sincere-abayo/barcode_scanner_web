import RPi.GPIO as GPIO
from mfrc522 import SimpleMFRC522

reader = SimpleMFRC522()

print("Ready to read RFID tag...")

try:
    while True:
        id, text = reader.read_no_block()
        if id:
            print(f"ID: {id}")
            print(f"Text: {text.strip()}")
            break
finally:
    GPIO.cleanup()
