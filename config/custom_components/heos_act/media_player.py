"""Denon ACT HEOS Media Player."""
from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

import homeassistant.components.heos.media_player
from homeassistant.components.heos.media_player import (
    HeosMediaPlayer,
    log_command_error,
)
from homeassistant.components.media_player.const import (
    DOMAIN,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_SET,
    SUPPORT_VOLUME_STEP,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, STATE_OFF
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client

from .act import DOWN, OFF, ON, UP, DenonACT
from .const import (
    CONF_VOLUME_CONTROL,
    DOMAIN as HEOS_DOMAIN,
    VOLUME_CONTROL_EXTERNAL,
    VOLUME_CONTROL_INTERNAL,
)

homeassistant.components.heos.media_player.HEOS_DOMAIN = HEOS_DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    """Add media players for a config entry."""
    host = entry.data[CONF_HOST]
    denon_act = DenonACT(host, lambda: get_async_client(hass))
    volume_control = entry.options.get(CONF_VOLUME_CONTROL)

    players = hass.data[HEOS_DOMAIN][DOMAIN]
    devices = [
        ACTHeosMediaPlayer(player, denon_act, volume_control)
        for player in players.values()
    ]
    async_add_entities(devices, True)


class ACTHeosMediaPlayer(HeosMediaPlayer):
    """The HEOS with ACT support player."""

    def __init__(self, player, denon_act, volume_control):
        """Initialize."""
        super().__init__(player)
        self._denon_act = denon_act
        self._power_state = None
        self._volume_control = volume_control

    @log_command_error("turn on")
    async def async_turn_on(self):
        await self._denon_act.set_device_power_state(ON)

    @log_command_error("turn off")
    async def async_turn_off(self):
        await self._denon_act.set_device_power_state(OFF)

    @log_command_error("volume up")
    async def async_volume_up(self):
        if self._volume_control == VOLUME_CONTROL_EXTERNAL:
            await self._denon_act.change_external_device_volume(UP)
        else:
            await self._player.volume_up()

    @log_command_error("volume down")
    async def async_volume_down(self):
        if self._volume_control == VOLUME_CONTROL_EXTERNAL:
            await self._denon_act.change_external_device_volume(DOWN)
        else:
            await self._player.volume_down()

    async def async_update(self):
        """Update supported features of the player."""
        await super().async_update()

        entry = self.hass.config_entries.async_entries(HEOS_DOMAIN)[0]
        self._volume_control = entry.options.get(
            CONF_VOLUME_CONTROL, VOLUME_CONTROL_INTERNAL
        )
        self._power_state = await self._denon_act.get_device_power_state()

    @property
    def should_poll(self) -> bool:
        """No polling needed for this device while it's ON."""
        return self._power_state != ON

    @property
    def state(self) -> str:
        """State of the player."""
        if self._power_state == OFF:
            return STATE_OFF
        return super().state

    @property
    def supported_features(self) -> int:
        """Flag media player features that are supported."""
        supported_features = self._supported_features
        supported_features |= SUPPORT_TURN_ON | SUPPORT_TURN_OFF
        if self._volume_control == VOLUME_CONTROL_EXTERNAL:
            supported_features ^= SUPPORT_VOLUME_SET
            supported_features |= SUPPORT_VOLUME_STEP

        return supported_features
