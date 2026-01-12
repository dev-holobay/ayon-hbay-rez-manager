import os
from ayon_core.hooks.pre_global_host_data import GlobalHostDataHook

class SetRezEnv(GlobalHostDataHook):
    """Injects Rez environment variables before DCC launch."""

    # Run after default AYON hooks
    order = 10

    def execute(self):
        # Access the addon settings
        rez_settings = self.data.get("addons_settings", {}).get("hbay-rez-manager",
                                                                {})
        rez_path = rez_settings.get("rez_packages_path")
        # "PATH": os.path.join(self.rez_folder, "Scripts", "rez"),
        # "REZ_PACKAGES_PATH": ";".join(packages_path),
        if not rez_path:
            self.log.warning("REZ_PACKAGES_PATH is not set in AYON settings.")
            return

        # Inject into the launch environment
        self.launch_context.env.update()
        # Optionally, if you need to add Rez to the PATH for the DCC
        # self.launch_context.env["PATH"] = os.pathsep.join([
        #     "path/to/rez/bin", self.launch_context.env.get("PATH", "")
        # ])

        self.log.info(f"Rez Environment Set: REZ_PACKAGES_PATH={rez_path}")
