import json
import os
import platform
import subprocess
from ayon_core.addon import AYONAddon, ITrayAddon
from platformdirs import user_data_dir

from qtpy import QtCore, QtWidgets, QtGui

from .version import __version__
from .qt_helper import ProgressBarDialog, ProgressSignalWrapper
from .rez_config_helper import manage_rez_config_from_settings
from .rez_apps import REZ_APPS

ADDON_ROOT = os.path.dirname(os.path.abspath(__file__))


class RezManagerAddon(AYONAddon, ITrayAddon):
    name = "hbay_rez_manager"
    version = __version__

    def initialize(self, settings):
        self.rez_settings = settings.get(self.name, {})
        self.rez_install_settings = self.rez_settings.get("rez_install_options",
                                                          {})
        self.log.debug(f"Initialized with settings: {self.rez_settings}")
        self.studio_code = settings.get("core", {}).get("studio_code",
                                                        "ayon-rez")
        self.log.debug(f"Studio code: {self.studio_code}")
        # Todo: add a progress bar or a spinner during install

    def tray_exit(self) -> None:
        pass

    def tray_menu(self, tray_menu) -> None:
        """Add Rez applications to the tray menu."""
        if not REZ_APPS:
            return

        # Create a submenu for Rez applications
        rez_menu = QtWidgets.QMenu("Rez Applications", tray_menu)

        for app_name, app_config in REZ_APPS.items():
            action = QtWidgets.QAction(app_name, rez_menu)

            # Set icon if it exists
            icon_path = app_config.get("icon")
            if icon_path and os.path.exists(icon_path):
                action.setIcon(QtGui.QIcon(icon_path))

            # Connect to launch function
            rez_request = app_config.get("rez-request", [])
            rez_executable = app_config.get("rez-executable", "").get(platform.system().lower())
            command = ["rez-env"] + rez_request + ["--", rez_executable,]
            action.triggered.connect(
                lambda checked=False, cmd=command, name=app_name: self._execute_command(cmd)
            )

            rez_menu.addAction(action)

        tray_menu.addMenu(rez_menu)

    def _execute_command(self, command):
        """Executes a command the logging output is logged back into the main log"""
        self.log.info("Executing command: %s", command)
        try:
            # Launch process without blocking
            if os.name == 'nt':  # Windows
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
                    close_fds=True,
                    text=True
                )
            else:  # Unix-like
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    start_new_session=True,
                    close_fds=True,
                    text=True
                )

            # Log output in a non-blocking way using a thread
            def log_output():
                stdout, stderr = process.communicate()
                if stdout:
                    self.log.debug(f"STDOUT:\n{stdout}")
                if stderr:
                    self.log.debug(f"STDERR:\n{stderr}")

            import threading
            threading.Thread(target=log_output, daemon=True).start()

        except Exception as e:
            self.log.error(f"Failed to execute command: {e}")

    def tray_init(self) -> None:
        pass

    def tray_start(self) -> None:
        # we dont want to import this at root level as it is ment for tray only
        from . import rez_installer
        path = user_data_dir(appname="rez", appauthor=self.studio_code)

        # Check if Rez is installed, if not, install it
        installer = rez_installer.RezInstaller(path,
                                               self.rez_install_settings.get(
                                                   "rez_version"),
                                               self.rez_install_settings.get(
                                                   "rez_python_version"),
                                               self.rez_install_settings.get(
                                                   "graphviz_version"),
                                               json.loads(
                                                   self.rez_install_settings.get(
                                                       "additional_dependencies_pip")),
                                               astral_python_tag=self.rez_install_settings.get("astral_python_tag"),
                                               logger=self.log)
        if not installer.check_if_installed():
            # quick check if all versions already line up
            # if not, we go ahead and install
            # individual versions might be skipped
            progress_signal_wrapper_rez_installer = ProgressSignalWrapper(
                installer)

            rez_installer_thread = QtCore.QThread()
            progress_signal_wrapper_rez_installer.moveToThread(
                rez_installer_thread)
            rez_installer_thread.started.connect(
                progress_signal_wrapper_rez_installer.run)
            rez_installer_thread.start()

            dialog = ProgressBarDialog(progress_signal_wrapper_rez_installer,
                                       "Rez Installer")
            dialog.exec_()
            rez_installer_thread.quit()
            rez_installer_thread.wait()

        else:
            self.log.info("Rez already installed.")

        # actual bootstrap of rez add the local folder to PATH
        self.append_to_path(installer.rez_path_folder)
        self.log.info(
            f"using Rez {installer.rez_path_folder}, adding to PATH."
        )
        # manage rez config
        rez_config_path = manage_rez_config_from_settings(self.rez_settings.get("rez_config_options", {}))
        if rez_config_path:
            self.log.info(f"Rez Config: {rez_config_path}")
            os.environ["REZ_CONFIG_FILE"] = rez_config_path

    def get_launch_hook_paths(self, app):
        return [
            os.path.join(ADDON_ROOT, "hooks")
        ]

    @staticmethod
    def append_to_path(new_path: str):
        paths = os.environ.get("PATH", "").split(os.pathsep)
        if new_path not in paths:
            paths.append(new_path)
            os.environ["PATH"] = os.pathsep.join(paths)
