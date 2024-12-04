from pathlib import Path
import random
import sys
import threading
import time
import json
from typing import List, Optional, Set, Tuple
import metrics
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

SCREEN_WIDTH, SCREEN_HEIGHT = 1024, 768

def load_class_images(dataset_path: str, class_name: str) -> List[str]:
    """Load all images for a specific class"""
    class_path = Path(dataset_path) / class_name
    return [
        str(f)
        for f in class_path.glob("*")
        if f.suffix.lower() in [".jpg", ".jpeg", ".png"]
    ]


def display_image(
    image_path: str, window_name: str = "Training Image", delay: float = 0.5
):
    """Display image centered on black background"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Could not load image: {image_path}")

    # Create black background
    screen_width, screen_height = SCREEN_WIDTH, SCREEN_HEIGHT  # Adjustable
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
    screen_width, screen_height = SCREEN_WIDTH, SCREEN_HEIGHT  # Same as in display_image
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


def random_split_dataset(
    dataset_path: str,
    class_names: List[str],
    max_examples_per_class: Optional[int] = None,
    exclude_classes: Optional[Set[int]] = None,
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    all_data = []

    for class_name in class_names:
        images = load_class_images(dataset_path, class_name)
        if max_examples_per_class:
            images = images[:max_examples_per_class]
        all_data.extend([(img, class_to_idx[class_name]) for img in images])
        print(f"Loaded {len(images)} images for class '{class_name}'")

    if exclude_classes:
        all_data = [data for data in all_data if data[1] not in exclude_classes]

    # Split data
    random.shuffle(all_data)
    train_split = 0.7
    train_size = int(len(all_data) * train_split)

    return all_data[:train_size], all_data[train_size:]


def sequential_split_dataset(
    dataset_path: str,
    class_names: List[str],
    max_examples_per_class: Optional[int] = None,
    exclude_classes: Optional[Set[int]] = None,
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]]]:
    """Prepare and split dataset into training and validation sets"""
    class_to_idx = {name: idx for idx, name in enumerate(class_names)}
    all_class_labels: List[List[Tuple[str, int]]] = []
    min_labels_per_class = 1_000_000

    for class_name in class_names:
        images = load_class_images(dataset_path, class_name)
        random.shuffle(images)
        if max_examples_per_class:
            images = images[:max_examples_per_class]
        all_class_labels.append([(img, class_to_idx[class_name]) for img in images])
        print(f"Loaded {len(images)} images for class '{class_name}'")
        min_labels_per_class = min(min_labels_per_class, len(images))

    if exclude_classes:
        # filter out classes to test gradient problems
        all_class_labels = [
            class_labels_array
            for class_labels_array in all_class_labels
            if class_labels_array[0][1] not in exclude_classes
        ]

    training_data: List[Tuple[str, int]] = []
    test_data: List[Tuple[str, int]] = []

    train_split = 0.7
    num_training_samples = int(min_labels_per_class * train_split)

    for i in range(min_labels_per_class):
        for class_labels_array in all_class_labels:
            # Add to training data if index is less than number of training samples
            if i < num_training_samples:
                training_data.append(class_labels_array.pop(0))
            else:
                test_data.append(class_labels_array.pop(0))

    return training_data, test_data


def run_validation(
    uart: UARTHandler, val_data: List[Tuple[str, int]], 
    metrics_tracker: metrics.MetricsTracker,
    phase: str = "Validation",
) -> Tuple[float, dict]:
    """Run validation and print detailed metrics

    Args:
        uart: UART handler for device communication
        val_data: List of (image_path, class) tuples
        phase: Description of validation phase (e.g., "Initial", "Final", etc.)

    Returns:
        metrics: Dictionary containing validation metrics (class accuracies, image paths, predictions, etc.)
    """
    print(f"\n=== Running {phase} Validation ===")
    uart.send_command("v")  # Enter validation mode

    val_start = time.time()
    metrics_tracker.val_mode()

    for idx, (image_path, true_class) in enumerate(val_data):
        # clear uart messages
        uart.last_messages = []
        print(f"\nValidating image {idx + 1}/{len(val_data)}")
        display_image(image_path, delay=1.0)
        try:
            predicted_class = uart.wait_for_consecutive_inference(num_consecutive=3)
            metrics_tracker.update(predicted_class, true_class)
        except TimeoutError:
            print(f"ERROR: Failed to get consistent prediction for {image_path}")

    val_time = time.time() - val_start
    metrics_tracker.metrics["run_time"] = val_time
    metrics_tracker.print_summary()
    metrics_tracker.save_metrics()

    return metrics_tracker.metrics


def run_training_epoch(
    uart: UARTHandler, train_data: List[Tuple[str, int]], epoch: int, epochs: int,
    metrics_tracker: metrics.MetricsTracker,
    record_every: int = 5, 
) -> dict:
    """Run a single training epoch and return metrics

    Args:
        uart: UART handler for device communication
        train_data: List of (image_path, class) tuples
        epoch: Current epoch number
        epochs: Total number of epochs
        record_every: If > 0, save metrics every N steps

    Returns:
        metrics: Dictionary containing training metrics (class accuracies, image paths, predictions, etc.)
    """

    uart.send_command("t")  # Enter training mode

    epoch_start = time.time()
    print(f"\nEpoch {epoch + 1}/{epochs}")
    metrics_tracker.train_mode()

    for idx, (image_path, true_class) in enumerate(train_data):
        # Initialize class metrics if not exists
        img_start = time.time()
        print(f"\nTraining image {idx + 1}/{len(train_data)} (Class: {true_class})")
        display_image(image_path)

        # Send class number and wait for training completion
        uart.send_command(str(true_class))

        # Wait for training completion and prediction
        if uart.wait_for_message("TRAINING DONE", timeout=5.0):
            # Look for prediction in messages
            predicted_class = None
            for msg in uart.last_messages:
                if "TRAINING PREDICTION:" in msg:
                    try:
                        predicted_class = int(msg.split(":")[-1].strip())
                        break
                    except ValueError:
                        continue

            if predicted_class is not None:
                # Update metrics
                metrics_tracker.update(predicted_class, true_class)
                img_time = time.time() - img_start
                print(f"Training successful - took {img_time:.2f}s")
                metrics_tracker.print_summary()
            else:
                print(f"WARNING: No prediction received for image {idx + 1}")
        else:
            print(f"WARNING: Training timeout for image {idx + 1}")

        if record_every > 0 and (idx + 1) % record_every == 0:
            print(f"Saving metrics after {idx + 1} images")
            metrics_tracker.save_metrics()

    # Calculate final metrics
    training_time = time.time() - epoch_start
    metrics_tracker.metrics["run_time"] = training_time

    metrics_tracker.print_summary()
    metrics_tracker.save_metrics()

    return metrics_tracker.metrics


def main(
    epochs: int = 3,
    max_examples_per_class: Optional[int] = None,
    random_seed: Optional[int] = None,
    clean: bool = False,
    split_method: str = "sequential",
    exclude_classes: Optional[Set[int]] = None,
    no_align: bool = False,
    preselected_dataset: Optional[str] = None,
    metrics_path: Optional[str] = "metrics",
    record_every: int = 5,
):
    try:
        if random_seed is not None:
            random.seed(random_seed)
            np.random.seed(random_seed)  # Also set numpy's random seed
            print(f"\nUsing random seed: {random_seed}")

        # Select dataset and get class names
        dataset_path, class_names = select_dataset(preselected_dataset)

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
        train_data, val_data = (
            random_split_dataset(
                dataset_path,
                class_names,
                max_examples_per_class,
                exclude_classes,
            )
            if split_method == "random"
            else sequential_split_dataset(
                dataset_path,
                class_names,
                max_examples_per_class,
                exclude_classes,
            )
        )
        print(
            f"\nData split: {len(train_data)} training samples, {len(val_data)} validation samples"
        )

        metrics_tracker = metrics.MetricsTracker(num_classes=len(class_names), 
                                                 mode="train",
                                                 model="base",
                                                 metrics_path=metrics_path,
                                                 track_predictions=True,
                                                 examples_per_class=max_examples_per_class)
        training_start_time = time.time()
        uart = UARTHandler()
        try:
            # TODO maybe this should be the first image to better determine camera focus
            # than just black text on white frame
            if not no_align:
                # Display blank frame and wait for alignment
                display_blank_frame()
                input("Position camera and press Enter to start training...")

            # Initial validation
            initial_metrics = run_validation(
                uart, val_data, metrics_tracker, "Initial"
            )
            # Training phase
            print("\n=== Starting Training Phase ===")

            for epoch in range(epochs):
                output_metrics = run_training_epoch(uart, train_data, epoch, epochs, metrics_tracker, record_every)

                print(f"\nEpoch {epoch + 1} Stats:")
                print(f"Time: {output_metrics['run_time']:.2f}s")
                if epoch != epochs - 1:
                    # Mid-training validation
                    val_metrics = run_validation(
                        uart, val_data, metrics_tracker, f"Epoch {epoch + 1}"
                    )

            # Final validation
            final_metrics = run_validation(
                uart, val_data, metrics_tracker, "Final"
            )

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
    # either random split or sequential split
    parser.add_argument(
        "--split",
        "-sp",
        default="sequential",
        choices=["sequential", "random"],
    )
    # enter the classes to exclude from training, should be a list of class numbers
    # note that this doesn't exclude them from the binary, it only excludes their images
    # from being included in the training and test set
    parser.add_argument(
        "--exclude-classes",
        "-ec",
        default=[],
        nargs="+",
        help="Exclude classes from training",
    )
    # skip asking for camera alignment
    parser.add_argument(
        "--no-align",
        "-na",
        default=False,
        action="store_true",
        help="Skip asking for camera alignment",
    )
    # preselect dataset
    parser.add_argument(
        "--dataset", "-d", type=str, default=None, help="Preselect dataset"
    )

    args = parser.parse_args()
    exit(
        main(
            epochs=args.epochs,
            max_examples_per_class=args.max_examples,
            random_seed=args.seed,
            clean=args.clean,
            split_method=args.split,
            exclude_classes=set([int(cls) for cls in args.exclude_classes])
            if args.exclude_classes
            else None,
            no_align=args.no_align,
            preselected_dataset=args.dataset,
        )
    )
