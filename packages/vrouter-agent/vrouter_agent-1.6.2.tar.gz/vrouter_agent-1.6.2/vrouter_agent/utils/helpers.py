from vrouter_agent.utils.cli import run_command
from vrouter_agent.utils.secure_subprocess import run_secure_command_output
import subprocess
from loguru import logger as log


def run_docker_command(command, container_name):
    """
    Run a command in a docker container
    """

    cmd = f"docker exec {container_name} {command}"
    res, returncode = run_command(cmd.split())

    if returncode != 0:
        log.error(f"Error running command: {cmd}")
        return False
    return res


def run_frr_command(command, container_name):
    """
    Run a command in a FRR container.

    :param command: Command string to run in the FRR container.
    :param container_name: Name of the Docker container running FRR.
    :return: The result of the command or False if an error occurs.
    """
    cmd = f'docker exec {container_name} vtysh -c "{command}"'

    try:
        res = subprocess.run(
            cmd, shell=True, check=True, capture_output=True, text=True
        )
        return res.stdout.strip()
    except subprocess.CalledProcessError as e:
        log.error(f"Error running command: {cmd}")
        log.error(f"Return code: {e.returncode}")
        log.error(f"Output: {e.output}")
        return False


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


def apply_ospf_config_to_frr(ospf_config_str: str, frr_container_name: str, file: str):
    with open(file, "w") as frr_config:
        frr_config.write(ospf_config_str)

    log.debug(f"Frr config wrote to file: {file}")

    cmd = f"docker cp {file} {frr_container_name}:/etc/frr/frr.conf"
    log.debug(f"Running command: {cmd}")
    res = run_command(cmd.split())
    log.debug(f"Copying file to FRR container: {res}")

    # Note: ignoring result as this will be in the end converted to vrouter config that checks result
    cmd1 = f"docker exec {frr_container_name} vtysh -b"
    log.debug(f"Running command: {cmd1}")
    res1 = run_command(cmd1.split())
    log.debug(f"Applying configuration to FRR: {res1}")


def get_system_info():
    try:
        # Use secure subprocess wrapper instead of direct subprocess call
        cmd = ["uname", "-a"]
        return run_secure_command_output(cmd)
    except Exception as e:
        log.error(f"Failed to get system info: {e}")
        return ""
