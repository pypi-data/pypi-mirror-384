# Import necessary libraries and modules.
import asyncio  # For asynchronous I/O operations.
import logging  # For logging messages.
import socket  # For low-level network operations.

# Import specific components from Home Assistant core.
from homeassistant.core import HomeAssistant

# Import TIS API protocol setup and handlers.
from TISApi.Protocols import setup_udp_protocol
from TISApi.Protocols.udp.ProtocolHandler import (
    TISPacket,
    TISProtocolHandler,
)

# Import a helper dictionary that maps device types to appliances.
from .DiscoveryHelpers import DEVICE_APPLIANCES


class TISApi:
    """Manages communication with TIS devices over UDP for Home Assistant."""

    def __init__(
        self,
        port: int,
        hass: HomeAssistant,
        domain: str,
        devices_dict: dict,
        host: str = "0.0.0.0",  # Default to listen on all available network interfaces.
    ):
        """Initialize the TIS API handler."""
        # Network configuration.
        self.host = host
        self.port = port

        # Will hold the asyncio transport and protocol instances after connection.
        self.protocol = None
        self.transport = None

        # Home Assistant specific objects.
        self.hass = hass  # The Home Assistant instance.
        self.domain = domain  # The integration's domain (e.g., 'tis_control').

        # Dictionaries to hold device information.
        self.config_entries = {}
        self.devices_dict = devices_dict  # Maps device type codes to names.

        # Pre-generate the discovery packet to be broadcasted for finding devices.
        self.discovery_packet: TISPacket = (
            TISProtocolHandler.generate_discovery_packet()
        )

    async def connect(self):
        """Establish the UDP connection and start listening for devices."""
        # Initialize the data storage in Home Assistant if not already present.
        self.hass.data[self.domain] = {}

        # Use the Home Assistant event loop for asyncio operations.
        self.loop = self.hass.loop

        # Create a UDP socket.
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        try:
            # Set up the asyncio UDP protocol endpoint. This starts listening for incoming packets.
            self.transport, self.protocol = await setup_udp_protocol(
                self.sock,
                self.loop,
                self.host,
                self.port,
                self.hass,
            )
        except Exception as e:
            # Log and raise an error if the connection fails.
            logging.error("Error connecting to TIS API %s", e)
            raise ConnectionError

        # Once connected, immediately scan for devices on the network.
        await self.scan_devices()

    async def scan_devices(self, prodcast_attempts=10):
        """Scan the network for TIS devices by broadcasting a discovery packet."""
        # Clear previous discovery results to ensure a fresh scan.
        self.hass.data[self.domain]["discovered_devices"] = []

        # Broadcast the discovery packet multiple times for reliability, as UDP is connectionless.
        for _ in range(prodcast_attempts):
            await self.protocol.sender.broadcast_packet(self.discovery_packet)
            # Wait for a short period to allow devices on the network time to respond.
            await asyncio.sleep(1)

        # Process the raw data from devices that responded to the discovery broadcast.
        devices = [
            {
                "device_id": device["device_id"],
                "device_type_code": device["device_type"],
                # Look up the human-readable device name using the device type code.
                "device_type_name": self.devices_dict.get(
                    tuple(device["device_type"]), tuple(device["device_type"])
                ),
                # Format the source IP address into a standard string format (e.g., "192.168.1.10").
                "gateway": ".".join(map(str, device["source_ip"])),
            }
            # The protocol handler populates 'discovered_devices' with raw device info.
            for device in self.hass.data[self.domain]["discovered_devices"]
        ]

        # Store the formatted list of discovered devices in the Home Assistant data dictionary.
        self.hass.data[self.domain]["devices"] = devices

    async def get_entities(self, platform: str):
        """Get a list of appliances (entities) for a specific Home Assistant platform (e.g., 'light', 'switch')."""
        # Load the list of devices discovered during the scan.
        devices = self.hass.data[self.domain]["devices"]

        # Parse the device list to generate a structured dictionary of appliances.
        appliances = self.parse_saved_devices(devices)
        logging.warning(
            f"appliances for platform {platform}: {appliances.get(platform, [])}"
        )

        # Return only the appliances that match the requested platform.
        return appliances.get(platform, [])

    def parse_saved_devices(self, devices: list[dict]):
        """Convert the saved device list into a structured format usable by Home Assistant."""
        # This dictionary will be structured by platform: {'light': [...], 'switch': [...]}.
        appliances = {}

        # Iterate over each discovered device.
        for device in devices:
            # Look up what kind of entities (appliances) this device type supports.
            device_appliances = DEVICE_APPLIANCES.get(
                tuple(device["device_type_code"]), None
            )

            # If the device type is known and supports appliances...
            if device_appliances:
                # Iterate over the platforms (e.g., 'light', 'climate') supported by this device.
                for platform, count in device_appliances["appliances"].items():
                    # If this is the first time we've seen this platform, initialize an empty list.
                    if platform not in appliances:
                        appliances[platform] = []

                    # Create an entity for each channel the device has for this platform.
                    for i in range(1, count + 1):
                        appliance = {
                            "name": f"{str(device['device_id'])} {platform} channel{i}",
                            "device_id": device["device_id"],
                            "device_type_name": device["device_type_name"],
                            "gateway": device["gateway"],
                            "channels": [
                                {
                                    "Output": i,  # The specific channel number for this entity.
                                }
                            ],
                            "is_protected": False,
                        }
                        # Add the fully-formed appliance dictionary to the list for its platform.
                        appliances[platform].append(appliance)

        return appliances
