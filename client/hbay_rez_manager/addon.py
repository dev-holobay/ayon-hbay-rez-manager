import json
import os
from ayon_core.addon import AYONAddon, ITrayAddon
from platformdirs import user_data_dir

from qtpy import QtCore

from . import rez_installer
from .version import __version__
from .qt_helper import ProgressBarDialog, ProgressSignalWrapper

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
        pass

    def tray_init(self) -> None:
        pass

    def tray_start(self) -> None:
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
