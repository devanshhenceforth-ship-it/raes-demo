import base64
import asyncio
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from ..core.config import settings
from ..models.inspection import AllAnalyzerResponse, ItemComparisonResult
from ..routers.queue import get_job_queue
from bson import ObjectId
from datetime import datetime
from ..db.collections import inspections_collection, items_collection,item_comparisons_collection, rooms_collection

import cv2, os
import numpy as np
import tempfile
from ..utils.minio_client import minio_client  



class InspectionService:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_MODEL, api_key=settings.GOOGLE_API_KEY
        )
        self.gemini = ChatGoogleGenerativeAI(
            model=settings.GOOGLE_MODEL,
            api_key=settings.GOOGLE_API_KEY
        )
        self.item_comparison_llm = self.llm.with_structured_output(ItemComparisonResult, method="json_schema")
        self.structured_llm = self.llm.with_structured_output(AllAnalyzerResponse)

    async def analyze_video_background(self, job_id: str, object_name: str, room_id: str):
        queue = get_job_queue(room_id)
        try:
            # Read video from MinIO
            video_bytes = minio_client.get_file_content(object_name)
            video_b64 = base64.b64encode(video_bytes).decode()

            # Get previously detected items for this job
            prev_items = await self.get_items(room_id)  # <-- await here!
            exclude_text = ""
            if prev_items:
                exclude_text = (
                    "Do NOT include the following items, they were already detected:\n"
                    + "\n".join(f"- {item['name']} with description: {item['description']}" for item in prev_items)
                )

            prompt = (
                "Analyze the attached video and extract the items that can be inspected "
                "before giving the property on rent. "
                "For each item, provide a structured list with: timestamp (ms), "
                "item name, description.\n\n"
                f"{exclude_text}"
            )

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                    {"type": "media", "data": video_b64, "mime_type": "video/mp4"},
                ]
            )

            async for chunk in self.structured_llm.astream([message]):
                # Serialize for SSE queue
                await queue.put(chunk.model_dump_json())

                # Save chunk to DB
                asyncio.create_task(self._save_chunk(job_id, chunk, object_name, room_id))

                # Update previous items
                if chunk.issues:
                    self.prev_items.setdefault(job_id, set()).update(
                        i.item for i in chunk.issues if i.item
                    )

        except Exception as e:
            print("[VIDEO_ANALYSIS] Background Error:", e)


    async def extract_best_images(self, room_id: str):
        # Fetch all items for this room from the DB
        items_col = items_collection()
        cursor = items_col.find({"room_id": room_id})
        
        saved_items = []
        async for item in cursor:
            saved_items.append({
                "item_id": str(item["_id"]),
                "name": item.get("name"),
                "category": item.get("category"),
                "imagePath": item.get("imagePath",""),
                "image": item.get("image",""),
                "description": item.get("description", ""),
                "created_at": item.get("created_at"),
                "updated_at": item.get("updated_at")
            })
        
        return saved_items

    async def _save_chunk(self, job_id, chunk, object_name, room_id):
    # ---------------------------------------------
    # Save inspection entry
        # ---------------------------------------------
        await inspections_collection().insert_one({
            "job_id": job_id,
            "room_id": room_id,
            "video_path": object_name,
            "issues": [issue.model_dump() for issue in chunk.issues] if chunk.issues else [],
            "created_at": datetime.utcnow()
        })

        # If no issues → nothing more to do
        if not chunk.issues:
            return

        # ---------------------------------------------
        # Open video for frame extraction
        # ---------------------------------------------
        final_items = []

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_video:
            minio_client.download_file(object_name, tmp_video.name)
            cap = cv2.VideoCapture(tmp_video.name)

        # print("chunk_data:::", chunk)

        for idx, issue in enumerate(chunk.issues):
            # Safely access attributes from Pydantic object
            ts = issue.timestamp if issue.timestamp is not None else idx * 1000
            item_name = issue.item if issue.item else f"item_{idx}"
            description = issue.description if issue.description else ""

            # Set video position and read frame
            cap.set(cv2.CAP_PROP_POS_MSEC, ts)
            ok, frame = cap.read()
            if not ok:
                continue

            # Encode frame to JPEG
            success, buffer = cv2.imencode(".jpg", frame)
            if not success:
                continue

            frame_bytes = buffer.tobytes()
            filename = f"frame_{job_id}_{idx}_{ts}.jpg"
            frame_object_name = f"frames/{job_id}/{filename}"

            # Upload to MinIO
            image_url = minio_client.upload_bytes(
                frame_bytes,
                frame_object_name,
                content_type="image/jpeg"
            )

            final_items.append({
                "room_id": room_id,
                "name": item_name,
                "timestamp": ts,
                "description": description,
                "image": image_url,
                "image_path": frame_object_name,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })

        # Release resources
        cap.release()
        os.unlink(tmp_video.name)

        # ---------------------------------------------
        # Save items to DB
        # ---------------------------------------------
        if final_items:
            await items_collection().insert_many(final_items)

#     async def compare_item_condition(self, item_id: str, video_bytes: bytes):
#         """
#         Minimal production version using Gemini (image + video comparison).
#         No cv2. Fully compliant with LangChain Gemini input format.
#         """
#         # --------------------------------------
#         # 1. VALIDATE ITEM
#         # --------------------------------------
#         try:
#             oid = ObjectId(item_id)
#         except Exception as e:
#             return {"error": f"Invalid item ID: {e}"}

#         item = await items_collection().find_one({"_id": oid})
#         if not item:
#             return {"error": "Item not found"}

#         room_id = item.get("room_id")
#         item_name = item.get("name", "Unknown")

#         # --------------------------------------
#         # 2. FIND PREVIOUS IMAGE (if exists)
#         # --------------------------------------
#         previous_image_object = None
#         last = await inspections_collection().find_one(
#             {"room_id": room_id},
#             sort=[("created_at", -1)]
#         )

#         if last and "job_id" in last:
#             # We need to find the image for this item in the previous inspection
#             # This logic was relying on file naming convention in local dir
#             # Now we should query the items collection for the previous item image
#             # OR list objects in MinIO (less efficient)
            
#             # Better approach: Find the item in the items collection that matches this room and name
#             # But we already have 'item' which IS the item.
#             # Wait, the logic below tries to find the image from the LAST inspection.
#             # The 'item' document contains 'images' list. The last image in that list should be the latest.
            
#             if item.get("images"):
#                 # item['images'] contains URLs. We need to parse object name if we want to download it.
#                 # But wait, we need base64 for Gemini.
#                 # If the URL is from MinIO, we can extract object name.
#                 # Let's assume the URL structure we created: protocol://endpoint/bucket/object_name
                
#                 latest_image_url = item["images"][-1]
#                 # Extract object name from URL
#                 # Example: http://localhost:9000/raes-demo/frames/job_id/filename.jpg
#                 parts = latest_image_url.split(f"/{settings.MINIO_BUCKET_NAME}/")
#                 if len(parts) > 1:
#                     previous_image_object = parts[1]

#         # --------------------------------------
#         # 3. ENCODE PREVIOUS IMAGE (optional)
#         # --------------------------------------
#         prev_b64 = None
#         prev_b64 = None
#         if previous_image_object:
#             try:
#                 img_bytes = minio_client.get_file_content(previous_image_object)
#                 prev_b64 = base64.b64encode(img_bytes).decode()
#             except Exception as e:
#                 print(f"Error reading previous image from MinIO: {e}")

#         # --------------------------------------
#         # 4. ENCODE CURRENT VIDEO DIRECTLY
#         # --------------------------------------
#         curr_video_b64 = base64.b64encode(video_bytes).decode()

#         # --------------------------------------
#         # 5. BUILD GEMINI CONTENT
#         # --------------------------------------
#         if prev_b64:
#             prompt = f"Compare the previous image and the current video of item: {item_name}."
#             content = [
#                     {"type": "text", "text": prompt},
#                     {"type": "image_url", "image_url": f"data:image/jpeg;base64,{prev_b64}"},
#                     {
#                         "type": "media",
#                         "data": curr_video_b64,        # base64 string (no data:<mime>;prefix)
#                         "mime_type": "video/mp4",      # set actual mime
#                     },
#                 ]
#         else:
#             prompt = f"Analyze the current condition of item (video only): {item_name}."
#             content = [
#     {"type": "text", "text": prompt},
#     {
#         "type": "media",
#         "data": curr_video_b64,        # base64 string (no data:<mime>;prefix)
#         "mime_type": "video/mp4",      # set actual mime
#     },
# ]

#         msg = HumanMessage(content=content)

#         # --------------------------------------
#         # 6. CALL GEMINI (STRUCTURED OUTPUT)
#         # --------------------------------------
#         try:
#             result: ItemComparisonResult = await asyncio.to_thread(
#                 self.item_comparison_llm.invoke, [msg]
#             )
#             ai_data = result.dict()
#         except Exception as e:
#             print("AI Error:", e)
#             ai_data = {
#                 "changes_detected": ["AI failure"],
#                 "condition_change": "Unknown",
#                 "severity": "Medium",
#                 "recommendations": ["Manual inspection required"],
#                 "analysis": str(e),
#             }

#         # --------------------------------------
#         # 7. SAVE TO DB
#         # --------------------------------------
#         doc = {
#             "item_id": item_id,
#             "room_id": room_id,
#             "item_name": item_name,
#             "previous_image_url": item.get("images", [])[-1] if item.get("images") else None,
#             "current_video_b64": None,  # not stored for size reasons
#             **ai_data,
#             "created_at": datetime.utcnow()
#         }

#         res = await item_comparisons_collection().insert_one(doc)
#         doc["_id"] = str(res.inserted_id)

#         return doc

    async def compare_item_condition(self, item_id: str, image_bytes: bytes):
        """
        Compare current image with the previous image stored in the 'image' field of the item.
        Input is raw image bytes (JPEG/PNG).
        """
        # --------------------------------------
        # 1. VALIDATE ITEM
        # --------------------------------------
        try:
            oid = ObjectId(item_id)
        except Exception as e:
            return {"error": f"Invalid item ID: {e}"}

        item = await items_collection().find_one({"_id": oid})
        if not item:
            return {"error": "Item not found"}

        room_id = item.get("room_id")
        item_name = item.get("name", "Unknown")

        # --------------------------------------
        # 2. GET PREVIOUS IMAGE FROM ITEM
        # --------------------------------------
        prev_b64 = None
        if item.get("image"):
            if item["image"].startswith("data:image"):
                # Already base64 encoded
                prev_b64 = item["image"].split(",")[1]
            else:
                # If image is a URL, skip fetching
                prev_b64 = None

        # --------------------------------------
        # 3. ENCODE CURRENT IMAGE
        # --------------------------------------
        curr_b64 = base64.b64encode(image_bytes).decode()

        # --------------------------------------
        # 4. BUILD GEMINI PROMPT & CONTENT
        # --------------------------------------
        if prev_b64:
            prompt = (
                f"Compare the previous image and the current image of item: {item_name}. "
                f"The first image is the previous state, the second image is the current state. "
                f"Describe any changes in condition, damage, or anomalies."
            )
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{prev_b64}"},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{curr_b64}"},
            ]
        else:
            prompt = f"Analyze the current condition of item (image only): {item_name}."
            content = [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": f"data:image/jpeg;base64,{curr_b64}"},
            ]

        msg = HumanMessage(content=content)

        # --------------------------------------
        # 5. CALL GEMINI (STRUCTURED OUTPUT)
        # --------------------------------------
        try:
            result: ItemComparisonResult = await asyncio.to_thread(
                self.item_comparison_llm.invoke, [msg]
            )
            ai_data = result.dict()
        except Exception as e:
            print("AI Error:", e)
            ai_data = {
                "changes_detected": ["AI failure"],
                "condition_change": "Unknown",
                "severity": "Medium",
                "recommendations": ["Manual inspection required"],
                "analysis": str(e),
            }

        # --------------------------------------
        # 6. SAVE TO DB
        # --------------------------------------
        doc = {
            "item_id": item_id,
            "room_id": room_id,
            "item_name": item_name,
            "previous_image_url": item.get("image"),
            "current_image_b64": curr_b64,  # optional: store if you want
            **ai_data,
            "created_at": datetime.utcnow()
        }

        res = await item_comparisons_collection().insert_one(doc)
        doc["_id"] = str(res.inserted_id)

        return doc


    async def get_comparisons(self, item_id: str = None):#, property_id: str = None):
        """
        List all stored comparisons based on room_id or property_id.
        """
        filter_query = {}
        
        if item_id:
            filter_query["item_id"] = item_id
        else:
            return []

        cursor = item_comparisons_collection().find(filter_query).sort("created_at", -1)
        results = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for res in results:
            res["_id"] = str(res["_id"])
            
        return results

    async def get_items(self, room_id: str = None, limit: int = 50):
        """
        Get previous items for a room: only name and description.
        """
        filter_query = {"room_id": room_id}
        cursor = items_collection().find(filter_query, {"_id": 0, "name": 1, "description": 1}) \
                                .sort("created_at", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        return results
        
inspection_service = InspectionService()

