from __future__ import annotations
from functools import wraps
import logging

from homeassistant.const import (
    STATE_OFF,
    STATE_ON,
    STATE_IDLE,
    STATE_PAUSED,
    STATE_PLAYING,
)

from homeassistant.components.media_player import (
    DEVICE_CLASS_RECEIVER,
    MediaPlayerEntity,
)
from homeassistant.components.media_player.const import (
    MEDIA_TYPE_MUSIC,
    MEDIA_TYPE_PLAYLIST,
    SUPPORT_STOP,
    SUPPORT_PAUSE,
    SUPPORT_PLAY,
    SUPPORT_NEXT_TRACK,
    SUPPORT_PREVIOUS_TRACK,
    SUPPORT_TURN_OFF,
    SUPPORT_TURN_ON,
    SUPPORT_VOLUME_MUTE,
    SUPPORT_VOLUME_STEP,
)

from .aios_device import (
    DenonAIOSDevice,
    PAUSED,
    PLAYING,
    STOPPED,
    TRANSITIONING,
    UP,
    DOWN,
    ON,
    OFF,
    PLAY,
    STOP,
    PAUSE,
    NEXT,
    PREVIOUS,
)
from .const import CONF_VOLUME_CONTROL, DOMAIN, CONF_DEVICE, VOLUME_CONTROL_EXTERNAL

_LOGGER = logging.getLogger(__name__)

states_map = {
    PLAYING: STATE_PLAYING,
    PAUSED: STATE_PAUSED,
    STOPPED: STATE_IDLE,
}

playback_controls_map = {
    PLAY: SUPPORT_PLAY,
    PAUSE: SUPPORT_PAUSE,
    STOP: SUPPORT_STOP,
    NEXT: SUPPORT_NEXT_TRACK,
    PREVIOUS: SUPPORT_PREVIOUS_TRACK,
}


async def async_setup_entry(hass, entry, async_add_entities):

    data = hass.data[DOMAIN][entry.entry_id]
    device = data[CONF_DEVICE]

    async_add_entities([DenonMediaPlayerEntity(entry, device)])


class DenonMediaPlayerEntity(MediaPlayerEntity):
    def __init__(self, entry, device):

        self._entry = entry
        self._device = device
        self._is_available = False
        self._state = DenonAIOSDevice.State()
        self._power_state = None
        self._is_volume_muted = False

    def async_log_errors(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                result = await func(self, *args, **kwargs)
                self._is_available = True
                return result
            except Exception as e:
                _LOGGER.exception("operation failed. \n%s" % e)
                self._is_available = False

        return wrapper

    @property
    def name(self):
        return self._device.name

    @property
    def unique_id(self):
        return self._device.serial

    @property
    def supported_features(self):
        playback_controls = 0
        for current_transport_action in self._state.current_transport_actions:
            playback_controls |= playback_controls_map.get(current_transport_action, 0)

        return (
            SUPPORT_TURN_ON
            | SUPPORT_TURN_OFF
            | SUPPORT_VOLUME_STEP
            | SUPPORT_VOLUME_MUTE
            | playback_controls
        )

    @property
    def device_class(self):
        return DEVICE_CLASS_RECEIVER

    @property
    def media_content_type(self):
        return MEDIA_TYPE_MUSIC

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._device.serial)},
            "name": self._device.name,
            "manufacturer": self._device.manufacturer,
            "model": self._device.model,
        }

    @property
    def is_available(self):
        return self._is_available

    @property
    def is_volume_muted(self):
        return self._is_volume_muted

    @property
    def state(self):
        if self._power_state == OFF:
            return STATE_OFF
        return states_map.get(self._state.transport_state)

    @property
    def media_image_url(self):
        return self._state.album_art_uri

    @property
    def media_title(self):
        return self._state.title

    @property
    def media_artist(self):
        return self._state.artist

    @async_log_errors
    async def async_turn_on(self, **kwargs):
        await self._device.set_device_power_state(ON)

    @async_log_errors
    async def async_turn_off(self, **kwargs):
        await self._device.set_device_power_state(OFF)

    @async_log_errors
    async def async_volume_up(self):
        await self.change_volume(UP)

    @async_log_errors
    async def async_volume_down(self):
        await self.change_volume(DOWN)

    async def change_volume(self, direction):
        if self._entry.options.get(CONF_VOLUME_CONTROL) == VOLUME_CONTROL_EXTERNAL:
            await self._device.change_external_device_volume(direction)
        else:
            _LOGGER.warn("not implemented")

    @async_log_errors
    async def async_mute_volume(self, mute):
        if self._entry.options.get(CONF_VOLUME_CONTROL) == VOLUME_CONTROL_EXTERNAL:
            await self._device.change_external_device_mute()
            self._is_volume_muted = mute
        else:
            _LOGGER.warn("not implemented")

    @async_log_errors
    async def async_media_play(self):
        await self._device.play()

    @async_log_errors
    async def async_media_pause(self):
        await self._device.pause()

    @async_log_errors
    async def async_media_previous_track(self):
        await self._device.previous()

    @async_log_errors
    async def async_media_next_track(self):
        await self._device.next()

    @async_log_errors
    async def async_update(self, **kwargs):
        self._power_state = await self._device.get_device_power_state()
        state: DenonAIOSDevice.State = await self._device.get_current_state()
        if state.transport_state != TRANSITIONING:
            self._state = state

    async_log_errors = staticmethod(async_log_errors)
