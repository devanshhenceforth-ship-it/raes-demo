from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, Form
from ..services.inspection_service import inspection_service
from ..services.detector import detect_items_from_bytes
from ..utils.minio_client import minio_client
import uuid
import asyncio
router = APIRouter(
    prefix="/inspection",
    tags=["Inspection"],
)


@router.post("/analyze-video")
async def analyze_video(
    background: BackgroundTasks,
    file: UploadFile = File(...),
    room_id: str = Form(...)
):
    """
    POST: Start video analysis job
    Returns: jobId (use with SSE endpoint)
    """
    try:
        if file.content_type not in ["video/mp4", "video/mov", "video/quicktime"]:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only video/mp4 or video/mov accepted."
            )

        job_id = str(uuid.uuid4())
        object_name = f"uploads/{job_id}.mp4"
        
        # Upload to MinIO
        file_content = await file.read()
        minio_client.upload_bytes(file_content, object_name, content_type=file.content_type)

        # Start background task
        background.add_task(
            inspection_service.analyze_video_background,
            job_id,
            object_name, 
            room_id
        )

        background.add_task(
            detect_items_from_bytes,
            file_content,
            room_id
        )

        return {"jobId": job_id, "status": "started","detected_items": {"items": []}}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/best-images/{room_id}")
async def get_best_images(room_id: str):
    """
    GET: Extract and return best images for detected items in the latest job for a room.
    """
    try:
        results = await inspection_service.extract_best_images(room_id)
        if results is None:
            raise HTTPException(status_code=404, detail="Room inspection not found or video missing")
        return {"images": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare-item/{item_id}")
async def compare_item_condition(item_id: str, inspection_id:str,property_id:str, file: UploadFile = File(...)):
    """
    POST: Compare item condition by analyzing video chunk against stored image.
    Accepts: video chunk of the item
    Returns: AI-powered comparison results with detected changes
    """
    try:
        # if file.content_type not in ["video/mp4", "video/mov", "video/quicktime"]:
        #     raise HTTPException(
        #         status_code=400,
        #         detail="Invalid file type. Only video/mp4 or video/mov accepted."
        #     )
        
        image_bytes = await file.read()
        
        result = await inspection_service.compare_item_condition(item_id,inspection_id,property_id, image_bytes)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/comparisons")
async def list_comparisons(item_id: str = None, inspection_id: str = None):
    """
    GET: List all stored comparisons based on item_id.
    """
    try:
        # if not item_id:
        #      raise HTTPException(status_code=400, detail="item_id must be provided")
             
        results = await inspection_service.get_comparisons(item_id,inspection_id)
        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unique-inspections")
async def get_unique_inspection_ids(property_id: str = None):
    """
    List all unique inspection_id values, optionally filtered by property_id.
    """
    filter_query = {}
    if property_id:
        filter_query["property_id"] = property_id

    # Use MongoDB's distinct to get unique inspection_id values
    unique_ids = await inspection_service.get_unique_inspection_ids(property_id)

    return unique_ids