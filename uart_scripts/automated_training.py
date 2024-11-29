import os
import random
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
import serial
import serial.tools.list_ports


def find_stm32_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower():
            return port.device
    return None


def load_datasets(base_path: str) -> Dict[str, List[str]]:
    """Load datasets from the datasets folder"""
    datasets = {}
    base = Path(base_path)

    # List all directories in datasets folder
    for dataset_dir in base.iterdir():
        if dataset_dir.is_dir():
            datasets[dataset_dir.name] = [
                d.name for d in dataset_dir.iterdir() if d.is_dir()
            ]

    if not datasets:
        raise RuntimeError("No datasets found")

    return datasets


def load_class_images(dataset_path: str, class_name: str) -> List[str]:
    """Load all images for a specific class"""
    class_path = Path(dataset_path) / class_name
    return [
        str(f)
        for f in class_path.glob("*")
        if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]


def display_image(image_path: str, window_name: str = "Training Image"):
    """Display image centered on black background"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Create black background
    screen_width, screen_height = 1024, 768  # Adjustable
    background = np.zeros((screen_height, screen_width, 3), dtype=np.uint8)

    # Resize image while maintaining aspect ratio
    scale = min(screen_width / img.shape[1], screen_height / img.shape[0]) * 0.8
    new_width = int(img.shape[1] * scale)
    new_height = int(img.shape[0] * scale)
    img_resized = cv2.resize(img, (new_width, new_height))

    # Calculate position to center image
    x_offset = (screen_width - new_width) // 2
    y_offset = (screen_height - new_height) // 2

    # Place image on background
    background[y_offset : y_offset + new_height, x_offset : x_offset + new_width] = (
        img_resized
    )

    cv2.imshow(window_name, background)
    cv2.waitKey(1)


def update_output_ch_file(num_classes: int, file_path: str):
    """Update the OUTPUT_CH value in the specified .h file"""
    with open(file_path, "r") as file:
        lines = file.readlines()

    with open(file_path, "w") as file:
        for line in lines:
            if line.startswith("#define OUTPUT_CH"):
                file.write(f"#define OUTPUT_CH {num_classes}\n")
            else:
                file.write(line)


# Add STM32CubeIDE toolchain paths
cube_ide_paths = [
    "/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.12.3.rel1.macos64_1.0.200.202406191456/tools/bin",
    "/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.make.macos64_2.1.100.202310310804/tools/bin",
]


def recompile_project():
    """Recompile the project using STM32CubeIDE's build system"""
    try:
        # Set up environment variables
        env = os.environ.copy()  # Start with current environment

        # Prepend the STM32CubeIDE paths to existing PATH
        env["PATH"] = ":".join(cube_ide_paths + [env.get("PATH", "")])

        # Set working directory
        build_dir = "./Debug"

        # Run make command with environment
        print("Building project...")
        # TODO in build error, print out logs
        subprocess.run(
            ["make", "-j7", "all"],
            cwd=build_dir,
            env=env,
            check=True,
            capture_output=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Error during recompilation: {e}")
        raise


def clean_project():
    """Clean the project build"""
    try:
        # Set up environment variables (same as recompile_project)
        env = os.environ.copy()
        env["PATH"] = ":".join(cube_ide_paths + [env.get("PATH", "")])

        build_dir = "./Debug"

        print("Cleaning project...")
        # TODO in clean error, print out logs
        subprocess.run(
            ["make", "-j7", "clean"],
            cwd=build_dir,
            env=env,
            check=True,
            capture_output=True,
        )

    except subprocess.CalledProcessError as e:
        print(f"Error during clean: {e}")
        raise


def is_macos():
    return os.uname().sysname == "Darwin"


def is_windows():
    return os.name == "nt"


def is_linux():
    return os.uname().sysname == "Linux"


def deploy_to_microcontroller():
    """Deploy the compiled binary to the microcontroller"""
    if is_macos():
        path_to_programmer = "/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.macos64_2.1.400.202404281720/tools/bin/STM32_Programmer_CLI"
    elif is_windows():
        # TODO make this work for windows
        path_to_programmer = "STM32_Programmer_CLI"
    else:
        raise RuntimeError(f"Unsupported OS: {os.uname().sysname}")

    # validate that the path to the programmer exists
    if not os.path.exists(path_to_programmer):
        raise RuntimeError(
            f"STM cli can't be found at: {path_to_programmer}; "
            "this likely needs to be tweaked to work for your system"
        )

    try:
        binary_path = "./Debug/TTE_demo_mcunet.elf"
        cmd = [
            path_to_programmer,
            "--connect",
            "port=SWD",
            "--write",
            binary_path,
            "--verify",
            "-rst",
        ]

        print(f"Deploying binary: {binary_path}")
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("Deployment complete")
    except subprocess.CalledProcessError as e:
        print(f"Error during deployment: {e}")
        print(f"Error output: {e.stdout}\n{e.stderr}")
        raise


class UARTHandler:
    def __init__(self):
        self.port = find_stm32_port()
        if not self.port:
            raise RuntimeError("No STM32 port found")

        self.ser = serial.Serial(
            port=self.port,
            baudrate=115200,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            timeout=0.1,
        )
        self.last_messages = []
        self.message_received = threading.Event()

        # Start reading thread
        self.running = True
        self.read_thread = threading.Thread(target=self._read_serial, daemon=True)
        self.read_thread.start()

    def _read_serial(self):
        while self.running:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode("utf-8").strip()
                    if line:
                        print(f"Received: {line}")
                        self.last_messages.append(line)
                        self.message_received.set()
                except Exception as e:
                    print(f"Error reading serial: {e}")
            time.sleep(0.01)

    def send_command(self, cmd: str):
        self.ser.write(cmd.encode())
        print(f"Sent command: {cmd}")
        # sleep 0.1s to allow for command to be processed
        time.sleep(0.1)

    def wait_for_message(self, expected_msg: str, timeout: float = 10.0) -> bool:
        self.message_received.clear()
        start_time = time.time()

        while time.time() - start_time < timeout:
            if any(expected_msg in msg for msg in self.last_messages[-5:]):
                return True
            self.message_received.wait(timeout=0.1)
            self.message_received.clear()
            # sleep 0.1s to allow for command to be processed
            time.sleep(0.1)

        return False

    def wait_for_consecutive_inference(
        self, num_consecutive: int = 3, timeout: float = 10.0
    ) -> int:
        """Wait for N consecutive identical inference results"""
        start_time = time.time()
        results = []

        while time.time() - start_time < timeout:
            if self.message_received.wait(timeout=0.1):
                self.message_received.clear()
                for msg in self.last_messages[-5:]:
                    if "INFERENCE COMPLETE:" in msg:
                        try:
                            class_num = int(msg.split(":")[-1].strip())
                            results.append(class_num)
                            if len(results) >= num_consecutive:
                                # Check last N results are identical
                                if len(set(results[-num_consecutive:])) == 1:
                                    return results[-1]
                        except ValueError:
                            continue

        raise TimeoutError("Failed to get consecutive inference results")

    def close(self):
        self.running = False
        if self.read_thread.is_alive():
            self.read_thread.join()
        self.ser.close()


def main():
    # Load available datasets
    datasets = load_datasets("datasets")
    print("Available datasets:")
    for idx, name in enumerate(datasets.keys()):
        print(f"{idx + 1}: {name}")

    dataset_idx = int(input("Select dataset number: ")) - 1
    if dataset_idx < 0 or dataset_idx >= len(datasets):
        raise ValueError("Invalid dataset number")

    dataset_name = list(datasets.keys())[dataset_idx]
    dataset_path = f"datasets/{dataset_name}"

    # Load all images and classes
    class_names = datasets[dataset_name]
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}

    all_data = []
    for class_name in class_names:
        images = load_class_images(dataset_path, class_name)
        all_data.extend([(img, class_to_idx[class_name]) for img in images])

    # Update OUTPUT_CH in the .h file
    output_ch_file = "Src/TinyEngine/include/OUTPUT_CH.h"
    update_output_ch_file(len(class_names), output_ch_file)

    # In your main function, before starting UART communication:
    try:
        clean_project()  # Optional, if you want to clean first
        recompile_project()
    except Exception as e:
        print(f"Build failed: {e}")
        return

    # Deploy to the microcontroller
    deploy_to_microcontroller()

    # Split data
    random.shuffle(all_data)
    train_split = 0.7
    train_size = int(len(all_data) * train_split)

    # since not tuning things like learning rate, etc, only need validation
    train_data = all_data[:train_size]
    val_data = all_data[train_size:]

    uart = UARTHandler()
    try:
        # Training phase
        print("\nStarting training phase...")
        uart.send_command("t")  # Enter training mode

        epochs = 3  # Adjustable
        for epoch in range(epochs):
            print(f"\nEpoch {epoch + 1}/{epochs}")

            for idx, (image_path, class_num) in enumerate(train_data):
                print(f"Training image {idx + 1}/{len(train_data)}")
                display_image(image_path)

                # First iteration: wait for camera positioning
                if epoch == 0 and idx == 0:
                    input("Position camera and press Enter to start...")

                # Send class number and wait for training completion
                uart.send_command(str(class_num))
                if not uart.wait_for_message("TRAINING DONE"):
                    print(f"Warning: No training confirmation for image {idx + 1}")

        # Validation phase
        print("\nStarting validation phase...")
        uart.send_command("v")  # Enter validation mode

        correct = 0
        total = 0

        for image_path, true_class in val_data:
            display_image(image_path)
            try:
                predicted_class = uart.wait_for_consecutive_inference(num_consecutive=3)
                correct += predicted_class == true_class
                total += 1
                print(f"Validation accuracy: {correct/total:.2%} ({correct}/{total})")
            except TimeoutError:
                print(f"Failed to get consistent prediction for {image_path}")

        print(f"\nFinal validation accuracy: {correct/total:.2%}")

    finally:
        uart.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
