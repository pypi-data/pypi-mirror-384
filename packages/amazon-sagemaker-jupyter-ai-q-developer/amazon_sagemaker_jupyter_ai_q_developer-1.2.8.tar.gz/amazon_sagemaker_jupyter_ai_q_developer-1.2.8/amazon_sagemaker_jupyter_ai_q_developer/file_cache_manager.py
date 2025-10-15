import functools
import logging
import os
from datetime import datetime, timezone

logging.basicConfig(format="%(levelname)s: %(message)s")


class FileCacheManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def timed_lru_cache(maxsize: int = 128):
        """
        Decorator function to cache file contents with a Least Recently Used (LRU) cache replacement policy.
        The cache also considers the last modified time of the file to ensure that changes are reflected.

        Args:
            maxsize (int): The maximum number of items to keep in the cache (default: 11).

        Returns:
            A decorated function that caches file contents based on the file path.
        """

        def wrapper_cache(lru_func):
            # Apply the functools.lru_cache decorator to the function being decorated
            lru_func = functools.lru_cache(maxsize=maxsize)(lru_func)
            # Initialize a dictionary to store file contents and metadata
            lru_func.cache = {}

            @functools.wraps(lru_func)
            def wrapped_func(self, file_path):
                """
                Cached function to read file contents, taking into account the last modified time.

                Args:
                    file_path (str): The path to the file to be read.

                Returns:
                    The contents of the file as a string.
                """
                # Get the last modified time of the file
                file_last_modified_time = datetime.fromtimestamp(
                    os.path.getmtime(file_path), timezone.utc
                )
                # Get the cached entry for the file, if it exists
                cache_entry = lru_func.cache.get(file_path)

                if cache_entry is None or cache_entry["last_modified"] < file_last_modified_time:
                    # Cache miss or file has been modified since the last cache update
                    logging.debug("Missed from the file cache")
                    with open(file_path, "r") as file:
                        logging.info(f"Reading from file {file_path}")
                        file_content = file.read()
                    # Update the cache with the new file content and last modified time
                    lru_func.cache[file_path] = {
                        "content": file_content,
                        "last_modified": file_last_modified_time,
                    }
                else:
                    # Cache hit
                    logging.debug(f"Hit from the file cache key {file_path}")
                    file_content = cache_entry["content"]
                return file_content

            return wrapped_func

        return wrapper_cache

    @timed_lru_cache()
    def get_cached_file_content(self, file_path):
        """
        Method to retrieve the cached contents of a file.

        Args:
            file_path (str): The path to the file to be read.

        Returns:
            The contents of the file as a string.
        """
        return self.get_cached_file_content(file_path)
