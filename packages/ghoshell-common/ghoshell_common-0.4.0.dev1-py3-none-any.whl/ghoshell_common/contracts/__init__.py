from ghoshell_common.contracts.storage import (
    Storage, FileStorage,
    FileStorageProvider,
    DefaultFileStorage,
)

from ghoshell_common.contracts.workspace import (
    Workspace,
    LocalWorkspaceProvider,
    LocalWorkspace,
)

from ghoshell_common.contracts.configs import (
    ConfigType, Configs,
    YamlConfig,
    DefaultConfigs,
    WorkspaceConfigs, WorkspaceConfigsProvider
)

from ghoshell_common.contracts.logger import (
    LoggerItf,
    LoggerProvider, WorkspaceLoggerProvider,
    get_console_logger, config_logger_from_yaml,
)

from ghoshell_common.contracts.assets import (
    FileAsset, FileAssetRepo,
    ImageAssetRepo, AudioAssetRepo,
    WorkspaceAssetsRepoProvider,
)


def workspace_providers(workspace_dir: str = "", stub_dir: str | None = None):
    """
    default providers.
    """
    yield LocalWorkspaceProvider(workspace_dir, stub_dir)
    yield WorkspaceConfigsProvider()
    yield WorkspaceLoggerProvider("ghoshell")
    yield WorkspaceAssetsRepoProvider(ImageAssetRepo, "images")
    yield WorkspaceAssetsRepoProvider(AudioAssetRepo, "audio")
