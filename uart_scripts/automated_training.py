import os
import random
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, List
from datetime import datetime

import cv2
import numpy as np
import serial
import serial.tools.list_ports

from utils import (
    clean_project,
    build_project,
    deploy_binary,
    find_stm32_port,
    create_serial_connection,
)

# Define project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def load_datasets(base_path: str) -> Dict[str, List[str]]:
    """Load datasets from the datasets folder"""
    print(f"\nLoading datasets from {base_path}")
    datasets = {}
    base = Path(base_path)

    # List all directories in datasets folder
    for dataset_dir in base.iterdir():
        if dataset_dir.is_dir():
            datasets[dataset_dir.name] = [
                d.name for d in dataset_dir.iterdir() if d.is_dir()
            ]
            print(f"Found dataset '{dataset_dir.name}' with {len(datasets[dataset_dir.name])} classes")

    if not datasets:
        print("ERROR: No datasets found in the specified path")
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


class UARTHandler:
    DEBUG_RECEIVED_MESSAGES = False

    def __init__(self):
        print("\nInitializing UART communication...")
        self.port = find_stm32_port()
        if not self.port:
            raise RuntimeError("No STM32 port found")

        print(f"Connected to STM32 on port {self.port}")
        self.ser = create_serial_connection(self.port)
        self.last_messages = []
        self.message_received = threading.Event()

        # Start reading thread
        self.running = True
        self.read_thread = threading.Thread(target=self._read_serial, daemon=True)
        self.read_thread.start()
        print("UART handler initialized successfully")

    def _read_serial(self):
        while self.running:
            if self.ser.in_waiting:
                try:
                    line = self.ser.readline().decode("utf-8").strip()
                    if line:
                        if self.DEBUG_RECEIVED_MESSAGES:
                            print(f"Received: {line}")
                        self.last_messages.append(line)
                        self.message_received.set()
                except Exception as e:
                    print(f"Error reading serial: {e}")
            time.sleep(0.01)

    def send_command(self, cmd: str):
        # Clear any old messages before sending new command
        self.last_messages = []
        self.message_received.clear()
        
        self.ser.write(cmd.encode())
        print(f"Sent command: {cmd}")
        # wait to receive "COMMAND RECEIVED: <cmd>"
        if not self.wait_for_message(f"COMMAND RECEIVED: {cmd}"):
            raise TimeoutError(f"Failed to receive command: {cmd}")
        # sleep 0.1s to allow for command to be processed
        time.sleep(0.1)

    def wait_for_message(self, expected_msg: str, timeout: float = 10.0) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check new messages
            for msg in self.last_messages:
                if expected_msg in msg:
                    return True
            
            # Wait for new messages
            self.message_received.wait(timeout=0.1)
            self.message_received.clear()

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
    datasets = load_datasets(str(PROJECT_ROOT / "datasets/ten_class_data"))
    if not datasets:
        raise RuntimeError("No datasets found")

    print("\nAvailable datasets:")
    for idx, name in enumerate(datasets.keys()):
        print(f"{idx + 1}: {name}")
    print()

    while True:
        dataset_input = input("Select dataset number: ")
        try:
            dataset_idx = int(dataset_input) - 1
        except ValueError:
            print("Invalid input")
            continue

        if dataset_idx < 0 or dataset_idx >= len(datasets):
            print("Invalid dataset number")
            continue

        break

    dataset_name = list(datasets.keys())[dataset_idx]
    dataset_path = str(PROJECT_ROOT / "datasets/ten_class_data" / dataset_name)
    print(f"\nSelected dataset: {dataset_name}")

    # Load all images and classes
    class_names = datasets[dataset_name]
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    all_data = []
    for class_name in class_names:
        images = load_class_images(dataset_path, class_name)
        all_data.extend([(img, class_to_idx[class_name]) for img in images])
        print(f"Loaded {len(images)} images for class '{class_name}'")

    # Update OUTPUT_CH in the .h file
    output_ch_file = str(PROJECT_ROOT / "Src/TinyEngine/include/OUTPUT_CH.h")
    update_output_ch_file(len(class_names), output_ch_file)
    print(f"\nUpdated OUTPUT_CH.h with {len(class_names)} classes")

    # In your main function, before starting UART communication:
    try:
        clean_project()  # Optional, if you want to clean first
        build_project()
    except Exception as e:
        print(f"Build failed: {e}")
        return

    # Deploy to the microcontroller
    deploy_binary()

    # Split data
    random.shuffle(all_data)
    train_split = 0.7
    train_size = int(len(all_data) * train_split)

    # since not tuning things like learning rate, etc, only need validation
    train_data = all_data[:train_size]
    val_data = all_data[train_size:]
    print(f"\nData split: {len(train_data)} training samples, {len(val_data)} validation samples")

    uart = UARTHandler()
    try:
        # Training phase
        print("\n=== Starting Training Phase ===")
        uart.send_command("t")  # Enter training mode

        epochs = 3  # Adjustable
        for epoch in range(epochs):
            epoch_start = time.time()
            print(f"\nEpoch {epoch + 1}/{epochs}")
            correct_trainings = 0
            failed_trainings = 0

            for idx, (image_path, class_num) in enumerate(train_data):
                img_start = time.time()
                print(f"\nTraining image {idx + 1}/{len(train_data)} (Class: {class_num})")
                display_image(image_path)

                # First iteration: wait for camera positioning
                if epoch == 0 and idx == 0:
                    input("Position camera and press Enter to start...")

                # Send class number and wait for training completion
                uart.send_command(str(class_num))
                received_training_done = uart.wait_for_message("TRAINING DONE")
                
                # If this is a training command (a number), wait for training completion and ready signal
                if received_training_done:
                    ready_for_next = uart.wait_for_message("READY FOR NEXT TRAINING")
                    if ready_for_next:
                        correct_trainings += 1
                        img_time = time.time() - img_start
                        print(f"Training successful - took {img_time:.2f}s")
                    else:
                        failed_trainings += 1
                        print("WARNING: Device not ready for next training")
                else:
                    failed_trainings += 1
                    print(f"WARNING: No training confirmation for image {idx + 1}")

            epoch_time = time.time() - epoch_start
            print(f"\nEpoch {epoch + 1} completed in {epoch_time:.2f}s")
            print(f"Training stats: {correct_trainings} successful, {failed_trainings} failed")

        # Validation phase
        print("\n=== Starting Validation Phase ===")
        uart.send_command("v")  # Enter validation mode

        correct = 0
        total = 0
        val_start = time.time()

        for idx, (image_path, true_class) in enumerate(val_data):
            print(f"\nValidating image {idx + 1}/{len(val_data)}")
            display_image(image_path)
            try:
                predicted_class = uart.wait_for_consecutive_inference(num_consecutive=3)
                correct += predicted_class == true_class
                total += 1
                accuracy = correct/total
                print(f"True class: {true_class}, Predicted: {predicted_class}")
                print(f"Current accuracy: {accuracy:.2%} ({correct}/{total})")
            except TimeoutError:
                print(f"ERROR: Failed to get consistent prediction for {image_path}")

        val_time = time.time() - val_start
        final_accuracy = correct/total
        print(f"\nValidation completed in {val_time:.2f}s")
        print(f"Final validation accuracy: {final_accuracy:.2%}")

        total_time = time.time() - start_time
        print(f"\n=== Training Session Completed in {total_time:.2f}s ===")

    finally:
        uart.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
