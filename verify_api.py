import asyncio
from src.db.collections import item_comparisons_collection, rooms_collection
from src.db.connection import db, connect
import httpx

async def verify():
    await connect()
    # 1. Create dummy data
    room_id = "test_room_123"
    property_id = "test_prop_456"
    
    # Insert room
    await rooms_collection().update_one(
        {"_id": room_id}, # Assuming _id can be string for test, or we let mongo generate it
        {"$set": {"property_id": property_id}},
        upsert=True
    )
    
    # Insert comparison
    await item_comparisons_collection().insert_one({
        "room_id": room_id,
        "item_name": "Test Item",
        "condition_change": "None",
        "created_at": "2023-01-01"
    })
    
    print(f"Created test data: room_id={room_id}, property_id={property_id}")
    
    # 2. Test API
    async with httpx.AsyncClient() as client:
        # Test by room_id
        response = await client.get(f"http://localhost:8002/api/inspection/comparisons?room_id={room_id}")
        print(f"By Room ID: {response.status_code}")
        print(response.json())
        
        # Test by property_id
        response = await client.get(f"http://localhost:8002/api/inspection/comparisons?property_id={property_id}")
        print(f"By Property ID: {response.status_code}")
        print(response.json())

if __name__ == "__main__":
    asyncio.run(verify())
