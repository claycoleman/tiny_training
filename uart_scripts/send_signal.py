# pip install pyserial to use this script
import re
import sys
import time
import serial
from typing import Match, Optional

from uart_scripts.utils import (
    get_key,
    find_stm32_port,
    create_serial_connection,
    read_serial_line,
)


def read_serial(ser: serial.Serial) -> None:
    """Function to continuously read from serial port"""
    while True:
        line = read_serial_line(ser)
        if line:
            print(f"Received: {line}")
        time.sleep(0.01)  # Sleep to prevent CPU hogging


def main() -> None:
    # TODO instead of defining just OUTPUT_CH, we should define a list of output classes
    # this allows us to be more clear about what each class index / label corresponds to
    # and avoid confusion

    # Try to open the file directly first, then try with parent directory if that fails
    file_path = "Src/TinyEngine/include/OUTPUT_CH.h"
    try:
        file = open(file_path, "r")
    except FileNotFoundError:
        # If file not found, try with parent directory
        file_path = "../" + file_path
        file = open(file_path, "r")

    output_channel: Optional[int] = None
    with file:
        for line in file:
            if "OUTPUT_CH" in line:
                match: Optional[Match[str]] = re.search(r"\d+", line)
                if match:
                    output_channel = int(match.group())
                break

    if output_channel is None:
        print("Failed to find OUTPUT_CH in OUTPUT_CH.h")
        return
    print(f"Found OUTPUT_CH {output_channel}")

    port = find_stm32_port()
    if not port:
        print("STM32 board not found! Please check the connection.")
        return
    print(f"Found port: {port}")

    ser: Optional[serial.Serial] = None
    try:
        ser = create_serial_connection(port)

        print("Connected to", port)
        print("\nCommands:")
        print("i: Inference mode")
        print("v: Validation mode")
        print("t: Training mode")
        for i in range(output_channel):
            print(f"{i}: Set ground truth to class {i}")
        print("q: Quit")

        valid_classes = [str(i) for i in range(output_channel)]
        valid_commands = valid_classes + ["t", "v", "i"]

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
        if ser is not None and ser.is_open:
            ser.close()
            print("\nSerial connection closed")


if __name__ == "__main__":
    main()
