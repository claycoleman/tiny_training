import re
import time
from typing import List, Optional

# pip install pyserial to use this script
import serial

from utils import (
    create_serial_connection,
    find_stm32_port,
    get_key,
    read_serial_line,
)


def parse_output_ch_header(file_path: str) -> List[str]:
    """Parse OUTPUT_CH.h to get the labels"""
    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Find the array definition
        array_match = re.search(
            r"OUTPUT_LABELS\[\]\s*=\s*{([^}]+)}", content, re.DOTALL
        )
        if not array_match:
            raise ValueError("Could not find OUTPUT_LABELS array in header file")

        # Extract and clean up the labels
        labels_text = array_match.group(1)
        labels = [
            label.strip().strip('"').strip("'")
            for label in labels_text.split(",")
            if label.strip()
        ]

        return labels
    except Exception as e:
        print(f"Error parsing OUTPUT_CH.h: {e}")
        return []


def read_serial(ser: serial.Serial) -> None:
    """Function to continuously read from serial port"""
    while True:
        line = read_serial_line(ser)
        if line:
            print(f"Received: {line}")
        time.sleep(0.01)  # Sleep to prevent CPU hogging


def main() -> None:
    # Load labels from OUTPUT_CH.h
    file_path = "Src/TinyEngine/include/OUTPUT_CH.h"
    try:
        labels = parse_output_ch_header(file_path)
    except FileNotFoundError:
        # If file not found, try with parent directory
        file_path = "../" + file_path
        labels = parse_output_ch_header(file_path)

    if not labels:
        print("Failed to parse labels from OUTPUT_CH.h")
        return

    output_channel = len(labels)
    print(f"Found {output_channel} labels: {', '.join(labels)}")

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
        for i, label in enumerate(labels):
            print(f"{i}: Set ground truth to class {label} ({i})")
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
