"""Settings for the addon."""
from typing import Any
from pydantic import Field
from ayon_server.settings import BaseSettingsModel, SettingsField

class MultiplatformPath(BaseSettingsModel):
    windows: str = Field("", title="Windows")
    linux: str = Field("", title="Linux")
    darwin: str = Field("", title="MacOS")

def _config_type_enum():
    return [
        {"value": "config_file", "label": "Use Rez Config File"},
        {"value": "config_web", "label": "Use Rez Config Json Field"},
        {"value": "config_envvar", "label": "Use Envvar to point to Rez Config"},
    ]

class RezInstallOptions(BaseSettingsModel):
    rez_python_version: str = SettingsField(
        title="Python Version",
        description="Python Version that is being used to create rez, we seperate this completely",
        default_factory=str,
    )

    astral_python_tag: str = SettingsField(
        title="Astral Python Tag",
        description="This speeds up install as we now can construct the full url to python, otherwise we fallback to a search in the latest releases",
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
    config_type: str = SettingsField(
        "config_web",
        title="Rez Config Type",
        enum_resolver=_config_type_enum,
        conditional_enum=True,
        description="Choose between file-based config via the repo under /data/rezconfig.py or web-based config (define inline) or define a path to a file which will be set via REZ_CONFIG",
    )
    config_file: str = SettingsField(
        "",
        title="Rez config file from addon data is being used",
        description="The rezconfig.py file is provided by the addon repository",
    )
    config_web: str = SettingsField(
        "",
        title="Rez Config JSON",
        description="Define rez configuration as JSON. Example:\n{\n  \"packages_path\": [\"P:/pipe/rez/packages\"],\n  \"local_packages_path\": \"~/rez/packages\"\n}",
        widget="textarea",
    )
    config_envvar: str = SettingsField(
        default_factory=str,
        title="Path pointing to file will be set to REZ_CONFIG_FILE",
        description="This can expand variables like %localappdata%.",
    )


class RezStandaloneAppConfig(BaseSettingsModel):
    app_name: str = SettingsField(
        "",
        title="Application Name",
        description="Display name for the application in the tray menu",
    )
    rez_request: list[str] = SettingsField(
        default_factory=list,
        title="Rez Request",
        description="List of rez packages to request (e.g., ['usd_nvidia'])",
    )
    rez_executable: MultiplatformPath = SettingsField(
        default_factory=MultiplatformPath,
        title="Rez Executable",
        description="Executable name for each platform",
    )
    icon_filename: str = SettingsField(
        "",
        title="Icon Filename",
        description="Icon filename (must exist in the addon's icons folder)",
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
    rez_standalone_apps: list[RezStandaloneAppConfig] = SettingsField(
        title="Rez Standalone Applications",
        default_factory=list,
        description="Configure standalone applications that can be launched via rez-env",
    )


DEFAULT_VALUES: dict[str, Any] = {
    "rez_install_options": {
        "rez_python_version": "3.13.11",
        "astral_python_tag": "20260127",
        "rez_version": "3.3.0",
        "graphviz_version": "14.1.1",
        "additional_dependencies_pip": '["PySide6==6.10.1", "Qt.py==1.4.8"]',
    },
    "rez_config_options": {
        "rez_packages_path": {"windows": "P:/pipe/rez/p-ext;P:/pipe/rez/p-int"}
    },
    "rez_standalone_apps": [
        {
            "app_name": "USD View",
            "rez_request": ["usd_nvidia"],
            "rez_executable": {
                "windows": "usdview_gui.bat",
                "linux": "usdview_gui",
                "darwin": "usdview_gui",
            },
            "icon_filename": "usd.png",
        },
        {
            "app_name": "Open Rv",
            "rez_request": ["openrv"],
            "rez_executable": {
                "windows": "rv.exe",
                "linux": "rv",
                "darwin": "rv",
            },
            "icon_filename": "rv.png",
        },
        {
            "app_name": "QuiltiX",
            "rez_request": ["QuiltiX"],
            "rez_executable": {
                "windows": "QuiltiX.bat",
                "linux": "",
                "darwin": "",
            },
            "icon_filename": "quiltix.png",
        },
        {
            "app_name": "F3d",
            "rez_request": ["f3d"],
            "rez_executable": {
                "windows": "f3d",
                "linux": "",
                "darwin": "",
            },
            "icon_filename": "f3d.png",
        },
    ],
}
