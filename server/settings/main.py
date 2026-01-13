"""Settings for the addon."""
from typing import Any

from ayon_server.settings import BaseSettingsModel, SettingsField


class RezInstallOptions(BaseSettingsModel):
    rez_python_version: str = SettingsField(
        title="Python Version",
        description="Python Version that is being used to create rez, we seperate this completely",
        default_factory=str,
    )

    rez_version: str = SettingsField(
        title="Rez Pip Version",
        description="The Version that is being used from pip to setup rez",
        default_factory=str,
    )

    graphviz_version: str = SettingsField(
        title="Graphviz Version",
        description="Graphviz Version used to render failedgraphs",
        default_factory=str,
    )

    additional_dependencies_pip: str = SettingsField(
        title="Additional Dependencies Pip",
        description="This is needed for rez-gui to run",
        default_factory=str,
    )


class RezConfigOptions(BaseSettingsModel):
    rez_packages_path_win: str = SettingsField(
        title="Rez Packages Path Win",
        description="Root directory where Rez packages are stored",
        default_factory=str,
    )


class RezManagerSettings(BaseSettingsModel):
    enabled: bool = SettingsField(True)
    rez_install_options: RezInstallOptions = SettingsField(
        title="Rez Install Options",
        default_factory=RezInstallOptions,
    )
    rez_config_options: RezConfigOptions = SettingsField(
        title="Rez Config Options",
        default_factory=RezConfigOptions,
    )


DEFAULT_VALUES: dict[str, Any] = {
    "rez_python_version": "3.13.11",
    "rez_version": "3.3.0",
    "graphviz_version": "14.1.1",
    "additional_dependencies_pip": '["PySide6==6.10.1", "Qt.py==1.4.8"]',
    "rez_packages_path_win": "P:/pipe/rez/p-ext;P:/pipe/rez/p-int",
}
