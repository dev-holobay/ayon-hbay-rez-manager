# Holobay Rez Manager

## Ayon Addon to manage Rez installation on each client

This is currently only working on Windows.
Other platforms need to be implemented.

The addon runs as a TrayAddon that is executed on the tray startup.
It checks the settings for the rez installation.
If the settings changed, it will automatically update the Rez installation according to the settings.
The addon will modify PATH to include the rez executables in the current environment.
This happens during tray startup, so a direct execution that circumvents the tray will not work.

The following parameters are supported:

### rez_python_version
It pulls a new python from nuget.org please check https://www.nuget.org/packages/python/3.15.0-a3#versions-body-tab
for versions there.
### rez_version
It pulls from https://github.com/AcademySoftwareFoundation/rez/archive to get a specific version.
### Dependencies
are Qt.py and PySide2/6 I have not checked all with PySide6 yet. 
If you intend to use PySide2 make sure to use the latest Python 3.10 as this is the last version where wheels are uploaded to pip.
### graphviz
is used to render failgraphs it is taken from gitlab
https://gitlab.com/api/v4/projects/4207231/packages/generic/graphviz-releases/{0}/windows_10_cmake_Release_Graphviz-{0}-win64.zip



## Rez Config

The prelaunch hook pre_set_rez_config propagates the rez_config_options.

- REZ_PACKAGES_PATH
- more to come

The prelaunch hook pre_set_rez_env merges the rez env that is based of AYON_REZ_PACKAGES defined in the application settings environment.
Thanks to [BigRoy](https://github.com/BigRoy) for the hook that really helped a ton.

![simple example](images/example.jpg)


# Future Work

- add support for other platforms
- add progress bar for rez install and updates
- add support for all rez_config options
- add ui in tray to rezify python from nuget
- add ui in tray to manage pip installations for the existing python variants
