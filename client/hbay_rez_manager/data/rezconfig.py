default_shell = "powershell"

plugins = {
    "shell": {
        "powershell": {
            "prompt": "> $ ",
            "additional_pathext": [".PY"],
            "executable_fullpath": None,
            "execution_policy": "Bypass"
        }
    }
}