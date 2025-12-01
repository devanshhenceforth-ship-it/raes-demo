from ultralytics import YOLO
import logging

logger = logging.getLogger(__name__)
yolo_model: YOLO | None = None

def load_model(model_path: str = "yolov8n.pt") -> YOLO:
    """
    Load YOLO model globally. Returns the model.
    """
    global yolo_model
    if yolo_model is None:
        try:
            logger.info("🔥 Loading YOLO model...")
            yolo_model = YOLO(model_path)
            logger.info("✅ YOLO model loaded!")
        except Exception as e:
            logger.error(f"Failed to load YOLO model: {e}")
            raise
    return yolo_model

def get_model() -> YOLO:
    """
    Get already-loaded YOLO model.
    """
    if yolo_model is None:
        raise RuntimeError("YOLO model not loaded. Call load_model() first.")
    return yolo_model
