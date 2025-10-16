from collections import defaultdict
import configparser
import subprocess
import socket
import os
from cryptography.fernet import Fernet
import re
import tempfile
from pathlib import Path

# import docker
import importlib.metadata
import datetime
from .cli import run_command
from loguru import logger as log


def version():
    """Prints version"""
    return importlib.metadata.version("vrouter-agent")


def get_device_serial_number():
    """
    Returns the serial number of the device.
    """
    val, _ = run_command(["sudo", "dmidecode", "-s", "system-serial-number"])
    return val.strip()

def get_device_short_hostname():
    """
    Returns the hostname of the device.
    """
    val, _ = run_command(["hostname", "-s"])
    return val.strip()

def get_vpp_version():
    """
    Returns the version of VPP.
    """
    val, _ = run_command(["sudo","vppctl", "sh","version"])
    return val.strip()

def get_tunnel_in_scope(order, device_serial_number):
    """
    If order status does not have `requested` status, it is not in scope.
    If the device hostname does not match the order hostname, it is not in scope.

    Params:
        order: Order object.
        device_serial_number: Serial number of the device.

    Returns:
        List of tunnels in scope or empty list.
    """
    tunnels = []
   
    for tunnel in order.tunnels:
        if tunnel.source.device_hostname == device_serial_number:
            tunnels.append(tunnel)
        if tunnel.destination.device_hostname == device_serial_number:
            tunnels.append(tunnel)
    return tunnels


def check_vpp():
    """Check vpp status"""
    try:
        run_command(["sudo", "systemctl", "status", "vpp", "--quiet"])
    except Exception:
        log.error("VPP is not installed or running.")
        return False
    return True


def check_vrouter():
    """Check vrouter status"""
    try:
        run_command(["sudo", "systemctl", "status", "vrouter", "--quiet"])
    except Exception:
        log.error("Vrouter is not installed or running.")
        return False
    return True


def check_frr(frr_container_name: str = "frr"):
    """Check frr status"""
    try:
        run_command(["docker", "inspect", frr_container_name])
    except Exception:
        log.error("FRR is not installed or running. Exiting...")
        return False
    return True


def restart_vpp():
    """Restart vpp"""
    try:
        run_command(["sudo", "systemctl", "restart", "vpp"])
    except Exception:
        log.error("Failed to restart VPP.")
        return False
    return True


def restart_vrouter():
    """Restart vrouter"""
    try:
        run_command(["sudo", "systemctl", "restart", "vrouter"])
    except Exception:
        log.error("Failed to restart vrouter.")
        return False
    return True


def restart_frr(frr_container_name: str = "frr"):
    """Restart frr"""
    try:
        run_command(["docker", "restart", frr_container_name])
    except Exception:
        log.error("Failed to restart FRR.")
        return False
    return True


def restart_services():
    """Restart all services"""
    if not restart_vpp():
        return False
    if not restart_vrouter():
        return False
    if not restart_frr():
        return False
    return True


def check_dependencies():
    log.info("Checking prerequisites...")
    vpp = check_vpp()
    vrouter = check_vrouter()
    frr = check_frr()
    if vpp and vrouter and frr:
        return True
    else:
        return False


def read_config(file_path):
    obj = {}
    config = configparser.ConfigParser()
    config.read(file_path)
    for section in config.sections():
        for key in config[section]:
            obj[key] = config[section][key]
    return obj


# def get_docker_ip_address(container_name: str):
#    """Get the IP address of a docker container

#    Args:
#        container_name (str): Name of the container

#    Returns:
#        str: IP address of the container
#    """

#    client = docker.from_env()
#    container = client.containers.get(container_name)
#    return container.attrs["NetworkSettings"]["IPAddress"]


# def run_docker_command(container_name: str, command: str):
#    """Run a command in a docker container

#    Args:
#        container_name (str): Name of the container
#        command (str): Command to run

#    Returns:
#        str: Output of the command
#    """

#    client = docker.from_env()
#    container = client.containers.get(container_name)
#    return container.exec_run(command)


def get_ip4_addr():
    """Get the IP address of the current machine

    Returns:
        str: IP address of the machine
    """
    return [
        (s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close())
        for s in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
    ][0][1]


def get_targeted_list(conf_list, conf_dir):
    """Get target list

    Args:
        conf_list (list): list of config file
        conf_dir (str): config dir

    Returns:
        _type_: _description_
    """
    if len(conf_list) == 0:
        log.warning("No configuration files found.")
    else:
        for x in conf_list:
            my_list = {
                "hostname": x["hostname"],
                "tunnel_id": x["tunnel_id"],
                "files": [],
            }
            my_list["files"] += [
                each
                for each in os.listdir(conf_dir)
                if each.startswith("tnn%s" % x["id"])
            ]
            if my_list["hostname"] == socket.gethostname():
                return my_list
    return None


def initialize_symmetric_key(key):
    f = Fernet(key)
    return f


def decrypt_data_symmetric(data, secret_key):
    f = initialize_symmetric_key(secret_key)
    token = f.decrypt(data)
    return token.decode("utf-8")


def decrypt_stream_item(args):
    """Decrypt stream item"""
    log.info("Decrypting stream item...")
    hex_data = args.hex_data
    # convert hex to bytes
    hex_data = bytes.fromhex(hex_data)
    # decrypt data
    log.debug("Decrypting data...")
    order_json = decrypt_data_symmetric(hex_data, args.secret_key)
    log.debug("Data decrypted!")
    return order_json


def is_system_rebooted():
    try:
        result = subprocess.check_output(["uptime", "-s"])
        boot_time = datetime.datetime.strptime(
            result.decode("utf-8").strip(), "%Y-%m-%d %H:%M:%S"
        )
        now = datetime.datetime.now()
        if (
            now - boot_time
        ).total_seconds() < 60:  # Check if the server has been rebooted in the last minute
            return True
        else:
            return False
    except Exception as e:
        print(f"An error occurred: {e}")
        return False


def convert_wg_to_gre_ip_addr(ip_address):
    """
    Manipulate the ip address to be in the range of 192.168.20x.0/24

    For example: 192.168.101.10 -> 192.168.201.10

    """
    ip_parts = ip_address.split(".")
    third_octet = ip_parts[2]
    if len(third_octet) >= 3:
        # If third octet has 3+ digits, take the last digit and prepend "20"
        ip_parts[2] = "20" + third_octet[2:]
    else:
        # If third octet has 1-2 digits, prepend "20" to the whole octet
        ip_parts[2] = "20" + third_octet
    return ".".join(ip_parts)


def convert_subnet_to_mask(subnet):
    return str(sum([bin(int(x)).count("1") for x in subnet.split(".")]))


def get_primary_interface(interfaces):
    """Filters the given interfaces to only include the primary one.

    Args:
      interfaces: A list of dictionaries representing interfaces,
        each with an 'is_primary' key.

    Returns:
      A list containing only the primary interface, or an empty list if
      no primary interface is found.
    """

    # Filter interfaces based on the is_primary flag
    primary_interfaces = [
        interface for interface in interfaces if interface["is_primary"] == "True"
    ]

    # Return the first primary interface (assuming only one primary exists)
    return primary_interfaces[0] if primary_interfaces else None


def extract_wan_ip_addresses(input_str):
    # Pattern to match IP addresses with labels
    pattern = (
        r"(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\((?P<label>primary|secondary)\)"
    )

    matches = re.findall(pattern, input_str)

    ip_dict = {"primary": None, "secondary": None}

    if matches:
        # Populate the dictionary with labeled IP addresses
        for ip, label in matches:
            ip_dict[label] = ip
    else:
        # If no labeled IPs are found, return the single IP address with key "primary"
        ip_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        match = re.search(ip_pattern, input_str)
        if match:
            ip_dict["primary"] = match.group(0)

    return ip_dict


def get_temp_dir():
    """Get a secure temporary directory for the application."""
    temp_dir = Path(tempfile.gettempdir()) / "vrouter-agent"
    temp_dir.mkdir(exist_ok=True, mode=0o700)  # Secure permissions
    return temp_dir

def get_frr_config_path():
    """Get the path for FRR configuration file."""
    return get_temp_dir() / "frr.conf"

def get_frr_sync_dir():
    """Get the directory for FRR sync files."""
    return get_temp_dir() / "frr-sync"
