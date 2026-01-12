import os
from ayon_core.addon import AyonAddon
from platformdirs import user_data_dir
from . import rez_installer

class RezManagerAddon(AyonAddon):
    name = "rez_manager"

    def initialize(self, settings):
        self.rez_settings = settings.get("rez_manager", {})
        studio_code = settings.get("core", {}).get("studio_code", "ayon-rez")
        path = user_data_dir(appname="rez", appauthor=studio_code)

        # Check if Rez is installed, if not, install it
        installer = rez_installer.RezInstaller(path,
                                               self.rez_settings.get(
                                                   "rez_version"),
                                               self.rez_settings.get(
                                                   "python_version"),
                                               self.rez_settings.get(
                                                   "graphiz_version"),
                                               self.rez_settings.get(
                                                   "dependencies"))
        if not installer.check_if_installed():
            # quick check if all versions already line up
            # if not, we go ahead and install
            # individual versions might be skipped
            installer.install_rez()

    def get_launch_hook_paths(self):
        return [
            os.path.join(os.path.dirname(__file__), "hooks")
        ]


def get_recipe_settings(self):
    return self.rez_settings.get("rez_packages_path")
