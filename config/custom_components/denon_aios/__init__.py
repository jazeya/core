from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.const import CONF_HOST

from .aios_device import DenonAIOSDevice
from .const import DOMAIN, CONF_DEVICE

PLATFORMS = ["media_player"]


async def async_setup_entry(hass, entry) -> bool:
    hass.data.setdefault(DOMAIN, {})

    device = DenonAIOSDevice(
        entry.data[CONF_HOST],
        lambda: get_async_client(hass),
    )
    await device.setup()
    hass.data[DOMAIN][entry.entry_id] = {CONF_DEVICE: device}

    for component in PLATFORMS:
        hass.async_create_task(
            hass.config_entries.async_forward_entry_setup(entry, component)
        )
    return True
