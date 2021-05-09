import httpx
import asyncio
from xml.etree import ElementTree as ET

from aios_device import DenonAIOSDevice

client = httpx.AsyncClient()
loop = asyncio.get_event_loop()

device = DenonAIOSDevice("192.168.1.41", lambda: client)
result = loop.run_until_complete(device.get_current_state())
print(result)

loop.run_until_complete(client.aclose())
loop.close()
