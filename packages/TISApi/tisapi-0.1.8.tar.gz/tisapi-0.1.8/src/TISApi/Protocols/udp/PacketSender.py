from socket import socket, SOL_SOCKET, SO_BROADCAST
import asyncio
import logging
from collections import deque

from TISApi.Protocols.udp.AckCoordinator import AckCoordinator
from TISApi.Protocols.udp.ProtocolHandler import TISPacket


class PacketSender:
    """Manages the sending of UDP packets with advanced features like acknowledgements, retries, and debouncing."""

    def __init__(self, socket: socket, coordinator: AckCoordinator, UDP_IP, UDP_PORT):
        self.UDP_IP = UDP_IP
        self.UDP_PORT = UDP_PORT
        self.socket = socket
        # Configure the socket to allow sending broadcast packets (e.g., for device discovery).
        self.socket.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

        # The AckCoordinator manages events for synchronizing sent packets with received acks.
        self.coordinator = coordinator

        # --- State management for command throttling and debouncing ---
        # Holds stacks of commands to ensure only the latest in a rapid sequence is sent (e.g., from a slider).
        self.command_stacks = {}
        # Holds the last time a command was sent to prevent network flooding.
        self.last_command_times = {}
        # Queues for a potential bulk update mechanism (currently unused in this snippet).
        self.update_packet_queue = deque()
        self.update_device_queue = set()

    async def send_packet(self, packet: TISPacket):
        """Sends a single packet without waiting for an acknowledgement (fire-and-forget)."""
        self.socket.sendto(packet.__bytes__(), (packet.destination_ip, self.UDP_PORT))

    async def send_packet_with_ack(
        self,
        packet: TISPacket,
        attempts: int = 10,
        timeout: float = 0.5,
        debounce_time: float = 0.5,  # The minimum time between commands of the same type.
    ):
        """
        Sends a packet reliably, waiting for an acknowledgement and retrying on failure.
        Also includes logic to throttle and debounce rapid commands.
        """
        # Create a unique ID for this specific command (device + operation + channel).
        # This is used to match a received ack to the sent command.
        unique_id = (
            tuple(packet.device_id),
            tuple(packet.operation_code),
            int(packet.additional_bytes[0]),
        )

        # --- Command Throttling Logic ---
        # If this is the first command of its type, create a stack for it.
        if unique_id not in self.command_stacks:
            self.command_stacks[unique_id] = []
        # Add the current command to its stack.
        self.command_stacks[unique_id].append(packet)

        # If this packet is not the MOST RECENT one in its stack, abort.
        # This effectively ignores all but the last command in a quick burst.
        if packet != self.command_stacks[unique_id][-1]:
            return

        # --- Debouncing Logic ---
        # If a command of this type was sent too recently, ignore the current request.
        if (
            unique_id in self.last_command_times
            and asyncio.get_event_loop().time() - self.last_command_times[unique_id]
            < debounce_time
        ):
            return

        # Update the timestamp for the last sent command of this type.
        self.last_command_times[unique_id] = asyncio.get_event_loop().time()

        # --- Acknowledgement (Ack) and Retry Logic ---
        # Create an asyncio Event that we can wait on. The packet receiver will set this event when an ack arrives.
        event = self.coordinator.create_ack_event(unique_id)

        # Try to send the packet up to `attempts` times.
        for attempt in range(attempts):
            await self.send_packet(packet)
            try:
                # Wait for the ack event to be set, with a specified timeout.
                await asyncio.wait_for(event.wait(), timeout)

                # If we get here, the ack was received successfully.
                # Remove the processed command from the stack and return True.
                self.command_stacks[unique_id].remove(packet)
                return True
            except asyncio.TimeoutError:
                # If the wait times out, log the failure and loop to the next attempt.
                logging.error(
                    f"ack not received within {timeout} seconds, attempt {attempt + 1}"
                )

        # If all attempts fail, clean up the event and log the final failure.
        self.coordinator.remove_ack_event(unique_id)
        logging.error(f"ack not received after {attempts} attempts")
        return False

    async def broadcast_packet(self, packet: TISPacket):
        """Sends a packet to the network's broadcast address."""
        # '<broadcast>' is a special address that sends the packet to all devices on the subnet.
        self.socket.sendto(packet.__bytes__(), ("<broadcast>", self.UDP_PORT))
