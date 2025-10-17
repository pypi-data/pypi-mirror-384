from homeassistant.core import HomeAssistant


async def handle_discovery_feedback(hass: HomeAssistant, info: dict):
    """
    Handles a 'discovery feedback' packet from a TIS device.

    This function is called when a device responds to a discovery broadcast.
    It checks if the device has already been discovered during the current
    scan and, if not, adds it to a shared list in Home Assistant's data store.

    :param hass: The Home Assistant instance, used to access shared data.
    :param info: A dictionary containing the parsed packet data from the discovered device.
    """
    # Check if a device with the same device_id already exists in our list of discovered devices.
    # This prevents adding duplicate entries if a device responds multiple times.
    if not any(
        device["device_id"] == info["device_id"]
        for device in hass.data["tis_control"]["discovered_devices"]
    ):
        # If the device is new, append its information to the shared list.
        # `hass.data` is the standard location for integrations to store runtime data.
        hass.data["tis_control"]["discovered_devices"].append(info)
