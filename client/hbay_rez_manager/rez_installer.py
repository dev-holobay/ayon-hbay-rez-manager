from __future__ import annotations
import json
import logging
import os
import platform
import re
import shutil
import subprocess
import tarfile
import tempfile
import urllib
import urllib.request
import zipfile
from pathlib import Path

import zstandard as zstd

from .constants import GRAPHVIZ_URL, REZ_URL


class RezInstaller:
    """RezInstaller class for managing Rez package install + dependencies."""
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
        self.log.info(
            "Initializing RezInstaller with settings: %s", self.__dict__
        )
        self.python = None
        self.root_folder = os.path.normpath(self.root_folder)
        self.python_folder = os.path.join(self.root_folder, "source", "python")
        self.rez_folder = os.path.join(
            self.root_folder,
            "source",
            "rez",
            f"{self.python_version}-{self.rez_version}",
        )
        self.bundle_version = f"{self.python_version}-{self.rez_version}"
        self.manifest_path = os.path.join(
            self.root_folder, "rez_installed.json"
        )
        self.installed = self.load_manifest()
        # Use platform-appropriate bin directory
        system = platform.system().lower()
        bin_dir = "Scripts" if system == "windows" else "bin"
        self.rez_path_folder = os.path.join(self.rez_folder, bin_dir, "rez")
        for i in [self.rez_folder, self.python_folder]:
            if not os.path.isdir(i):
                try:
                    os.makedirs(i, exist_ok=True)
                except OSError:
                    pass
        self.__garbage = []
        self.progress_callback = None

    def get_python(self) -> None:
        """Installs Python if not already installed."""
        # Determine Python executable path based on platform
        system = platform.system().lower()
        if system == "windows":
            python_exe = os.path.join(
                self.python_folder,
                f"python-{self.python_version}",
                "install",
                "python.exe",
            )
        else:
            python_exe = os.path.join(
                self.python_folder,
                f"python-{self.python_version}",
                "install",
                "bin",
                "python3",
            )

        if not self._should_install(
            "python_version", self.python_version
        ) or os.path.exists(python_exe):
            self.log.info(
                "Python %s already found on disk or manifest, skipping installation.",
                self.python_version,
            )
            self.python = python_exe
            if self.installed.get("python_version") != self.python_version:
                self.write_manifest("python_version", self.python_version)
            return

        try:
            target = self._get_platform_target()

            # Resolve correct URL dynamically instead of hardcoding the date tag (e.g. 20240814)
            python_build_url = self._resolve_python_build_standalone_url(
                self.python_version, target
            )

            temp_folder = tempfile.mkdtemp(prefix="python-")
            python_archive = os.path.join(
                temp_folder, "python.tar." + python_build_url.split(".")[-1]
            )

            self.log.info("Downloading Python from %s", python_build_url)
            urllib.request.urlretrieve(python_build_url, python_archive)
            self.__garbage.append(python_archive)

            self.log.info("Extracting Python to %s", self.python_folder)

            self._extract_archive(
                Path(python_archive), Path(self.python_folder)
            )

            extracted_folder = os.path.join(self.python_folder, "python")
            target_folder = os.path.join(
                self.python_folder, f"python-{self.python_version}"
            )
            if os.path.exists(extracted_folder):
                if os.path.exists(target_folder):
                    shutil.rmtree(target_folder)
                shutil.move(extracted_folder, target_folder)

            self.python = python_exe
            self.log.info("Installed Python to %s", self.python)
            self.write_manifest("python_version", self.python_version)

        except Exception as e:
            self.log.exception(e)
            self.errors.append("python install failed")

    def post_install(self) -> None:
        """Cleanup temporary files directories created during installation."""
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

    def write_manifest(self, key: str = None, value: any = None) -> None:
        """Writes or updates the manifest file."""
        manifest = self.load_manifest() or {}

        if key and value:
            manifest[key] = value
        else:
            # Fallback to full write if no specific key provided
            manifest.update(
                {
                    "rez_version": self.rez_version,
                    "python_version": self.python_version,
                    "graphviz_version": self.graphviz_version,
                    "dependencies": self.dependencies,
                }
            )

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

            self.log.info(
                "Manifest updated for %s: %s",
                self.bundle_version,
                key if key else "all",
            )
            # Update local cache
            self.installed = manifest

        except Exception as e:
            self.log.error("Failed to write manifest: %s", e)

    def load_manifest(self) -> dict | None:
        """Loads the manifest file for the current bundle version."""
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
            "Checking if requested configuration matches installed manifest."
        )
        return (
            self.installed.get("rez_version") == self.rez_version
            and self.installed.get("python_version") == self.python_version
            and self.installed.get("graphviz_version") == self.graphviz_version
            and set(self.installed.get("dependencies", []))
            == set(self.dependencies)
        )

    def run(self):
        self.errors = []
        try:
            if self.progress_callback:
                self.progress_callback(0, "Getting Python")
            self.get_python()
            if "python install failed" in self.errors:
                raise RuntimeError("Python installation failed")

            if self.progress_callback:
                self.progress_callback(20, "Getting Rez")
            rez_zip = self.download_rez()

            if self.progress_callback:
                self.progress_callback(40, "Installing Rez")
            self.install_rez(rez_zip)
            if (
                not self.installed.get("rez_version") == self.rez_version
                and rez_zip is not None
            ):
                raise RuntimeError("Rez installation failed")

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
        except Exception as e:
            self.log.exception("Installation failed: %s", e)
            raise

    def download_rez(self) -> str | None:
        """Downloads Rez from GitHub and returns the path to the zip file."""
        if not self._should_install("rez_version", self.rez_version):
            self.log.info(
                "Rez %s already downloaded/installed, skipping download.",
                self.rez_version,
            )
            return None

        temp_folder = tempfile.mkdtemp(prefix="python-")
        rez_temp = os.path.join(temp_folder, f"{self.rez_version}.zip")
        self.log.info("Downloading Rez to temporary path")
        urllib.request.urlretrieve(REZ_URL.format(self.rez_version), rez_temp)
        self.__garbage.append(rez_temp)
        self.log.debug(rez_temp)
        self.log.info("Downloaded Rez")
        return rez_temp

    def install_rez(self, archive: str) -> None:
        """Installs Rez from the provided zip file."""
        if archive is None:
            return

        temp_folder = tempfile.mkdtemp(prefix="rez-temp-")
        with zipfile.ZipFile(archive, "r") as zip_ref:
            zip_ref.extractall(temp_folder)
        self.__garbage.append(temp_folder)
        self.log.info("Installing Rez...")
        try:
            cmd = [
                self.python,
                os.path.join(
                    temp_folder, f"rez-{self.rez_version}", "install.py"
                ),
                "-v",
                self.rez_folder,
            ]
            self.log.debug(" ".join(cmd))

            # On macOS, clear PYTHONHOME and PYTHONPATH to avoid interference
            # with the installer script.
            env = os.environ.copy()
            env.pop("PYTHONHOME", None)
            env.pop("PYTHONPATH", None)

            # Add DYLD_LIBRARY_PATH for Rez installation to help find libpython
            system = platform.system().lower()
            if system == "darwin":
                actual_lib_path = os.path.join(
                    self.python_folder,
                    f"python-{self.python_version}",
                    "install",
                    "lib",
                )
                env["DYLD_LIBRARY_PATH"] = actual_lib_path + (
                    ":" + env.get("DYLD_LIBRARY_PATH", "")
                    if env.get("DYLD_LIBRARY_PATH")
                    else ""
                )

            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True,
                env=env,
            )
            self.log.debug(result.stdout)
            if result.stderr:
                self.log.warning(result.stderr)

            if system != "windows":
                lib_path = os.path.join(
                    os.path.dirname(self.python), "..", "lib"
                )
                if os.path.exists(lib_path):
                    files = os.listdir(lib_path)
                    dylibs = [
                        f for f in files if f.endswith((".dylib", ".so"))
                    ]
                    if dylibs:
                        for dylib in dylibs:
                            shutil.copy(
                                os.path.join(lib_path, dylib),
                                os.path.join(self.rez_folder, "lib"),
                            )
                            self.log.info(
                                f"Copied {dylib} to {self.rez_folder}"
                            )

        except subprocess.CalledProcessError as e:
            self.log.error(f"Command failed with exit code {e.returncode}")
            self.log.error(f"stdout: {e.stdout}")
            self.log.error(f"stderr: {e.stderr}")
            self.log.exception(e)
        except Exception as e:
            self.log.exception(e)
        else:
            self.log.info("Successfully installed Rez to %s", self.rez_folder)
            self.write_manifest("rez_version", self.rez_version)

    def get_additional_packages(self) -> None:
        """Installs additional dependencies using pip."""
        if not self._should_install("dependencies", self.dependencies):
            self.log.info("Dependencies already match manifest, skipping.")
            return

        # Determine pip path based on platform
        system = platform.system().lower()
        if system == "windows":
            pip_exe = os.path.join(self.rez_folder, "Scripts", "pip.exe")
        else:
            pip_exe = os.path.join(self.rez_folder, "bin", "pip")

        for package in self.dependencies:
            try:
                self.log.info("Installing %s ...", package)
                # Use list-style cmd to avoid shell issues and better handle paths with spaces
                cmd = [pip_exe, "install", package]

                # Similar to Rez installation, clean environment for pip
                env = os.environ.copy()
                env.pop("PYTHONHOME", None)
                env.pop("PYTHONPATH", None)

                # Add the library path to DYLD_LIBRARY_PATH on macOS to help pip
                if system == "darwin":
                    # Use actual lib path
                    actual_lib_path = os.path.join(
                        self.python_folder,
                        f"python-{self.python_version}",
                        "install",
                        "lib",
                    )
                    env["DYLD_LIBRARY_PATH"] = actual_lib_path + (
                        ":" + env.get("DYLD_LIBRARY_PATH", "")
                        if env.get("DYLD_LIBRARY_PATH")
                        else ""
                    )

                subprocess.run(
                    cmd,
                    env=env,
                    check=True,
                    capture_output=True,
                )
            except Exception as e:
                self.log.exception(e)
            else:
                self.log.info("Successfully installed %s", package)
        self.write_manifest("dependencies", self.dependencies)

    def get_graphviz(self) -> str | None:
        """Downloads Graphviz from GitHub and returns the path to the zip file."""
        if not self._should_install("graphviz_version", self.graphviz_version):
            self.log.info(
                "Graphviz %s already installed, skipping.",
                self.graphviz_version,
            )
            return None

        system = platform.system().lower()
        if system != "windows":
            self.log.info(
                "Skipping Graphviz installation on non-Windows platform."
            )
            self.write_manifest("graphviz_version", self.graphviz_version)
            return None

        temp_folder = tempfile.mkdtemp(prefix="graphviz-")
        temp = os.path.join(temp_folder, "graphviz.zip")
        self.log.info(
            "Downloading Graphviz to temporary path from %s",
            GRAPHVIZ_URL.format(self.graphviz_version),
        )
        urllib.request.urlretrieve(
            GRAPHVIZ_URL.format(self.graphviz_version), temp
        )
        self.__garbage.append(temp)
        self.log.debug(temp)
        temp_folder = tempfile.mkdtemp(prefix="rez-temp-")
        self.log.info("Installing Graphviz ...")
        with zipfile.ZipFile(temp, "r") as zip_ref:
            zip_ref.extractall(temp_folder)

        graphviz_bin_dir = os.path.join(
            temp_folder, f"Graphviz-{self.graphviz_version}-win64", "bin"
        )

        if not os.path.isdir(graphviz_bin_dir):
            self.log.error(
                f"Graphviz bin directory not found: {graphviz_bin_dir}"
            )
            return None

        file_names = os.listdir(graphviz_bin_dir)

        # Ensure the destination Scripts/rez directory exists
        dest_dir = os.path.join(self.rez_folder, "Scripts", "rez")
        os.makedirs(dest_dir, exist_ok=True)

        for file_name in file_names:
            shutil.move(
                os.path.join(graphviz_bin_dir, file_name),
                dest_dir,
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

    @staticmethod
    def _get_platform_target() -> str:
        """Get the python-build-standalone platform target string."""
        system = platform.system().lower()
        machine = platform.machine().lower()

        # Normalize arch
        arch_map = {
            "amd64": "x86_64",
            "x86_64": "x86_64",
            "arm64": "aarch64",
            "aarch64": "aarch64",
        }
        arch = arch_map.get(machine, machine)

        # python-build-standalone naming convention
        platform_map = {
            ("windows", "x86_64"): "x86_64-pc-windows-msvc",
            ("linux", "x86_64"): "x86_64-unknown-linux-gnu",
            ("linux", "aarch64"): "aarch64-unknown-linux-gnu",
            ("darwin", "x86_64"): "x86_64-apple-darwin",
            ("darwin", "aarch64"): "aarch64-apple-darwin",
        }

        target = platform_map.get((system, arch))
        if not target:
            raise RuntimeError(f"Unsupported platform: {system} {arch}")
        return target

    @staticmethod
    def _github_json(url: str) -> dict:
        """Fetch JSON from GitHub API (no auth)."""
        req = urllib.request.Request(
            url,
            headers={
                "Accept": "application/vnd.github+json",
                "User-Agent": "hbay-rez-manager",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))

    def _resolve_python_build_standalone_url(
        self, python_version: str, target: str
    ) -> str:
        """
        Resolve a python-build-standalone asset URL dynamically.

        We search GitHub releases and pick the first asset matching:
          cpython-<version>+<tag>-<target>-install_only.tar.gz
        """
        wanted = re.compile(
            rf"^cpython-{re.escape(python_version)}\+\d{{8}}-{re.escape(target)}-(pgo\+lto-full|pgo-full)\.tar\.(gz|zst)$"
        )
        self.log.info("%s", wanted)
        "cpython-3.12.12+20251202-x86_64-pc-windows-msvc-pgo-full.tar.zst"
        # GitHub API: list releases (newest first)
        releases = self._github_json(
            "https://api.github.com/repos/astral-sh/python-build-standalone/releases?per_page=20"
        )
        for rel in releases:
            for asset in rel.get("assets", []):
                name = asset.get("name", "")
                self.log.debug(f"Checking asset: {name}")
                if wanted.match(name):
                    url = asset.get("browser_download_url")
                    if url:
                        return url

        raise RuntimeError(
            f"Could not find python-build-standalone asset for "
            f"python={python_version}, target={target}. "
            f"The requested version may not be published for this platform yet."
        )

    @staticmethod
    def _extract_archive(archive_path: Path, dest: Path) -> None:
        if archive_path.suffix == ".zst" or archive_path.name.endswith(
            ".tar.zst"
        ):
            with open(archive_path, "rb") as fh:
                dctx = zstd.ZstdDecompressor()
                with dctx.stream_reader(fh) as reader:
                    with tarfile.open(fileobj=reader, mode="r|") as tar:
                        tar.extractall(dest)
        else:
            with tarfile.open(archive_path, "r:gz") as tar:
                tar.extractall(dest)
