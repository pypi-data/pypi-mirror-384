import errno
import os
import shutil
from pathlib import Path
from typing import Union

from w.services.abstract_service import AbstractService
from w.services.technical.date_service import DateService


class FilesystemService(AbstractService):
    """Service Filesystem"""

    @classmethod
    def is_dir_exists(cls, directory) -> bool:
        """
        Is it refers to an existing directory

        Args:
            directory(str):

        Returns:
            bool
        """
        return os.path.isdir(directory)

    @classmethod
    def is_file_exists(cls, filename) -> bool:
        """
        Is it refers to an existing file

        Args:
            filename(str):

        Returns:
            bool
        """
        return os.path.isfile(filename)

    @classmethod
    def check_dir_exists(cls, directory) -> None:
        """
        Check if a directory exists

        Args:
            directory(str):

        Returns:
            None if directory exists

        Raises:
            RuntimeError if directory does not exist
        """
        if cls.is_dir_exists(directory):
            return None
        raise RuntimeError(f"{directory} does not exist")

    @classmethod
    def check_file_exists(cls, filename) -> None:
        """
        Check if a file exists

        Args:
            filename(str):

        Returns:
            None if file exists

        Raises:
            RuntimeError if file does not exists
        """
        if cls.is_file_exists(filename):
            return None
        raise RuntimeError(f"{filename} does not exists")

    @classmethod
    def copy_dir(cls, src, dst) -> None:
        """
        Copy directory tree and overwrite existing files

        Args:
            src:
            dst:
        """
        cls.check_dir_exists(src)
        for root, dirs, files in os.walk(src):
            for file in files:
                rel_path = root.replace(src, "").lstrip(os.sep)
                dest_path = os.path.join(dst, rel_path)
                if not os.path.exists(dest_path):
                    os.makedirs(dest_path)
                shutil.copy(os.path.join(root, file), os.path.join(dest_path, file))

    @classmethod
    def copy_file(
        cls, src, dst, overwrite=False
    ) -> None:  # pragma: no cover (todo one day)
        """
        Copy file in a new location

        Args:
            src(str): file path ( ex : "/foo/bar/file.txt" )
            dst(str): new file path ( ex : "/foo/bar/file.txt" )
            overwrite(bool): force overwriting existing file
        """
        cls.check_file_exists(src)
        dest_path = os.path.dirname(dst)
        if not os.path.exists(dest_path):
            os.makedirs(dest_path)
        if not overwrite:
            if not cls.is_file_exists(dst):
                shutil.copy(src, dst)
        else:
            shutil.copy(src, dst)

    @classmethod
    def empty_dir(cls, directory) -> None:
        """
        Empty a directory

        Args:
            directory(str):

        Returns:
            None

        Raises:
            RuntimeError if directory does not exists
        """
        cls.check_dir_exists(directory)
        for root, dirs, files in os.walk(directory, topdown=False):
            for file in files:
                os.remove(os.path.join(root, file))
            if root != directory:
                os.rmdir(root)

    @classmethod
    def remove(cls, filename) -> None:
        """
        Remove a file

        Args:
            filename(str):

        Returns:
            None
        """
        if cls.is_file_exists(filename):
            os.remove(filename)

    @classmethod
    def write_file(cls, filename, content):
        """
        Write content into file, erase it if already exists
        Args:
            filename(str): full path
            content(str): text content to write

        Returns:

        """
        cls.check_dir_exists(os.path.dirname(filename))
        with open(filename, "w") as f:
            f.write(content)

    @classmethod
    def write_binary_file(cls, filename, content):
        """
        Write content into file, erase it if already exists
        Args:
            filename(str): full path
            content(bites): text content to write

        Returns:

        """
        cls.check_dir_exists(os.path.dirname(filename))
        with open(filename, "wb") as f:
            f.write(content)

    @classmethod
    def read_file(cls, filename):
        """
        Read file
        Args:
            filename(str): full path

        Returns:
            str
        """
        cls.check_file_exists(filename)
        with open(filename) as f:
            return f.read()

    @classmethod
    def read_binary_file(cls, filename) -> bytes:
        """
        Read binary file
        Args:
            filename(str): full path

        Returns:
            str
        """
        cls.check_file_exists(filename)
        with open(filename, "rb") as f:
            return f.read()

    @staticmethod
    def check_file_can_be_created(filename) -> None:
        """
        DEPRECATED use create_missing instead
        create missing directories for filename

        Args:
            filename (str) : fullpath filename

        Returns:
            None
        """
        if not os.path.exists(filename):
            try:
                return os.makedirs(os.path.dirname(filename))
            except OSError as exc:  # Guard against race condition
                if exc.errno != errno.EEXIST:  # pragma: no cover (todo one day)
                    raise

    @classmethod
    def create_missing(cls, path: str | Path) -> None:
        path_path = cls.get_path(path)
        if path_path.suffix:
            path_path = path_path.parent
        path_path.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def get_path(path: str | Path) -> Path:
        """Get Path instance if path is not"""
        if isinstance(path, Path):
            return path
        return Path(path)

    @classmethod
    def get_basename(cls, filename):
        """
        Get string representing the final path component, excluding the drive and root

        Args:
            filename(str|Path): filename

        Returns:
            str: string representing the final path component
        """
        return cls.get_path(filename).name

    @classmethod
    def has_suffix(cls, filename, suffix: Union[str, list]) -> bool:
        """
        Check if filename has suffix(es)

        Args:
            filename(str):
            suffix(str|list): suffix or list of suffixes

        Returns:
            bool
        """
        filename = cls.get_path(filename)
        if not isinstance(suffix, list):
            suffix = [suffix]
        return filename.suffix in suffix

    @staticmethod
    def prefix_filename_to_now(filename):
        """
        Add timestamp as prefix to the provided filename.
        Timestamp is set to current date and time.

        Args:
            filename(str):

        Returns:
            filename with prefix
        """
        return f"{DateService.to_str('YYYYMMDD_HHmmss')}-{filename}"

    @classmethod
    def get_file_size(cls, filename: str) -> int:
        cls.check_file_exists(filename)
        file = Path(filename)
        return file.stat().st_size
