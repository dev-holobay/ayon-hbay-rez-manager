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
        for i in [self.rez_folder, self.python_folder]:
            if not os.path.isdir(i):
                try:
                    os.makedirs(i, exist_ok=True)
                except WindowsError:
                    pass
        self.__garbage = []

    def get_python(self):
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

    def install_rez(self):
        self.errors = []
        self.get_python()
        rez_zip = self.get_rez()
        self.setup_rez(rez_zip)
        self.get_additional_packages()
        self.get_graphviz()
        self.post_install()

    def get_rez(self):
        temp_folder = tempfile.mkdtemp(prefix="python-")
        rez_temp = os.path.join(temp_folder, f"{self.rez_version}.zip")
        self.log.info("Downloading Rez to temporary path")
        urllib.request.urlretrieve(REZ_URL.format(self.rez_version), rez_temp)
        self.__garbage.append(rez_temp)
        self.log.debug(rez_temp)
        self.log.info("Downloaded Rez")
        return rez_temp

    def setup_rez(self, archive:str):
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
        """ "D:\\p4test\\PIPELINE\rez\\source\rez\2.112.0\\Scripts\\pip.exe" """
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
