
from .base import BaseCache
from typing import Union
from datetime import datetime, UTC, timedelta

from battlenet_base.utils.utils import slugify
import pymongo

class MongoCache(BaseCache):

    def __init__(self, connector: pymongo.MongoClient, database_name: str, region: str, chunk_size:int=16*1024**2) -> None:
        super().__init__(region, chunk_size)
        self.database = connector[database_name]
        self.cache = self.database["cache"]
        self.categories = self.database["categories"]
        self.chunks = self.database["chunks"]

    def __del__(self) -> None:
        self.database.close()


    def check(self, category_tag: str, *args, **kwargs) -> bool:
        hashed_value = self.compute_hash(category_tag, *args, **kwargs)
        try:
            category = self.categories.find_one({"name": slugify(category_tag)})
        except TypeError:
            return False
        else:
            if category["duration"] == 0:
                return False

        try:
            result = self.cache.find_one(
                {"_id": hashed_value,
                 "categoryId": category["_id"],
                 "last_updated": {"$gt": datetime.now(UTC) - timedelta(seconds=category["duration"])}})
        except TypeError:
            return False
        else:
            return result is not None

    def select(self, catagory_tag: str, *args, **kwargs) -> Union[None, bytes]:
        hashed_value = self.compute_hash(catagory_tag, *args, **kwargs)
        category = self.categories.find_one({"name": slugify(catagory_tag)})
        parent = self.cache.find_one(
            {"hash": hashed_value,
             "category": category["_id"],
             "last_updated": {"$gt": datetime.now(UTC) - timedelta(seconds=category["duration"])}}
        )

        if parent:
            res = self.chunks.find({"cacheId": hashed_value}, sort=[("sequence", pymongo.ASCENDING)])
            return b''.join([chunk["data"] for chunk in res]) if res is not None else None
        else:
            return None

    def upsert(self, catagory_tag: str, chunk_size: int, data: bytes, *args, **kwargs) -> bool:
        hashed_value = self.check(catagory_tag, *args, **kwargs)
        try:
            category = self.categories.find_one({"name": slugify(catagory_tag)})
        except TypeError:
            return False

        parent = self.cache.find_one(
            { "hash": hashed_value, "last_updated": {"$gt": datetime.now(UTC) - timedelta(seconds=category["duration"])}},
            projection={"_id": False, "hash": True, "last_updated": False})

        chunks = self.chunk_data(data)

        res = self.chunks.update_many(
                {"cacheId": hashed_value},
                [{
                    "$set": {
                        "cacheId": parent["_id"],
                        "data": chunk,
                        "sequence": counter,
                        "last_updated": datetime.now(UTC)
                    }
                } for counter, chunk in enumerate(chunks)],
                upsert=True, return_document=pymongo.ReturnDocument.AFTER)

        return (len(res) == len(chunks)) and parent

    def delete(self, catagory_tag: str, *args, **kwargs) -> bool:
        hashed_value = self.check(catagory_tag, *args, **kwargs)
        chunk_counter = len(self.chunks.find({"cacheId": hashed_value}))
        deleted_chunks = self.chunks.delete({"cacheId": hashed_value})
        deleted_parent = self.cache.delete({"_id": hashed_value})
        return deleted_parent and chunk_counter == len(deleted_chunks)
