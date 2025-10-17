from asyncio import get_event_loop, AbstractEventLoop
import socket

# Import the main protocol class that orchestrates the sender, receiver, etc.
from TISApi.Protocols.udp.PacketProtocol import PacketProtocol
from homeassistant.core import HomeAssistant

# Get the global asyncio event loop (though the function below correctly uses a passed loop).
loop = get_event_loop()


async def setup_udp_protocol(
    sock: socket,
    loop: AbstractEventLoop,
    udp_ip: str,
    udp_port: int,
    hass: HomeAssistant,
) -> tuple[socket.socket, PacketProtocol]:
    """
    Initializes and configures an asyncio UDP datagram endpoint.

    This function is the bootstrap for the entire UDP communication system. It
    tells asyncio to start listening for UDP packets using our custom PacketProtocol class.

    :param sock: The socket object to use.
    :param loop: The asyncio event loop.
    :param udp_ip: The target IP address for sending.
    :param udp_port: The port to listen on and send to.
    :param hass: The Home Assistant instance.
    :return: A tuple containing the asyncio transport and the protocol instance.
    """
    # This is the core asyncio call to create a UDP endpoint (a listener).
    transport, protocol = await loop.create_datagram_endpoint(
        # protocol_factory: A function that returns a new protocol instance.
        # We use a lambda to create an instance of our main PacketProtocol class.
        lambda: PacketProtocol(sock, udp_ip, udp_port, hass),
        # remote_addr: Default destination for sending packets (can be overridden).
        remote_addr=(udp_ip, udp_port),
        # local_addr: The address and port to listen on.
        # '0.0.0.0' means listen on all available network interfaces.
        local_addr=("0.0.0.0", udp_port),
        # allow_broadcast: Must be True to allow sending discovery packets.
        allow_broadcast=True,
        # reuse_port: Allows other sockets to bind to this port, useful for robustness.
        reuse_port=True,
    )

    # Return the transport (for sending data) and protocol (for handling logic) objects.
    return transport, protocol
