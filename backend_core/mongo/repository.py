from typing import Any, Dict, List, Optional, Type, TypeVar
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorCollection

from .connection import get_database

T = TypeVar("T", bound=BaseModel)


class BaseRepository:
    """
    Base repository with CRUD operations.
    """
    
    def __init__(self, collection_name: str, schema_class: Optional[Type[T]] = None):
        self.collection_name = collection_name
        self.schema_class = schema_class
        self._collection: Optional[AsyncIOMotorCollection] = None
    
    @property
    def collection(self) -> AsyncIOMotorCollection:
        if self._collection is None:
            db = get_database()
            self._collection = db[self.collection_name]
        return self._collection
    
    async def find_one(
        self,
        filter_dict: Dict[str, Any],
        sort: Optional[List[tuple]] = None
    ) -> Optional[Dict[str, Any]]:
        """Find a single document."""
        if sort:
            return await self.collection.find_one(filter_dict, sort=sort)
        return await self.collection.find_one(filter_dict)
    
    async def find_many(
        self,
        filter_dict: Dict[str, Any] = {},
        skip: int = 0,
        limit: int = 100,
        sort: Optional[List[tuple]] = None
    ) -> List[Dict[str, Any]]:
        """Find multiple documents."""
        cursor = self.collection.find(filter_dict).skip(skip).limit(limit)
        if sort:
            cursor = cursor.sort(sort)
        return await cursor.to_list(length=None)
    
    async def insert_one(self, document: Dict[str, Any]) -> str:
        """Insert a single document."""
        result = await self.collection.insert_one(document)
        return str(result.inserted_id)
    
    async def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Insert multiple documents."""
        result = await self.collection.insert_many(documents)
        return [str(id) for id in result.inserted_ids]
    
    async def update_one(
        self,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """Update a single document."""
        result = await self.collection.update_one(filter_dict, update_dict, upsert=upsert)
        return result.modified_count > 0 or result.upserted_id is not None
    
    async def update_many(
        self,
        filter_dict: Dict[str, Any],
        update_dict: Dict[str, Any]
    ) -> int:
        """Update multiple documents."""
        result = await self.collection.update_many(filter_dict, update_dict)
        return result.modified_count
    
    async def delete_one(self, filter_dict: Dict[str, Any]) -> bool:
        """Delete a single document."""
        result = await self.collection.delete_one(filter_dict)
        return result.deleted_count > 0
    
    async def delete_many(self, filter_dict: Dict[str, Any]) -> int:
        """Delete multiple documents."""
        result = await self.collection.delete_many(filter_dict)
        return result.deleted_count
    
    async def count(self, filter_dict: Dict[str, Any] = {}) -> int:
        """Count documents."""
        return await self.collection.count_documents(filter_dict)
    
    async def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline."""
        cursor = self.collection.aggregate(pipeline)
        return await cursor.to_list(length=None)