from fastapi import APIRouter, UploadFile, File, BackgroundTasks, HTTPException, Form
from ..utils.minio_client import minio_client
from ..utils import yolo_video_utils
import uuid
import os
import tempfile
import shutil
import logging
import asyncio

router = APIRouter(
    prefix="/yolo",
    tags=["YOLO Analysis"],
)

logger = logging.getLogger(__name__)


async def process_yolo_video(room_id: str, job_id: str, file_content: bytes):
    """
    Background task: download video, run YOLO detection, upload frames.
    """
    try:
        tmp_dir = tempfile.mkdtemp()
        video_path = os.path.join(tmp_dir, "input.mp4")
        with open(video_path, "wb") as f:
            f.write(file_content)   

        output_dir = os.path.join(tmp_dir, "frames")
        saved_count = await yolo_video_utils.extract_detection_frames(room_id, video_path, output_dir)
        logger.info(f"YOLO extracted {saved_count} frames for job {room_id}")

        if os.path.exists(output_dir):
            for filename in os.listdir(output_dir):
                if filename.endswith(".jpg"):
                    file_path = os.path.join(output_dir, filename)
                    with open(file_path, "rb") as f:
                        content = f.read()
                    frame_object_name = f"yolo_frames/{room_id}/{job_id}{filename}"
                    minio_client.upload_bytes(content, frame_object_name, content_type="image/jpeg")

    except Exception as e:
        logger.error(f"Error in YOLO background task: {e}")
    finally:
        shutil.rmtree(tmp_dir)

@router.post("/analyze")
async def analyze_video(
    background: BackgroundTasks,
    room_id: str,
    file: UploadFile = File(...),
):
    """
    Upload video for YOLO analysis. Extracts frames with detections.
    """

    if file.content_type not in ["video/mp4", "video/mov", "video/quicktime"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only video/mp4 or video/mov accepted."
        )

    try:
        job_id = str(uuid.uuid4())
        object_name = f"uploads/{room_id}/{job_id}.mp4"
        file_content = await file.read()
        minio_client.upload_bytes(file_content, object_name, content_type=file.content_type)

        background.add_task(
            process_yolo_video,
            room_id,
            job_id,
            file_content,
        )

        return {"jobId": job_id, "status": "processing_started"}
    except Exception as e:
        logger.error(f"Error starting YOLO job: {e}")
        raise HTTPException(status_code=500, detail=str(e))
