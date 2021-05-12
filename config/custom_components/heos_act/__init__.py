"""Denon HEOS Media Player."""
import homeassistant.components.heos.__init__
from homeassistant.components.heos.__init__ import (
    ControllerManager,
    SourceManager,
    async_setup,
    async_setup_entry,
    async_unload_entry,
)

from .const import DOMAIN

homeassistant.components.heos.__init__.DOMAIN = DOMAIN
