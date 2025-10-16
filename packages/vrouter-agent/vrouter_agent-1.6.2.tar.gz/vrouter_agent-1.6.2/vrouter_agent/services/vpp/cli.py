from loguru import logger as log
from vrouter_agent.utils import run_command
from vrouter_agent.vpp.vpp_api import add_linux_route, add_vpp_route


# Note: this is a temporary solution, to be replaced with proper python client API
def expose_lan_interface_to_frr_container(
    lan_intf: str, frr_container_name: str, lan_intf_ip: str, lan_intf_ip_mask: str
):
    cmd = f"sudo vppctl lcp create {lan_intf} host-if {lan_intf} netns frr tun"
    res = run_command(cmd.split())
    log.debug(f"Running command: {cmd}")
    log.debug(f"Exposing LAN interface to FRR container: {res}")

    cmd1 = f"sudo vppctl set interface ip address del {lan_intf} {lan_intf_ip}/{lan_intf_ip_mask}"
    res1 = run_command(cmd1.split())
    log.debug(f"Running command: {cmd1}")
    log.debug(f"Deleting IP address from LAN interface: {res1}")

    cmd2 = f"sudo vppctl set interface ip address {lan_intf} {lan_intf_ip}/{lan_intf_ip_mask}"
    res2 = run_command(cmd2.split())
    log.debug(f"Running command: {cmd2}")
    log.debug(f"Setting IP address to LAN interface: {res2}")


def add_ospf_lcp_fix(client, client_vpp_intf_address, vpp_lan_intf):
    # https://lists.fd.io/g/vpp-dev/topic/83103366#19478
    # for 224.0.0.5 and 224.0.0.6 used by OSPF (https://en.wikipedia.org/wiki/Open_Shortest_Path_First)

    # run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", "local", "Forward"])
    # for i in range(4):
    #     run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", os.environ[os.environ["VPP"]+f"_WG{i}_INTERFACE_NAME"], "Accept"])

    # to steer OSPF Hello packets from FRR container to client
    add_vpp_route(
        client,
        "224.0.0.0/24",  # static due to OSPF hello packets always destined for 224.0.0.5
        client_vpp_intf_address,
        vpp_lan_intf,
    )

    # to get ospf hello packets from client to frr container through vpp
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "mroute",
            "add",
            client_vpp_intf_address,
            "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
            "via",
            vpp_lan_intf,
            "Accept",
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "mroute",
            "add",
            client_vpp_intf_address,
            "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
            "via",
            "local",  # static, set to be locally processed (processed by LCP)
            "Forward",
        ]
    )


# Note: this does not include RR-node wireguard tunnel (for that see makefile) and RR setup => only path from linux WG
# on node to BGP in container on node
def add_routes_for_bidirectional_bgp_communication(
    client,
    frr_container_name: str,
    local_bgp_loop_ip: str,
    rr_bgp_loop_ip: str,
    rr_wg_ip: str,
):
    # Some path explanation:
    # RR-to-node path: node-linux-wg0 -(adding here route1+iptables forwarding)-> FRR container default interface ->
    #   FRR container routing to local loopback -(ping echo going back, need to add route2)-> FRR container default
    #   interface -(routing path was added as part of wg configuration)-> node-linux-wg0
    # Node-to-RR path: FRR instance in FRR container -(need to add route3)-> FRR container default interface
    #   -> node linux host route(actually controlled by WG allowed ip configuration) -> wg tunnel to RR
    host_ip_from_docker_container = "172.17.0.1"

    # adding route1
    frr_container_ip_address, _ = run_command(
        [
            "docker",
            "inspect",
            "-f",
            "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
            frr_container_name,
        ]
    )
    frr_container_ip_address = frr_container_ip_address.replace("\n", "").replace(
        "'", ""
    )
    log.debug(f"FRR container IP address: {frr_container_ip_address}")

    add_linux_route(
        client,
        local_bgp_loop_ip,
        frr_container_ip_address,
    )
    run_command(
        [
            "sudo",
            "iptables",
            "-A",
            "FORWARD",
            "-i",
            "wg0",
            "-o",
            "docker0",  # static for default docker installation
            "-j",
            "ACCEPT",
        ]
    )
    # adding route2
    add_linux_route(
        client,
        rr_wg_ip,
        host_ip_from_docker_container,
        "",
        frr_container_name,
    )
    # adding route3
    add_linux_route(
        client,
        rr_bgp_loop_ip,
        host_ip_from_docker_container,
        "",
        frr_container_name,
    )
    # TODO check that setting "echo 1 > /proc/sys/net/ipv4/ip_forward" is always set for node (it seems to be true,
    #  just don't know where it is persisted to survive the machine reboot)


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


def add_client_neighbour_info(
    vpp_lan_intf: str, client_vpp_intf_ip: str, client_vpp_intf_mac: str
):
    """Adds neighbor L2 information to VPP so that VPP won't drop packets from TRex and send ARP packets(=question
    for client)"""

    # using MAC address of client interface (or at least what TREX traffic destination MAC address that VPP must
    # steer back to Trex through client interface)
    cmd = f"sudo vppctl ip neighbor {vpp_lan_intf} {client_vpp_intf_ip} {client_vpp_intf_mac}"
    res = run_command(cmd.split())
    log.debug(f"Running command: {cmd}")
    log.debug(f"Adding neighbour info to VPP: {res}")

    # NOTE: this could be also moved to bootstrap.vpp as it is static for given vpp-client setup
