# app/routers/clients.py
from fastapi import APIRouter, Body, HTTPException, status
from typing import List
from bson import ObjectId

from ..db.collections import clients_collection
from ..models.client import Client, Property, ResponseClient



from ..core.config import settings

router = APIRouter(prefix="/clients", tags=["clients"])

def _doc_to_client(doc: dict) -> dict:
    """Convert Mongo doc to API-friendly dict (stringify _id)."""
    if not doc:
        return doc
    doc = doc.copy()
    doc["_id"] = str(doc["_id"])
    return doc

@router.post("/", response_description="Add new client", response_model=ResponseClient, status_code=status.HTTP_201_CREATED)
async def create_client(client: Client = Body(...)):
    client_dict = client.model_dump(by_alias=True, exclude={"_id"})
    col = clients_collection()
    result = await col.insert_one(client_dict)
    created = await col.find_one({"_id": result.inserted_id})
    if created is None:
        raise HTTPException(status_code=500, detail="Failed to create client")
    return _doc_to_client(created)

@router.get("/", response_description="List all clients",response_model=List[ResponseClient])
async def list_clients(limit: int = settings.MAX_CLIENT_FETCH_LIMIT):
    col = clients_collection()
    docs = await col.find().to_list(length=limit)
    return [_doc_to_client(d) for d in docs]

@router.get("/{id}", response_description="Get a single client")  # response_model=Client)
async def show_client(id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    col = clients_collection()
    doc = await col.find_one({"_id": oid})

    if not doc:
        raise HTTPException(status_code=404, detail=f"Client {id} not found")

    # -----------------------------
    # NEW: items_count INSIDE EACH PROPERTY
    # -----------------------------
    from ..db.collections import rooms_collection, items_collection

    updated_properties = []

    for prop in doc.get("properties", []):
        property_id = prop.get("id")

        # 1) Fetch rooms for that property
        rooms = await rooms_collection().find({"property_id": property_id}).to_list(None)
        room_ids = [str(r["_id"]) for r in rooms]

        # 2) Count items across rooms
        if room_ids:
            total_items = await items_collection().count_documents(
                {"room_id": {"$in": room_ids}}
            )
        else:
            total_items = 0

        # 3) Inject items_count into property object
        prop["no_of_entities"] = total_items
        prop["no_of_rooms"] = len(room_ids)

        updated_properties.append(prop)

    doc["properties"] = updated_properties
    # -----------------------------

    return _doc_to_client(doc)


@router.post("/{id}/properties/", response_description="Add property to client", response_model=Client)
async def add_property_to_client(id: str, property: Property = Body(...)):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")

    prop_dict = property.model_dump()
    col = clients_collection()
    update_result = await col.update_one({"_id": oid}, {"$push": {"properties": prop_dict}})
    if update_result.modified_count == 1:
        updated = await col.find_one({"_id": oid})
        return _doc_to_client(updated)
    # if nothing modified, check if client exists (maybe properties didn't change)
    if (existing := await col.find_one({"_id": oid})) is not None:
        return _doc_to_client(existing)
    raise HTTPException(status_code=404, detail=f"Client {id} not found")

@router.delete("/{id}", response_description="Delete a client")
async def delete_client(id: str):
    try:
        oid = ObjectId(id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    col = clients_collection()
    delete_result = await col.delete_one({"_id": oid})
    if delete_result.deleted_count == 1:
        return {"message": "Client deleted successfully"}
    raise HTTPException(status_code=404, detail=f"Client {id} not found")


