"""Services for the ACT HEOS integration."""
import homeassistant.components.heos.services

from homeassistant.components.heos.services import (
    register,
    remove,
    _sign_in_handler,
    _sign_out_handler,
)

from .const import DOMAIN

homeassistant.components.heos.services.DOMAIN = DOMAIN
