from abc import ABC, abstractmethod
from hashlib import sha1
from json import dumps


class BaseCache(ABC):

    def __init__(self, region: str, chunk_size=1024**3):
        self.region_tag = region.lower()
        self.chunk_size = chunk_size

    def compute_hash(self, catagory_tag: str, *args, **kwargs) -> str:

        if not isinstance(catagory_tag, str):
            raise TypeError("catagory tag must be a string")

        return sha1(f"{self.region_tag}|{catagory_tag}|{dumps(args)}|{dumps(kwargs)}".encode("utf8")).hexdigest()

    def chunk_data(self, data: bytes) -> list[bytes]:

        if not isinstance(data, bytes):
            raise TypeError("Data must be of type bytes")
        if len(data) < 1:
            raise ValueError("data size must be at least 1 byte")

        chunks = []
        for chunk in range(0, len(data), self.chunk_size):
            chunks.append(data[chunk:chunk+self.chunk_size])
        return chunks

    @abstractmethod
    def check(self, catagory_tag: str, *args, **kwargs) -> bool:
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def select(self, catagory_tag: str, *args, **kwargs) -> bytes:
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def upsert(self, catagory_tag: str, chunk_size:int, data: bytes, *args, **kwargs) -> bool:
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def delete(self, catagory_tag: str, *args, **kwargs) -> bool:
        raise NotImplementedError("This method is not implemented")
