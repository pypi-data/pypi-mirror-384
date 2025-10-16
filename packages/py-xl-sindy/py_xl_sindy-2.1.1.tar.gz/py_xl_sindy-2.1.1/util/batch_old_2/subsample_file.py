import os
import shutil
import random
from collections import defaultdict


def subsample_files(source_dir, destination_dir, sample_size=20):
    if not os.path.exists(destination_dir):
        os.makedirs(destination_dir)

    # Categorize files
    category_files = defaultdict(set)

    for file_name in os.listdir(source_dir):
        if "__" in file_name and (
            file_name.endswith(".json") or file_name.endswith(".npz")
        ):
            base_name = file_name.rsplit(".", 1)[0]  # Remove extension to pair files
            category = base_name.split("__")[0]  # Extract category
            category_files[category].add(base_name)

    # Ensure unique base names and subsample
    for category, base_names in category_files.items():
        base_names = sorted(base_names)  # Ensure deterministic order
        if len(base_names) > sample_size:
            step = len(base_names) // sample_size
            sampled_bases = base_names[::step][:sample_size]  # Uniform subsampling
        else:
            sampled_bases = base_names  # Copy all if less than required sample size

        for base_name in sampled_bases:
            for ext in [".json", ".npz"]:
                file_name = base_name + ext
                src_path = os.path.join(source_dir, file_name)
                dest_path = os.path.join(destination_dir, file_name)
                if os.path.exists(src_path):
                    shutil.copy(src_path, dest_path)
                    print(f"Copied {file_name} to {destination_dir}")


if __name__ == "__main__":
    source_directory = "result.second"  # Change this to your actual source folder
    destination_directory = "result"  # Change this to your actual destination folder
    sample_size = 20  # Change this as needed

    subsample_files(source_directory, destination_directory, sample_size)
