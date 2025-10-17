from abc import ABC, abstractmethod
from hashlib import sha1
from json import dumps


class BaseCache(ABC):
    """ Abstract base class for the cache system

    Atributes:
        region_tag (str): region for the cache
        chunk_size (int): number of bytes to read at a time from the cache
    """

    def __init__(self, region: str, chunk_size=1024**3):
        self.region_tag = region.lower()
        self.chunk_size = chunk_size

    def compute_hash(self, catagory_tag: str, *args, **kwargs) -> str:
        """ Computes the hash of the given arguments

        Args:
            catagory_tag (str): category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            str: hash of the given arguments
        """
        if not isinstance(catagory_tag, str):
            raise TypeError("catagory tag must be a string")

        return sha1(f"{self.region_tag}|{catagory_tag}|{dumps(args)}|{dumps(kwargs)}".encode("utf8")).hexdigest()

    def chunk_data(self, data: bytes) -> list[bytes]:
        """ Breaks the data into chunks

        Args:
            data (bytes): data to chunk

        Returns:
            list of bytes: returns the list of chunks
        """
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
        """ Checks if the cache is avaiable for the given arguments

        Args:
            catagory_tag (str): category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the cache is available and valid for the given arguments else False

        Raises:
            NotImplementedError: if the function is not implemented in a subclass
        """
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def select(self, catagory_tag: str, *args, **kwargs) -> bytes:
        """ Retrieves the data from the cache

        Args:
            catagory_tag (str): category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bytes: the data from the cache if available and valid
            None: upon failure or no valid data

        Raises:
            NotImplementedError: if the function is not implemented in a subclass
        """
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def upsert(self, catagory_tag: str, chunk_size:int, data: bytes, *args, **kwargs) -> bool:
        """ Insert or update the data in the cache

        Args:
            catagory_tag (str): category name
            chunk_size: number of bytes to read at a time from the cache
            data (bytes): data to insert
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Raises:
            NotImplementedError: if the function is not implemented in a subclass
        """
        raise NotImplementedError("This method is not implemented")

    @abstractmethod
    def delete(self, catagory_tag: str, *args, **kwargs) -> bool:
        """ Deletes the data from the cache

        Args:
            catagory_tag: category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the cache is deleted or false if it was not deleted or deleted completely

        Raises:
            NotImplementedError: if the function is not implemented in a subclass
        """
        raise NotImplementedError("This method is not implemented")
