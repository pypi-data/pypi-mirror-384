from pathlib import Path


class Cacheable:
    """Abstract class for anything that can or should be cached"""

    def to_file(self, path: Path, name: str, ext: str, date: str, separator: str, *args) -> str:
        """
        Save cacheable object to file.

        :param path: Path-like path to cache directory
        :param name: rather a type of the file
        :param ext: extension of the file
        :param date: creation date of the file
        :param separator: separator used for filename
        :param args: specification for the file to distinguish between
        """
        pass
    
    @staticmethod
    def from_file(path: Path, name: str):
        """
        Retrieve object from cache.
        
        Args:
            path (Path): Path-like path to cache directory
            name (str): name of file
        """
        pass
