import json
import logging
import os
import shutil
import subprocess
import tempfile
import urllib
import zipfile

from .constants import GRAPHVIZ_URL, REZ_URL


class RezInstaller:
    def __init__(
            self,
            root: str,
            rez_version: str,
            python_version: str,
            graphviz_version: str,
            dependencies: list,
    ):
        self.log = logging.getLogger(self.__class__.__name__)
        self.root_folder = root
        self.rez_version = rez_version
        self.python_version = python_version
        self.graphviz_version = graphviz_version
        self.dependencies = dependencies

        if os.name == "nt":
            self.root_folder = self.root_folder.replace("/", "\\")
        self.python_folder = os.path.join(self.root_folder, "source", "python")
        self.rez_folder = os.path.join(
            self.root_folder, "source", "rez", self.rez_version
        )
        self.manifest_path = os.path.join(self.root_folder,
                                          "rez_installed.json")
        self.installed = self.load_manifest()

        for i in [self.rez_folder, self.python_folder]:
            if not os.path.isdir(i):
                try:
                    os.makedirs(i, exist_ok=True)
                except WindowsError:
                    pass
        self.__garbage = []

    def _should_install(self, key: str, requested_value: any) -> bool:
        """Internal check to see if a specific component needs installation."""
        if not self.installed:
            return True
        
        if key == "dependencies":
            return set(self.installed.get(key, [])) != set(requested_value)
        
        return self.installed.get(key) != requested_value

    def get_python(self):
        if not self._should_install("python_version", self.python_version):
            self.log.info("Python %s already installed, skipping.", self.python_version)
            self.python = os.path.join(
                self.python_folder,
                f"python.{self.python_version}",
                "tools",
                "python.exe",
            )
            return

        temp_folder = tempfile.mkdtemp(prefix="python-")
        nuget_path = os.path.join(temp_folder, "nuget.exe")
        self.log.info("Downloading nuget to temporary path")
        urllib.request.urlretrieve(
            "https://dist.nuget.org/win-x86-commandline/latest/nuget.exe",
            nuget_path,
        )
        self.__garbage.append(nuget_path)
        try:
            self.log.info("Installing Python to %s", self.python_folder)
            cmd = [
                nuget_path,
                "install",
                "python",
                "-OutputDirectory",
                self.python_folder,
                "-Version",
                self.python_version,
            ]

            subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
            )
        except Exception as e:
            self.log.exception(e)
            self.errors.append("python install failed")
        else:
            self.log.info("Installed Python")
            # "python.3.9.13\tools\python.exe"
            self.python = os.path.join(
                self.python_folder,
                f"python.{self.python_version}",
                "tools",
                "python.exe",
            )
            self.log.debug(self.python)

    def post_install(self):
        if self.__garbage:
            for i in self.__garbage:
                try:
                    if os.path.isfile(i):
                        os.unlink(i)
                    if os.path.isdir(i):
                        shutil.rmtree(i)
                except:
                    pass
                else:
                    self.log.info("removed tempfile %s", i)
        self.write_manifest()

    def write_manifest(self):
        manifest = {
            "rez_version": self.rez_version,
            "python_version": self.python_version,
            "graphviz_version": self.graphviz_version,
            "dependencies": self.dependencies,
        }
        try:
            with open(self.manifest_path, "w") as f:
                json.dump(manifest, f, indent=4)
            self.log.info("Manifest written to %s", self.manifest_path)
        except Exception as e:
            self.log.error("Failed to write manifest: %s", e)

    def load_manifest(self):
        if not os.path.exists(self.manifest_path):
            return None
        try:
            with open(self.manifest_path, "r") as f:
                return json.load(f)
        except Exception as e:
            self.log.error("Failed to load manifest: %s", e)
            return None

    def check_if_installed(self) -> bool:
        """Checks if the requested configuration matches the installed manifest."""

        if self.installed is None:
            return False
        return (
                self.installed.get("rez_version") == self.rez_version and
                self.installed.get("python_version") == self.python_version and
                self.installed.get("graphviz_version") == self.graphviz_version and
                set(self.installed.get("dependencies", [])) == set(self.dependencies)
        )

    def install_rez(self):
        self.errors = []
        self.get_python()
        rez_zip = self.get_rez()
        self.setup_rez(rez_zip)
        self.get_additional_packages()
        self.get_graphviz()
        self.post_install()

    def get_rez(self):
        if not self._should_install("rez_version", self.rez_version):
            self.log.info("Rez %s already downloaded/installed, skipping download.", self.rez_version)
            return None

        temp_folder = tempfile.mkdtemp(prefix="python-")
        rez_temp = os.path.join(temp_folder, f"{self.rez_version}.zip")
        self.log.info("Downloading Rez to temporary path")
        urllib.request.urlretrieve(REZ_URL.format(self.rez_version), rez_temp)
        self.__garbage.append(rez_temp)
        self.log.debug(rez_temp)
        self.log.info("Downloaded Rez")
        return rez_temp

    def setup_rez(self, archive: str):
        if archive is None:
            return

        temp_folder = tempfile.mkdtemp(prefix="rez-temp-")
        with zipfile.ZipFile(archive, "r") as zip_ref:
            zip_ref.extractall(temp_folder)
        self.__garbage.append(temp_folder)
        self.log.info("Installing Rez...")
        try:
            cmd = "{} {} -v {}".format(
                self.python,
                os.path.join(
                    temp_folder, f"rez-{self.rez_version}", "install.py"
                ),
                self.rez_folder,
            )
            self.log.debug(cmd)
            subprocess.run(
                cmd,
                shell=True,
                check=True,
                capture_output=True,
            )

        except Exception as e:
            self.log.exception(e)
        else:
            self.log.info("Successfully installed Rez to %s", self.rez_folder)

    def get_additional_packages(self):
        if not self._should_install("dependencies", self.dependencies):
            self.log.info("Dependencies already match manifest, skipping.")
            return

        for package in self.dependencies:
            try:
                self.log.info("Installing %s ...", package)
                cmd = "{} install {}".format(
                    os.path.join(self.rez_folder, "Scripts", "pip.exe"),
                    package,
                )
                subprocess.run(
                    cmd,
                    shell=True,
                    check=True,
                    capture_output=True,
                )
            except Exception as e:
                self.log.exception(e)
            else:
                self.log.info("Successfully installed %s", package)

    def get_graphviz(self):
        if not self._should_install("graphviz_version", self.graphviz_version):
            self.log.info("Graphviz %s already installed, skipping.", self.graphviz_version)
            return None

        temp_folder = tempfile.mkdtemp(prefix="graphviz-")
        temp = os.path.join(temp_folder, "graphviz.zip")
        self.log.info("Downloading Graphviz to temporary path")
        urllib.request.urlretrieve(
            GRAPHVIZ_URL.format(self.graphviz_version), temp
        )
        self.__garbage.append(temp)
        self.log.debug(temp)
        temp_folder = tempfile.mkdtemp(prefix="rez-temp-")
        self.log.info("Installing Graphviz ...")
        with zipfile.ZipFile(temp, "r") as zip_ref:
            zip_ref.extractall(temp_folder)
        file_names = os.listdir(os.path.join(temp_folder, "Graphviz", "bin"))
        for file_name in file_names:
            shutil.move(
                os.path.join(temp_folder, "Graphviz", "bin", file_name),
                os.path.join(self.rez_folder, "Scripts", "rez"),
            )
        self.__garbage.append(temp_folder)
        self.log.info("Installed Graphviz")
        return temp


if __name__ == "__main__":
    from platformdirs import user_data_dir
    from settings.main import DEFAULT_VALUES

    logging.basicConfig(level=logging.INFO)
    path = user_data_dir(appname="rez", appauthor="holobay")

    # additional_dependencies_pip is a string representation of a list in DEFAULT_VALUES
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
    installer.install_rez()
