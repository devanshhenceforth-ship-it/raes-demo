import asyncio
import httpx
import os

BASE_URL = "http://localhost:8000/api"

async def verify():
    async with httpx.AsyncClient() as client:
        # 1. Create a dummy room
        property_id = "test_prop_delete_verify"
        room_data = {
            "property_id": property_id,
            "name": "Delete Verify Room",
            "type": "Test",
            "floor": 1,
            "size_sqft": 100.0
        }
        print("Creating room...")
        resp = await client.post(f"{BASE_URL}/inventory/properties/{property_id}/rooms", json=room_data)
        if resp.status_code != 200:
            print(f"Failed to create room: {resp.text}")
            return
        room = resp.json()
        room_id = room["_id"]
        print(f"Room created: {room_id}")

        # 2. Create a dummy item with image
        print("Creating item...")
        # Create a dummy image file
        files = {'file': ('test.jpg', b'fake image content', 'image/jpeg')}
        resp = await client.post(f"{BASE_URL}/inventory/rooms/{room_id}/items", files=files)
        if resp.status_code != 200:
            print(f"Failed to create item: {resp.text}")
            return
        item = resp.json()
        item_id = item["_id"]
        print(f"Item created: {item_id}")
        print(f"Item image: {item.get('image')}")

        # 3. Verify item exists
        print("Verifying item exists...")
        resp = await client.get(f"{BASE_URL}/inventory/items/{item_id}")
        if resp.status_code != 200:
            print(f"Failed to get item: {resp.text}")
            return
        print("Item found.")

        # 4. Delete item
        print("Deleting item...")
        resp = await client.delete(f"{BASE_URL}/inventory/items/{item_id}")
        if resp.status_code != 204:
            print(f"Failed to delete item: {resp.status_code} {resp.text}")
            return
        print("Item deleted (204).")

        # 5. Verify item is gone
        print("Verifying item is gone...")
        resp = await client.get(f"{BASE_URL}/inventory/items/{item_id}")
        if resp.status_code == 404:
            print("Success: Item not found (404).")
        else:
            print(f"Failure: Item still exists or other error: {resp.status_code}")

if __name__ == "__main__":
    asyncio.run(verify())
