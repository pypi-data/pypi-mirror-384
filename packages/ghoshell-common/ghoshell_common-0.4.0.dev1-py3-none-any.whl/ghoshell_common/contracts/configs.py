import yaml
from abc import ABC, abstractmethod
from typing import ClassVar, TypeVar, Type, Optional, List
from typing_extensions import Self
from pydantic import BaseModel
from ghoshell_common.helpers import generate_import_path
from ghoshell_common.contracts.storage import FileStorage
from ghoshell_container import Container, Provider
from os.path import join, abspath, exists

__all__ = [
    'ConfigType', 'Configs', 'YamlConfig',
    'WorkspaceConfigs', 'WorkspaceConfigsProvider',
    'DefaultConfigs',
]


class ConfigType(ABC):
    """
    从 workspace 中获取配置文件, 基于 Pydantic + Yaml 或 toml 定义配置.
    """

    @classmethod
    @abstractmethod
    def conf_path(cls) -> str:
        """
        当前 Config 存储时对于 configs 目录的相对路径.
        """
        pass

    @classmethod
    @abstractmethod
    def unmarshal(cls, content: bytes) -> Self:
        """
        反序列化存储数据的方法.
        """
        pass

    def marshal(self) -> bytes:
        """
        生成自己存储数据的方法.
        """
        pass


CONF_TYPE = TypeVar('CONF_TYPE', bound=ConfigType)


class Configs(ABC):
    """
    存储所有 Config 对象的仓库.
    """

    @abstractmethod
    def get(self, conf_type: Type[CONF_TYPE], relative_path: Optional[str] = None) -> CONF_TYPE:
        """
        从仓库中读取一个配置对象.
        :param conf_type: C 类型配置对象的类.
        :param relative_path: 默认不需要填. 如果读取路径不是 C 类型默认的, 才需要传入.
        :return: C 类型的实例.
        :exception: FileNotFoundError
        """
        pass

    @abstractmethod
    def get_or_create(self, conf: CONF_TYPE) -> CONF_TYPE:
        """
        如果配置对象不存在, 则创建一个.
        """
        pass

    @abstractmethod
    def save(self, conf: ConfigType, relative_path: Optional[str] = None) -> None:
        """
        保存一个 Config 对象.
        :param conf: the conf object
        :param relative_path: if pass, override the conf_type default path.
        """
        pass


class YamlConfig(ConfigType, BaseModel):
    """
    基于 Yaml + BaseModel 实现的配置文件.
    """

    relative_path: ClassVar[str]
    """定义默认的相对存储路径. 通常存储在 workspace/configs/relative_path"""

    @classmethod
    def conf_path(cls) -> str:
        return cls.relative_path

    @classmethod
    def unmarshal(cls, content: str) -> "ConfigType":
        value = yaml.safe_load(content)
        return cls(**value)

    def marshal(self) -> bytes:
        value = self.model_dump()
        comment = f"# from class: {generate_import_path(self.__class__)}"
        result = yaml.safe_dump(value)
        return "\n".join([comment, result]).encode()


class BasicConfigs(Configs, ABC):
    """
    A Configs(repository) based on Storage, no matter what the Storage is.
    """

    def get(self, conf_type: Type[CONF_TYPE], relative_path: Optional[str] = None) -> CONF_TYPE:
        path = conf_type.conf_path()
        relative_path = relative_path if relative_path else path
        content = self._get(relative_path)
        return conf_type.unmarshal(content)

    def get_or_create(self, conf: CONF_TYPE) -> CONF_TYPE:
        path = conf.conf_path()
        if not self._exists(path):
            self._put(path, conf.marshal())
            return conf
        return self.get(type(conf))

    @abstractmethod
    def _get(self, relative_path: str) -> bytes:
        pass

    @abstractmethod
    def _put(self, relative_path: str, content: bytes) -> None:
        pass

    @abstractmethod
    def _exists(self, relative_path: str) -> bool:
        pass

    def save(self, conf: ConfigType, relative_path: Optional[str] = None) -> None:
        marshaled = conf.marshal()
        relative_path = relative_path if relative_path else conf.conf_path()
        self._put(relative_path, marshaled)


class DefaultConfigs(BasicConfigs):
    """
    A Configs(repository) based on Storage, no matter what the Storage is.
    """

    def __init__(self, configs_dir: str):
        self._configs_dir = configs_dir

    def _get(self, relative_path: str) -> bytes:
        abs_path = abspath(join(self._configs_dir, relative_path))
        with open(abs_path, 'rb') as f:
            return f.read()

    def _put(self, relative_path: str, content: bytes) -> None:
        abs_path = abspath(join(self._configs_dir, relative_path))
        with open(abs_path, 'wb') as f:
            f.write(content)

    def _exists(self, relative_path: str) -> bool:
        abs_path = abspath(join(self._configs_dir, relative_path))
        return exists(abs_path)


class WorkspaceConfigs(BasicConfigs):

    def __init__(self, storage: FileStorage):
        self._storage = storage

    def _get(self, relative_path: str) -> bytes:
        return self._storage.get(relative_path)

    def _put(self, relative_path: str, content: bytes) -> None:
        self._storage.put(relative_path, content)

    def _exists(self, relative_path: str) -> bool:
        return self._storage.exists(relative_path)


class WorkspaceConfigsProvider(Provider[Configs]):
    """
    默认的 configs 实现.
    """

    def __init__(self, default_configs: List[ConfigType] | None = None):
        self._create_default_configs = default_configs

    def singleton(self) -> bool:
        return True

    def factory(self, con: Container) -> Optional[Configs]:
        from ghoshell_common.contracts.workspace import Workspace
        ws = con.force_fetch(Workspace)

        configs = WorkspaceConfigs(ws.configs())
        # 创建默认的配置文件
        if self._create_default_configs:
            for default_config in self._create_default_configs:
                configs.get_or_create(default_config)
        return configs
