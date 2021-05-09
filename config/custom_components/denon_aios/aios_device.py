import logging
from xml.etree import ElementTree as ET
from dataclasses import dataclass, field
from typing import List

_LOGGER = logging.getLogger(__name__)

PORT = 60006
OK = 200

DEVICE_URL = "/upnp/desc/aios_device/aios_device.xml"
DEVICE_NS = "{urn:schemas-upnp-org:device-1-0}"

ACT_NS = "{urn:schemas-denon-com:service:ACT:1}"
ACT_URL = "/ACT/control"

AVTRANSPORT_NS = "{urn:schemas-upnp-org:service:AVTransport:1}"
AVTRANSPORT_URL = "/upnp/control/renderer_dvc/AVTransport"

AVT_NS = "{urn:schemas-upnp-org:metadata-1-0/AVT/}"
DIDL_LITE_NS = "{urn:schemas-upnp-org:metadata-1-0/DIDL-Lite/}"
DC_NS = "{http://purl.org/dc/elements/1.1/}"
UPNP_NS = "{urn:schemas-upnp-org:metadata-1-0/upnp/}"

UP = "UP"
DOWN = "DOWN"

ON = "ON"
OFF = "OFF"
TOGGLE = "TOGGLE"

PLAYING = "PLAYING"
PAUSED = "PAUSED_PLAYBACK"
STOPPED = "STOPPED"
TRANSITIONING = "TRANSITIONING"

PLAY = "Play"
PAUSE = "Pause"
STOP = "Stop"
NEXT = "Next"
PREVIOUS = "Previous"


class DenonAIOSDevice:
    def __init__(self, host, async_client_getter):
        self.host = host
        self._http_client = async_client_getter()

    @dataclass
    class State:
        transport_state: str = ""
        current_transport_actions: list = field(default_factory=list)
        title: str = ""
        artist: str = ""
        album_art_uri: str = ""

    async def get(self, url):
        response = await self._http_client.get(f"http://{self.host}:{PORT}{url}")
        if response.status_code != OK:
            raise Exception("get failed")

        return ET.fromstring(response.content)

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
        ROOT_NS = "{http://schemas.xmlsoap.org/soap/envelope/}"

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

    async def setup(self):
        response = await self.get(DEVICE_URL)

        device_el = response.find(f"./{DEVICE_NS}device")
        self.serial = device_el.find(f"./{DEVICE_NS}serialNumber").text
        self.model = device_el.find(f"./{DEVICE_NS}modelName").text
        self.manufacturer = device_el.find(f"./{DEVICE_NS}manufacturer").text
        self.type = device_el.find(f"./{DEVICE_NS}deviceType").text
        self.name = device_el.find(f"./{DEVICE_NS}friendlyName").text

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

    async def get_current_state(self):
        ACTION = "GetCurrentState"

        def parse_event(root):
            current_state_el = root.find(f".//CurrentState")
            return ET.fromstring(current_state_el.text)

        def parse_current_transport_actions(event_el):
            current_transport_actions_el = event_el.find(
                f".//{AVT_NS}CurrentTransportActions"
            )
            return current_transport_actions_el.attrib["val"].split(",")

        def parse_transport_state(event_el):
            transport_state_el = event_el.find(f".//{AVT_NS}TransportState")
            return transport_state_el.attrib["val"]

        def parse_didl_lite(event_el):
            current_track_metadata_el = event_el.find(
                f".//{AVT_NS}CurrentTrackMetaData"
            )
            return ET.fromstring(current_track_metadata_el.attrib["val"])

        def parse_title(didl_lite_el):
            return didl_lite_el.find(f".//{DC_NS}title").text

        def parse_artist(didl_lite_el):
            return didl_lite_el.find(f".//{UPNP_NS}artist").text

        def parse_album_art_uri(didl_lite_el):
            return didl_lite_el.find(f".//{UPNP_NS}albumArtURI").text

        response = await self.build_and_post(
            AVTRANSPORT_URL, AVTRANSPORT_NS, ACTION, []
        )

        event_el = parse_event(response)
        transport_state = parse_transport_state(event_el)
        current_transport_actions = parse_current_transport_actions(event_el)

        didl_lite_el = parse_didl_lite(event_el)
        title = parse_title(didl_lite_el).strip('"')
        artist = parse_artist(didl_lite_el).strip('"')
        album_art_uri = parse_album_art_uri(didl_lite_el).strip('"')

        return DenonAIOSDevice.State(
            transport_state, current_transport_actions, title, artist, album_art_uri
        )

    async def play(self):
        ACTION = "Play"

        await self.build_and_post(AVTRANSPORT_URL, AVTRANSPORT_NS, ACTION, [])

    async def pause(self):
        ACTION = "Pause"

        await self.build_and_post(AVTRANSPORT_URL, AVTRANSPORT_NS, ACTION, [])

    async def previous(self):
        ACTION = "Previous"

        await self.build_and_post(AVTRANSPORT_URL, AVTRANSPORT_NS, ACTION, [])

    async def next(self):
        ACTION = "Next"

        await self.build_and_post(AVTRANSPORT_URL, AVTRANSPORT_NS, ACTION, [])
