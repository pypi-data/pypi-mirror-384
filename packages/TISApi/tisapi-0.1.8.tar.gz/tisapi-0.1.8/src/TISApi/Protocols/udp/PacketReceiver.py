# Import helper functions, networking components, and Home Assistant core.
from TISApi.BytesHelper import *
from socket import socket
from TISApi.Protocols.udp.PacketExtractor import PacketExtractor
from TISApi.Protocols.udp.PacketDispatcher import PacketDispatcher
import logging
from homeassistant.core import HomeAssistant


class PacketReceiver:
    """
    An asyncio Protocol class for receiving and processing UDP datagrams.

    This class is designed to be used with asyncio's create_datagram_endpoint.
    It listens for incoming packets, extracts their information, and dispatches
    them for further action.
    """

    def __init__(
        self,
        socket: socket,
        OPERATIONS_DICT: dict,
        hass: HomeAssistant,
    ):
        """Initialize the PacketReceiver."""
        self.socket = socket
        self._hass = hass  # The Home Assistant instance.

        # The dispatcher is responsible for acting on the parsed packet information
        # (e.g., firing events, setting ack signals).
        self.dispatcher = PacketDispatcher(self._hass, OPERATIONS_DICT)

        # This will hold the asyncio transport object once the connection is made.
        self.transport = None

    def connection_made(self, transport):
        """
        Callback executed by asyncio when the datagram endpoint is set up.
        """
        self.transport = transport
        logging.info("UDP connection made and listener is active.")

    def datagram_received(self, data, addr):
        """
        Callback executed by asyncio every time a UDP datagram is received.

        :param data: The raw bytes of the received packet.
        :param addr: A tuple containing the sender's (IP, port).
        """
        try:
            # Convert the raw bytes into a list of integers.
            hex_list = bytes2hex(data, [])

            # Use the PacketExtractor to parse the byte list into a structured dictionary.
            info = PacketExtractor.extract_info(hex_list)

            # --- Dispatch the packet for processing ---
            # It is crucial to schedule the dispatcher as a new task in the Home Assistant
            # event loop. This prevents the datagram_received method from blocking,
            # ensuring the receiver is always ready for the next incoming packet.
            self._hass.async_create_task(self.dispatcher.dispatch_packet(info))

        except Exception as e:
            # Catch any errors during parsing to prevent a single malformed packet
            # from crashing the entire listener.
            logging.error(f"Error processing received datagram: {e}")
