import json
import logging
from pathlib import Path

import pytest
from platformdirs import user_data_dir
from hbay_rez_manager.rez_installer import RezInstaller
from typing import Any

DEFAULT_VALUES: dict[str, Any] = {
    "rez_python_version": "3.13.11",
    "rez_version": "3.3.0",
    # "rez_packages_path": {"windows": "P:/pipe/rez/p-ext;P:/pipe/rez/p-int"},
    "graphviz_version": "14.1.1",
    "additional_dependencies_pip": '["PySide6==6.10.1", "Qt.py==1.4.8"]'
}



def test_rez_installation():
    """Test the full Rez installation process using default settings."""
    logging.basicConfig(level=logging.INFO)
    path = user_data_dir(appname="rez", appauthor="holobay-test2")
    # path = Path.home() / ".rez"
    # Parse dependencies from default settings
    path = r"C:\TEMP\test mit leerzeichen"
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
    installer.run()

    # Basic assertions to ensure manifest was created
    assert installer.check_if_installed() is True



def test_astral_python_getter():
    logging.basicConfig(level=logging.INFO)
    path = user_data_dir(appname="rez", appauthor="holobay-test2")
    # path = Path.home() / ".rez"
    # Parse dependencies from default settings
    path = r"C:\TEMP\test mit leerzeichen"
    dependencies = DEFAULT_VALUES["additional_dependencies_pip"]
    if isinstance(dependencies, str):
        try:
            dependencies = json.loads(dependencies)
        except json.JSONDecodeError:
            dependencies = []

    installer = RezInstaller(
        root=path,
        rez_version=DEFAULT_VALUES["rez_version"],
        python_version="3.13.11",
        graphviz_version=DEFAULT_VALUES["graphviz_version"],
        dependencies=dependencies,
        astral_python_tag="20260127"
    )


    target = installer._get_platform_target()

    python_build_url = installer._resolve_python_build_standalone_url(
        installer.python_version, target
    )
    assert python_build_url == "https://github.com/astral-sh/python-build-standalone/releases/download/20260127/cpython-3.13.11+20260127-x86_64-pc-windows-msvc-pgo-full.tar.zst"

def test_astral_python_getter_2():
    logging.basicConfig(level=logging.INFO)
    path = user_data_dir(appname="rez", appauthor="holobay-test2")
    # path = Path.home() / ".rez"
    # Parse dependencies from default settings
    path = r"C:\TEMP\test mit leerzeichen"
    dependencies = DEFAULT_VALUES["additional_dependencies_pip"]
    if isinstance(dependencies, str):
        try:
            dependencies = json.loads(dependencies)
        except json.JSONDecodeError:
            dependencies = []

    installer = RezInstaller(
        root=path,
        rez_version=DEFAULT_VALUES["rez_version"],
        python_version="3.13.11",
        graphviz_version=DEFAULT_VALUES["graphviz_version"],
        dependencies=dependencies,
        astral_python_tag=""
    )


    target = installer._get_platform_target()

    python_build_url = installer._resolve_python_build_standalone_url(
        installer.python_version, target
    )
    assert python_build_url == "https://github.com/astral-sh/python-build-standalone/releases/download/20260127/cpython-3.13.11+20260127-x86_64-pc-windows-msvc-pgo-full.tar.zst"