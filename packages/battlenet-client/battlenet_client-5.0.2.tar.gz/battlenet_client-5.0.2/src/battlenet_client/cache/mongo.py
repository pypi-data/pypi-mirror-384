import pymongo
from typing import Union
from datetime import datetime, UTC, timedelta

from ..utils.utils import slugify
from .base import BaseCache

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
        """ Checks if the cache is avaiable for the given arguments

        Args:
            category_tag (str): the category tag
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the cache is available and valid for the given arguments else False
        """
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
                 "next_update": {"$gt": datetime.now(UTC)}})
        except TypeError:
            return False
        else:
            return result is not None

    def select(self, category_tag: str, *args, **kwargs) -> Union[None, bytes]:
        """ Retrieves the data from the cache

        Args:
            category_tag (str): category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bytes: the data from the cache if available and valid
            None: upon failure or no valid data
        """
        hashed_value = self.compute_hash(category_tag, *args, **kwargs)
        category = self.categories.find_one({"name": slugify(category_tag)})
        parent = self.cache.find_one(
            {"hash": hashed_value,
             "category": category["_id"],
             "next_update": {"$gt": datetime.now(UTC)}}
        )

        if parent:
            res = self.chunks.find({"cacheId": parent["_id"]}, sort=[("sequence", pymongo.ASCENDING)])
            return b''.join([chunk["data"] for chunk in res]) if res is not None else None
        else:
            return None

    def upsert(self, category_tag: str, data: bytes, *args, **kwargs) -> bool:
        """ Insert or update the data in the cache

        Args:
            category_tag (str): category name
            data (bytes): data to insert
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the data was inserted or not, False otherwise
        """
        hashed_value = self.check(category_tag, *args, **kwargs)
        try:
            category = self.categories.find_one({"name": slugify(category_tag)})
        except TypeError:
            return False

        parent = self.cache.find_one_and_update(
            { "hash": hashed_value, "last_updated": {"$gt": datetime.now(UTC) - timedelta(seconds=category["duration"])}},
            {"$setOnInsert": {"hash": hashed_value, "last_updated": datetime.now(UTC)}},
            projection={"_id": False, "hash": True, "last_updated": False}, upsert=True,
            return_document=pymongo.ReturnDocument.AFTER)

        chunks = self.chunk_data(data)

        res = [self.chunks.find_one_and_update(
            {"cacheId": hashed_value, "sequence": counter},
                {
                    "$set": {
                        "data": chunk,
                        "sequence": counter,
                        "last_updated": datetime.now(UTC)
                    }
                }, upsert=True, return_document=pymongo.ReturnDocument.AFTER)
            for counter, chunk in enumerate(chunks)]


        return (len(res) == len(chunks)) and parent

    def delete(self, category_tag: str, *args, **kwargs) -> bool:
        """ Deletes the data from the cache

        Args:
            category_tag: category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the cache is deleted or false if it was not deleted or deleted completely
        """
        hashed_value = self.check(category_tag, *args, **kwargs)
        chunk_counter = self.chunks.count_documents({"cacheId": hashed_value})
        deleted_chunks = self.chunks.delete_many({"cacheId": hashed_value})
        deleted_parent = self.cache.delete_one({"_id": hashed_value})
        return deleted_parent.deleted_count and chunk_counter == deleted_chunks.deleted_count
