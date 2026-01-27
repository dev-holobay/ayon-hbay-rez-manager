import platform

from ayon_applications import PreLaunchHook, LaunchTypes, manager


class PreLaunchSetRezConfig(PreLaunchHook):
    """Injects Rez config environment variables before DCC launch."""

    order = -101  # this hook needs to execute first as it sets the rez config environment variables
    platforms = {"windows"}
    launch_types = {LaunchTypes.local}

    def execute(self):
        # Access the addon settings
        self.log.info("Setting Rez Config Environment Variables")
        self.log.info(self.launch_context.data.get("project_settings").get(
            "hbay_rez_manager"))
        rez_settings = self.launch_context.data.get("project_settings", {}).get(
            "hbay_rez_manager", {}).get("rez_config_options", {})
        rez_path = rez_settings.get("rez_packages_path").get(platform.system().lower())
        if not rez_path:
            self.log.warning("REZ_PACKAGES_PATH is not set in AYON settings.")
            return

        self.launch_context.env.update({"REZ_PACKAGES_PATH": rez_path})
        self.log.info(f"Rez Environment Set: REZ_PACKAGES_PATH={rez_path}")
