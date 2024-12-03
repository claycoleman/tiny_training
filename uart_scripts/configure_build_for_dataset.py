from pathlib import Path
import sys
from utils import (
    PROJECT_ROOT,
    select_dataset,
    update_output_ch_file,
    clean_project,
    build_project,
    deploy_binary,
)

def main():
    try:
        # Select dataset and get class names
        dataset_path, class_names = select_dataset()
        print(f"\nSelected dataset with {len(class_names)} classes:")
        for i, name in enumerate(class_names):
            print(f"{i}: {name}")

        # Update OUTPUT_CH.h file
        output_ch_file = str(PROJECT_ROOT / "Src/TinyEngine/include/OUTPUT_CH.h")
        update_output_ch_file(class_names, output_ch_file)
        print(f"\nUpdated {output_ch_file} with new class definitions")

        # if --no-deploy flag is not provided, build and deploy the project
        if "--no-deploy" not in sys.argv:
            print("\nRebuilding project...")
            clean_project()
            build_project()
            deploy_binary()
            print("\nBuild complete! You can now deploy the binary to your device.")

    except Exception as e:
        print(f"\nError: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main()) 