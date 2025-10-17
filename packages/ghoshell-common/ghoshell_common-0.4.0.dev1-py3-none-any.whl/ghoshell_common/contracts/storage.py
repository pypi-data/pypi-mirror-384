from abc import abstractmethod
from typing import Optional, Iterable, Protocol
import os
from ghoshell_container import Container, Provider
import fnmatch

__all__ = ['Storage', 'FileStorage', 'DefaultFileStorage', 'FileStorageProvider']


class Storage(Protocol):

    @abstractmethod
    def sub_storage(self, relative_path: str) -> "Storage":
        """
        生成一个次级目录下的 storage.
        :param relative_path:
        :return:
        """
        pass

    @abstractmethod
    def get(self, file_path: str) -> bytes:
        """
        获取一个 Storage 路径下一个文件的内容.
        :param file_path: storage 下的一个相对路径.
        """
        pass

    @abstractmethod
    def remove(self, file_path: str) -> None:
        pass

    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """
        if the object exists
        :param file_path: file_path or directory path
        """
        pass

    @abstractmethod
    def put(self, file_path: str, content: bytes) -> None:
        """
        保存一个文件的内容到 file_path .
        :param file_path: storage 下的一个相对路径.
        :param content: 文件的内容.
        """
        pass

    @abstractmethod
    def dir(self, prefix_dir: str, recursive: bool, patten: Optional[str] = None) -> Iterable[str]:
        """
        遍历一个路径下的文件, 返回相对的文件名.
        :param prefix_dir: 目录的相对路径位置.
        :param recursive: 是否递归查找.
        :param patten: 文件的正则规范.
        :return: 多个文件路径名.
        """
        pass


class FileStorage(Storage, Protocol):
    """
    Storage Based on FileSystem.
    """

    @abstractmethod
    def abspath(self) -> str:
        """
        storage root directory's absolute path
        """
        pass

    @abstractmethod
    def sub_storage(self, relative_path: str) -> "FileStorage":
        """
        FileStorage's sub storage is still FileStorage
        """
        pass


class DefaultFileStorage(FileStorage):
    """
    FileStorage implementation based on python filesystem.
    Simplest implementation.
    """

    def __init__(self, dir_: str):
        self._dir: str = os.path.abspath(dir_)

    def abspath(self) -> str:
        return self._dir

    def get(self, file_path: str) -> bytes:
        file_path = self._join_file_path(file_path)
        with open(file_path, 'rb') as f:
            return f.read()

    def remove(self, file_path: str) -> None:
        file_path = self._join_file_path(file_path)
        os.remove(file_path)

    def exists(self, file_path: str) -> bool:
        file_path = self._join_file_path(file_path)
        return os.path.exists(file_path)

    def _join_file_path(self, path: str) -> str:
        file_path = os.path.join(self._dir, path)
        file_path = os.path.abspath(file_path)
        if not file_path.startswith(self._dir):
            raise FileNotFoundError(f"file path {path} is not allowed")
        return file_path

    def put(self, file_path: str, content: bytes) -> None:
        file_path = self._join_file_path(file_path)
        if not file_path.startswith(self._dir):
            raise FileNotFoundError(f"file path {file_path} is not allowed")
        file_dir = os.path.dirname(file_path)
        if not os.path.exists(file_dir):
            os.makedirs(file_dir)
        with open(file_path, 'wb') as f:
            f.write(content)

    def sub_storage(self, relative_path: str) -> "FileStorage":
        if not relative_path:
            return self
        dir_path = self._join_file_path(relative_path)
        return DefaultFileStorage(dir_path)

    def dir(self, prefix_dir: str, recursive: bool, patten: Optional[str] = None) -> Iterable[str]:
        dir_path = self._join_file_path(prefix_dir)
        for root, ds, fs in os.walk(dir_path):
            # 遍历单层的文件名.
            for filename in fs:
                if self._match_file_pattern(filename, patten):
                    yield filename

            # 深入遍历目录.
            if recursive and ds:
                for _dir in ds:
                    sub_dir_iterator = self.dir(_dir, recursive, patten)
                    for filename in sub_dir_iterator:
                        yield filename

    @staticmethod
    def _match_file_pattern(filename: str, pattern: Optional[str]) -> bool:
        if pattern is None:
            return True
        matched = True
        if pattern.startswith('!'):
            matched = False
            pattern = pattern[1:]
        if pattern and fnmatch.fnmatch(filename, pattern):
            return matched
        return not matched


class FileStorageProvider(Provider[FileStorage]):

    def __init__(self, dir_: str):
        self._dir: str = dir_

    def singleton(self) -> bool:
        return True

    def aliases(self) -> Iterable[Storage]:
        yield Storage

    def factory(self, con: Container) -> Optional[Storage]:
        return DefaultFileStorage(self._dir)
