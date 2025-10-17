from homeassistant.core import HomeAssistant
import logging


async def handle_update_response(hass: HomeAssistant, info: dict):
    """
    Handles a parsed 'update response' packet from a TIS device.

    This function takes the packet information, formats it into a dictionary,
    and fires it as an event on the Home Assistant event bus. Entities can
    listen for this event to update their state.

    :param hass: The Home Assistant instance.
    :param info: A dictionary containing the parsed packet data.
    """
    # According to the TIS protocol for this message type, the first byte of the
    # payload indicates the number of channels/scenarios included in the response.
    channels_number = info["additional_bytes"][0]

    # Prepare the payload for the Home Assistant event.
    event_data = {
        "device_id": info["device_id"],
        "feedback_type": "update_response",
        "additional_bytes": info["additional_bytes"],
        "channel_number": channels_number,
    }

    try:
        # --- Fire the event on the Home Assistant event bus ---
        # The event's "type" or "topic" is the device_id itself. This allows
        # entities to efficiently subscribe only to events from their parent device.
        hass.bus.async_fire(str(info["device_id"]), event_data)
    except Exception as e:
        # Log any errors that occur during the event firing process.
        logging.error(f"Error firing update_response event: {e}")
