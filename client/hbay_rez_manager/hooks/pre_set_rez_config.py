from ayon_applications import PreLaunchHook, LaunchTypes
from hbay_rez_manager.rez_config_helper import manage_rez_config_from_settings

class PreLaunchSetRezConfig(PreLaunchHook):
    """Injects Rez config environment variables before DCC launch."""

    order = -100  # this hook needs to execute first as it sets the rez config environment variables
    platforms = {"windows"}
    launch_types = {LaunchTypes.local}

    def execute(self):
        # Access the addon settings
        self.log.info("Setting Rez Config Environment Variables")
        rez_settings = self.launch_context.data.get("project_settings", {}).get(
            "hbay_rez_manager", {}).get("rez_config_options", {})

        rez_config_path = manage_rez_config_from_settings(rez_settings)

        if rez_config_path:
            self.launch_context.env.update({"REZ_CONFIG_FILE": rez_config_path})
            self.log.info(f"Rez Environment Set: REZ_CONFIG={rez_config_path}")

