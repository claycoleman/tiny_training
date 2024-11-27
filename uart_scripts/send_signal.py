# pip install pyserial to use this script
import re
from typing import Optional
import serial
import serial.tools.list_ports
import time
import sys
import termios
import tty
import threading


def get_key():
    """Get a single keypress from stdin without requiring Enter."""
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def find_stm32_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower():
            return port.device
    return None


def read_serial(ser):
    """Function to continuously read from serial port"""
    while True:
        if ser.in_waiting:
            try:
                line = ser.readline().decode("utf-8").strip()
                if line:
                    print(f"Received: {line}")
            except UnicodeDecodeError:
                print("Received some non-text data")
            except:
                break
        time.sleep(0.01)  # Sleep to prevent CPU hogging


def main():
    # read ../Src/main.cpp to find the OUTPUT_CH
    # formatted like this: #define OUTPUT_CH 2
    OUTPUT_CH: Optional[int] = None
    # TODO if we're in the uart_scripts folder, append ..
    with open("Src/main.cpp", "r") as file:
        for line in file:
            if "OUTPUT_CH" in line:
                OUTPUT_CH = re.search(r"\d+", line).group()
                break

    if OUTPUT_CH is None:
        print("Failed to find OUTPUT_CH in ../Src/main.cpp")
        return
    print(f"Found OUTPUT_CH {OUTPUT_CH}")

    port = find_stm32_port()
    if not port:
        print("STM32 board not found! Please check the connection.")
        return
    print(f"Found port: {port}")

    try:
        ser = serial.Serial(
            port=port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        )

        print("Connected to", port)
        print("\nCommands:")
        print("i: Inference mode")
        print("t: Training mode")
        for i in range(OUTPUT_CH):
            print(f"{i}: Set ground truth to class {i}")
        print("q: Quit")

        # TODO: add back in reading thread if not using listen.py
        # # Start the reading thread
        # read_thread = threading.Thread(target=read_serial, args=(ser,), daemon=True)
        # read_thread.start()

        valid_classes = [
            str(i) for i in range(OUTPUT_CH)
        ]  # ['0', '1'] for OUTPUT_CH = 2
        valid_commands = valid_classes + ["t", "i"]

        while True:
            key = get_key()

            if key.lower() == "q":
                break

            if key in valid_commands:
                print(f"\nSending command: {key}")
                ser.write(key.encode())
            elif key == "\x03":  # Ctrl+C
                raise KeyboardInterrupt

    except serial.SerialException as e:
        print(f"Error: {e}")
    except KeyboardInterrupt:
        print("\nExiting...")
    finally:
        if "ser" in locals() and ser.is_open:
            ser.close()
            print("\nSerial connection closed")


if __name__ == "__main__":
    main()
