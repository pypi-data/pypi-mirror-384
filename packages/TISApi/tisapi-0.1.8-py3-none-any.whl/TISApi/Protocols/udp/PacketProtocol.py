# Import all the necessary components for the TIS protocol.
from TISApi.BytesHelper import *
from TISApi.Protocols.udp.PacketSender import PacketSender
from TISApi.Protocols.udp.PacketReceiver import PacketReceiver
from TISApi.Protocols.udp.AckCoordinator import AckCoordinator
from TISApi.shared import ack_events

# Import the specific handler functions for different types of received packets.
from .PacketHandlers.ControlResponseHandler import handle_control_response
from .PacketHandlers.DiscoveryFeedbackHandler import handle_discovery_feedback
from .PacketHandlers.UpdateResponseHandler import handle_update_response

import socket as Socket
from homeassistant.core import HomeAssistant


# --- Packet Routing Table ---
# This dictionary is the core of the packet dispatching logic. It maps a packet's
# operation code (as a tuple) to the specific function that should handle it.
# This makes the system easy to extend with new packet types.
OPERATIONS_DICT = {
    (0x00, 0x32): handle_control_response,  # Response to a control command (on/off).
    (
        0x00,
        0x0F,
    ): handle_discovery_feedback,  # A device responding to a discovery broadcast.
    (0x00, 0x34): handle_update_response,  # Response to a status update request.
}


class PacketProtocol:
    """
    The main protocol class that orchestrates the entire communication system.

    This class assembles the sender, receiver, and acknowledgement coordinator.
    It's the top-level object that asyncio's datagram endpoint interacts with,
    delegating the actual protocol logic to its specialized components.
    """

    def __init__(
        self,
        socket: Socket.socket,
        UDP_IP,
        UDP_PORT,
        hass: HomeAssistant,
    ):
        """Initializes and wires together all protocol components."""
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        self.socket = socket
        self.hass = hass

        # --- State attributes (can be used for device discovery, etc.) ---
        self.searching = False
        self.search_results = []
        self.discovered_devices = []

        # --- Instantiate the core components of the protocol ---

        # The coordinator manages asyncio.Events for matching sent packets with received acks.
        self.coordinator = AckCoordinator()

        # The sender handles the logic for sending packets, including retries and debouncing.
        self.sender = PacketSender(
            socket=self.socket,
            coordinator=self.coordinator,
            UDP_IP=self.UDP_IP,
            UDP_PORT=self.UDP_PORT,
        )

        # The receiver handles the logic for listening and parsing incoming packets.
        # It's given the OPERATIONS_DICT to know how to dispatch them.
        self.receiver = PacketReceiver(self.socket, OPERATIONS_DICT, self.hass)

        # --- Delegate asyncio's protocol methods to the receiver ---
        # This is a clean design pattern. When asyncio calls `connection_made` or
        # `datagram_received` on this PacketProtocol instance, the calls are
        # forwarded directly to the PacketReceiver, which contains the actual implementation.
        self.connection_made = self.receiver.connection_made
        self.datagram_received = self.receiver.datagram_received
