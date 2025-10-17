import binascii

# Import CRC (Cyclic Redundancy Check) functions for error checking.
from TISApi.crc import checkCRC, packCRC


def bytes2hex(data, rtype=[]):
    """A helper function to parse bytes to hex.

    :param data: The raw bytes array to be converted.
    :type data: bytes array
    :param rtype: Determines the return type. If a list is passed (default),
                  it returns a list of integers. Otherwise, it returns a hex string.
    :type rtype: list, optional
    :return: A list of integers (each representing a byte) or a single hex string.
    :rtype: list | str
    """
    # Convert the raw bytes into a hexadecimal string (e.g., b'\x1a\x2b' -> '1a2b').
    hex_string = binascii.hexlify(data).decode()

    # Use a list comprehension to create a list of integers from the hex string.
    # It takes two characters at a time (e.g., '1a', '2b') and converts them to an integer.
    hex_list = [int(hex_string[i : i + 2], 16) for i in range(0, len(hex_string), 2)]

    # Check the type of the 'rtype' argument to determine the function's return format.
    if isinstance(rtype, list):
        return hex_list
    else:
        return hex_string


def build_packet(
    operation_code: list,
    ip_address: str,
    device_id: list = [],
    source_device_id: list = [
        0x01,
        0xFE,
    ],  # Default source ID, likely representing a gateway or controller.
    additional_bytes: list = [],
    header="SMARTCLOUD",  # The standard header for TIS packets.
):
    """Constructs a TIS command packet from its components."""

    # Convert the IP address string (e.g., "192.168.1.10") into a list of integers.
    ip_bytes = [int(part) for part in ip_address.split(".")]
    # Convert the header string into a list of its ASCII character codes.
    header_bytes = [ord(char) for char in header]

    # Calculate the length of the core packet data.
    length = 11 + len(additional_bytes)

    # Assemble the packet by concatenating all its parts in the correct order.
    # The structure is: IP + Header + Delimiter + Length + Source ID + Dest ID + Op Code + Target Device ID + Extra Data.
    packet = (
        ip_bytes
        + header_bytes
        + [0xAA, 0xAA]  # Static delimiter bytes.
        + [length]  # The calculated length of the packet payload.
        + source_device_id
        + [
            0xFF,
            0xFE,
        ]  # Destination ID (0xFFFE often means broadcast or generic target).
        + operation_code
        + device_id
        + additional_bytes
    )

    # Calculate the CRC for the assembled packet and append it for error checking.
    packet = packCRC(packet)
    return packet


def decode_mac(mac: list):
    """Formats a list of bytes into a standard MAC address string."""
    # Example: [10, 27, 44, 62, 79, 95] -> "0A:1B:2C:3E:4F:5F"
    # The f-string format `f"{byte:02X}"` ensures each byte is represented by
    # two uppercase hexadecimal characters with a leading zero if needed.
    return ":".join([f"{byte:02X}" for byte in mac])


def int_to_8_bit_binary(number):
    """Converts an integer to a reversed, 8-bit binary string."""
    # Convert the number to a binary string and remove the "0b" prefix.
    binary_string = bin(number)[2:]

    # Pad the string with leading zeros to ensure it is 8 bits long.
    # Then, reverse the string [::-1], as some protocols read bits from right to left (little-endian).
    return binary_string.zfill(8)[::-1]
