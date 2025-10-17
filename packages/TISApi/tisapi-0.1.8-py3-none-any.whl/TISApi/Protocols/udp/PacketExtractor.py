# Import the CRC checking function and the logging module.
from TISApi.BytesHelper import checkCRC
import logging


class PacketExtractor:
    """
    A utility class to parse raw TIS network packets.

    This class contains a static method to dissect a list of bytes (representing
    a packet) into a structured dictionary, making the data easy to work with.
    """

    @staticmethod
    def extract_info(packet: list) -> dict:
        """
        Extracts structured information from a raw packet list.

        This function first validates the packet's integrity using a CRC check.
        If valid, it slices the list at predefined offsets corresponding to the
        TIS protocol structure to extract different fields.

        :param packet: A list of integers, where each integer is a byte from the packet.
        :return: A dictionary containing the parsed fields, or an empty dictionary if the CRC check fails.
        """
        # First, validate the packet's integrity by checking its CRC.
        packet_check = checkCRC(packet)

        info = {}
        if packet_check:
            # If the CRC is valid, parse the packet based on its fixed structure.
            # The numbers used in the slicing (e.g., 0:4, 17:19) are the byte offsets
            # for each field in the TIS protocol.
            info["source_ip"] = packet[0:4]
            info["device_id"] = packet[17:19]
            info["device_type"] = packet[19:21]
            info["operation_code"] = packet[21:23]
            info["source_device_id"] = packet[23:25]
            # The additional_bytes are the payload of the packet, located between the header
            # and the final two CRC bytes.
            info["additional_bytes"] = packet[25:-2]

        else:
            # If the CRC check fails, the packet is likely corrupted. Log an error.
            logging.error(f"CRC check failed for packet: {packet}")

        return info
