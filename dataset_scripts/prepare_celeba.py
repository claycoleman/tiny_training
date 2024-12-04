import os
from pathlib import Path
import zipfile
import gdown
from torchvision import transforms
from PIL import Image
from tqdm import tqdm

base_path = Path(__file__).parent.parent / "datasets"
data_path = base_path / "data" / "img_align_celeba"
raw_path = base_path / "raw_data"
source_path = raw_path / "img_align_celeba"
txt_path = base_path / "identity_CelebA.txt"
zip_path = base_path / "img_align_celeba.zip"


def download_celeba():
    """Download CelebA dataset using gdown"""
    if not zip_path.exists():
        print("Downloading CelebA dataset...")
        print("If download fails, please manually:")
        print(
            "1. Visit: https://drive.google.com/drive/folders/0B7EVK8r0v71pWEZsZE9oNnFzTm8"
        )
        print("2. Download 'img_align_celeba.zip'")
        print(f"3. Place it at: {zip_path}")

        # Try automatic download first
        url = "https://drive.google.com/uc?id=0B7EVK8r0v71pZjFTYXZWM3FlRnM"
        try:
            gdown.download(url, str(zip_path), quiet=False)
        except Exception as e:
            print(
                "\nAutomatic download failed. Please follow manual download instructions above."
            )
            return False
    return True


def download_identity_mapping():
    """Download identity mapping file"""
    if not txt_path.exists():
        print("Downloading identity mapping file...")
        url = "https://drive.google.com/uc?id=1_ee_0u7vcNLOfNLegJRHmolfH5ICW-XS"
        try:
            gdown.download(url, str(txt_path), quiet=False)
        except Exception as e:
            print("\nFailed to download identity mapping file.")
            return False
    return True


def extract_dataset():
    """Extract the CelebA dataset"""
    if not zip_path.exists():
        print("Dataset zip file not found!")
        return False

    if not source_path.exists():
        print("Extracting dataset...")
        raw_path.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(raw_path)
    return True


def prepare_dataset():
    """Prepare CelebA dataset"""
    if (
        not download_celeba()
        or not extract_dataset()
        or not download_identity_mapping()
    ):
        return

    # First, let's count images per identity
    identity_counts = {}
    identity_mapping = {}

    print("Analyzing identity distribution...")
    with open(txt_path, "r") as f:
        for line in f:
            img_name, identity = line.strip().split()
            identity = int(identity)
            identity_counts[identity] = identity_counts.get(identity, 0) + 1
            identity_mapping[img_name] = identity

    # Get top 4 identities by image count
    identities = sorted(identity_counts.items(), key=lambda x: x[1], reverse=True)
    top_identities = [identities[i] for i in [0, 1, 4, 5]]
    selected_individuals = {
        f"person_{i+1}": id for i, (id, count) in enumerate(top_identities)
    }

    print("\nSelected individuals (by number of images):")
    for person, identity in selected_individuals.items():
        print(f"{person} (ID {identity}): {identity_counts[identity]} images")

    # Create output directories
    for person_name in selected_individuals.keys():
        person_dir = data_path / person_name
        person_dir.mkdir(parents=True, exist_ok=True)

    # Process images
    img_dir = source_path
    if not img_dir.exists():
        print(f"Image directory not found at {img_dir}")
        return

    print("\nProcessing images...")
    processed_counts = {name: 0 for name in selected_individuals.keys()}

    # List all images and process them
    all_images = sorted(list(img_dir.glob("*.jpg")))
    print(f"Found {len(all_images)} images.")

    for img_path in tqdm(all_images):
        img_name = img_path.name
        if img_name in identity_mapping:
            identity_id = identity_mapping[img_name]

            # Check if this image belongs to our selected individuals
            for person_name, target_id in selected_individuals.items():
                if identity_id == target_id:
                    # Open, resize and save image
                    img = Image.open(img_path)
                    img = img.resize((528, 528), Image.LANCZOS)
                    save_path = (
                        data_path
                        / person_name
                        / f"{person_name}_{processed_counts[person_name]:04d}.jpg"
                    )
                    img.save(save_path, "JPEG")
                    processed_counts[person_name] += 1
                    break

            # Check if we have enough images for all individuals
            if all(count >= 100 for count in processed_counts.values()):
                break

    print("\nDataset preparation complete!")
    for person, count in processed_counts.items():
        print(f"{person}: {count} images")


if __name__ == "__main__":
    # Create necessary directories
    base_path.mkdir(parents=True, exist_ok=True)
    data_path.mkdir(parents=True, exist_ok=True)

    prepare_dataset()
