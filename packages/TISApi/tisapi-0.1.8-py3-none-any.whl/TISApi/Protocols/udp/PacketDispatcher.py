from homeassistant.core import HomeAssistant
import logging


class PacketDispatcher:
    """
    Routes parsed packet information to the appropriate handler function.

    This class acts as a central hub after a packet has been received and parsed.
    It uses a dictionary to look up the correct action to take based on the
    packet's operation code.
    """

    def __init__(self, hass: HomeAssistant, OPERATIONS_DICT: dict):
        """
        Initialize the PacketDispatcher.

        :param hass: The Home Assistant instance, passed to handler functions.
        :param OPERATIONS_DICT: A dictionary mapping operation codes to handler functions.
        """
        self.hass = hass
        self.operations_dict = OPERATIONS_DICT

    async def dispatch_packet(self, info: dict):
        """
        Dispatches a packet based on its operation code.

        :param info: A dictionary containing the parsed information from the packet.
        """
        try:
            # Look up the handler function in the operations dictionary using the packet's operation code.
            # The operation code (a list) is converted to a tuple to be used as a dictionary key.
            packet_handler = self.operations_dict.get(
                tuple(info["operation_code"]), "unknown operation"
            )

            # If a handler function was found, execute it.
            if packet_handler != "unknown operation":
                # The handler itself is an async function, so it must be awaited.
                await packet_handler(self.hass, info)
            else:
                # If the operation code is not in our dictionary, log it as an error.
                logging.error(
                    f"Unknown operation code received: {info['operation_code']}"
                )
        except Exception as e:
            # Catch any unexpected errors during the dispatch process to prevent a crash.
            logging.error(f"Error dispatching packet: {e} , info: {info}")
