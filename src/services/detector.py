from ultralytics import YOLO
import cv2
import numpy as np

yolo_model = YOLO("yolov8n.pt")  # nano model (lightweight)

def detect_items_from_bytes(video_bytes: bytes):
    temp = "/tmp/detect_temp.mp4"
    with open(temp, "wb") as f:
        f.write(video_bytes)

    cap = cv2.VideoCapture(temp)

    if not cap.isOpened():
        return []

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_step = int(fps) if fps > 0 else 1  # 1 frame per second

    detected = []
    last_label = None     
    frame_idx = 0

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
        ret, frame = cap.read()
        if not ret:
            break

        results = yolo_model(frame)

        for r in results:
            for box in r.boxes:
                cls = int(box.cls)
                label = r.names[cls]
                if label == last_label:
                    continue
                last_label = label

                detected.append({
                    "timestamp": int(frame_idx / fps) if fps > 0 else 0,
                    "item": label,
                    "description": ""   # empty description as required
                })

        frame_idx += frame_step

    cap.release()
    return detected
