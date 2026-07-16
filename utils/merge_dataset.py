import os
import yaml
import shutil
import argparse


def count_img(path):
    if not os.path.exists(path):
        return 0
    return len(
        [f for f in os.listdir(path) if f.lower().endswith((".jpg", ".jpeg", ".png"))]
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--new_dir", type=str, required=True)
    parser.add_argument("--old_dir", type=str, required=True)
    args = parser.parse_args()

    new_dataset_dir = args.new_dir
    old_dataset_dir = args.old_dir
    new_yaml_path = os.path.join(new_dataset_dir, "data.yaml")

    print("Initializing dataset merge for traffic-lights-5i6fs...")

    if not os.path.exists(new_yaml_path):
        print(f"Error: YAML file not found at {new_yaml_path}")
        return

    with open(new_yaml_path, "r") as f:
        new_data_info = yaml.safe_load(f)

    new_names = new_data_info.get("names", [])
    print(f"Detected classes in Roboflow dataset: {new_names}")

    id_mapping = {}
    if isinstance(new_names, list):
        for idx, class_name in enumerate(new_names):
            name_lower = class_name.lower()
            if "yellow" in name_lower:
                continue
            if "green" in name_lower:
                id_mapping[idx] = 1
            elif "red" in name_lower:
                id_mapping[idx] = 3

    print(f"Generated ID Mapping: {id_mapping}")

    if not id_mapping:
        print("Error: Could not map any target classes.")
        return

    old_train_img_dir = os.path.join(old_dataset_dir, "train", "images")
    old_val_img_dir = os.path.join(old_dataset_dir, "validation", "images")
    new_train_img_dir = os.path.join(new_dataset_dir, "train", "images")
    new_val_img_dir = os.path.join(new_dataset_dir, "valid", "images")

    old_train_before = count_img(old_train_img_dir)
    old_val_before = count_img(old_val_img_dir)
    old_total_before = old_train_before + old_val_before

    new_train_total = count_img(new_train_img_dir)
    new_val_total = count_img(new_val_img_dir)
    new_total = new_train_total + new_val_total

    roboflow_split_folders = {"train": "train", "valid": "validation"}

    total_copied_images = 0
    total_extracted_boxes = 0

    for rb_folder, my_folder in roboflow_split_folders.items():
        new_labels_dir = os.path.join(new_dataset_dir, rb_folder, "labels")
        new_images_dir = os.path.join(new_dataset_dir, rb_folder, "images")

        old_labels_dir = os.path.join(old_dataset_dir, my_folder, "labels")
        old_images_dir = os.path.join(old_dataset_dir, my_folder, "images")

        os.makedirs(old_labels_dir, exist_ok=True)
        os.makedirs(old_images_dir, exist_ok=True)

        if os.path.exists(new_labels_dir):
            for label_file in os.listdir(new_labels_dir):
                if not label_file.endswith(".txt"):
                    continue

                new_label_path = os.path.join(new_labels_dir, label_file)
                valid_lines = []

                with open(new_label_path, "r") as f:
                    for line in f:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            old_id = int(parts[0])
                            if old_id in id_mapping:
                                new_id = id_mapping[old_id]
                                valid_lines.append(f"{new_id} {' '.join(parts[1:])}\n")

                if valid_lines:
                    base_name = os.path.splitext(label_file)[0]
                    img_found = False

                    for ext in [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]:
                        new_img_path = os.path.join(new_images_dir, base_name + ext)
                        if os.path.exists(new_img_path):
                            dest_img_name = f"rf_{base_name}{ext}"
                            dest_label_name = f"rf_{base_name}.txt"

                            old_img_path = os.path.join(old_images_dir, dest_img_name)
                            old_label_path = os.path.join(
                                old_labels_dir, dest_label_name
                            )

                            with open(old_label_path, "w") as f:
                                f.writelines(valid_lines)

                            shutil.copy2(new_img_path, old_img_path)

                            total_copied_images += 1
                            total_extracted_boxes += len(valid_lines)
                            img_found = True
                            break

                    if not img_found:
                        print(f"Warning: Missing image file for {label_file}")

    old_train_after = count_img(old_train_img_dir)
    old_val_after = count_img(old_val_img_dir)
    old_total_after = old_train_after + old_val_after

    print("--------------------------------------------------")
    print("Merge completed successfully!")
    print(f"Total original Roboflow images: {new_total}")
    print(f"Total original Custom images: {old_total_before}")
    print("--------------------------------------------------")
    print(f"Train split before merge: {old_train_before}")
    print(f"Valid split before merge: {old_val_before}")
    print("--------------------------------------------------")
    print(f"Images imported from Roboflow: {total_copied_images}")
    print(f"Total traffic light bounding boxes extracted: {total_extracted_boxes}")
    print("--------------------------------------------------")
    print(f"Train split after merge: {old_train_after}")
    print(f"Valid split after merge: {old_val_after}")
    print(f"Total images in final merged dataset: {old_total_after}")
    print("--------------------------------------------------")
    print(
        f"Final Dataset Composition -> Custom : Roboflow = {old_total_before} : {total_copied_images}"
    )


if __name__ == "__main__":
    main()
