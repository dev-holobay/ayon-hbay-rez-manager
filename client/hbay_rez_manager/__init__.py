import os
from ayon_core.addon import AyonAddon
from platformdirs import user_data_dir
from . import rez_installer


class RezManagerAddon(AyonAddon):
    name = "rez_manager"

    def initialize(self, settings):
        """This runs when the addon is loaded."""
        self.rez_settings = settings.get("rez_manager", {})
        studio_code = settings.get("core", {}).get("studio_code", "ayon-rez")
        path = user_data_dir(appname="rez", appauthor=studio_code)

        # Check if Rez is installed, if not, install it
        if not self._is_rez_installed():
            installer = rez_installer.RezInstaller(path,
                                                   self.rez_settings.get(
                                                       "rez_version"),
                                                   self.rez_settings.get(
                                                       "python_version"),
                                                   self.rez_settings.get(
                                                       "graphiz_version"),
                                                   self.rez_settings.get(
                                                       "dependencies"))
            installer.install_rez()

    def get_launch_hook_paths(self):
        return [
            os.path.join(os.path.dirname(__file__), "hooks")
        ]

    def _is_rez_installed(self):
        # create a check file at the end of the install
        return False


def get_recipe_settings(self):
    """Example of passing settings to the environment"""
    return self.rez_settings.get("rez_packages_path")
