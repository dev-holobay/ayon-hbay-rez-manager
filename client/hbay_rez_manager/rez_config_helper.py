import logging
from pathlib import Path
import os
import json

logger = logging.getLogger(__name__)


def _update_python_config(config_path, config_dict):
    """Update Python config file if JSON doesn't match existing content."""
    config_path_obj = Path(config_path)

    # Generate Python code from JSON
    python_lines = ["# Auto-generated from web config JSON\n"]
    for key, value in config_dict.items():
        python_lines.append(f"{key} = {repr(value)}\n")
    new_content = "".join(python_lines)

    # Check if file exists and content matches
    if config_path_obj.exists():
        existing_content = config_path_obj.read_text()
        if existing_content == new_content:
            logger.debug("Python config matches JSON, no update needed")
            return

    # Write updated config
    config_path_obj.write_text(new_content)
    logger.info(f"Updated Python config at {config_path}")


def manage_rez_config_from_settings(rez_config_settings):
    """Manage Rez configuration based on settings.

    This function handles the configuration of Rez based on the settings provided.
    It supports different types of configuration sources: config_file, config_web, and config_envvar.
    """

    config_type = rez_config_settings.get("config_type", "config_web")
    rez_config_path = None

    if config_type == "config_file":
        # Point to rezconfig.py in ../data/rezconfig.py
        module_dir = Path(__file__).resolve().parent
        rez_config_path = str(module_dir / "data" / "rezconfig.py")
        logger.info(f"Using config_file: {rez_config_path}")

    elif config_type == "config_web":
        # Parse JSON and create Python file in ../webconfig/rezconfig.py
        config_json = rez_config_settings.get("config_web", "")
        if config_json:
            module_dir = Path(__file__).resolve().parent
            webconfig_dir = module_dir / "webconfig"
            webconfig_dir.mkdir(exist_ok=True)
            rez_config_path = str(webconfig_dir / "rezconfig.py")

            # Parse JSON and convert to Python config
            try:
                config_dict = json.loads(config_json)
                _update_python_config(rez_config_path, config_dict)
                logger.info(f"Using config_web, generated: {rez_config_path}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config_web: {e}")
                return
        else:
            logger.warning("config_web selected but no JSON provided")
            return

    elif config_type == "config_envvar":
        # Expand environment variables in the path
        config_envvar = rez_config_settings.get("config_envvar", "")
        if config_envvar:
            rez_config_path = os.path.expandvars(config_envvar)
            logger.info(f"Using config_envvar: {rez_config_path}")
        else:
            logger.warning("config_envvar selected but no path provided")
            return
    return rez_config_path