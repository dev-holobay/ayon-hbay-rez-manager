import json
import os
from ayon_core.addon import AYONAddon, ITrayAddon
from platformdirs import user_data_dir
from . import rez_installer
from .version import __version__

class RezManagerAddon(AYONAddon, ITrayAddon):
    name = "hbay-rez-manager"
    version = __version__

    def initialize(self, settings):
        self.rez_settings = settings.get(self.name, {})
        self.log.info(f"Initialized with settings: {self.rez_settings}")
        self.studio_code = settings.get("core", {}).get("studio_code", "ayon-rez")
        self.log.info(f"Studio code: {self.studio_code}")

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
                                               self.rez_settings.get(
                                                   "rez_version"),
                                               self.rez_settings.get(
                                                   "rez_python_version"),
                                               self.rez_settings.get(
                                                   "graphiz_version"),
                                               json.loads(self.rez_settings.get(
                                                   "additional_dependencies_pip")))
        if not installer.check_if_installed():
            # quick check if all versions already line up
            # if not, we go ahead and install
            # individual versions might be skipped
            installer.install_rez()

    def get_launch_hook_paths(self):
        return [
            os.path.join(os.path.dirname(__file__), "hooks")
        ]
