# pip install pyserial
from uart_scripts.utils import read_serial_line
import time
import threading


def read_serial():
    """Function to continuously read from serial port"""
    while True:
        line = read_serial_line(ser)
        if line:
            print(f"Received: {line}")
        time.sleep(0.01)


try:
    # Start the reading thread
    read_thread = threading.Thread(target=read_serial, daemon=True)
    read_thread.start()

    # listening for commands
    print("Listening for UART responses. Press Ctrl+C to exit")
    while True:
        # no cpu hogging
        time.sleep(0.1)

except KeyboardInterrupt:
    print("\nExiting...")
finally:
    ser.close()
    print("Serial port closed")
