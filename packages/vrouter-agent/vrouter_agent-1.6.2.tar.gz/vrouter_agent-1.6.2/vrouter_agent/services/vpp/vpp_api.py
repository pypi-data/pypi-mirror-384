import ipaddress
import os
from itertools import chain
from typing import List
from loguru import logger as log
from vpp_vrouter.common import models

from vrouter_agent.utils import run_command

WG_TUNNELS_PER_CONNECTION = 4


def add_vpp_route(
    client,
    dest_net: str,
    next_hop_addr: str,
    outgoing_iface: str,
):
    reply = client.add_configuration(
        models.RouteConfigurationItem(
            destination_network=dest_net,
            next_hop_address=next_hop_addr,
            outgoing_interface=outgoing_iface,
        )
    )
    log.debug(reply)  # TODO error handling


def add_linux_route(
    client,
    dest_net: str,
    next_hop_addr: str = "",
    outgoing_iface: str = "",
    container: str = "",  # empty container name means default linux namespace
):
    reply = client.add_configuration(
        models.LinuxRouteConfigurationItem(
            docker_container_name=container,
            destination_network=dest_net,
            next_hop_address=next_hop_addr,
            outgoing_interface=outgoing_iface,
        )
    )
    log.debug(reply)  # TODO error handling


def add_lcp_interface(
    client,
    vpp_iface: str,
    host_iface: str,
    host_netns: str,
    is_tun: bool = False,
):
    iface_type = (
        models.LCPHostInterfaceTypeEnum.TUN
        if is_tun
        else models.LCPHostInterfaceTypeEnum.TAP
    )
    reply = client.add_configuration(
        models.LCPPairConfigurationItem(
            interface=vpp_iface,
            mirror_interface_host_name=host_iface,
            mirror_interface_type=iface_type,
            host_namespace=host_netns,
        )
    )
    log.debug(reply)  # TODO error handling


def add_wireguard_interface(
    client,
    interface_name: str,
    interface_ip_network: str,
    port: int,
    private_key: str,
    src_ip: str,
    mtu: int,
):
    reply = client.add_configuration(
        models.InterfaceConfigurationItem(
            name=interface_name,
            type=models.InterfaceType.WIREGUARD_TUNNEL,
            enabled=True,
            ip_addresses=[interface_ip_network],
            mtu=mtu,
            link=models.WireguardInterfaceLink(
                private_key=private_key,
                port=port,
                src_addr=ipaddress.IPv4Address(src_ip),
            ),
        )
    )
    log.debug(reply)  # TODO error handling


def add_wireguard_peer(
    client,
    interface_name: str,
    port: int,
    endpoint: str,
    remote_public_key: str,
    persistent_keepalive: int,
):
    reply = client.add_configuration(
        models.WireguardPeerConfigurationItem(
            public_key=remote_public_key,
            port=port,
            endpoint=ipaddress.IPv4Address(endpoint),
            allowed_ips=["0.0.0.0/0"],
            wg_if_name=interface_name,
            persistent_keepalive=persistent_keepalive,
        )
    )
    log.debug(reply)  # TODO error handling


def add_wireguard_tunnel(
    client,
    interface_name: str,
    interface_ip: str,
    interface_ip_network: str,
    port: int,
    private_key: str,
    remote_public_key: str,
    remote_ip_network: str,
    remote_tunnel_end_ip: str,
    gre_interface_name: str,
    gre_interface_ip_address: str,
    gre_interface_ip_address_mask: str,
    remote_gre_interface_ip_address: str,
    src_ip: str,
    dst_ip: str,
    mtu: int,
    keepalive: int,
):
    add_wireguard_interface(
        client,
        interface_name,
        interface_ip_network,
        port,
        private_key,
        src_ip,
        mtu,
    )
    add_wireguard_peer(
        client,
        interface_name,
        port,
        dst_ip,
        remote_public_key,
        keepalive,
    )

    # add_route_to_wireguard_peer(interface_name, remote_ip_network, remote_tunnel_end_ip)
    add_gre_tunnel_to_wg_and_lcp_it_to_frr_container(
        client,
        gre_interface_name,
        gre_interface_ip_address,
        gre_interface_ip_address_mask,
        remote_gre_interface_ip_address,
        interface_name,
        remote_tunnel_end_ip,
    )

    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "mroute",
            "add",
            remote_gre_interface_ip_address,
            "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
            "via",
            gre_interface_name,
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
            remote_gre_interface_ip_address,
            "224.0.0.5",  # static destination ip address of Hello OSPF packets, fixed by OSPF protocol itself
            "via",
            "local",  # static forwarding to local processing (it will be processed by LCP)
            "Forward",
        ]
    )

    add_frr_agent_ip_translation_from_gre_to_wg(
        gre_interface_ip_address,
        interface_ip,
        remote_gre_interface_ip_address,
        remote_tunnel_end_ip,
    )
    return interface_name, f"{gre_interface_ip_address}/{gre_interface_ip_address_mask}"


def add_frr_agent_ip_translation_from_gre_to_wg(
    gre_interface_ip_address: str,
    interface_ip: str,
    remote_gre_interface_ip_address: str,
    remote_tunnel_end_ip: str,
    frr_container_name: str = "frr",
    replace_file_path: str = "/rr-ip-replace.txt",
):
    # TODO when proper python client API will be created for this then replace this with python client code
    _, code1 = run_command(
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
    _, code2 = run_command(
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
    return code1 == 0 and code2 == 0


def add_bgp_loopback(client, ip_addr: str):
    reply = client.add_configuration(
        models.InterfaceConfigurationItem(
            name="loop0",
            type=models.InterfaceType.SOFTWARE_LOOPBACK,
            enabled=True,
            ip_addresses=[ip_addr + "/32"],
        )
    )
    log.debug(reply)  # TODO error handling


def add_gre_tunnel_to_wg_and_lcp_it_to_frr_container(
    client,
    gre_interface_name: str,
    gre_interface_ip_address: str,
    gre_interface_ip_address_mask: str,
    remote_gre_interface_ip_address: str,
    interface_name: str,
    remote_tunnel_end_ip: str,
    frr_container_name: str = "frr",
):
    gre_iface = models.InterfaceConfigurationItem(
        name=gre_interface_name,
        type=models.InterfaceType.GRE_TUNNEL,
        enabled=False,
        ip_addresses=[],
        link=models.GREInterfaceLink(
            type=models.GRELinkType.L3,
            src_addr=ipaddress.IPv4Address(gre_interface_ip_address),
            dst_addr=ipaddress.IPv4Address(remote_gre_interface_ip_address),
        ),
    )

    reply = client.add_configuration(gre_iface)
    log.debug(reply)  # TODO error handling

    add_vpp_route(
        client,
        remote_gre_interface_ip_address
        + "/32",  # route to one ip address => mask /32 is static value
        remote_tunnel_end_ip,
        interface_name,
    )

    add_lcp_interface(
        client,
        gre_interface_name,
        interface_name,
        frr_container_name,
        True,
    )

    reply = client.update_configuration(
        gre_iface,
        models.InterfaceConfigurationItem(
            name=gre_interface_name,
            type=models.InterfaceType.GRE_TUNNEL,
            enabled=True,
            ip_addresses=[
                gre_interface_ip_address + "/" + gre_interface_ip_address_mask
            ],
            link=models.GREInterfaceLink(
                type=models.GRELinkType.L3,
                src_addr=ipaddress.IPv4Address(gre_interface_ip_address),
                dst_addr=ipaddress.IPv4Address(remote_gre_interface_ip_address),
            ),
        ),
    )
    log.debug(reply)  # TODO error handling


def add_frr_configuration(
    client,
    wg_iface_info: dict[str, str],
    frr_hostname: str,
    bgp_loop_ip_addr: str,
    rr_bgp_loop_ip_addr: str,
    customer_iface: str,
    customer_ip_addr: str,
    customer_ip_mask: str,
    customer_ip_net: str,
    customer_ospf_area: str,
    customer_ospf_router_id: str,
    core_ospf_router_id: str,
    customer_ospf_hello_interval: int = 2,
    customer_ospf_dead_interval: int = 8,
    core_ospf_hello_interval: int = 2,
    core_ospf_dead_interval: int = 8,
    core_ospf_cost: int = 10,
    bgp_connection_retry_interval: int = 10,
    customer_ospf_filtering: str = "",
    ospf_zebra_filtering: str = "",
):
    ospf_bgp_redistribution_route_map_ref = (
        " route-map customer-ospf-filtering" if customer_ospf_filtering else ""
    )
    ospf_bgp_redistribution_route_map = (
        f"""{customer_ospf_filtering}
ip prefix-list other seq 5 permit any
!
route-map customer-ospf-filtering deny 5
 match ip address prefix-list customer-underlay
!
route-map customer-ospf-filtering permit 10
 match ip address prefix-list other
!"""
        if customer_ospf_filtering
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
    for wg_name, wg_ip in wg_iface_info.items():
        wg_interface_frr_config += f"""!
interface {wg_name}
 ip address {wg_ip}
 # 0.0.0.0 is static as all core-OSPF ends on all nodes are in the same OSPF area
 ip ospf 2 area 0.0.0.0
 ip ospf network point-to-point
 ip ospf hello-interval {core_ospf_hello_interval}
 ip ospf dead-interval {core_ospf_dead_interval}
 ip ospf cost {core_ospf_cost}
!
"""
    config_str = f"""!
frr version 8.3
frr defaults traditional
hostname {frr_hostname}
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
 ip address {bgp_loop_ip_addr}/32
 ip ospf 2 area 0.0.0.0
!
{wg_interface_frr_config}
interface {customer_iface}
 ip address {customer_ip_addr}/{customer_ip_mask}
 ip ospf 1 area {customer_ospf_area}
 ip ospf network point-to-point
 ip ospf hello-interval {customer_ospf_hello_interval}
 ip ospf dead-interval {customer_ospf_dead_interval}
!
router ospf 1
 ospf router-id {customer_ospf_router_id}
 redistribute bgp{ospf_bgp_redistribution_route_map_ref}
!
router ospf 2
 ospf router-id {core_ospf_router_id}
!
# BGP ASN is the same for all BGP nodes -> 64512 is static ASN
router bgp 64512
 bgp router-id {bgp_loop_ip_addr}
# no bgp ebgp-requires-policy
# no bgp suppress-duplicates
# no bgp network import-check
 neighbor {rr_bgp_loop_ip_addr} remote-as internal
 neighbor {rr_bgp_loop_ip_addr} update-source lo
 # in case of peer connection failure, retry connection every 10s
 neighbor {rr_bgp_loop_ip_addr} timers connect {bgp_connection_retry_interval}
# neighbor {rr_bgp_loop_ip_addr} timers 5 15
 !
 address-family ipv4 unicast
  network {customer_ip_net}
  redistribute ospf 1
 exit-address-family
!{ospf_bgp_redistribution_route_map}{ospf_zebra_route_map}
line vty
!
"""
    # Apply FRR configuration to the system
    reply = client.add_configuration(models.FRRConfigurationItem(config=config_str))
    log.debug(reply)  # TODO error handling


def add_nat_configuration(
    client,
    lan_iface: str,
    wan_iface: str,
    wan_iface_addr: str,
    wg_ports_to_open: List[int],
    tcp_ports: List[int] = [],
    udp_ports: List[int] = [],
):
    lan_nat_iface = models.Nat44InterfaceConfigurationItem(
        name=lan_iface,
        nat_inside=True,
        nat_outside=False,
        output_feature=False,
    )
    wan_nat_iface = models.Nat44InterfaceConfigurationItem(
        name=wan_iface,
        nat_inside=False,
        nat_outside=True,
        output_feature=False,
    )
    nat_address_pool = models.Nat44AddressPoolConfigurationItem(
        name="nat-pool",
        first_ip=ipaddress.IPv4Address(wan_iface_addr),
        last_ip=ipaddress.IPv4Address(wan_iface_addr),
    )

    wg_port_mappings = [
        models.IdentityMapping(
            interface=wan_iface, protocol=models.ProtocolInNAT.UDP, port=p
        )
        for p in wg_ports_to_open
    ]
    tcp_port_mappings = [
        models.IdentityMapping(
            interface=wan_iface, protocol=models.ProtocolInNAT.TCP, port=p
        )
        for p in tcp_ports
    ]
    udp_port_mappings = [
        models.IdentityMapping(
            interface=wan_iface, protocol=models.ProtocolInNAT.UDP, port=p
        )
        for p in udp_ports
    ]

    nat_mappings = models.DNat44ConfigurationItem(
        label="nat-mappings",
        static_mappings=[],
        identity_mappings=list(
            chain(wg_port_mappings, tcp_port_mappings, udp_port_mappings)
        ),
    )

    reply = client.add_configuration(
        lan_nat_iface,
        wan_nat_iface,
        nat_address_pool,
        nat_mappings,
    )
    log.debug(reply)  # TODO error handling


def add_acl_configuration(
    client,
    ingress_iface: str,
    deny_network: str,
):
    reply = client.add_configuration(
        models.ACLConfigurationItem(
            name="lab-acl-rules",
            ingress=[ingress_iface],
            rules=[
                models.ACLRuleConfigurationItem(
                    action=models.ACLAction.DENY,
                    refinement=models.IPSpecification(
                        addresses=models.IPAddresses(
                            destination_network=ipaddress.IPv4Network(deny_network)
                        )
                    ),
                ),
                models.ACLRuleConfigurationItem(
                    action=models.ACLAction.PERMIT,
                ),
            ],
        )
    )
    log.debug(reply)  # TODO error handling


def add_lcp_global_configuration(client, network_namespace: str):
    reply = client.add_configuration(
        models.LCPGlobalsConfigurationItem(
            default_namespace=network_namespace,
            lcp_sync=True,
            lcp_auto_subint=True,
        )
    )
    log.debug(reply)  # TODO error handling


#
def add_node_part_of_client_to_node_frr_path(client, use_ebgp):
    if use_ebgp:
        add_ebgp_route_in_frr_container(client)
        add_ebgp_routes_in_vpp(client)
    else:
        add_ospf_lcp_fix_env(client)


def add_ebgp_route_in_frr_container(client):
    # direction to client
    add_linux_route(
        client,
        os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"],
        "",
        os.environ[os.environ["VPP"] + "_LAN_INTF"],
        os.environ["NODE_FRR_CONTAINER_NAME"],
    )
    # note: the opposite direction is handled automatically
    #  by linux network namespace as it points to present loopback interface


def add_ebgp_routes_in_vpp(client):
    # direction to client
    add_vpp_route(
        client,
        os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"] + "/32",
        os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
        os.environ[os.environ["VPP"] + "_LAN_INTF"],
    )
    # note: the opposite direction is handled correctly by LCP

    # fixing VPP's neighbor view of client's BGP loop (despite client responding to ARP packets, VPP keeps sending
    # them and doesn't learn needed things...)
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "neighbor",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
            os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"],
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_MAC"],
        ]
    )


#
def add_node_part_of_client_to_node_frr_path(client, use_ebgp):
    if use_ebgp:
        add_ebgp_route_in_frr_container(client)
        add_ebgp_routes_in_vpp(client)
    else:
        add_ospf_lcp_fix_env(client)


def add_ebgp_route_in_frr_container(client):
    # direction to client
    add_linux_route(
        client,
        os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"],
        "",
        os.environ[os.environ["VPP"] + "_LAN_INTF"],
        os.environ["NODE_FRR_CONTAINER_NAME"],
    )
    # note: the opposite direction is handled automatically
    #  by linux network namespace as it points to present loopback interface


def add_ebgp_routes_in_vpp(client):
    # direction to client
    add_vpp_route(
        client,
        os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"] + "/32",
        os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
        os.environ[os.environ["VPP"] + "_LAN_INTF"],
    )
    # note: the opposite direction is handled correctly by LCP

    # fixing VPP's neighbor view of client's BGP loop (despite client responding to ARP packets, VPP keeps sending
    # them and doesn't learn needed things...)
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "neighbor",
            os.environ[os.environ["VPP"] + "_LAN_INTF"],
            os.environ[os.environ["CLIENT"] + "_BGP_LOOP_IP"],
            os.environ[os.environ["CLIENT"] + "_VPP_INTF_MAC"],
        ]
    )


def add_ospf_lcp_fix_env(client):
    # https://lists.fd.io/g/vpp-dev/topic/83103366#19478
    # for 224.0.0.5 and 224.0.0.6 used by OSPF (https://en.wikipedia.org/wiki/Open_Shortest_Path_First)

    # run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", "local", "Forward"])
    # for i in range(4):
    #     run_command(["sudo", "vppctl", "ip", "mroute", "add", "224.0.0.0/24", "via", os.environ[os.environ["VPP"]+f"_WG{i}_INTERFACE_NAME"], "Accept"])

    # to steer OSPF Hello packets from FRR container to client
    add_vpp_route(
        client,
        "224.0.0.0/24",  # static due to OSPF hello packets always destined for 224.0.0.5
        os.environ[os.environ["CLIENT"] + "_VPP_INTF_IP"],
        os.environ[os.environ["VPP"] + "_LAN_INTF"],
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


# Note: this does not include RR-node wireguard tunnel (for that see makefile) and RR setup => only path from linux WG
# on node to BGP in container on node
def add_routes_for_bidirectional_bgp_communication_env(client):
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
    add_linux_route(
        client,
        os.environ["LAB_" + os.environ["NODE"] + "_BGP_LOOP_IP"],
        frr_container_ip_address,
    )
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
    add_linux_route(
        client,
        os.environ["LAB_RR_WG_INTERFACE_IP"],
        host_ip_from_docker_container,
        "",
        os.environ["NODE_FRR_CONTAINER_NAME"],
    )
    # adding route3
    add_linux_route(
        client,
        os.environ["LAB_RR_BGP_LOOP_IP"],
        host_ip_from_docker_container,
        "",
        os.environ["NODE_FRR_CONTAINER_NAME"],
    )
    # TODO check that setting "echo 1 > /proc/sys/net/ipv4/ip_forward" is always set for node (it seems to be true,
    #  just don't know where it is persisted to survive the machine reboot)
