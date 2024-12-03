import sys
import termios
import time
import tty
import serial
import serial.tools.list_ports
from typing import Optional, Dict, List, Tuple
import os
import subprocess
from pathlib import Path


# Define project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def find_stm32_port() -> Optional[str]:
    """Find the STM32 board port.

    Returns:
        str | None: Port name if found, None otherwise
    """
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "usbmodem" in port.device.lower():
            return port.device
    return None


def create_serial_connection(port: str) -> serial.Serial:
    """Create a serial connection with standard settings.

    Args:
        port (str): Port name to connect to

    Returns:
        serial.Serial: Configured serial connection
    """
    return serial.Serial(
        port=port,
        baudrate=115200,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        timeout=0.1,
    )


def get_key() -> str:
    """Get a single keypress from the user.

    Returns:
        str: The character pressed
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


def read_serial_line(ser: serial.Serial) -> Optional[str]:
    """Read a line from the serial port if available.

    Args:
        ser (serial.Serial): Serial connection to read from

    Returns:
        str | None: Decoded line if available, None otherwise
    """
    if ser.in_waiting:
        try:
            line = ser.readline().decode("utf-8").strip()
            if line:
                return line
        except Exception as e:
            print(f"Error reading serial: {e}")
    return None


# STM32CubeIDE toolchain paths for macOS
CUBE_IDE_PATHS = [
    "/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.gnu-tools-for-stm32.12.3.rel1.macos64_1.0.200.202406191456/tools/bin",
    "/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.make.macos64_2.1.100.202310310804/tools/bin",
]


def is_macos() -> bool:
    """Check if running on macOS"""
    return os.uname().sysname == "Darwin"


def is_windows() -> bool:
    """Check if running on Windows"""
    return os.name == "nt"


def is_linux() -> bool:
    """Check if running on Linux"""
    return os.uname().sysname == "Linux"


def get_build_env() -> dict:
    """Get environment variables for building"""
    env = os.environ.copy()
    env["PATH"] = ":".join(CUBE_IDE_PATHS + [env.get("PATH", "")])
    return env


def clean_project(
    build_dir: str = str(PROJECT_ROOT / "Debug"), verbose: bool = False
) -> None:
    """Clean the project build

    Args:
        build_dir (str): Directory containing the Makefile
        verbose (bool): Whether to print the output of the command
    """
    try:
        print("Cleaning project...")
        result = subprocess.run(
            ["make", "-j7", "clean"],
            cwd=build_dir,
            env=get_build_env(),
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error during clean: {e}")
        if e.output:
            print(f"Build output:\n{e.output} {e.stderr}")
        raise


def build_project(
    build_dir: str = str(PROJECT_ROOT / "Debug"), verbose: bool = False
) -> None:
    """Build the project

    Args:
        build_dir (str): Directory containing the Makefile
        verbose (bool): Whether to print the output of the command
    """
    try:
        print("Building project...")
        result = subprocess.run(
            ["make", "-j7", "all"],
            cwd=build_dir,
            env=get_build_env(),
            check=True,
            capture_output=True,
            text=True,
        )
        if verbose:
            print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error during build: {e}")
        if e.output:
            print(f"Build output:\n{e.output} {e.stderr}")
        raise


def get_programmer_path() -> str:
    """Get the path to the STM32 programmer CLI"""
    if is_macos():
        path = "/Applications/STM32CubeIDE.app/Contents/Eclipse/plugins/com.st.stm32cube.ide.mcu.externaltools.cubeprogrammer.macos64_2.1.400.202404281720/tools/bin/STM32_Programmer_CLI"
    elif is_windows():
        path = "STM32_Programmer_CLI"  # TODO: Add proper Windows path
    else:
        raise RuntimeError(f"Unsupported OS: {os.uname().sysname}")

    if not os.path.exists(path):
        raise RuntimeError(
            f"STM32 programmer CLI not found at: {path}; "
            "this likely needs to be tweaked to work for your system"
        )
    return path


def deploy_binary(
    binary_path: str = str(PROJECT_ROOT / "Debug" / "TTE_demo_mcunet.elf"),
    verbose: bool = False,
) -> None:
    """Deploy binary to the microcontroller

    Args:
        binary_path (str): Path to the binary file
        verbose (bool): Whether to print the output of the command
    """
    try:
        programmer = get_programmer_path()
        cmd = [
            programmer,
            "--connect",
            "port=SWD",
            "--write",
            binary_path,
            "--verify",
            "-rst",
        ]

        print(f"Deploying binary: {binary_path}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if verbose:
            print(result.stdout)
        # sleep for 5 seconds to allow the device to boot
        time.sleep(5)
        print("Deployment complete")
    except subprocess.CalledProcessError as e:
        print(f"Error during deployment: {e}")
        print(f"Error output: {e.stdout}\n{e.stderr}")
        raise


def load_datasets(base_path: str) -> Dict[str, List[str]]:
    """Load datasets from the datasets folder"""
    datasets = {}
    base = Path(base_path)

    # List all directories in datasets folder
    for dataset_dir in base.iterdir():
        if dataset_dir.is_dir():
            # Get class names from subdirectories, and sort them to ensure consistent order
            datasets[dataset_dir.name] = sorted(
                d.name for d in dataset_dir.iterdir() if d.is_dir()
            )

    if not datasets:
        raise RuntimeError("No datasets found")

    return datasets


def update_output_ch_file(class_names: List[str], file_path: str):
    """Update the OUTPUT_CH and labels in the specified file"""
    class_names_str = ",\n".join([f'"{class_name}"' for class_name in class_names])
    with open(file_path, "w") as file:
        file.write(
f"""// GENERATED FILE FROM AUTOMATED TRAINING SCRIPT

#ifndef OUTPUT_CH_H
#define OUTPUT_CH_H
                   
#define OUTPUT_CH {len(class_names)}

static const char *const OUTPUT_LABELS[] = {{
{class_names_str}
}};

#endif // OUTPUT_CH_H                
""")


def select_dataset() -> Tuple[str, List[str]]:
    """Interactive dataset selection, returns (dataset_path, class_names)"""
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
    
    class_names = datasets[dataset_name]
    
    return dataset_path, class_names
