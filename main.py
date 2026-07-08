from ultralytics import YOLO
import cv2
import numpy as np
import argparse


def get_stop_line(roi_frame):

    gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blur, 20, 30)

    height, width = edges.shape
    mask = np.zeros_like(edges)
    polygon = np.array(
        [
            [
                (0, height),
                (0, height // 2 + 50),
                (width, height // 2 + 50),
                (width, height),
            ]
        ]
    )
    cv2.fillPoly(mask, polygon, 255)

    masked_edges = cv2.bitwise_and(edges, mask)
    lines = cv2.HoughLinesP(
        masked_edges,
        rho=1,
        theta=np.pi / 180,
        threshold=50,
        minLineLength=100,
        maxLineGap=20,
    )

    y_stop = None
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line
            if abs(y2 - y1) < 15:
                cv2.line(roi_frame, (x1, y1), (x2, y2), (255, 0, 0), 2)
                y_stop = (y1 + y2) // 2
                break

    return y_stop


def detect_and_draw(roi_frame, model, y_stop):

    results = model(roi_frame)
    boxes = results[0].boxes
    class_names = model.names

    red_light_on = False

    for box in boxes:
        cls_id = int(box.cls[0])
        if class_names[cls_id] == "red_light":
            red_light_on = True
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cv2.rectangle(roi_frame, (x1, y1), (x2, y2), (0, 0, 255), 2)
            cv2.putText(
                roi_frame,
                "Red Light",
                (x1, y1 - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 255),
                2,
            )
            break

    if y_stop is not None:
        height, width = roi_frame.shape[:2]

        cv2.line(roi_frame, (0, y_stop), (width, y_stop), (0, 0, 255), 2)

        for box in boxes:
            cls_id = int(box.cls[0])
            class_name = class_names[cls_id]

            if class_name in ["car", "motorbike"]:
                x1, y1, x2, y2 = map(int, box.xyxy[0])

                is_violating = False

                # Xe đè vạch khi đèn đỏ
                if red_light_on and (y1 <= y_stop <= y2):
                    is_violating = True

                if is_violating:
                    color = (0, 0, 255)  # Đỏ - Vi phạm
                    label = f"VIOLATION: {class_name}"
                    cv2.rectangle(roi_frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        roi_frame,
                        label,
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        color,
                        2,
                    )

    return roi_frame


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source", type=str, required=True, help="Input video file path"
    )
    parser.add_argument(
        "--weights", type=str, default="best.pt", help="YOLO model weights path"
    )
    parser.add_argument(
        "--output", type=str, default="output.mp4", help="Output video file path"
    )
    args = parser.parse_args()

    model = YOLO(args.weights)

    video_path = args.source
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        print(f"Error: Cannot open video at {video_path}")
        return

    x_min, x_max = 1800, 2920
    y_min, y_max = 0, 940

    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = x_max - x_min
    height = y_max - y_min
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))

    y_stop = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("End of video stream or cannot fetch frame")
            break

        roi_frame = frame[y_min:y_max, x_min:x_max]

        if y_stop is None:
            y_stop = get_stop_line(roi_frame)
            if y_stop is not None:
                print(f"Stop line detected at Y coordinate (in ROI) = {y_stop}")

        processed_roi = detect_and_draw(roi_frame, model, y_stop)

        out.write(processed_roi)

    cap.release()
    out.release()


if __name__ == "__main__":
    main()

