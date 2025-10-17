from homeassistant.core import HomeAssistant
import logging
import asyncio

# Import the shared dictionary that holds acknowledgement events.
from TISApi.shared import ack_events


async def handle_control_response(hass: HomeAssistant, info: dict):
    """
    Handles a 'control response' packet, which acts as an acknowledgement.

    This function has two primary responsibilities:
    1. Fire an event on the Home Assistant event bus to let the corresponding
       entity know its state has changed.
    2. Signal the PacketSender that the command was successfully received
       by setting an asyncio.Event.

    :param hass: The Home Assistant instance.
    :param info: A dictionary containing the parsed packet data.
    """
    # Extract the channel number from the first byte of the payload.
    channel_number = info["additional_bytes"][0]

    # --- 1. Fire an event to update Home Assistant state ---
    # Prepare the payload for the event.
    event_data = {
        "device_id": info["device_id"],
        "channel_number": channel_number,
        "feedback_type": "control_response",
        "additional_bytes": info["additional_bytes"],
    }
    try:
        # Fire the event, using the device_id as the topic for efficient listening.
        hass.bus.async_fire(str(info["device_id"]), event_data)
    except Exception as e:
        logging.error(f"Error firing control_response event: {e}")

    # --- 2. Signal the sender that the command was acknowledged ---
    try:
        # Construct the unique ID for the original command. This ID MUST EXACTLY MATCH
        # the one created in the PacketSender's `send_packet_with_ack` method.
        unique_id = (
            tuple(info["device_id"]),
            (0x00, 0x31),  # The original command's operation code.
            int(channel_number),
        )

        # Retrieve the event that the sender is waiting on.
        event: asyncio.Event = ack_events.get(unique_id)

        # If an event exists, it means the sender is waiting for this acknowledgement.
        if event is not None:
            # Setting the event unblocks the `await event.wait()` call in the PacketSender,
            # confirming the command was successful.
            event.set()
    except Exception as e:
        logging.error(f"Error setting the acknowledgement event: {e}")
