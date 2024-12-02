import os
import shutil
from pathlib import Path
from tqdm import tqdm
import requests
import tarfile
from PIL import Image
import urllib.request

base_path = Path(__file__).parent.parent / "datasets"
zip_path = base_path / "tiny-imagenet-200.zip"
source_path = base_path / "raw_data" / "tiny_imagenet"
data_path = base_path / "ten_class_data" / "tiny_imagenet"


def download_tiny_imagenet():
    """Download Tiny-ImageNet dataset"""
    url = "http://cs231n.stanford.edu/tiny-imagenet-200.zip"

    # Download if not exists
    if not zip_path.exists():
        print(f"Downloading Tiny-ImageNet from {url}...")
        response = requests.get(url, stream=True)
        total_size = int(response.headers.get("content-length", 0))

        with open(zip_path, "wb") as f:
            with tqdm(total=total_size, unit="B", unit_scale=True) as pbar:
                for data in response.iter_content(chunk_size=1024):
                    f.write(data)
                    pbar.update(len(data))

    # Extract if needed
    if not source_path.exists():
        print("Extracting zip file...")
        import zipfile
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(base_path / "raw_data")
            # Rename extracted directory
            (base_path / "raw_data" / "tiny-imagenet-200").rename(source_path)


def prepare_selected_classes():
    """Prepare selected classes from Tiny-ImageNet"""
    # Define our target classes
    selected_classes = {
        "keyboard": "n03085013",     # computer keyboard, keypad
        "backpack": "n02769748",     # backpack, back pack, knapsack, rucksack, haversack
        "desk": "n03179701",         # desk - common furniture
        "dining_table": "n03201208", # dining table, board
        "remote": "n04074963",       # remote control, remote
    }

    # Download dataset if needed
    if not source_path.exists():
        download_tiny_imagenet()

    print("Organizing selected classes...")
    for class_name, wnid in selected_classes.items():
        # Create class directory
        class_dir = data_path / class_name
        class_dir.mkdir(exist_ok=True)

        # Source directory for this class
        source_class_dir = source_path / "train" / wnid / "images"

        if not source_class_dir.exists():
            print(f"Warning: Could not find source directory for {class_name}")
            continue

        # Copy and rename images
        print(f"Processing {class_name}...")
        for idx, img_file in enumerate(source_class_dir.glob("*.JPEG")):
            try:
                # Open and save as JPG with Pillow to ensure compatibility
                img = Image.open(img_file)
                target_file = class_dir / f"{class_name}_{idx:04d}.jpg"
                img.save(target_file, "JPEG")
            except Exception as e:
                print(f"Error processing {img_file}: {e}")


if __name__ == "__main__":
    # Create necessary directories first
    base_path.mkdir(parents=True, exist_ok=True)
    (base_path / "raw_data").mkdir(exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)
    
    prepare_selected_classes()
