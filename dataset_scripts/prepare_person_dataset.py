import os
import json
import shutil
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import urllib.request
import zipfile
import face_recognition
import numpy as np

base_path = Path(__file__).parent.parent / "datasets"
source_path = base_path / "raw_data" / "coco"
data_path = base_path / "data" / "person_detection"


def download_coco_subset():
    """Download COCO validation dataset subset"""
    # Create directories
    source_path.mkdir(parents=True, exist_ok=True)
    
    # COCO 2017 validation set URLs
    val_images_url = "http://images.cocodataset.org/zips/val2017.zip"
    val_annot_url = "http://images.cocodataset.org/annotations/annotations_trainval2017.zip"
    
    # Download images if needed
    image_zip = source_path / "val2017.zip"
    if not image_zip.exists():
        print("Downloading COCO validation images...")
        urllib.request.urlretrieve(val_images_url, image_zip)
        
    # Download annotations if needed
    annot_zip = source_path / "annotations.zip"
    if not annot_zip.exists():
        print("Downloading COCO annotations...")
        urllib.request.urlretrieve(val_annot_url, annot_zip)
        
    # Extract files if needed
    if not (source_path / "val2017").exists():
        print("Extracting images...")
        with zipfile.ZipFile(image_zip, 'r') as zip_ref:
            zip_ref.extractall(source_path)
            
    if not (source_path / "annotations").exists():
        print("Extracting annotations...")
        with zipfile.ZipFile(annot_zip, 'r') as zip_ref:
            zip_ref.extractall(source_path)


def prepare_person_classes():
    """Prepare person and no-person classes from COCO dataset"""
    # Define our target classes
    target_classes = {
        "person": 1,      # Images containing people's faces
        "without_person": 0    # Images without people
    }
    
    # Number of images to use per class
    images_per_class = 500

    # Download dataset if needed
    if not source_path.exists():
        download_coco_subset()

    # Load COCO annotations
    print("Loading COCO annotations...")
    with open(source_path / "annotations" / "instances_val2017.json", 'r') as f:
        coco = json.load(f)
    
    # Create image id to filename mapping
    id_to_file = {img['id']: img['file_name'] for img in coco['images']}
    
    # Find person category ID
    person_cat_id = None
    for cat in coco['categories']:
        if cat['name'] == 'person':
            person_cat_id = cat['id']
            break
            
    if person_cat_id is None:
        raise ValueError("Could not find person category in COCO dataset")
    
    # Find images with and without people
    person_images = set()
    for ann in coco['annotations']:
        if ann['category_id'] == person_cat_id:
            person_images.add(ann['image_id'])
    
    all_image_ids = {img['id'] for img in coco['images']}
    no_person_images = all_image_ids - person_images
    
    # Process each class
    print("Organizing classes...")
    for class_name in target_classes.keys():
        # Create class directory
        class_dir = data_path / class_name
        class_dir.mkdir(parents=True, exist_ok=True)
        
        # Select source images
        source_images = list(person_images if class_name == "person" else no_person_images)
        
        # Process images
        print(f"Processing {class_name}...")
        processed_count = 0
        for idx, img_id in enumerate(tqdm(source_images)):
            if processed_count >= images_per_class:
                break
                
            try:
                # Source and target paths
                src_file = source_path / "val2017" / id_to_file[img_id]
                target_file = class_dir / f"{class_name}_{processed_count:04d}.jpg"
                
                # Open and convert image
                img = Image.open(src_file)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # For person class, check if image contains a face
                if class_name == "person":
                    # Convert PIL image to numpy array for face_recognition
                    img_array = np.array(img)
                    # Detect faces in the image
                    face_locations = face_recognition.face_locations(img_array)
                    if not face_locations:  # Skip if no face detected
                        continue
                
                # Calculate dimensions for center crop
                width, height = img.size
                # Take the larger dimension and use it to resize while maintaining aspect ratio
                if width > height:
                    new_height = 640
                    new_width = int(width * (640 / height))
                else:
                    new_width = 640
                    new_height = int(height * (640 / width))
                
                # Resize image
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                
                # Center crop to 640x640
                left = (new_width - 640) // 2
                top = (new_height - 640) // 2
                right = left + 640
                bottom = top + 640
                img = img.crop((left, top, right, bottom))
                
                # Save with high quality
                img.save(target_file, "JPEG", quality=95)
                processed_count += 1
                
            except Exception as e:
                print(f"Error processing {src_file}: {e}")


if __name__ == "__main__":
    # Create necessary directories first
    base_path.mkdir(parents=True, exist_ok=True)
    (base_path / "raw_data").mkdir(exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)
    
    prepare_person_classes()
