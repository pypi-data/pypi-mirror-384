# Import necessary types and helpers from Python's standard library.
from collections.abc import Callable
from typing import Any

# Import custom modules from this integration.
from ...api import TISApi  # The main API for communicating with TIS devices.
from ...Protocols.udp.ProtocolHandler import (
    TISProtocolHandler,
    TISPacket,
)  # TIS protocol specifics.


class TISAPISwitch:
    """Base class for TIS switches, providing common functionality."""

    def __init__(
        self,
        tis_api: TISApi,
        channel_number: int,
        device_id: list[int],
        gateway: str,
        is_protected: bool = False,
        switch_name: str | None = None,
    ) -> None:
        """Initialize the base switch attributes."""
        self.api = tis_api

        # Store device-specific information.
        self.device_id = device_id
        self._name = (
            switch_name if switch_name else f"Switch {device_id} {channel_number}"
        )
        self.gateway = gateway
        self.channel_number = int(channel_number)
        self.is_protected = is_protected
        self._is_on: bool | None = None
        self._available: bool = True
        self._update_callback: Callable[[], None] | None = None

        # This avoids rebuilding the byte arrays every time a command is sent.
        self.on_packet: TISPacket = TISProtocolHandler.generate_control_on_packet(self)
        self.off_packet: TISPacket = TISProtocolHandler.generate_control_off_packet(
            self
        )
        self.update_packet: TISPacket = (
            TISProtocolHandler.generate_control_update_packet(self)
        )

    @property
    def is_on(self) -> bool | None:
        """Return true if the switch is on."""
        return self._is_on

    @property
    def available(self) -> bool:
        """Return True if the switch is available."""
        return self._available

    @property
    def name(self) -> str:
        """Return the name of the switch."""
        return self._name

    @property
    def unique_id(self) -> str:
        """Return the unique ID for this switch."""
        return f"tis_{'_'.join(map(str, self.device_id))}_ch{self.channel_number}"

    def register_callback(self, callback: Callable[[], None]) -> None:
        """Register a callback function to call when the state changes."""
        self._update_callback = callback

    def process_update(self, event_data: dict[str, Any]) -> None:
        """Process an incoming event from the TIS gateway and update state."""
        state_changed = False
        availability_changed = False
        new_state: bool | None = self._is_on

        feedback_type = event_data.get("feedback_type")

        # Any valid response from the device means it is online.
        if feedback_type in ("control_response", "update_response"):
            if not self._available:
                self._available = True
                availability_changed = True

            if feedback_type == "control_response":
                if int(event_data["channel_number"]) == self.channel_number:
                    channel_value = event_data["additional_bytes"][2]
                    new_state = int(channel_value) == 100

            elif feedback_type == "update_response":
                additional_bytes = event_data["additional_bytes"]
                channel_status = int(additional_bytes[self.channel_number])
                new_state = channel_status > 0

        elif feedback_type == "offline_device":
            # The gateway explicitly told us the device is offline.
            if self._available:
                self._available = False
                availability_changed = True
            new_state = None  # State is unknown when offline

        # Check if the on/off state changed
        if new_state != self._is_on:
            self._is_on = new_state
            state_changed = True

        # If either state or availability changed, call the callback to notify listeners.
        if (state_changed or availability_changed) and self._update_callback:
            self._update_callback()

    async def turn_switch_on(self) -> bool | None:
        """Turn the switch on by sending the on_packet."""
        # Send the pre-generated 'on' packet and wait for an acknowledgement (ack).
        return await self.api.protocol.sender.send_packet_with_ack(self.on_packet)

    async def turn_switch_off(self) -> bool | None:
        """Turn the switch off by sending the off_packet."""
        # Send the pre-generated 'off' packet and wait for an acknowledgement (ack).
        return await self.api.protocol.sender.send_packet_with_ack(self.off_packet)

    async def request_update(self) -> None:
        """Send a request to the device for its current state."""
        await self.api.protocol.sender.send_packet(self.update_packet)
