from .base import BaseCache
from typing import Union
from datetime import datetime, UTC, timedelta

from battlenet_client.utils import slugify
import redis


class RedisCache(BaseCache):
    connector = None

    def check(self, catagory_tag: str, *args, **kwargs) -> bool:
        hashed_value = self.check(catagory_tag, *args, **kwargs)
        return False

    def select(self, catagory_tag: str, *args, **kwargs) -> Union[None, bytes]:
        return None

    def insert(self, catagory_tag: str, data: bytes, *args, **kwargs) -> bool:
        return False

    def update(self, catagory_tag: str, data: bytes, *args, **kwargs) -> bool:
        return False

    def delete(self, catagory_tag: str, *args, **kwargs) -> bool:
        return False
