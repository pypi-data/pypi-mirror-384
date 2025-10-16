import socket
import struct
import fcntl
import subprocess
import re
from loguru import logger as log


def subnet_mask_to_prefix_length(subnet_mask):
    # Convert the subnet mask to a list of integers
    subnet_mask = list(map(int, subnet_mask.split(".")))

    # Convert each octet to binary and concatenate
    binary_representation = "".join(format(octet, "08b") for octet in subnet_mask)

    # Count the number of consecutive 1 bits
    prefix_length = binary_representation.count("1")

    return prefix_length


def get_ip_addr(interface) -> str:
    """
    Uses the Linux SIOCGIFADDR ioctl to find the IP address associated
    with a network interface, given the name of that interface, e.g.
    "eth0". Only works on GNU/Linux distributions.
    Source: https://bit.ly/3dROGBN
    Returns:
        The IP address in quad-dotted notation of four decimal integers.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        packed_iface = struct.pack("256s", interface.encode("utf_8"))
        packed_addr = fcntl.ioctl(sock.fileno(), 0x8915, packed_iface)[20:24]
        return socket.inet_ntoa(packed_addr)
    except Exception:
        return


def ping_accross(addr):
    cmd = "vppctl ping %s interval 0.01 repeat 10" % addr
    p = subprocess.run(cmd.split(), stdout=subprocess.PIPE)
    de = p.stdout.decode("utf-8")
    for item in de.split("\n"):
        if "Statistics" in item:
            log.info(item.strip())
            str = item.strip()
    try:
        x = re.search("sent,(.+?)received", str).group(1).strip()
        return int(x)
    except AttributeError:
        pass

