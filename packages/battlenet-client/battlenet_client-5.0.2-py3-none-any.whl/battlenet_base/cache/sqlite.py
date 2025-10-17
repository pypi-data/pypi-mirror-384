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

        """ Used to check if a valid cache entry exists.

        Args:
            category_tag (str): category tag for the API
            args (list): list of positional arguments for the api endpoint function
            kwargs (dict): dict of keyword arguments for the api endpoint function

        Returns:
            bool: True if the cache entry exists, False if doesn't exist or expired
        """

        hash_value = self.compute_hash(category_tag, *args, **kwargs)
        try:
            res = self.connector.execute("""SELECT COUNT(*) as count
FROM cache, categories
WHERE cache.hash = ? and categories.name = ? and cache.categoryId = categories.ROWID and 
unixepoch('now') - cache.last_updated <= categories.duration;""",
                                   (hash_value, category_tag)).fetchone()
        except TypeError:
            return False
        else:
            return res[0] > 0

    def select(self, category_tag: str, *args, **kwargs) -> Union[None, bytes]:
        """ Perform cached data from the selected record(s)

        Args:
            category_tag (str): category tag for the API
            args (list): list of positional arguments for the api endpoint function
            kwargs (dict): dict of keyword arguments for the api endpoint function

        Returns:
            bytes or None: content of the requested cache if it exists or None otherwise
        """

        hash_value = self.compute_hash(category_tag, *args, **kwargs)

        if not self.check(category_tag, *args, **kwargs):
            return None

        cache_id = self.connector.execute("""SELECT ROWID FROM cache WHERE hash = ?;""", (hash_value,)).fetchone()[0]

        try:
            results = self.connector.execute("""SELECT data FROM chunks WHERE cacheId = ? ORDER BY sequence;""", (cache_id,)).fetchall()
        except TypeError:
            return None
        else:
            if len(results) == 0:
                return None

            return b''.join([row[0] for row in results])

    def upsert(self, category_tag: str, data: bytes, *args, **kwargs) -> int:
        """ Insert/Update  the data within the given record

        Args:
            category_tag (str): category tag for the API
            data (bytes): data to be inserted into the cache
            args (list): list of positional arguments for the api endpoint function
            kwargs (dict): dict of keyword arguments for the api endpoint function

        Returns:
            int: returns the number of inserted/updated rows
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
        """ Delete the records that match given criteria

        Args:
            category_tag (str): category tag for the API
            args (list): list of positional arguments for the api endpoint function
            kwargs (dict): dict of keyword arguments for the api endpoint function

        Returns:
            int: returns the number of deleted rows
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
