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

    async def analyze_video_background(self, job_id: str, file_content: bytes, room_id: str, object_name: str, current_time: datetime):
        queue = get_job_queue(room_id)
        print("detect items from AI hit start")
        try:
            # Read video from MinIO
            image_bytes = file_content
            image_b64 = base64.b64encode(image_bytes).decode()
            prompt = (
                "Analyze the attached images and extract the item that can be inspected "
                "before giving the property on rent. "
                "Try to extract only single item."
                "For each item, provide a structured list with: "
                "item name, description of item.\n\n"
                # f"{exclude_text}"
            )

            message = HumanMessage(
                content=[
                    {"type": "text", "text": prompt},
                     {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"},
                ]
            )
            chunk = await self.structured_llm.ainvoke([message])
            print("chunk: ", chunk.model_dump_json())
            print("relapsed_time:",(datetime.now()- current_time).total_seconds() * 1000)
            await queue.put(chunk.model_dump_json())
            asyncio.create_task(self._save_chunk(job_id, chunk, file_content,object_name, room_id))

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

    async def _save_chunk(self, job_id, chunk, file_content, object_name, room_id):
        await inspections_collection().insert_one({
            "job_id": job_id,
            "room_id": room_id,
            "video_path": object_name,
            "issues": [issue.model_dump() for issue in chunk.issues] if chunk.issues else [],
            "created_at": datetime.utcnow()
        })

        if not chunk.issues:
            return

        final_items = []
        frame_object_name = f"frames/{object_name}"

        # Upload to MinIO
        image_url = minio_client.upload_bytes(
            file_content,
            frame_object_name,
            content_type="image/png"
        )

        for i in chunk.issues:
            final_items.append({
                "room_id": room_id,
                "name": i.item,
                "description": i.description,
                "image": image_url,
                "image_path": frame_object_name,
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            })
        if final_items:
            await items_collection().insert_many(final_items)

    async def compare_item_condition(self, item_id: str, inspection_id: str, property_id: str, image_bytes: bytes):
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
        image_value = item.get("image")

        if image_value:
            if image_value.startswith("data:image"):
                # Already base64
                prev_b64 = image_value.split(",", 1)[1]

            else:
                # Treat as URL — fetch and convert to base64
                try:
                    import aiohttp
                    import base64

                    async with aiohttp.ClientSession() as session:
                        async with session.get(image_value) as resp:
                            if resp.status == 200:
                                img_bytes = await resp.read()
                                prev_b64 = base64.b64encode(img_bytes).decode()
                            else:
                                print("Failed to fetch previous image, status:", resp.status)

                except Exception as e:
                    print("Error fetching previous image:", e)
                    prev_b64 = None

        print("image_url_previous:",item.get("image"))

        frame_object_name = f"frames/{inspection_id}/{item_id}/{item_name}.png"

        # --------------------------------------
        # 3. ENCODE CURRENT IMAGE
        # --------------------------------------
        curr_b64 = base64.b64encode(image_bytes).decode()
        image_url = minio_client.upload_bytes(
            image_bytes,
            frame_object_name,
            content_type="image/png"
        )


        # --------------------------------------
        # 4. BUILD GEMINI PROMPT & CONTENT
        # --------------------------------------
        if prev_b64:
            prompt = (
                f"Compare the previous image and the current image of item: {item_name}. "
                f"The first image is the previous state, the second image is the current state. "
                f"Describe any changes in condition, damage, or anomalies."
                f"If the image is of different item, return 'different_item'"
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

        try:
            result: ItemComparisonResult = await asyncio.to_thread(
                self.item_comparison_llm.invoke, [msg]
            )
            print("compare result: ", result.model_dump_json())
            ai_data = result.dict()

            # Add change_status based on condition_change
            ai_data["condition_change"] = "changed" if ai_data["condition_status"] == "major_change" or ai_data["condition_status"] == "moderate_change" or ai_data["condition_status"] == "different_item" else "same"

        except Exception as e:
            print("AI Error:", e)
            ai_data = {
                "changes_detected": ["AI failure"],
                "condition_change": "same",  # fallback int
                "severity": "medium",
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
            "current_image_url": image_url,
            "inspection_id": inspection_id,
            "property_id": property_id,
            **ai_data,
            "created_at": datetime.utcnow()
        }

        res = await item_comparisons_collection().insert_one(doc)
        doc["_id"] = str(res.inserted_id)

        return doc


    async def get_comparisons(self, item_id: str = None, inspection_id: str = None):#, property_id: str = None):
        """
        List all stored comparisons based on room_id or property_id.
        """
        filter_query = {}
        
        if item_id:
            filter_query["item_id"] = item_id
        if inspection_id:
            filter_query["inspection_id"] = inspection_id

        cursor = item_comparisons_collection().find(filter_query).sort("created_at", -1)
        results = await cursor.to_list(length=100)
        
        # Convert ObjectId to string
        for res in results:
            res["_id"] = str(res["_id"])
            
        return results

    async def get_items(self, room_id: str = None, limit: int = 5):
        """
        Get previous items for a room: only name and description.
        """
        filter_query = {"room_id": room_id}
        cursor = items_collection().find(filter_query, {"_id": 0, "name": 1, "description": 1}) \
                                .sort("created_at", -1).limit(limit)
        results = await cursor.to_list(length=limit)
        return results

    async def get_unique_inspection_ids(self, property_id: str = None):
        """
        List all unique inspection_id values, optionally filtered by property_id.
        """
        filter_query = {}
        if property_id:
            filter_query["property_id"] = property_id

        # Use MongoDB's distinct to get unique inspection_id values
        unique_ids = await item_comparisons_collection().distinct("inspection_id", filter_query)

        return unique_ids
        
inspection_service = InspectionService()

