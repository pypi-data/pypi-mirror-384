import os
from abc import ABC, abstractmethod
from typing import Optional

from ghoshell_common.contracts.storage import FileStorage, DefaultFileStorage
from ghoshell_container import Container, Provider
from os.path import abspath
import shutil

__all__ = ['Workspace', 'LocalWorkspace', 'LocalWorkspaceProvider']


class Workspace(ABC):
    """
    workspace 目录文件管理.
    用于管理一个项目的本地文件存储.
    """

    @abstractmethod
    def root(self) -> FileStorage:
        """
        workspace 根 storage.
        """
        pass

    @abstractmethod
    def configs(self) -> FileStorage:
        """
        配置文件存储路径.
        """
        pass

    @abstractmethod
    def runtime(self) -> FileStorage:
        """
        运行时数据存储路径.
        """
        pass

    @abstractmethod
    def assets(self) -> FileStorage:
        """
        数据资产存储路径.
        """
        pass


class LocalWorkspace(Workspace):

    def __init__(self, workspace_dir: str):
        workspace_dir = abspath(workspace_dir)
        self._ws_root_dir = workspace_dir
        self._root = DefaultFileStorage(workspace_dir)

    def root(self) -> FileStorage:
        return self._root

    def configs(self) -> FileStorage:
        return self._root.sub_storage("configs")

    def runtime(self) -> FileStorage:
        return self._root.sub_storage("runtime")

    def assets(self) -> FileStorage:
        return self._root.sub_storage("assets")


class LocalWorkspaceProvider(Provider[Workspace]):

    def __init__(
            self,
            workspace_dir: str = "",
            stub_dir: Optional[str] = None,
    ):
        if workspace_dir == "":
            # 使用脚本运行的路径作为 workspace.
            workspace_dir = os.path.join(abspath(os.getcwd()), ".ghoshell_ws/")
        self._ws_dir = abspath(workspace_dir)
        self._stub_dir = abspath(stub_dir) if stub_dir else None

    def singleton(self) -> bool:
        return True

    def factory(self, con: Container) -> Optional[Workspace]:
        if self._stub_dir and not os.path.exists(self._stub_dir):
            os.makedirs(self._stub_dir)
            shutil.copytree(self._stub_dir, self._ws_dir)
        return LocalWorkspace(self._ws_dir)
