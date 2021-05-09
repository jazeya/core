from __future__ import annotations

import logging
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.const import CONF_HOST, CONF_TYPE
from homeassistant.core import callback

from .const import (
    CONF_VOLUME_CONTROL,
    DOMAIN,
    CONF_MANUFACTURER,
    CONF_MODEL,
    CONF_SERIAL_NUMBER,
    VOLUME_CONTROL_EXTERNAL,
    VOLUME_CONTROL_INTERNAL,
)
from .aios_device import DenonAIOSDevice

_LOGGER = logging.getLogger(__name__)

CONFIG_DATA_SCHEMA = vol.Schema({CONF_HOST: str})


class OptionsFlowHandler(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_VOLUME_CONTROL,
                        default=self.config_entry.options.get(
                            CONF_VOLUME_CONTROL, VOLUME_CONTROL_EXTERNAL
                        ),
                    ): vol.In([VOLUME_CONTROL_INTERNAL, VOLUME_CONTROL_EXTERNAL])
                }
            ),
        )


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)

    async def async_step_user(self, user_input=None):
        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=CONFIG_DATA_SCHEMA)

        errors = {}

        try:
            device = await self.async_step_connect(user_input[CONF_HOST])
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            return self.async_create_entry(
                title=device.name,
                data={
                    CONF_HOST: device.host,
                    CONF_TYPE: device.type,
                    CONF_MODEL: device.model,
                    CONF_MANUFACTURER: device.manufacturer,
                    CONF_SERIAL_NUMBER: device.serial,
                },
            )

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_DATA_SCHEMA, errors=errors
        )

    async def async_step_connect(self, host):
        device = DenonAIOSDevice(
            host,
            lambda: get_async_client(self.hass),
        )
        await device.setup()

        return device
