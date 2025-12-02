from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from bson import ObjectId

from ..db.collections import rooms_collection, items_collection
from ..models.inventory import Room, Item
from ..services.inspection_service import inspection_service

router = APIRouter(prefix="/inventory", tags=["inventory"])

def _doc_to_model(doc: dict) -> dict:
    if not doc:
        return doc
    doc = doc.copy()
    doc["_id"] = str(doc["_id"])
    return doc

# ---------- ROOMS ---------- #

@router.post("/properties/{property_id}/rooms", response_description="Add new room", response_model=Room)
async def create_room(property_id: str, room: Room = Body(...)):
    room.property_id = property_id
    room_dict = room.model_dump(by_alias=True, exclude={"id"})
    
    col = rooms_collection()
    result = await col.insert_one(room_dict)
    created = await col.find_one({"_id": result.inserted_id})
    return _doc_to_model(created)

@router.get("/properties/{property_id}/rooms", response_description="List rooms for property")
async def list_rooms(property_id: str):
    col = rooms_collection()
    items_col = items_collection()

    docs = await col.find({"property_id": property_id}).to_list(length=100)

    result = []
    for d in docs:
        room = _doc_to_model(d)

        # minimal addition → count items
        count = await items_col.count_documents({"room_id": room["_id"]})
        room["no_of_entities"] = count

        result.append(room)

    return result

@router.get("/rooms/{room_id}", response_description="Get a single room", response_model=Room)
async def get_room(room_id: str):
    try:
        oid = ObjectId(room_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Room ID")
        
    col = rooms_collection()
    if (doc := await col.find_one({"_id": oid})) is not None:
        return _doc_to_model(doc)
    raise HTTPException(status_code=404, detail=f"Room {room_id} not found")

# ---------- ITEMS ---------- #

@router.post("/rooms/{room_id}/items", response_description="Add new item", response_model=Item)
async def create_item(room_id: str, item: Item = Body(...)):
    item.room_id = room_id
    item_dict = item.model_dump(by_alias=True, exclude={"id"})
    
    col = items_collection()
    result = await col.insert_one(item_dict)
    created = await col.find_one({"_id": result.inserted_id})
    return _doc_to_model(created)

@router.get("/rooms/{room_id}/items", response_description="List items for room", response_model=List[Item])
async def list_items(room_id: str):
    col = items_collection()
    docs = await col.find({"room_id": room_id}).to_list(length=100)
    return [_doc_to_model(d) for d in docs]

@router.get("/items/{item_id}", response_description="Get a single item", response_model=Item)
async def get_item(item_id: str):
    try:
        oid = ObjectId(item_id)
    except:
        raise HTTPException(status_code=400, detail="Invalid Item ID")
        
    col = items_collection()
    if (doc := await col.find_one({"_id": oid})) is not None:
        return _doc_to_model(doc)
    raise HTTPException(status_code=404, detail=f"Item {item_id} not found")

@router.get("/properties/{property_id}/inspection-tasks", response_description="Get inspection tasks for all items in property")
async def get_property_inspection_tasks(property_id: str):
    """
    GET: Generate inspection tasks for all items in a property.
    Returns a summary with tasks organized by room.
    """
    from ..models.tasks import InspectionTask, PropertyInspectionSummary
    from ..db.collections import clients_collection
    from bson import ObjectId
    
    # Get property details from client
    clients_col = clients_collection()
    client = await clients_col.find_one({"properties.id": property_id})
    
    if not client:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    
    # Find the specific property
    property_data = None
    for prop in client.get("properties", []):
        if prop.get("id") == property_id:
            property_data = prop
            break
    
    if not property_data:
        raise HTTPException(status_code=404, detail=f"Property {property_id} not found")
    
    # Get all rooms for this property
    rooms_col = rooms_collection()
    rooms = await rooms_col.find({"property_id": property_id}).to_list(length=100)
    
    # Get all items for each room and generate tasks
    items_col = items_collection()
    
    all_tasks = []
    rooms_summary = []
    total_items = 0
    
    for room in rooms:
        room_id = str(room["_id"])
        items = await items_col.find({"room_id": room_id}).to_list(length=100)
        total_items += len(items)
        
        room_tasks = []
        for item in items:
            item_id = str(item["_id"])
            comparisons = await inspection_service.get_comparisons(item_id=item_id)
            number_of_inspections = len(comparisons)
            status = "inspected" if number_of_inspections > 0 else "pending"
            
            # Generate task based on item condition
            task_type = "Inspect"
            priority = "Medium"
            description = f"Routine inspection of {item['name']}"
            
            task = {
                "item_id": item_id,
                "item_name": item["name"],
                "room_id": room_id,
                "room_name": room["name"],
                "task_type": task_type,
                "priority": priority,
                "description": description,
                "number_of_inspections": number_of_inspections,
                "status": status,
                "category": item.get("category", "Unknown"),
                "condition": item.get("condition", "Unknown")
            }
            
            room_tasks.append(task)
            all_tasks.append(task)
        
        rooms_summary.append({
            "room_id": room_id,
            "room_name": room["name"],
            "room_type": room.get("type", "Unknown"),
            "item_count": len(items),
            "tasks": room_tasks
        })
    
    # Calculate task statistics
    tasks_by_priority = {"Low": 0, "Medium": 0, "High": 0, "Urgent": 0}
    for task in all_tasks:
        priority = task.get("priority", "Medium")
        tasks_by_priority[priority] = tasks_by_priority.get(priority, 0) + 1
    
    summary = {
        "property_id": property_id,
        "property_name": property_data.get("name", "Unknown"),
        "property_address": property_data.get("address", ""),
        "total_rooms": len(rooms),
        "total_items": total_items,
        "total_tasks": len(all_tasks),
        "tasks_by_priority": tasks_by_priority,
        "rooms": rooms_summary
    }
    
    return summary

