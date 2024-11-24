# pip install pyserial
import serial
import serial.tools.list_ports
import time
import threading


def find_stm32_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if 'usbmodem' in port.device.lower():
            return port.device
    return None

port = find_stm32_port()
if port is None:
    print("No STM32 port found")
    exit(1)
print(f"Found port: {port}")

# Configure the serial port
ser = serial.Serial(
    port=port,
    baudrate=115200,
    bytesize=serial.EIGHTBITS,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    timeout=0.1
)

def read_serial():
    """Function to continuously read from serial port"""
    while True:
        if ser.in_waiting:
            try:
                line = ser.readline()
                # Try to decode as UTF-8 first
                try:
                    text = line.decode('utf-8').strip()
                    print(f"Received text: {text}")
                except UnicodeDecodeError:
                    # If decode fails, show as hex
                    hex_str = ' '.join([f'{b:02X}' for b in line])
                    print(f"Received binary: {hex_str}")
            except Exception as e:
                print(f"Error reading serial, not text or binary: {e}")
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