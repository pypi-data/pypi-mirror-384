from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union, Type
from mimetypes import guess_type
from pydantic import BaseModel, Field
from ghoshell_common.contracts.storage import Storage
from ghoshell_common.helpers import uuid, yaml_pretty_dump
from ghoshell_container import Provider, IoCContainer
import yaml

__all__ = [
    'FileAsset', 'FileAssetRepo',
    'AudioAssetRepo', 'ImageAssetRepo',
    'StorageFileAssetRepo',
    'WorkspaceAssetsRepoProvider',
]


class FileAsset(BaseModel):
    fileid: str = Field(default_factory=uuid, description="ID of the file.")
    filename: str = Field(description="The file name of the file.")
    description: str = Field(default="", description="The description of the file.")
    filetype: str = Field(default="", description="The file type of the file.")
    summary: str = Field(default="", description="The text summary of the file.")
    url: Optional[str] = Field(default=None, description="The URL of the file.")

    def get_format(self) -> str:
        return self.filetype.split("/")[-1]


class FileAssetRepo(ABC):

    @classmethod
    def new_fileinfo(
            cls,
            fileid: str,
            filename: str,
            description: str = "",
            filetype: Optional[str] = None,
    ) -> FileAsset:
        if filetype is None:
            filetype, _ = guess_type(filename)
        fileinfo = FileAsset(
            fileid=fileid,
            filename=filename,
            description=description,
            filetype=filetype,
        )
        return fileinfo

    @abstractmethod
    def save(self, file: FileAsset, binary: Optional[bytes]) -> str:
        """
        save file info and binary data to storage
        :param file: the file info
        :param binary: binary data of the file. if None, the url must be provided
        :return: relative file path of the saved file
        """
        pass

    @abstractmethod
    def get_binary(self, filename: str) -> Optional[bytes]:
        """
        get binary data of the file
        :param filename: the relative filename of the file
        :return: binary data of the file, None if binary data is not available
        """
        pass

    @abstractmethod
    def get_fileinfo(self, fileid: str) -> Optional[FileAsset]:
        """
        get file info from storage
        :param fileid: the file id
        :return: None if no file info is available
        """
        pass

    @abstractmethod
    def has_binary(self, fileid: str) -> bool:
        pass

    def get_file_and_binary_by_id(self, fileid: str) -> Tuple[Union[FileAsset, None], Union[bytes, None]]:
        """
        get binary data by file id
        :param fileid: the file info id.
        :return: file info and binary data, if binary data is None, means the file has url.
        """
        file_info = self.get_fileinfo(fileid)
        if file_info is None:
            return None, None
        return file_info, self.get_binary(file_info.filename)


class ImageAssetRepo(FileAssetRepo, ABC):
    pass


class AudioAssetRepo(FileAssetRepo, ABC):
    pass


class StorageFileAssetRepo(FileAssetRepo):
    """
    simple implementation of FileAssets
    """

    def __init__(self, storage: Storage):
        self._storage = storage

    @staticmethod
    def _get_fileinfo_filename(fileid: str) -> str:
        return f"{fileid}.yml"

    def save(self, file: FileAsset, binary: Optional[bytes]) -> str:
        if binary is None and file.url is None:
            raise AttributeError("failed to save image: binary is None and image info is not from url.")
        fileinfo_filename = self._get_fileinfo_filename(file.fileid)
        data = file.model_dump(exclude_none=True)
        content = yaml_pretty_dump(data)
        self._storage.put(fileinfo_filename, content.encode())
        if binary:
            self._storage.put(file.filename, binary)
        return file.filename

    def get_binary(self, filename: str) -> Optional[bytes]:
        if self._storage.exists(filename):
            return self._storage.get(filename)
        return None

    def has_binary(self, fileid: str) -> bool:
        fileinfo = self.get_fileinfo(fileid)
        if fileinfo is None:
            return False
        filename = fileinfo.filename
        return self._storage.exists(filename)

    def get_fileinfo(self, fileid: str) -> Optional[FileAsset]:
        fileinfo_filename = self._get_fileinfo_filename(fileid)
        if not self._storage.exists(fileinfo_filename):
            return None
        content = self._storage.get(fileinfo_filename)
        data = yaml.safe_load(content)
        return FileAsset(**data)


class WorkspaceAssetsRepoProvider(Provider):

    def __init__(self, assets_type: Type[FileAssetRepo], relative_path: str):
        self._assets_type = assets_type
        self._relative_path = relative_path

    def singleton(self) -> bool:
        return True

    def contract(self) -> Type[FileAssetRepo]:
        return self._assets_type

    def factory(self, con: IoCContainer) -> FileAssetRepo:
        from ghoshell_common.contracts.workspace import Workspace
        ws = con.force_fetch(Workspace)
        repo = StorageFileAssetRepo(ws.assets().sub_storage(self._relative_path))
        return repo
