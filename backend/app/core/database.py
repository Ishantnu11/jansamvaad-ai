import motor.motor_asyncio
import certifi
from app.core.config import settings

client: motor.motor_asyncio.AsyncIOMotorClient = None
db: motor.motor_asyncio.AsyncIOMotorDatabase = None


async def connect_db():
    global client, db
    try:
        test_client = motor.motor_asyncio.AsyncIOMotorClient(
            settings.MONGODB_URL,
            tlsCAFile=certifi.where(),
            serverSelectionTimeoutMS=4000
        )
        test_db = test_client[settings.MONGODB_DB_NAME]
        await test_db.command("ping")
        client = test_client
        db = test_db
        await db["calls"].create_index("call_id", unique=True)
        await db["calls"].create_index("created_at")
        await db["calls"].create_index("status")
        print(f"[OK] Connected to MongoDB: {settings.MONGODB_DB_NAME}")
    except Exception as e:
        client = None
        db = None
        print(f"[WARNING] MongoDB Atlas unreachable ({e}). Operating in in-memory mode.")


async def disconnect_db():
    global client
    if client:
        client.close()
        print("[INFO] Disconnected from MongoDB")


def get_db() -> motor.motor_asyncio.AsyncIOMotorDatabase:
    return db
