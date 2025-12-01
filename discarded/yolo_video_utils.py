# import os
# import cv2
# from ultralytics import YOLO
# import logging
# from ..helper import get_result_queue
# logger = logging.getLogger(__name__)

# # Global model
# yolo_model: YOLO | None = None

# def load_model(model_path: str = "yolov8n.pt") -> YOLO:
#     """
#     Load YOLO model globally and return it.
#     """
#     global yolo_model
#     if yolo_model is None:
#         logger.info("🔥 Loading YOLO model...")
#         yolo_model = YOLO(model_path)
#         logger.info("✅ YOLO model loaded!")
#     return yolo_model

# def get_model() -> YOLO:
#     """
#     Get the already loaded YOLO model.
#     """
#     if yolo_model is None:
#         raise RuntimeError("YOLO model not loaded. Call load_model() first.")
#     return yolo_model

# # Load model at import
# load_model()
# model = get_model()


# async def extract_detection_frames(
#     room_id: str,
#     video_path: str,
#     output_dir: str,
#     target_fps: float = 2.0,
#     conf_threshold: float = 0.4,
#     resize: tuple[int,int] | None = None
# ) -> int:
#     """
#     Process video and save frames with any detection above conf_threshold.
#     Automatically skips frames to achieve target FPS.
#     """
#     os.makedirs(output_dir, exist_ok=True)

#     cap = cv2.VideoCapture(video_path)
#     if not cap.isOpened():
#         raise ValueError(f"Could not open video: {video_path}")

#     video_fps = cap.get(cv2.CAP_PROP_FPS)
#     frame_skip = max(1, int(video_fps / target_fps))

#     result_queue = get_result_queue(room_id)

#     saved = 0
#     frame_idx = 0

#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break

#         # Skip frames
#         if frame_idx % frame_skip != 0:
#             frame_idx += 1
#             continue

#         img = frame
#         if resize:
#             img = cv2.resize(frame, resize)

#         results = model(img)[0]
#         boxes = results.boxes
#         detections = [b for b in boxes if float(b.conf[0]) >= conf_threshold]

#         if detections:
#             out_path = os.path.join(output_dir, f"frame_{frame_idx:06d}.jpg")
#             cv2.imwrite(out_path, frame)
#             saved += 1

#             await result_queue.put({"detection_frames_items": detections})


#         frame_idx += 1

#     cap.release()
#     logger.info(f"Saved {saved} frames with detections.")
#     return saved



import os
import cv2
from ultralytics import YOLO
import logging
from ..helper import get_result_queue

logger = logging.getLogger(__name__)

# Global YOLO model
yolo_model: YOLO | None = None

def load_model(model_path: str = "yolov8n.pt") -> YOLO:
    """
    Load YOLO model globally and return it.
    """
    global yolo_model
    if yolo_model is None:
        logger.info("🔥 Loading YOLO model...")
        yolo_model = YOLO(model_path)
        logger.info("✅ YOLO model loaded!")
    return yolo_model

def get_model() -> YOLO:
    """
    Get already-loaded YOLO model.
    """
    if yolo_model is None:
        raise RuntimeError("YOLO model not loaded. Call load_model() first.")
    return yolo_model

# Load model at import
load_model()
model = get_model()


async def extract_detection_frames(
    room_id: str,
    video_path: str,
    output_dir: str,
    target_fps: float = 3,
    conf_threshold: float = 0.6,
    resize: tuple[int,int] | None = None
) -> int:
    """
    Process video and save frames with any detection above conf_threshold.
    Puts detected item names into an asyncio.Queue for live consumption.
    """
    os.makedirs(output_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    frame_skip = max(1, int(video_fps / target_fps))
    saved = 0
    frame_idx = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Skip frames to match target FPS
        if frame_idx % frame_skip != 0:
            frame_idx += 1
            continue

        img = cv2.resize(frame, resize) if resize else frame
        results = model(img)[0]
        boxes = results.boxes

        # Collect detected item names above confidence threshold
        item_names = [model.names[int(b.cls[0])] for b in boxes if float(b.conf[0]) >= conf_threshold]

        if item_names:
            frame_name = f"frame_{frame_idx:06d}.jpg"
            cv2.imwrite(os.path.join(output_dir, frame_name), frame)
            saved += 1

            issues = [
                {
                    "timestamp": frame_idx,
                    "item": item_name,
                    "description": ""
                }
                for item_name in item_names
            ]

            await result_queue.put({
                "issues": issues
            })

            logger.info(f"Queued issues for frame {frame_idx}: {issues}")


        frame_idx += 1

    cap.release()
    logger.info(f"Saved {saved} frames with detections for video {video_path}.")
    return saved
