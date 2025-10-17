import logging
import asyncio
from typing import Union

# This shared dictionary is crucial. It allows the sender and receiver, which operate
# in different parts of the code, to access the same set of asyncio Events.
from TISApi.shared import ack_events


class AckCoordinator:
    """
        Manages the lifecycle of asyncio.Event objects for acknowledgement (ack) handling.

        This class acts as a bridge between the PacketSender and the PacketReceiver.
        When the sender sends a command, it creates an 'ack event' here. When the
        receiver gets the corresponding acknowledgement, it uses this coordinator
    to find and set that event, unblocking the sender.
    """

    def __init__(self):
        """Initializes the coordinator, using a shared dictionary for events."""
        self.ack_events = ack_events

    def create_ack_event(self, unique_id: Union[str, tuple]) -> asyncio.Event:
        """
        Creates and stores a new event for a given command ID.

        This is called by the sender *before* a command is sent.

        :param unique_id: A unique identifier for the command being sent.
        :return: The newly created asyncio.Event object.
        """
        logging.error(f"Creating ack event for {unique_id}")
        # Create a new event, which is initially in an 'unset' state.
        event = asyncio.Event()
        # Store the event in the shared dictionary, keyed by the command's unique ID.
        self.ack_events[unique_id] = event
        return event

    def get_ack_event(self, unique_id: Union[str, tuple]) -> Union[asyncio.Event, None]:
        """
        Retrieves an existing event for a given command ID.

        This is called by the receiver when an acknowledgement packet arrives.

        :param unique_id: The unique identifier from the received ack packet.
        :return: The corresponding asyncio.Event, or None if not found.
        """
        return self.ack_events.get(unique_id)

    def remove_ack_event(self, unique_id: Union[str, tuple]) -> None:
        """
        Removes an event from the dictionary.

        This is used for cleanup after a command has been successfully ack'd
        or has failed after all retry attempts.

        :param unique_id: The unique identifier of the event to remove.
        """
        # Safely remove the key-value pair if it exists.
        if unique_id in self.ack_events:
            del self.ack_events[unique_id]
