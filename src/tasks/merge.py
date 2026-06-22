# src/tasks/merge_data.py
import os
import shutil
import yaml
from pathlib import Path
from src.core.logger import sys_logger


def merge_yolo_datasets():
    sys_logger.info("Starting YOLO dataset merging process...")

    # =========================================================================
    # 1. CẤU HÌNH ĐƯỜNG DẪN VÀ NHÃN
    # =========================================================================

    # Trỏ tới thư mục 'data' nằm ở gốc dự án dựa theo hình ảnh bạn cung cấp
    ROOT_DIR = Path(__file__).resolve().parent.parent.parent
    BASE_INPUT_DIR = ROOT_DIR / "data"

    # Thư mục đầu ra sau khi gộp xong
    OUTPUT_DIR = BASE_INPUT_DIR / "Data_Merge"

    # Danh sách nhãn tổng hợp (Master Classes).
    MASTER_CLASSES = [
        "bicycle",  # 0
        "bus",  # 1
        "car",  # 2
        "green_light",  # 3
        "motorcycle",  # 4
        "red_light",  # 5
        "stop_line",  # 6
        "truck",  # 7
        "van",  # 8
        "yellow_light",  # 9
    ]

    # Khai báo cấu trúc các nhãn cũ của từng thư mục
    DATASETS_CONFIG = {
        "Data1": {
            "classes": [
                "car",
                "green_light",
                "motobike",
                "red_light",
                "stop_line",
                "yellow_light",
            ]
        },
        "Data2": {
            "classes": [
                "bus",
                "car",
                "green_light",
                "motorcycle",
                "red_light",
                "truck",
                "van",
                "yellow_light",
            ]
        },
        "Data3": {
            "classes": [
                "bicycle",
                "bus",
                "car",
                "green_light",
                "motobike",
                "red_light",
                "stop_line",
                "truck",
                "yellow_light",
            ]
        },
    }

    # =========================================================================
    # 2. KHỞI TẠO CẤU TRÚC THƯ MỤC ĐẦU RA (Khớp với format Roboflow)
    # =========================================================================
    # Dựa vào hình ảnh, các thư mục chia là train, valid, test
    splits = ["train", "valid", "test"]

    # Xóa thư mục cũ nếu đã tồn tại để tránh rác
    if OUTPUT_DIR.exists():
        sys_logger.warning(
            f"Output directory {OUTPUT_DIR} already exists. Cleaning up..."
        )
        shutil.rmtree(OUTPUT_DIR)

    for split in splits:
        # Tạo cấu trúc: OUTPUT_DIR / train / images
        (OUTPUT_DIR / split / "images").mkdir(parents=True, exist_ok=True)
        (OUTPUT_DIR / split / "labels").mkdir(parents=True, exist_ok=True)

    sys_logger.info("Created output directory structure successfully.")

    # =========================================================================
    # 3. TIẾN HÀNH SAO CHÉP VÀ CHUYỂN ĐỔI ID NHÃN
    # =========================================================================
    for dataset_name, config in DATASETS_CONFIG.items():
        dataset_path = BASE_INPUT_DIR / dataset_name

        if not dataset_path.exists():
            sys_logger.error(f"Directory not found: {dataset_path}. Skipping...")
            continue

        sys_logger.info(f"Processing dataset: {dataset_name}")
        old_classes = config["classes"]

        # Tạo từ điển map ID cũ sang ID mới cho dataset hiện tại
        id_mapping = {}
        for old_id, class_name in enumerate(old_classes):
            # Đồng nhất tên bị sai chính tả
            normalized_name = "motorcycle" if class_name == "motobike" else class_name
            if normalized_name in MASTER_CLASSES:
                new_id = MASTER_CLASSES.index(normalized_name)
                id_mapping[old_id] = new_id
            else:
                sys_logger.warning(
                    f"Class '{class_name}' in {dataset_name} not found in MASTER_CLASSES!"
                )

        # Bắt đầu quét qua train, valid, test
        for split in splits:
            # Cấu trúc mới khớp với ảnh: Data1/train/images
            images_dir = dataset_path / split / "images"
            labels_dir = dataset_path / split / "labels"

            if not images_dir.exists() or not labels_dir.exists():
                sys_logger.info(
                    f"Missing images/labels for split '{split}' in {dataset_name}. Skipping this split."
                )
                continue

            # Duyệt qua từng file ảnh
            for img_file in images_dir.glob("*.*"):
                if img_file.suffix.lower() not in [".jpg", ".jpeg", ".png"]:
                    continue

                # Tìm file txt tương ứng
                txt_file = labels_dir / f"{img_file.stem}.txt"
                if not txt_file.exists():
                    continue

                # Tạo tên mới chống trùng lặp (vd: data1_img_001.jpg)
                new_basename = f"{dataset_name.lower()}_{img_file.name}"
                new_txtname = f"{dataset_name.lower()}_{txt_file.name}"

                # 3.1 Copy ảnh
                dest_img = OUTPUT_DIR / split / "images" / new_basename
                shutil.copy2(img_file, dest_img)

                # 3.2 Đọc, chuyển đổi ID và ghi file txt
                dest_txt = OUTPUT_DIR / split / "labels" / new_txtname
                with (
                    open(txt_file, "r", encoding="utf-8") as f_in,
                    open(dest_txt, "w", encoding="utf-8") as f_out,
                ):
                    for line in f_in:
                        parts = line.strip().split()
                        if not parts:
                            continue

                        old_id = int(parts[0])
                        if old_id in id_mapping:
                            new_id = id_mapping[old_id]
                            # Ráp lại chuỗi tọa độ giữ nguyên, chỉ thay con số đầu tiên
                            new_line = f"{new_id} " + " ".join(parts[1:]) + "\n"
                            f_out.write(new_line)

        sys_logger.info(f"Finished processing {dataset_name}")

    # =========================================================================
    # 4. TẠO FILE DATASET.YAML MỚI
    # =========================================================================
    # Cấu hình đường dẫn chéo theo đúng chuẩn YOLO yêu cầu
    yaml_content = {
        "path": ".",
        "train": "train/images",
        "val": "valid/images",  # YOLO bắt buộc key tên là 'val', dù thư mục tên là 'valid'
        "test": "test/images",
        "nc": len(MASTER_CLASSES),
        "names": MASTER_CLASSES,
    }

    yaml_path = OUTPUT_DIR / "dataset.yaml"
    with open(yaml_path, "w", encoding="utf-8") as f:
        yaml.dump(yaml_content, f, default_flow_style=None, sort_keys=False)

    sys_logger.info(f"Generated new YAML config at {yaml_path}")
    sys_logger.info("Dataset merging completed successfully!")


if __name__ == "__main__":
    merge_yolo_datasets()
