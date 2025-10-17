# Import the main API class and the Platform enum from Home Assistant.
from .api import TISApi
from homeassistant.const import Platform


async def async_get_switches(tis_api: TISApi) -> list[dict]:
    """Fetch switches from TIS API and normalize to a list of dictionaries.

    Returns a list with items like:
    {
        "switch_name": str,
        "channel_number": int,
        "device_id": list[int],
        "is_protected": bool,
        "gateway": str,
    }

    Having this helper makes the setup code easier to test and keeps the
    API parsing logic in one place.
    """
    # Call the API to get all entities that are classified as switches.
    raw = await tis_api.get_entities(platform=Platform.SWITCH)

    # If the API returns no switches, return an empty list immediately.
    if not raw:
        return []

    # Prepare a list to hold the formatted switch data.
    result: list[dict] = []

    # Iterate through the raw data for each switch appliance returned by the API.
    for appliance in raw:
        # --- Extract the channel number from the nested data structure ---
        # The raw data looks like: "channels": [{"Output": 1}]
        # 1. appliance["channels"][0]: Get the first dictionary in the list -> {"Output": 1}
        # 2. .values(): Get the dictionary's values -> dict_values([1])
        # 3. list(...)[0]: Convert to a list and get the first element -> 1
        channel_number = int(list(appliance["channels"][0].values())[0])

        # Create a new, clean dictionary with a standardized format.
        result.append(
            {
                "switch_name": appliance.get("name"),
                "channel_number": channel_number,
                "device_id": appliance.get("device_id"),
                "is_protected": appliance.get("is_protected", False),
                "gateway": appliance.get("gateway"),
            }
        )

    # Return the final list of formatted switches.
    return result
