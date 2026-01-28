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
            logger: logging.Logger = None,
    ):
        self.log = logger or logging.getLogger(self.__class__.__name__)
        self.root_folder = root
        self.rez_version = rez_version
        self.python_version = python_version
        self.graphviz_version = graphviz_version
        self.dependencies = dependencies
        self.log.info("Initializing RezInstaller with settings: %s",
                      self.__dict__)
        self.python = None
        if os.name == "nt":
            self.root_folder = self.root_folder.replace("/", "\\")
        self.python_folder = os.path.join(self.root_folder, "source", "python")
        self.rez_folder = os.path.join(
            self.root_folder, "source", "rez",
            f"{self.python_version}-{self.rez_version}"
        )
        self.bundle_version = f"{self.python_version}-{self.rez_version}"
        self.manifest_path = os.path.join(self.root_folder,
                                          "rez_installed.json")
        self.installed = self.load_manifest()
        self.rez_path_folder = os.path.join(self.rez_folder, "Scripts", "rez")
        for i in [self.rez_folder, self.python_folder]:
            if not os.path.isdir(i):
                try:
                    os.makedirs(i, exist_ok=True)
                except WindowsError:
                    pass
        self.__garbage = []
        self.progress_callback = None

    def get_python(self):
        python_exe = os.path.join(
            self.python_folder,
            f"python.{self.python_version}",
            "tools",
            "python.exe",
        )
        if not self._should_install("python_version",
                                    self.python_version) or os.path.exists(
            python_exe):
            self.log.info(
                "Python %s already found on disk or manifest, skipping installation.",
                self.python_version)
            self.python = python_exe
            # Ensure the current manifest entry is updated if it was missing
            if self.installed.get("python_version") != self.python_version:
                self.write_manifest("python_version", self.python_version)
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
            self.log.info(" ".join(cmd))
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
            self.write_manifest("python_version", self.python_version)

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

    def write_manifest(self, key: str = None, value: any = None):
        """Writes or updates the manifest file."""
        manifest = self.load_manifest() or {}

        if key and value:
            manifest[key] = value
        else:
            # Fallback to full write if no specific key provided
            manifest.update({
                "rez_version": self.rez_version,
                "python_version": self.python_version,
                "graphviz_version": self.graphviz_version,
                "dependencies": self.dependencies,
            })

        try:
            # Load the full file content first, not just the bundle-specific part
            full_manifest_data = {}
            if os.path.exists(self.manifest_path):
                with open(self.manifest_path, "r") as f:
                    try:
                        full_manifest_data = json.load(f)
                    except json.JSONDecodeError:
                        full_manifest_data = {}

            # Update ONLY the current bundle's entry within the full data
            full_manifest_data[self.bundle_version] = manifest

            with open(self.manifest_path, "w") as f:
                json.dump(full_manifest_data, f, indent=4)

            self.log.info("Manifest updated for %s: %s", self.bundle_version,
                          key if key else "all")
            # Update local cache
            self.installed = manifest

        except Exception as e:
            self.log.error("Failed to write manifest: %s", e)

    def load_manifest(self):
        if not os.path.exists(self.manifest_path):
            return None
        try:
            with open(self.manifest_path, "r") as f:
                data = json.load(f)
                return data.get(self.bundle_version, {})
        except Exception as e:
            self.log.error("Failed to load manifest: %s", e)
            return None

    def check_if_installed(self) -> bool:
        """Checks if the requested configuration matches the installed manifest."""

        if self.installed is None:
            return False
        self.log.debug(
            "Checking if requested configuration matches installed manifest.")
        return (
                self.installed.get("rez_version") == self.rez_version and
                self.installed.get("python_version") == self.python_version and
                self.installed.get(
                    "graphviz_version") == self.graphviz_version and
                set(self.installed.get("dependencies", [])) == set(
            self.dependencies)
        )

    def run(self):
        self.errors = []
        if self.progress_callback:
            self.progress_callback(0, "Getting Python")
        self.get_python()

        if self.progress_callback:
            self.progress_callback(20, "Getting Rez")
        rez_zip = self.get_rez()

        if self.progress_callback:
            self.progress_callback(40, "Installing Rez")
        self.setup_rez(rez_zip)

        if self.progress_callback:
            self.progress_callback(60, "Getting Additional Dependencies")
        self.get_additional_packages()

        if self.progress_callback:
            self.progress_callback(80, "Getting Graphviz")
        self.get_graphviz()

        if self.progress_callback:
            self.progress_callback(90, "Cleanup")
        self.post_install()

        if self.progress_callback:
            self.progress_callback(100, "Done")

    def get_rez(self):
        if not self._should_install("rez_version", self.rez_version):
            self.log.info(
                "Rez %s already downloaded/installed, skipping download.",
                self.rez_version)
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
            self.write_manifest("rez_version", self.rez_version)

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
        self.write_manifest("dependencies", self.dependencies)

    def get_graphviz(self):
        if not self._should_install("graphviz_version", self.graphviz_version):
            self.log.info("Graphviz %s already installed, skipping.",
                          self.graphviz_version)
            return None

        temp_folder = tempfile.mkdtemp(prefix="graphviz-")
        temp = os.path.join(temp_folder, "graphviz.zip")
        self.log.info("Downloading Graphviz to temporary path from %s",
                      GRAPHVIZ_URL.format(self.graphviz_version))
        urllib.request.urlretrieve(
            GRAPHVIZ_URL.format(self.graphviz_version), temp
        )
        self.__garbage.append(temp)
        self.log.debug(temp)
        temp_folder = tempfile.mkdtemp(prefix="rez-temp-")
        self.log.info("Installing Graphviz ...")
        with zipfile.ZipFile(temp, "r") as zip_ref:
            zip_ref.extractall(temp_folder)
        file_names = os.listdir(
            os.path.join(temp_folder, f"Graphviz-{self.graphviz_version}-win64",
                         "bin"))
        for file_name in file_names:
            shutil.move(
                os.path.join(temp_folder,
                             f"Graphviz-{self.graphviz_version}-win64", "bin",
                             file_name),
                os.path.join(self.rez_folder, "Scripts", "rez"),
            )
        self.__garbage.append(temp_folder)
        self.log.info("Installed Graphviz")
        self.write_manifest("graphviz_version", self.graphviz_version)
        return temp

    def _should_install(self, key: str, requested_value: any) -> bool:
        """Internal check to see if a specific component needs installation."""
        if not self.installed:
            return True

        if key == "dependencies":
            return set(self.installed.get(key, [])) != set(requested_value)

        return self.installed.get(key) != requested_value
