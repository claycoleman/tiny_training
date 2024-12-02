import os
from pathlib import Path

base_path = Path(__file__).parent.parent / "datasets" / "raw_data" / "tiny_imagenet"
words_file = base_path / "words.txt"

target_classes = {
    "bicycle": "n02834778",
    "coffee_mug": "n03063599",
    "laptop": "n03642806",
    "backpack": "n02769748",
    "traffic_light": "n06874185",
    "park_bench": "n03891251",
    "book": "n02870880",
    "pedestrian": "n10412055",
    "cell_phone": "n02992529",
    "water_bottle": "n04557648"
}

def check_class_exists(class_id):
    train_dir = base_path / "train" / class_id
    if train_dir.exists():
        print(f"Class {class_id} exists in training set")
    else:
        print(f"Class {class_id} NOT FOUND in training set")

print("Checking class existence...")
for class_name, class_id in target_classes.items():
    print(f"\nChecking {class_name} ({class_id}):")
    check_class_exists(class_id)
