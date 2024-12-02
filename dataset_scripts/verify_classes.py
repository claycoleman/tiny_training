import os
from pathlib import Path

base_path = Path(__file__).parent.parent / "datasets" / "raw_data" / "tiny_imagenet"
words_file = base_path / "words.txt"

def find_class_id(search_term):
    with open(words_file, 'r') as f:
        for line in f:
            wnid, descriptions = line.strip().split('\t')
            if search_term.lower() in descriptions.lower():
                print(f"Found match for '{search_term}':")
                print(f"ID: {wnid}")
                print(f"Full description: {descriptions}")
                print("---")

search_terms = [
    "bicycle", "coffee", "laptop", "backpack", 
    "traffic light", "bench", "book", 
    "person", "phone", "bottle"
]

print("Searching for class IDs...")
for term in search_terms:
    find_class_id(term)
