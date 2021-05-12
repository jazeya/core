import logging
from xml.etree import ElementTree as ET

PORT = 60006
OK = 200

ACT_NS = "{urn:schemas-denon-com:service:ACT:1}"
ACT_URL = "/ACT/control"
ROOT_NS = "{http://schemas.xmlsoap.org/soap/envelope/}"

ON = "ON"
OFF = "OFF"
TOGGLE = "TOGGLE"

UP = "UP"
DOWN = "DOWN"


class DenonACT:
    def __init__(self, host, async_client_getter):
        self.host = host
        self._http_client = async_client_getter()

    async def post(self, url, ns, action, payload):
        headers = {
            "SOAPACTION": f'"{ns[1:-1]}#{action}"',
            "Content-Type": "text/xml",
        }

        response = await self._http_client.post(
            f"http://{self.host}:{PORT}{url}",
            headers=headers,
            data=ET.tostring(payload),
        )
        if response.status_code != OK:
            raise Exception("post failed")

        return ET.fromstring(response.content)

    def build_payload(self, ns, action, args):
        root_el = ET.Element(f"{ROOT_NS}Envelope")
        body_el = ET.Element(f"{ROOT_NS}Body")
        action_el = ET.Element(f"{ns}{action}")
        root_el.append(body_el)
        body_el.append(action_el)
        for arg in args:
            action_el.append(arg)

        return root_el

    async def build_and_post(self, url, ns, action, args):
        payload = self.build_payload(ns, action, args)
        return await self.post(url, ns, action, payload)

    async def get_device_power_state(self):
        ACTION = "GetDevicePowerState"

        response = await self.build_and_post(ACT_URL, ACT_NS, ACTION, [])
        power_state = response.find(f".//devicePower").text

        return power_state

    async def set_device_power_state(self, state):
        ACTION = "SetDevicePowerState"

        device_power = ET.Element("devicePower")
        device_power.text = state

        await self.build_and_post(ACT_URL, ACT_NS, ACTION, [device_power])

    async def change_external_device_volume(self, direction):
        ACTION = "ChangeExternalDeviceVolume"

        change = ET.Element("change")
        change.text = direction

        await self.build_and_post(ACT_URL, ACT_NS, ACTION, [change])

    async def change_external_device_mute(self):
        ACTION = "ChangeExternalDeviceMute"

        change = ET.Element("change")
        change.text = TOGGLE

        await self.build_and_post(ACT_URL, ACT_NS, ACTION, [change])
