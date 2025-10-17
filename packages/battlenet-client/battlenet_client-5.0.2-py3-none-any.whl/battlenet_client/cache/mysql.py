from typing import Union

from .base import BaseCache


class MySQLCache(BaseCache):

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
WHERE cache.object_hash = ? and categories.name = ? and cache.category = categories.cat_id and 
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

        try:
            res = self.connector.execute("""SELECT data 
FROM cache, categories
WHERE cache.object_hash = ? and categories.name = ? and cache.category = categories.cat_id and 
unixepoch('now') - cache.last_updated <= categories.duration order by seq;""",
                                      (hash_value, category_tag)).fetchall()
        except TypeError:
            return None
        else:
            if len(res) == 0:
                return None

            return b''.join([row[0] for row in res])

    def upsert(self, category_tag: str, data: bytes, chunk_size: int=32 * 1024, *args, **kwargs) -> int:
        """ Insert or update the data within the given record

        Args:
            category_tag (str): category tag for the API
            data (bytes): data to be inserted into the cache
            chunk_size (int): size of the chunk to insert into the cache
            args (list): list of positional arguments for the api endpoint function
            kwargs (dict): dict of keyword arguments for the api endpoint function

        Returns:
            int: returns the number of inserted/updated rows
        """

        hash_value = self.compute_hash(category_tag, *args, **kwargs)
        count = 1
        data_list = []
        for chunk in self.chunk_data(data):
            data_list.append({'hash': hash_value, "sequence": count, "data": chunk, "name": category_tag})
            count += 1

        try:
            res = self.connector.executemany("""INSERT INTO cache (object_hash, seq, data, category, last_updated)
SELECT :hash, :sequence, :data, cat_id, unixepoch('now') FROM categories WHERE name=:name
ON CONFLICT (object_hash, seq) DO UPDATE SET data = excluded.data, category=excluded.category, last_updated = excluded.last_updated;""",
                            data_list)
        except TypeError:
            return False
        else:
            self.connector.commit()
            return res.rowcount


    def delete(self, category_tag: str, *args, **kwargs) -> int:
        """ Delete the records that match given criteria

        Args:
            category_tag (str): category tag for the API
            args (list): list of positional arguments for the api endpoint function
            kwargs (dict): dict of keyword arguments for the api endpoint function

        Returns:
            int: returns the number of deleted rows
        """

        delete_dict = {"hash": self.compute_hash(category_tag, *args, **kwargs)}

        try:
            res = self.connector.execute("""DELETE FROM cache WHERE object_hash = :hash;""",
                                         delete_dict)
        except TypeError:
            return False
        else:
            self.connector.commit()
            return res.rowcount
