from typing import Any, Dict, List, Optional
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import logging

logger = logging.getLogger(__name__)

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def connect_to_mongo(
    mongo_uri: str,
    database: str = "boilerplate"
) -> AsyncIOMotorDatabase:
    """
    Connect to MongoDB.
    
    Args:
        mongo_uri: MongoDB connection URI
        database: Database name
    
    Returns:
        Motor database instance
    """
    global _client, _db
    try:
        _client = AsyncIOMotorClient(mongo_uri)
        _db = _client[database]
        logger.info(f"Connected to MongoDB: {mongo_uri} (database: {database})")
        return _db
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise


async def close_mongo_connection() -> None:
    """
    Close MongoDB connection.
    """
    global _client
    if _client:
        _client.close()
        logger.info("MongoDB connection closed")


def get_database() -> AsyncIOMotorDatabase:
    """
    Get the MongoDB database instance.
    
    Returns:
        Motor database instance
    
    Raises:
        RuntimeError: If not connected to MongoDB
    """
    if _db is None:
        raise RuntimeError("Not connected to MongoDB. Call connect_to_mongo first.")
    return _db


def is_connected() -> bool:
    """Check if MongoDB is connected."""
    return _client is not None