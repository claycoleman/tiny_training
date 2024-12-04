from pathlib import Path
import random
import threading
import time
from typing import List, Optional, Tuple

import cv2
import numpy as np

from utils import (
    clean_project,
    build_project,
    deploy_binary,
    find_stm32_port,
    create_serial_connection,
    PROJECT_ROOT,
    select_dataset,
    update_output_ch_file,
    smart_build_and_deploy,
)


def load_class_images(dataset_path: str, class_name: str) -> List[str]:
    """Load all images for a specific class"""
    class_path = Path(dataset_path) / class_name
    return [
        str(f)
        for f in class_path.glob("*")
        if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]


def display_image(image_path: str, window_name: str = "Training Image", delay: float = 0.5):
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

    time.sleep(delay)  # Small delay to ensure display is complete


def display_blank_frame(window_name: str = "Training Image"):
    """Display blank white frame for camera alignment"""
    screen_width, screen_height = 1024, 768  # Same as in display_image
    # Create white background
    background = np.ones((screen_height, screen_width, 3), dtype=np.uint8) * 255

    # Add alignment text
    font = cv2.FONT_HERSHEY_SIMPLEX
    text = "Align camera with this window"
    text_size = cv2.getTextSize(text, font, 1, 2)[0]
    text_x = (screen_width - text_size[0]) // 2
    text_y = screen_height // 2
    cv2.putText(background, text, (text_x, text_y), font, 1, (0, 0, 0), 2)

    cv2.imshow(window_name, background)
    cv2.waitKey(1)


class UARTHandler:
    DEBUG_RECEIVED_MESSAGES = False

    def __init__(self):
        print("\nInitializing UART communication...")
        self.port = find_stm32_port()
        if not self.port:
            raise RuntimeError("No STM32 port found")

        print(f"Connected to STM32 on port {self.port}")
        self.ser = create_serial_connection(self.port)
        print(f"Connected to STM32 on port {self.port}")
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


def prepare_dataset(
    dataset_path: str,
    class_names: List[str],
    max_examples_per_class: Optional[int] = None,
    random_seed: Optional[int] = None,
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """Prepare and split dataset into training and validation sets"""
    if random_seed is not None:
        random.seed(random_seed)

    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    all_data = []

    for class_name in class_names:
        images = load_class_images(dataset_path, class_name)
        if max_examples_per_class:
            images = images[:max_examples_per_class]
        all_data.extend([(img, class_to_idx[class_name]) for img in images])
        print(f"Loaded {len(images)} images for class '{class_name}'")

    # Split data
    random.shuffle(all_data)
    train_split = 0.7
    train_size = int(len(all_data) * train_split)

    return all_data[:train_size], all_data[train_size:]


def main(
    epochs: int = 3,
    max_examples_per_class: Optional[int] = None,
    random_seed: Optional[int] = None,
    clean: bool = False,
):
    try:
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)  # Also set numpy's random seed
            print(f"\nUsing random seed: {random_seed}")

        # Select dataset and get class names
        dataset_path, class_names = select_dataset()

        # Update OUTPUT_CH.h file
        output_ch_file = str(PROJECT_ROOT / "Src/TinyEngine/include/OUTPUT_CH.h")
        update_output_ch_file(class_names, output_ch_file)
        print(f"\nUpdated OUTPUT_CH.h with {len(class_names)} classes")

        # Build and deploy
        if clean:
            clean_project()
            build_project()
            deploy_binary()
        else:
            smart_build_and_deploy()  # Use smart build instead

        # Prepare dataset with max examples limit and random seed
        train_data, val_data = prepare_dataset(
            dataset_path, class_names, max_examples_per_class, random_seed
        )
        print(
            f"\nData split: {len(train_data)} training samples, {len(val_data)} validation samples"
        )

        training_start_time = time.time()
        uart = UARTHandler()
        try:
            # Training phase
            print("\n=== Starting Training Phase ===")
            uart.send_command("t")  # Enter training mode

            # Display blank frame and wait for alignment
            display_blank_frame()
            input("Position camera and press Enter to start training...")

            for epoch in range(epochs):
                epoch_start = time.time()
                print(f"\nEpoch {epoch + 1}/{epochs}")
                correct_trainings = 0
                failed_trainings = 0

                for idx, (image_path, class_num) in enumerate(train_data):
                    """
                    For each image that we train on, here is the process:
                    1. Display the image on the screen for 0.2s (hopefully long enough for the microcontroller camera to capture it)
                    # this is the gap that we can't really control, since there is no feedback from the microcontroller for seeing if it has received the image
                    2. Send the class number to the microcontroller (all send commands wait for "COMMAND RECEIVED" before returning as a success)
                    3. Microcontroller processes the image and trains on it
                    4. Wait for the microcontroller to finish training (wait for "TRAINING DONE")
                    """
                    img_start = time.time()
                    print(
                        f"\nTraining image {idx + 1}/{len(train_data)} (Class: {class_num})"
                    )
                    display_image(image_path)

                    # in theory, we need to wait to make sure the microcontroller has received the image
                    # but since we display the image for 0.2s, we can assume it has received it

                    # Send class number and wait for training completion
                    uart.send_command(str(class_num))

                    # If this is a training command (a number), wait for training completion and ready signal
                    if uart.wait_for_message("TRAINING DONE"):
                        correct_trainings += 1
                        img_time = time.time() - img_start
                        print(f"Training successful - took {img_time:.2f}s")
                    else:
                        failed_trainings += 1
                        print(f"WARNING: No training confirmation for image {idx + 1}")

                epoch_time = time.time() - epoch_start
                print(f"\nEpoch {epoch + 1} completed in {epoch_time:.2f}s")
                print(
                    f"Training stats: {correct_trainings} successful, {failed_trainings} failed"
                )

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
                    predicted_class = uart.wait_for_consecutive_inference(
                        num_consecutive=3
                    )
                    correct += predicted_class == true_class
                    total += 1
                    accuracy = correct / total
                    print(f"True class: {true_class}, Predicted: {predicted_class}")
                    print(f"Current accuracy: {accuracy:.2%} ({correct}/{total})")
                except TimeoutError:
                    print(
                        f"ERROR: Failed to get consistent prediction for {image_path}"
                    )

            val_time = time.time() - val_start
            final_accuracy = correct / total
            print(f"\nValidation completed in {val_time:.2f}s")
            print(f"Final validation accuracy: {final_accuracy:.2%}")

            total_time = time.time() - training_start_time
            print(f"\n=== Training Session Completed in {total_time:.2f}s ===")

        finally:
            uart.close()
            cv2.destroyAllWindows()

    except Exception as e:
        print(f"Error: {e}")
        return 1

    return 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run automated training with customizable parameters"
    )
    parser.add_argument(
        "--epochs", "-e", type=int, default=3, help="Number of training epochs"
    )
    parser.add_argument(
        "--max-examples",
        "-m",
        type=int,
        default=None,
        help="Maximum number of examples to use per class",
    )
    parser.add_argument(
        "--seed", "-s", type=int, default=None, help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--clean",
        "-c",
        default=False,
        action="store_true",
        help="Clean the project before building",
    )

    args = parser.parse_args()
    exit(
        main(
            epochs=args.epochs,
            max_examples_per_class=args.max_examples,
            random_seed=args.seed,
            clean=args.clean,
        )
    )
