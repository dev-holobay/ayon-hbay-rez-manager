"""Server package."""
from typing import Type

from ayon_server.addons import BaseServerAddon

from .settings import DEFAULT_VALUES, RezManagerSettings


class RezManagerAddon(BaseServerAddon):
    """Add-on class for the server."""
    settings_model: Type[RezManagerSettings] = RezManagerSettings

    async def get_default_settings(self) -> RezManagerSettings:
        """Return default settings."""
        settings_model_cls = self.get_settings_model()
        return settings_model_cls(**DEFAULT_VALUES)
