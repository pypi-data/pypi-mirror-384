"""Class for handling the UDP protocol"""

# Import helper functions and type hints.
from ...BytesHelper import build_packet
from typing import List


class TISPacket:
    """
    A data class representing a single TIS network packet.

    This class encapsulates all the necessary information for a TIS command
    and builds the raw byte representation upon initialization.

    :param device_id: List of integers representing the target device ID.
    :param operation_code: List of integers representing the command's operation code.
    :param source_ip: Source IP address as a string.
    :param destination_ip: Destination IP address as a string.
    :param additional_bytes: Optional list of additional bytes for the command payload.
    """

    def __init__(
        self,
        device_id: List[int],
        operation_code: List[int],
        source_ip: str,
        destination_ip: str,
        additional_bytes: List[int] = None,
    ):
        # Ensure additional_bytes is an empty list if not provided, avoiding mutable default arguments.
        if additional_bytes is None:
            additional_bytes = []

        # Store the packet's components as instance attributes.
        self.device_id = device_id
        self.operation_code = operation_code
        self.source_ip = source_ip
        self.destination_ip = destination_ip
        self.additional_bytes = additional_bytes

        # --- Build the raw packet ---
        # The final byte array for the packet is constructed immediately when the object is created.
        self._packet = build_packet(
            ip_address=self.source_ip,
            device_id=self.device_id,
            operation_code=self.operation_code,
            additional_bytes=self.additional_bytes,
        )

    def __str__(self) -> str:
        """Return a user-friendly string representation of the packet."""
        return f"Packet: {self._packet}"

    def __repr__(self) -> str:
        """Return a developer-friendly, unambiguous string representation of the packet."""
        return f"Packet: {self._packet}"

    def __bytes__(self) -> bytes:
        """Allow the object to be cast directly to bytes, for sending over a network socket."""
        return bytes(self._packet)


class TISProtocolHandler:
    """
    A handler class with static methods to generate specific TIS packets.
    This class acts as a factory and is not intended to be instantiated.
    """

    # --- Protocol Operation Codes ---
    # These constants define the specific codes for different TIS commands.
    OPERATION_CONTROL = [0x00, 0x31]  # General control command (e.g., on/off).
    OPERATION_DISCOVERY = [0x00, 0x0E]  # Command to discover devices on the network.
    OPERATION_CONTROL_UPDATE = [0x00, 0x33]  # Command to request a status update.

    @staticmethod
    def generate_control_on_packet(entity) -> TISPacket:
        """
        Generate a packet to switch ON a specific channel of a device.

        :param entity: The entity object containing device information.
        :return: A TISPacket instance for the 'ON' command.
        """
        return TISPacket(
            device_id=entity.device_id,
            operation_code=TISProtocolHandler.OPERATION_CONTROL,
            source_ip=entity.api.host,
            destination_ip=entity.gateway,
            # Payload: [channel, value, fade_time_high, fade_time_low]
            # 0x64 is 100 in decimal, representing 100% ON.
            additional_bytes=[entity.channel_number, 0x64, 0x00, 0x00],
        )

    @staticmethod
    def generate_control_off_packet(entity) -> TISPacket:
        """
        Generate a packet to switch OFF a specific channel of a device.

        :param entity: The entity object containing device information.
        :return: A TISPacket instance for the 'OFF' command.
        """
        return TISPacket(
            device_id=entity.device_id,
            operation_code=TISProtocolHandler.OPERATION_CONTROL,
            source_ip=entity.api.host,
            destination_ip=entity.gateway,
            # Payload: [channel, value, fade_time_high, fade_time_low]
            # 0x00 represents 0% ON, i.e., OFF.
            additional_bytes=[entity.channel_number, 0x00, 0x00, 0x00],
        )

    @staticmethod
    def generate_control_update_packet(entity) -> TISPacket:
        """
        Generate a packet to request a status UPDATE from a device.

        :param entity: The entity object containing device information.
        :return: A TISPacket instance for the 'UPDATE' command.
        """
        return TISPacket(
            device_id=entity.device_id,
            operation_code=TISProtocolHandler.OPERATION_CONTROL_UPDATE,
            source_ip=entity.api.host,
            destination_ip=entity.gateway,
            additional_bytes=[],
        )

    @staticmethod
    def generate_discovery_packet() -> TISPacket:
        """
        Generate a broadcast packet to DISCOVER TIS devices on the network.

        :return: A TISPacket instance for the 'DISCOVERY' command.
        """
        return TISPacket(
            # The device ID 0xFFFF is a broadcast address, targeting all devices.
            device_id=[0xFF, 0xFF],
            operation_code=TISProtocolHandler.OPERATION_DISCOVERY,
            source_ip="0.0.0.0",
            destination_ip="0.0.0.0",
            additional_bytes=[],
        )
