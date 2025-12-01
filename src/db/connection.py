
from motor.motor_asyncio import AsyncIOMotorClient
from ..core.config import settings

MONGO_URI = settings.MONGO_URI
DB_NAME = settings.MONGO_DB_NAME

client: AsyncIOMotorClient | None = None    
db = None

async def connect():
    global client, db
    if client is None:
        client = AsyncIOMotorClient(MONGO_URI)
        db = client[DB_NAME]
        # Optionally test connection
        # await client.admin.command("ping")

async def close():
    global client
    if client:
        client.close()
        client = None
