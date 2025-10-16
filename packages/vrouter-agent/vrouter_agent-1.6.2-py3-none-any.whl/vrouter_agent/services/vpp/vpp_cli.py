import os
import subprocess
from pprint import pprint
from typing import List, Tuple
from loguru import logger as log
from vpp_vrouter.client import ExtendedVPPAPIClient
from vpp_vrouter.common import models

from vrouter_agent.utils import run_command
from vrouter_agent.vpp.vpp_api import (
    add_gre_tunnel_to_wg_and_lcp_it_to_frr_container,
    add_wireguard_interface,
    add_wireguard_peer,
    add_wireguard_tunnel,
)
from vrouter_agent.vpp.vpp_utils import (
    WG_TUNNELS_PER_CONNECTION,
)
from vrouter_agent.utils.secure_subprocess import run_secure_command


def add_route_to_wireguard_peer(
    interface_name: str, remote_ip_network: str, remote_tunnel_end_ip: str
):
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "route",
            "add",
            remote_ip_network,
            "via",
            remote_tunnel_end_ip,
            interface_name,
        ]
    )


def add_frr_agent_ip_translation_from_gre_to_wg(
    gre_interface_ip_address: str,
    interface_ip: str,
    remote_gre_interface_ip_address: str,
    remote_tunnel_end_ip: str,
    frr_container_name: str = "frr",
    replace_file_path: str = "/rr-ip-replace.txt",
):
    # TODO when proper python client API will be created for this then replace this with python client code
    run_command(
        [
            "docker",
            "exec",
            "-t",
            frr_container_name,
            "sh",
            "-c",
            "echo '"
            + gre_interface_ip_address
            + "=>"
            + interface_ip
            + "' >> "
            + replace_file_path,
        ]
    )
    run_command(
        [
            "docker",
            "exec",
            "-t",
            frr_container_name,
            "sh",
            "-c",
            "echo '"
            + remote_gre_interface_ip_address
            + "=>"
            + remote_tunnel_end_ip
            + "' >> "
            + replace_file_path,
        ]
    )


def add_bgp_loop_interface_with_lcp():
    run_command(["sudo", "vppctl", "create", "loopback", "interface"])
    # run_command(["sudo", "vppctl", "lcp", "create", "loop0", "host-if", "bgp-loop", "netns", os.environ["NODE_FRR_NETNS"], "tun"])
    run_command(["sudo", "vppctl", "set", "int", "state", "loop0", "up"])
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "int",
            "ip",
            "address",
            "loop0",
            os.environ["LAB_" + os.environ["NODE"] + "_BGP_LOOP_IP"] + "/32",
        ]
    )


def add_frr_configuration(
    wg_interface_info: List[Tuple[str, str, int]],
    use_ebgp: bool,
    customer_filtering: str = "",
    ospf_zebra_filtering: str = "",
):
    customer_filtering_route_map = (
        f"""{customer_filtering}
ip prefix-list other seq 5 permit any
!
route-map customer-filtering deny 5
 match ip address prefix-list customer-underlay
!
route-map customer-filtering permit 10
 match ip address prefix-list other
!"""
        if customer_filtering
        else ""
    )
    ospf_zebra_route_map = (
        f"""
!
! filtering out installation of WG and BGP loopback subnets that are not needed for this node
ip protocol ospf route-map ospf-zebra-filtering
!
{ospf_zebra_filtering}
ip prefix-list other2 seq 5 permit any
!
route-map ospf-zebra-filtering permit 5
match ip address prefix-list wg-and-bgp-loopbacks-needed
!
route-map ospf-zebra-filtering deny 10
 match ip address prefix-list all-wg-and-bgp-loopbacks
!
route-map ospf-zebra-filtering permit 15
 match ip address prefix-list other2
!"""
        if ospf_zebra_filtering
        else ""
    )

    wg_interface_frr_config = ""
    for wg_name, wg_ip, wg_link_index in wg_interface_info:
        wg_interface_frr_config += f"""!
interface {wg_name}
 ip address {wg_ip}
 # 0.0.0.0 is static as all core-OSPF ends on all nodes are in the same OSPF area
 ip ospf 2 area 0.0.0.0
 ip ospf network point-to-point
 ip ospf hello-interval {os.environ["VPP_CORE_OSPF_HELLO_INTERVAL"]}
 ip ospf dead-interval {os.environ["VPP_CORE_OSPF_DEAD_INTERVAL"]}
 ip ospf cost {os.environ[f"VPP_CORE_OSPF_NODE_CONNECTION{wg_link_index}_COST"]}
!
"""
    if use_ebgp:
        customer_filtering_for_neighbor = (
            f"neighbor {os.environ[os.environ['CLIENT'] + '_BGP_LOOP_IP']} route-map customer-filtering out"
            if customer_filtering
            else "!"
        )
        customer_interface_config = f"""interface {os.environ[os.environ["VPP"] + "_LAN_INTF"]}
 ip address {os.environ[os.environ["VPP"] + "_LAN_INTF_IP"]}/{os.environ[os.environ["VPP"] + "_LAN_INTF_IP_MASK"]}
!"""
        ospf_one_config = "!"
        bgp_router_and_filtering_config = f"""!{customer_filtering_route_map}
# BGP ASN is the same for all BGP nodes -> 64512 is static ASN
router bgp 64512
 bgp router-id {os.environ["LAB_" + os.environ["NODE"] + "_BGP_LOOP_IP"]}
 # need to disable default need for policy to be talk to other eBGP peers
 no bgp ebgp-requires-policy
# no bgp suppress-duplicates
# no bgp network import-check
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} remote-as internal
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} update-source lo
 # change next hop to self to not need to distribute also customer's eBGP router id (bgp loop ip)
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} next-hop-self
 # in case of peer connection failure, retry connection every 10s
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} timers connect {os.environ["BGP_PEER_CONNECTION_RETRY_INTERVAL"]}
# neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} timers 5 15
 neighbor {os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"]} remote-as external
 neighbor {os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"]} update-source lo
 neighbor {os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"]} ebgp-multihop 20
 {customer_filtering_for_neighbor}
 !
 address-family ipv4 unicast
  network {os.environ[os.environ["VPP"] + "_LAN_INTF_IP_NETWORK"]}
 exit-address-family
!{ospf_zebra_route_map}"""

    else:  # customer OSPF (OSPF1)
        customer_filtering_route_map_ref = (
            " route-map customer-filtering" if customer_filtering else ""
        )
        customer_interface_config = f"""interface {os.environ[os.environ["VPP"] + "_LAN_INTF"]}
 ip address {os.environ[os.environ["VPP"] + "_LAN_INTF_IP"]}/{os.environ[os.environ["VPP"] + "_LAN_INTF_IP_MASK"]}
 ip ospf 1 area {os.environ[os.environ["VPP"] + "_CUSTOMER_OSPF_AREA"]}
 ip ospf network point-to-point
 ip ospf hello-interval {os.environ["VPP_CUSTOMER_OSPF_HELLO_INTERVAL"]}
 ip ospf dead-interval {os.environ["VPP_CUSTOMER_OSPF_DEAD_INTERVAL"]}
!"""
        ospf_one_config = f"""router ospf 1
 ospf router-id {os.environ[os.environ["VPP"] + "_CUSTOMER_OSPF_ROUTER_ID"]}
 redistribute bgp{customer_filtering_route_map_ref}
!"""
        bgp_router_and_filtering_config = f"""# BGP ASN is the same for all BGP nodes -> 64512 is static ASN
router bgp 64512
 bgp router-id {os.environ["LAB_" + os.environ["NODE"] + "_BGP_LOOP_IP"]}
# no bgp ebgp-requires-policy
# no bgp suppress-duplicates
# no bgp network import-check
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} remote-as internal
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} update-source lo
 # in case of peer connection failure, retry connection every 10s
 neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} timers connect {os.environ["BGP_PEER_CONNECTION_RETRY_INTERVAL"]}
# neighbor {os.environ["LAB_RR_BGP_LOOP_IP"]} timers 5 15
 !
 address-family ipv4 unicast
  network {os.environ[os.environ["VPP"] + "_LAN_INTF_IP_NETWORK"]}
  redistribute ospf 1
 exit-address-family
!{customer_filtering_route_map}{ospf_zebra_route_map}"""

    config_str = f"""!
frr version 8.3
frr defaults traditional
hostname bgp{os.environ[os.environ["NODE"] + "_INDEX"]}
service integrated-vtysh-config
log file /var/log/frr/debug.log
log stdout
log commands
no ipv6 forwarding
!
debug zebra events
debug bgp zebra
debug bgp neighbor-events
debug bgp updates
debug bgp keepalives
debug bgp update-groups
debug bgp nht
debug ospf event
debug ospf zebra
#debug ospf packet all send detail
#debug ospf packet all recv detail
debug static events
debug static route
!
interface lo
 ip address {os.environ["LAB_" + os.environ["NODE"] + "_BGP_LOOP_IP"]}/32
 ip ospf 2 area 0.0.0.0
!
{wg_interface_frr_config}
{customer_interface_config}
{ospf_one_config}
router ospf 2
 ospf router-id {os.environ[os.environ["VPP"] + "_CORE_OSPF_ROUTER_ID"]}
!
{bgp_router_and_filtering_config}
line vty
!
"""
    # clean previous configuration (the vtysh -b just adds stuff, but can delete it -> need to wipe out everything)
    # subprocess.run(
    #     "sudo sh -c \"echo '' > /etc/frr/frr.conf\"", shell=True, capture_output=True
    # )
    # subprocess.run("sudo vtysh -b", shell=True, capture_output=True)
    # time.sleep(2)

    # add new configuration
    with open(os.environ["NODE_FRR_TMP_FRR_CONFIG_FILE"], "w") as frr_config:
        frr_config.write(config_str)
    return True


def add_nat_configuration(
    wg_ports_to_open: List[int], tcp_ports: List[int] = [], udp_ports: List[int] = []
):
    run_command(
        [
            "sudo",
            "vppctl",
            "nat44",
            "plugin",
            "enable",
            "sessions",
            os.environ["VPP_NAT_SESSION_COUNT"],
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "int",
            "nat44",
            "in",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "int",
            "nat44",
            "out",
            os.environ[os.environ["VPP"] + "_WAN_INTF"],
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "nat44",
            "add",
            "address",
            os.environ[os.environ["VPP"] + "_WAN_INTF_IP"],
        ]
    )  # ip address of eth4
    # run_command(["sudo", "vppctl", "nat44", "forward", "enable"])  # disables the NAT drop of unknown UDP, but it doesn't help the performance :/
    for port in wg_ports_to_open:
        run_command(
            [
                "sudo",
                "vppctl",
                "nat44",
                "add",
                "identity",
                "mapping",
                "external",
                os.environ[os.environ["VPP"] + "_WAN_INTF"],
                "udp",  # wireguard's encrypted communication are UDP packets
                str(port),
            ]
        )
    for port in tcp_ports:
        run_command(
            [
                "sudo",
                "vppctl",
                "nat44",
                "add",
                "identity",
                "mapping",
                "external",
                os.environ[os.environ["VPP"] + "_WAN_INTF"],
                "tcp",
                str(port),
            ]
        )
    for port in udp_ports:
        run_command(
            [
                "sudo",
                "vppctl",
                "nat44",
                "add",
                "identity",
                "mapping",
                "external",
                os.environ[os.environ["VPP"] + "_WAN_INTF"],
                "udp",
                str(port),
            ]
        )


def add_acl_configuration():
    # NOTE: this is test ACL configuration that has nothing to do with productions requirements (unknown currently)
    # -> will parametrize into env file only the one ip address that is denied
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "acl-plugin",
            "acl",
            "deny",
            "dst",
            os.environ["VPP_ACL_DENIED_IP"] + "/32,permit",
            "tag",
            "my-test-rules",
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "acl-plugin",
            "interface",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
            "input",
            "acl",
            "0",
        ]
    )
    # for ACL info use this VPP CLI:
    # sh acl-plugin acl
    # sh acl-plugin interface sw_if_index 1


def add_client_neighbour_info():
    """Adds neighbor L2 information to VPP so that VPP won't drop packets from TRex and send ARP packets(=question
    for client)"""

    # using MAC address of client interface (or at least what TREX traffic destination MAC address that VPP must
    # steer back to Trex through client interface)
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "neighbor",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_MAC"],
        ]
    )
    # NOTE: this could be also moved to bootstrap.vpp as it is static for given vpp-client setup


# Note: this does not include RR-node wireguard tunnel (for that see makefile) and RR setup => only path from linux WG
# on node to BGP in container on node
def add_routes_for_bidirectional_bgp_communication():
    # Some path explanation:
    # RR-to-node path: node-linux-wg0 -(adding here route1+iptables forwarding)-> FRR container default interface ->
    #   FRR container routing to local loopback -(ping echo going back, need to add route2)-> FRR container default
    #   interface -(routing path was added as part of wg configuration)-> node-linux-wg0
    # Node-to-RR path: FRR instance in FRR container -(need to add route3)-> FRR container default interface
    #   -> node linux host route(actually controlled by WG allowed ip configuration) -> wg tunnel to RR

    # this can be hardcoded unless you want change default networking for all docker containers
    host_ip_from_docker_container = "172.17.0.1"

    # adding route1
    frr_container_ip_address = run_command(
        [
            "docker",
            "inspect",
            "-f",
            "'{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'",
            os.environ["NODE_FRR_CONTAINER_NAME"],
        ]
    )
    frr_container_ip_address = frr_container_ip_address.replace("\n", "").replace(
        "'", ""
    )
    try:
        run_command(
            [
                "sudo",
                "ip",
                "route",
                "add",
                os.environ["LAB_" + os.environ["NODE"] + "_BGP_LOOP_IP"],
                "via",
                frr_container_ip_address,
            ]
        )
    except RuntimeError:
        pass  # route already exists
    # allow packet pass from safe wireguard interface into docker container (i guess it is disabled by default because
    # safe wireguard interface is external interface and therefore seen as unsafe outside world)
    run_command(
        [
            "sudo",
            "iptables",
            "-A",
            "FORWARD",
            "-i",
            os.environ["LAB_" + os.environ["NODE"] + "_LINUX_WG_INTERFACE"],
            "-o",
            "docker0",  # static for default docker installation
            "-j",
            "ACCEPT",
        ]
    )
    # adding route2
    try:
        run_command(
            [
                "docker",
                "exec",
                "-t",
                os.environ["NODE_FRR_CONTAINER_NAME"],
                "ip",
                "route",
                "add",
                os.environ["LAB_RR_WG_INTERFACE_IP"],
                "via",
                host_ip_from_docker_container,
            ]
        )
    except RuntimeError:
        pass

    try:
        # adding route3
        run_command(
            [
                "docker",
                "exec",
                "-t",
                os.environ["NODE_FRR_CONTAINER_NAME"],
                "ip",
                "route",
                "add",
                os.environ["LAB_RR_BGP_LOOP_IP"],
                "via",
                host_ip_from_docker_container,
            ]
        )
    except RuntimeError:
        pass

    # TODO check that setting "echo 1 > /proc/sys/net/ipv4/ip_forward" is always set for node (it seems to be true,
    #  just don't know where it is persisted to survive the machine reboot)


def add_ospf_lcp_fix():
    # https://lists.fd.io/g/vpp-dev/topic/83103366#19478
    # for 224.0.0.5 and 224.0.0.6 used by OSPF (https://en.wikipedia.org/wiki/Open_Shortest_Path_First)

    # run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", "local", "Forward"])
    # for i in range(4):
    #     run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", os.environ[os.environ["VPP"]+f"_WG{i}_INTERFACE_NAME"], "Accept"])

    # to steer OSPF Hello packets from FRR container to client
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "route",
            "add",
            "224.0.0.0/24",  # static due to OSPF hello packets always destined for 224.0.0.5
            "via",
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
        ]
    )

    # to get ospf hello packets from client to frr container through vpp
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "mroute",
            "add",
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
            "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
            "via",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
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
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
            "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
            "via",
            "local",  # static, set to be locally processed (processed by LCP)
            "Forward",
        ]
    )


def add_lcp_global_configuration():
    run_command(
        ["sudo", "vppctl", "lcp", "default", "netns", os.environ["NODE_FRR_NETNS"]]
    )
    run_command(["sudo", "vppctl", "lcp", "lcp-sync", "on"])  # static LCP setting
    run_command(
        ["sudo", "vppctl", "lcp", "lcp-auto-subint", "on"]
    )  # static LCP setting


def add_tap_tunnel_to_dhcp_container():
    run_command(
        [
            "sudo",
            "vppctl",
            "create",
            "tap",
            "id",
            os.environ["NODE_DHCP_VPP_INTF_TAP_ID"],
            "host-ns",
            os.environ["NODE_DHCP_NETNS"],
            "host-ip4-addr",
            os.environ["NODE_DHCP_CONTAINER_INTF_IP"]
            + "/"
            + os.environ["NODE_DHCP_CONTAINER_INTF_IP_MASK"],
            "host-if-name",
            os.environ["NODE_DHCP_CONTAINER_INTF"],
            "host-mtu-size",
            os.environ["NODE_DHCP_CONTAINER_INTF_MTU"],
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "interface",
            "state",
            os.environ["NODE_DHCP_VPP_INTF"],
            "up",
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "interface",
            "ip",
            "address",
            os.environ["NODE_DHCP_VPP_INTF"],
            os.environ["NODE_DHCP_VPP_INTF_IP"]
            + "/"
            + os.environ["NODE_DHCP_VPP_INTF_IP_MASK"],
        ]
    )


def add_dhcp_broadcast_forwarding():
    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "acl-plugin",
            "acl",
            "permit",
            "dst",
            "255.255.255.255/32",  # broadcast address is constant
            "dport",
            "67",  # static DHCP port defined in DHCP protocol (port on client side)
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "abf",
            "policy",
            "add",
            "id",
            os.environ["NODE_DHCP_ABF_INDEX_FOR_PATH_TO_DHCP_SERVER"],
            "acl",
            "1",
            # this index should be index of ACL created by previous call -> hardcoded for now # FIXME pythonization should use ACL index from previous call
            "via",
            os.environ["NODE_DHCP_CONTAINER_INTF_IP"],
            os.environ["NODE_DHCP_VPP_INTF"],
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "abf",
            "attach",
            "ip4",
            "policy",
            os.environ["NODE_DHCP_ABF_INDEX_FOR_PATH_TO_DHCP_SERVER"],
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
        ]
    )

    run_command(
        [
            "sudo",
            "vppctl",
            "set",
            "acl-plugin",
            "acl",
            "permit",
            "dst",
            "255.255.255.255/32",  # broadcast address is constant
            "dport",
            "68",  # another static DHCP port defined in DHCP protocol (port on DHCP server side)
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "abf",
            "policy",
            "add",
            "id",
            os.environ["NODE_DHCP_ABF_INDEX_FOR_PATH_TO_DHCP_CLIENT"],
            "acl",
            "2",
            # this index should be index of ACL created by previous call -> hardcoded for now # FIXME pythonization should use ACL index from previous call
            "via",
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
        ]
    )
    run_command(
        [
            "sudo",
            "vppctl",
            "abf",
            "attach",
            "ip4",
            "policy",
            os.environ["NODE_DHCP_ABF_INDEX_FOR_PATH_TO_DHCP_CLIENT"],
            os.environ["NODE_DHCP_VPP_INTF"],
        ]
    )


def add_dhcp_unicast_forwarding():
    # unicast should be handled by automatically added routes from ip address setting on interfaces (LAN and tap to
    # DHCP container), but arp neighbor checking can get into way at DHCP server to DHCP client path
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "neighbor",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_MAC"],
        ]
    )


def add_dhcp_configuration():
    add_tap_tunnel_to_dhcp_container()
    add_dhcp_broadcast_forwarding()
    add_dhcp_unicast_forwarding()
    with ExtendedVPPAPIClient() as client:
        configure_dhcp(client)


def configure_dhcp(client):
    config = (
        """
{
    "Dhcp4": {
        // for all keys for this config check https://gitlab.isc.org/isc-projects/kea/-/blob/master/doc/examples/kea4/all-keys.json?ref_type=heads
        "subnet4": [
            {
                "subnet": """
        + '"'
        + os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP_NETWORK"]
        + '"'
        + """,
                "pools": [
                    {
                        "pool": """
        + '"'
        + os.environ[os.environ["NODE"] + "_DHCP_START_IP"]
        + "-"
        + os.environ[os.environ["NODE"] + "_DHCP_END_IP"]
        + '"'
        + """
                    }
                ],
                // Specifies that this subnet is selected for requests
                // received on a particular interface.
                "interface": """
        + '"'
        + os.environ["NODE_DHCP_CONTAINER_INTF"]
        + '"'
        + """,

                // Specify whether the server should look up global reservations.
                "reservations-global": false,

                // Specify whether the server should look up in-subnet reservations.
                "reservations-in-subnet": true,

                // Specify whether the server can assume that all reserved addresses
                // are out-of-pool.
                // Ignored when reservations-in-subnet is false.
                // If specified, it is inherited by "shared-networks" and
                // "subnet4" levels.
                "reservations-out-of-pool": false,

                "reservations": [
                    // This is a reservation for a specific hardware/MAC address.
                    {
                        "hw-address": """
        + '"'
        + os.environ[os.environ["CLIENT"] + "_VPP_INTF_MAC"]
        + '"'
        + """,
                        "ip-address": """
        + '"'
        + os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"]
        + '"'
        + """,
                        "hostname": """
        + '"'
        + os.environ[os.environ["NODE"] + "_DHCP_HOST_NAME"]
        + '"'
        + """,

                        // Reservation-specific list of DHCP options.
                        // for all options check https://gitlab.isc.org/isc-projects/kea/-/blob/master/doc/examples/kea4/all-options.json?ref_type=heads
                        // or check options in DHCP rfc(could have different names but is the source of truth for DHCP protocol) https://datatracker.ietf.org/doc/html/rfc2132 (i.e https://datatracker.ietf.org/doc/html/rfc2132#section-3.5)
                        "option-data": [
                           {
                                "code": 3,
                                "data": """
        + '"'
        + os.environ[os.environ["VPP"] + "_LAN_INTF_IP"]
        + '"'
        + """,
                                // only 1 router, the default gateway
                                "name": "routers"
                           },
                           {
                                "code": 6,
                                "data": """
        + '"'
        + os.environ[os.environ["NODE"] + "_DHCP_DNS"]
        + '"'
        + """,
                                "name": "domain-name-servers"
                           },
                           {
                                "code": 15,
                                "data": """
        + '"'
        + os.environ[os.environ["NODE"] + "_DHCP_DOMAIN_NAME"]
        + '"'
        + """,
                                "name": "domain-name"
                           },
                           {
                                "code": 26,
                                "data": """
        + '"'
        + os.environ[os.environ["CLIENT"] + "_VPP_INTF_MTU"]
        + '"'
        + """,
                                "name": "interface-mtu"
                           },
                           {
                                "code": 42,
                                // ping of ntp.ubuntu.com
                                "data": """
        + '"'
        + os.environ[os.environ["NODE"] + "_DHCP_NTP_SERVERS"]
        + '"'
        + """,
                                "name": "ntp-servers"
                           },
                           {
                              "code": 121,
                              // please mind the convenience notation used:
                              // subnet1 - router1 IP addr, subnet2 - router2 IP addr, ..., subnetN - routerN IP addr
                              "data": """
        + '"'
        + os.environ["NODE_DHCP_CONTAINER_INTF_IP"]
        + "/32"
        + " - "
        + os.environ[os.environ["VPP"] + "_LAN_INTF_IP"]
        + '"'
        + """,
                              "name": "classless-static-route",
                              // needed to parse "data" as string and requiring "data" in hexadecimal format
                              "csv-format": true
                           }
                        ]
                    }
                ]
            }
        ],
        "interfaces-config": {
            // Specifies a list of interfaces on which the Kea DHCPv4
            // server should listen to DHCP requests.
            "interfaces": [
                """
        + '"'
        + os.environ["NODE_DHCP_CONTAINER_INTF"]
        + '"'
        + """
            ],
            "dhcp-socket-type": "raw",
            "service-sockets-max-retries": 20,
            "service-sockets-require-all": true
        },
        "control-socket": {
            "socket-type": "unix",
            "socket-name": """
        + '"'
        + os.environ["NODE_DHCP_CONTROL_SOCKET"]
        + '"'
        + """
        },
        // for timers meaning see http://www.tcpipguide.com/free/t_DHCPLeaseRenewalandRebindingProcesses-2.htm
        "renew-timer": """
        + os.environ["NODE_DHCP_RENEW_TIMER"]
        + """,
        "rebind-timer": """
        + os.environ["NODE_DHCP_REBIND_TIMER"]
        + """,
        "valid-lifetime": """
        + os.environ["NODE_DHCP_VALID_LIFETIME"]
        + """,
        "loggers": [
            {
                "name": "kea-dhcp4",
                "output-options": [
                    {
                        "output": "stdout"
                    }
                ],
                // "severity": "INFO"
                "severity": """
        + '"'
        + os.environ["NODE_DHCP_LOG_LEVEL"]
        + '"'
        + """,
                // Debug level, a value between 0..99. The greater the value
                // the more detailed the debug log.
                "debuglevel": """
        + os.environ["NODE_DHCP_DEBUG_LEVEL"]
        + """
            }
        ],
        "lease-database": {
            "type": "memfile",
            "persist": true,
            "name": """
        + '"'
        + os.environ["NODE_DHCP_LEASE_DB_FILE"]
        + '"'
        + """
        }
    }
}
    """
    )

    reply = client.add_configuration(
        models.DHCPConfigurationItem(
            config=config,
            restart_before_config_apply=True,  # need only when new interfaces were created after DHCP server start
        )
    )
    pprint(reply, width=200)  # TODO error handling


def add_multiple_wireguard_tunnels(
    client, vpp_pairs_to_connect_together, redundant_link_count=1
):
    for _, (src_vpp, dst_vpp) in enumerate(vpp_pairs_to_connect_together):
        for link_index in range(redundant_link_count):
            for i in range(WG_TUNNELS_PER_CONNECTION):
                wg_index = link_index * WG_TUNNELS_PER_CONNECTION + i
                wan_suffix = "2" if link_index == 1 else ""
                add_wireguard_tunnel(
                    client,
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_INTERFACE_NAME"
                    ],
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_INTERFACE_IP"
                    ],
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_INTERFACE_IP"
                    ]
                    + "/"
                    + os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_INTERFACE_IP_MASK"
                    ],
                    int(os.environ[f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_PORT"]),
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_PRIVATE_KEY"
                    ],
                    os.environ[f"VPP{dst_vpp}_TO_VPP{src_vpp}_WG{wg_index}_PUBLIC_KEY"],
                    os.environ[
                        f"VPP{dst_vpp}_TO_VPP{src_vpp}_WG{wg_index}_INTERFACE_IP_NETWORK"
                    ],
                    os.environ[
                        f"VPP{dst_vpp}_TO_VPP{src_vpp}_WG{wg_index}_INTERFACE_IP"
                    ],
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_GRE_INTERFACE_NAME"
                    ],
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_GRE_INTERFACE_IP_ADDRESS"
                    ],
                    os.environ[
                        f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_GRE_INTERFACE_IP_ADDRESS_MASK"
                    ],
                    os.environ[
                        f"VPP{dst_vpp}_TO_VPP{src_vpp}_WG{wg_index}_GRE_INTERFACE_IP_ADDRESS"
                    ],
                    os.environ[f"VPP{src_vpp}_WAN{wan_suffix}_INTF_IP"],
                    os.environ[f"VPP{dst_vpp}_WAN{wan_suffix}_INTF_IP"],
                    int(os.environ["VPP_WG_INTF_MTU"]),
                    int(os.environ["VPP_WG_PERSISTENT_KEEPALIVE"]),
                )


def apply_frr_config(self):
    try:
        # Use secure subprocess wrapper with proper command list
        cmd = ["docker", "exec", "frr", "cp", os.environ['NODE_FRR_TMP_FRR_CONFIG_FILE'], "/etc/frr/frr.conf"]
        stdout, stderr = run_secure_command(cmd)
        
        # Use secure subprocess wrapper for vtysh command
        vtysh_cmd = ["docker", "exec", "frr", "vtysh", "-b"]
        stdout, stderr = run_secure_command(vtysh_cmd)
        
        return True
    except Exception as e:
        log.error(f"Failed to apply FRR config: {e}")
        return False
