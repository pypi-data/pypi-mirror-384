import datetime
from typing import Any

from idustorage.storage.interfaces.cacheable import Cacheable


class StorageInterface:
    """Abstract class for a storage service"""

    def save(self, cacheable: Cacheable, name: str, ext: str, date: datetime.datetime, *args) -> str:
        pass

    def retrieve_cached_file(self, pattern: str, ext: str, date: datetime.datetime, *args):
        pass
    
    def open(self, cacheable: Cacheable, name: str):
        pass

    def get_actuality(self) -> str:
        pass

    def set_actuality(self, val: str) -> str:
        pass

    def delete_existing_cache(self, filename: str):
        pass
