"""Config flow to configure Heos."""
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.heos.config_flow import HeosFlowHandler, format_title
from homeassistant.core import callback

from .const import (
    CONF_VOLUME_CONTROL,
    DOMAIN,
    VOLUME_CONTROL_EXTERNAL,
    VOLUME_CONTROL_INTERNAL,
)


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


class ACTHeosFlowHandler(HeosFlowHandler, domain=DOMAIN):
    """Define a flow for HEOS."""

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return OptionsFlowHandler(config_entry)
