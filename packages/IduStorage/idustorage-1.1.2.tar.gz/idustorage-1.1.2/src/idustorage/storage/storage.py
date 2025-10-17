import datetime
from pathlib import Path
from typing import Any, Type

from iduconfig import Config
from loguru import logger

from idustorage.storage.interfaces.cacheable import Cacheable
from idustorage.storage.interfaces.storage_interface import StorageInterface


class Storage(StorageInterface):
    def __init__(self, cache_path: Path, config: Config, separator: str = "_"):
        """
        Initialize storage service

        Args:
            cache_path (Path): Path-like path to the caching directory.
            config (Config): idu config.
            separator (str): naming separator, default is `_`; change if arg names have `_` as well (change to `&`).
        """

        self.config = config
        self.cache_path: Path = cache_path
        self.cache_path.mkdir(parents=True, exist_ok=True)
        self.separator = separator

    def save(self, cacheable: Cacheable, name: str, ext: str, date: datetime.datetime, *args) -> str:
        """
        Save file with concrete format: date_name_(...args).extension

        Implement your cacheable if you need one like this:


        class MyCacheableType(Cacheable):
            def __init__(...):
                ...

            def to_file(self, path: Path, name: str, ext: str, date: str, separator: str, *args) -> str:
                filename = f"{date}{separator}{name}"

                for arg in args:
                    filename += f"{separator}{arg}"

                filename += ext

                # SAVE YOUR FILE HERE

                return filename


        Args:
            cacheable (Cacheable): Cacheable implementation with to_file() method.
            name (str): rather type of the file.
            ext (str): extension of the file.
            date (datetime): date of the file.
            args: specification for the file to distinguish between (a.e. 123, schools, modeled).
        """
        date = date.strftime("%Y-%m-%d-%H-%M-%S")
        return cacheable.to_file(self.cache_path, name, ext, date, self.separator, *args)

    def retrieve_cached_file(self, pattern: str, ext: str, *args) -> str:
        """
        Get filename of the most recent file created of such type.

        :param pattern: rather a name of the file.
        :param ext: extension of the file.
        :param args: specification for the file to distinguish between.

        :return: filename of the most recent file created of such type if it's in the span of actuality.
        """

        files = [file.name for file in self.cache_path.glob(f"*{self.separator}{pattern}{''.join([f'{self.separator}{arg}' for arg in args])}{ext}")]
        files.sort(reverse=True)
        logger.info(f"found files for pattern {pattern} with args {args}: {files}")
        actual_filename: str = ""
        for file in files:
            broken_filename = file.split(self.separator)
            date = datetime.datetime.strptime(broken_filename[0], "%Y-%m-%d-%H-%M-%S")
            hours_diff = (datetime.datetime.now() - date).total_seconds() // 3600
            if hours_diff < int(self.config.get("actuality")):
                actual_filename = file
                logger.info(f"Found cached file - {actual_filename}")
                break
        return actual_filename
    
    def open(self, cacheable: Type[Cacheable], name: str):
        """
        Get object from cache. Name can be retrieved from `retrieve_cached_file` method.
        
        Args:
            cacheable (Cacheable): Cacheable implementation with to_file() method.
            name (str): name of the file.
        """
        return cacheable.from_file(self.cache_path, name)

    def delete_existing_cache(self, filename: str):
        """
        Delete existing cache file.
        
        Args:
            filename (str): name of file
        """
        
        if filename != "" and (self.cache_path / filename).exists():
            logger.info(f"Deleting {filename}")
            Path.unlink(self.cache_path / filename)

    def get_cache_list(self) -> list[str]:
        return sorted([file.name for file in self.cache_path.glob("*")], reverse=True)

    def get_actuality(self) -> str:
        return self.config.get("actuality")

    def pget_cache_list(self, pattern: str, ext: str) -> list[str]:
        files = [file.name for file in self.cache_path.glob(f"*{pattern}*{ext}")]
        files.sort(reverse=True)
        for i in range(len(files)):
            broken_filename = files[i].split(self.separator)
            date = datetime.datetime.strptime(broken_filename[0], "%Y-%m-%d-%H-%M-%S")
            hours_diff = (datetime.datetime.now() - date).total_seconds() // 3600
            if hours_diff > int(self.config.get("actuality")):
                files = files[:i]
                break
        return files

    def pget_reinit_list(self, pattern: str, ext: str) -> list[str]:
        files = [file.name for file in self.cache_path.glob(f"*{pattern}*{ext}")]
        files.sort(reverse=True)
        reinit = []
        for i in range(len(files)):
            broken_filename = files[i].split(self.separator)
            date = datetime.datetime.strptime(broken_filename[0], "%Y-%m-%d-%H-%M-%S")
            hours_diff = (datetime.datetime.now() - date).total_seconds() // 3600
            if int(self.config.get("actuality")) - 24 <= hours_diff:
                reinit.append(files[i])
            elif hours_diff > int(self.config.get("actuality")):
                break
        return reinit

    def set_actuality(self, val: str) -> str:
        self.config.set("actuality", val)
        return self.config.get("actuality")
