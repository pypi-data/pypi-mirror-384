from typing import Union

from .base import BaseCache


class SQLiteCache(BaseCache):

    connector = None

    def __init__(self, connector, region_tag: str) -> None:
        super().__init__(region_tag, 1024**3)
        self.connector = connector

    def __del__(self) -> None:
        self.connector.close()

    def check(self, category_tag: str, *args, **kwargs) -> bool:
        """ Checks if the cache is avaiable for the given arguments

        Args:
            category_tag (str): the category tag
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the cache is available and valid for the given arguments else False
        """
        hash_value = self.compute_hash(category_tag, *args, **kwargs)
        try:
            res = self.connector.execute("""SELECT COUNT(*) as count
FROM cache, categories
WHERE cache.hash = ? and unixepoch('now') < cache.next_update;""",
                                   (hash_value, category_tag)).fetchone()
        except TypeError:
            return False
        else:
            return res[0] > 0

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
        hash_value = self.compute_hash(category_tag, *args, **kwargs)
        try:
            results = self.connector.execute("""SELECT chunks.data FROM cache, chunks
                                                WHERE cache.hash = ? AND chunks.cacheId = cache.ROWID AND
                                                    cache.next_update > unixepoch('now')
                                                ORDER BY sequence;""", (hash_value,)).fetchall()
        except TypeError:
            return None
        else:
            if len(results) == 0:
                return None

            return b''.join([row[0] for row in results])

    def upsert(self, category_tag: str, data: bytes, *args, **kwargs) -> int:
        """ Insert or update the data in the cache

        Args:
            category_tag (str): category name
            data (bytes): data to insert
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the data was inserted or not, False otherwise
        """
        hash_value = self.compute_hash(category_tag, *args, **kwargs)
        data_list = []
        chunk_count = 0
        cache_id = self.connector.execute("""SELECT ROWID FROM cache WHERE hash = ?;""", (hash_value,)).fetchone()[0]
        for counter, chunk in enumerate(self.chunk_data(data), start=1):
            data_list.append({'cacheId': cache_id, "sequence": counter, "data": chunk})
            chunk_count = counter

        try:
            results = self.connector.executemany("""INSERT INTO chunks (cacheId, sequence, data) VALUES (:cacheId, :sequence, :data)
            ON CONFLICT (cacheId, sequence) DO UPDATE SET data=excluded.data;""", data_list)
        except TypeError:
            return False
        else:
            self.connector.commit()

        return results.rowcount == chunk_count

    def delete(self, category_tag: str, *args, **kwargs) -> bool:
        """ Deletes the data from the cache

        Args:
            category_tag: category name
            *args: list of arguments for the API endpoint
            **kwargs: dict of keyword arguments for the API endpoint

        Returns:
            bool: True if the cache is deleted or false if it was not deleted or deleted completely
        """
        hashed_value = self.compute_hash(category_tag, *args, **kwargs)
        cache_id = self.connector.execute("""SELECT FROM cache WHERE hash = ?;""", (hashed_value,)).fetchone()[0]

        try:
            chunk_results = self.connector.execute("""DELETE FROM chunks WHERE cacheId = ?;""", (cache_id,))
            cache_results = self.connector.execute("""DELETE FROM cache WHERE hash = ?;""", (hashed_value,))
        except TypeError:
            return False
        else:
            self.connector.commit()

        return chunk_results.rowcount + cache_results.rowcount > 0
