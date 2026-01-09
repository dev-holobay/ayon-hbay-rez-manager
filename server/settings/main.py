"""Settings for the addon."""
from typing import Any

from ayon_server.settings import BaseSettingsModel, SettingsField

"""
old set of settings

REZ_VERSION = "2.112.0"
GRAPHVIZ_VERSION = "8.0.2"
PYTHON_VERSION = "3.9.13"
ADD_PYTHON_PACKAGES = ["PySide2==6.10.1", "Qt.py==1.4.8"]

GRAPHVIZ_URL = "https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/{0}/windows_10_msbuild_Release_graphviz-{0}-win32.zip".format(GRAPHVIZ_VERSION)
#               https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/14.1.1/windows_10_cmake_Release_Graphviz-14.1.1-win64.zip
REZ_LATEST_URL = "https://api.github.com/repos/AcademySoftwareFoundation/rez/releases/latest"
REZ_URL = "https://github.com/AcademySoftwareFoundation/rez/archive/{}.zip".format(REZ_VERSION)
"""


class RezManagerSettings(BaseSettingsModel):
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

    rez_packages_path_win: str = SettingsField(
        title="Rez Packages Path Win",
        description="Root directory where Rez packages are stored",
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


DEFAULT_VALUES: dict[str, Any] = {
    "rez_python_version": "3.13.11",
    "rez_version": "3.3.0",
    "rez_packages_path_win": "P:/rez-prod",
    "graphviz_version": "14.1.1",
    "additional_dependencies_pip": '["PySide2==6.10.1", "Qt.py==1.4.8"]'
}
