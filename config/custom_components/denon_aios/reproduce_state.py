import asyncio
import logging

from typing import Iterable, Optional
from homeassistant.core import Context, HomeAssistant, State

_LOGGER = logging.getLogger(__name__)


async def async_reproduce_states(
    hass: HomeAssistant, states: Iterable[State], context: Optional[Context] = None
) -> None:
    """Reproduce component states."""
    # TODO reproduce states
