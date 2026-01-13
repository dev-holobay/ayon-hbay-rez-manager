from ayon_applications import PreLaunchHook, LaunchTypes, manager

class SetRezEnv(PreLaunchHook):
    """Injects Rez environment variables before DCC launch."""

    order = 1000
    platforms = {"windows"}
    launch_types = {LaunchTypes.local}

    def execute(self):
        # Access the addon settings
        self.log.info("Setting Rez Environment Variables")
        self.log.info(self.launch_context.data.get("project_settings").get("hbay_rez_manager"))
        rez_settings = self.launch_context.data.get("project_settings", {}).get("hbay_rez_manager", {})
        rez_path = rez_settings.get("rez_packages_path_win")
        if not rez_path:
            self.log.warning("REZ_PACKAGES_PATH is not set in AYON settings.")
            return

        self.launch_context.env.update({"REZ_PACKAGES_PATH": rez_path})
        self.log.info(f"Rez Environment Set: REZ_PACKAGES_PATH={rez_path}")
