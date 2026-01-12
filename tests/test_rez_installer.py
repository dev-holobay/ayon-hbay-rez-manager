import json
import logging
import pytest
from platformdirs import user_data_dir
from hbay_rez_manager.rez_installer import RezInstaller
from typing import Any

DEFAULT_VALUES: dict[str, Any] = {
    "rez_python_version": "3.13.11",
    "rez_version": "3.2.0",
    "rez_packages_path_win": "P:/rez-prod",
    "graphviz_version": "14.1.1",
    "additional_dependencies_pip": '["PySide6==6.10.1", "Qt.py==1.4.8"]'
}



def test_rez_installation():
    """Test the full Rez installation process using default settings."""
    logging.basicConfig(level=logging.INFO)
    path = user_data_dir(appname="rez", appauthor="holobay")

    # Parse dependencies from default settings
    dependencies = DEFAULT_VALUES["additional_dependencies_pip"]
    if isinstance(dependencies, str):
        try:
            dependencies = json.loads(dependencies)
        except json.JSONDecodeError:
            dependencies = []

    installer = RezInstaller(
        root=path,
        rez_version=DEFAULT_VALUES["rez_version"],
        python_version=DEFAULT_VALUES["rez_python_version"],
        graphviz_version=DEFAULT_VALUES["graphviz_version"],
        dependencies=dependencies
    )

    # We run the installer. If it crashes, the test fails.
    installer.install_rez()

    # Basic assertions to ensure manifest was created
    assert installer.check_if_installed() is True