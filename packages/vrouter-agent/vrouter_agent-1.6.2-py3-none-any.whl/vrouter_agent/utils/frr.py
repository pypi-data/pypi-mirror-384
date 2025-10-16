from collections import defaultdict
import re

from vrouter_agent.utils.cli import run_command


def get_ospf_neighbors():
    output, _ = run_command(
        ["docker", "exec", "frr", "vtysh", "-c", "show ip ospf neighbor"]
    )
    # Regex patterns
    instance_pattern = re.compile(r"OSPF Instance:\s+(\d+)")
    neighbor_pattern = re.compile(
        r"(\d+\.\d+\.\d+\.\d+)\s+(\d+)\s+([^\s]+)\s+([^\s]+)\s+([^\s]+)\s+(\d+\.\d+\.\d+\.\d+)\s+([^\s]+)"
    )

    # Data structure to store OSPF neighbor information
    ospf_neighbors = defaultdict(list)

    # State variables
    current_instance = None

    # Split the output into sections by line
    lines = output.splitlines()

    for line in lines:
        # Check for OSPF instance
        instance_match = instance_pattern.match(line)
        if instance_match:
            current_instance = instance_match.group(1)

        # Check for neighbor information
        neighbor_match = neighbor_pattern.match(line)
        if neighbor_match and current_instance:
            neighbor_info = {
                "Neighbor ID": neighbor_match.group(1),
                "Pri": neighbor_match.group(2),
                "State": neighbor_match.group(3),
                "Up Time": neighbor_match.group(4),
                "Dead Time": neighbor_match.group(5),
                "Address": neighbor_match.group(6),
                "Interface": neighbor_match.group(7),
            }
            ospf_neighbors[current_instance].append(neighbor_info)
    return ospf_neighbors if ospf_neighbors else None
