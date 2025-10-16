import re


def get_gre_ip_address(ip_address) -> str:
    """
    Manipulate the ip address to be in the range of 192.168.20x.0/24

    For example: 192.168.101.10 -> 192.168.201.10

    """
    ip_parts = ip_address.split(".")
    ip_parts[2] = "20" + ip_parts[2][2:]
    return ".".join(ip_parts)


def get_ip_address_no_prefix(value) -> str:
    """
    Only return the IP address without the prefix

    For example:
    x.x.x.x/x -> x.x.x.x

    """
    return value.split("/")[0]


def get_wan_ip_addresses(val) -> dict:
    """
    Get the WAN IP addresses of the tunnel
    For example:
    x.x.x.x(primary), x.x.x.x(secondary) -> {"primary": x.x.x.x, "secondary": x.x.x.x}

    :return: List of WAN IP addresses

    """
    pattern = (
        r"(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\((?P<label>primary|secondary)\)"
    )

    matches = re.findall(pattern, val)

    ip_dict = {"primary": None, "secondary": None}

    if matches:
        # Populate the dictionary with labeled IP addresses
        for ip, label in matches:
            ip_dict[label] = ip
    else:
        # If no labeled IPs are found, return the single IP address with key "primary"
        ip_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        match = re.search(ip_pattern, val)
        if match:
            ip_dict["primary"] = match.group(0)

    return ip_dict


def subnet_mask_to_prefix_length(subnet_mask):
    # Convert the subnet mask to a list of integers
    subnet_mask = list(map(int, subnet_mask.split(".")))

    # Convert each octet to binary and concatenate
    binary_representation = "".join(format(octet, "08b") for octet in subnet_mask)

    # Count the number of consecutive 1 bits
    prefix_length = binary_representation.count("1")

    return prefix_length


def convert_wireguard_to_gre_ip_addr(ip_address):
    """
    Manipulate the ip address to be in the range of 192.168.20x.0/24

    For example: 192.168.101.10 -> 192.168.201.10

    """
    ip_parts = ip_address.split(".")
    ip_parts[2] = "20" + ip_parts[2][2:]
    return ".".join(ip_parts)
