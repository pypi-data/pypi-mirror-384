import os

from vpp_vrouter.client import ExtendedVPPAPIClient

from vrouter_agent.utils import load_env_variables, run_command
from vrouter_agent.vpp_cli import (
    add_acl_configuration,
    add_bgp_loop_interface_with_lcp,
    add_client_neighbour_info,
    add_frr_configuration,
    add_lcp_global_configuration,
    add_multiple_wireguard_tunnels,
    add_nat_configuration,
    add_ospf_lcp_fix,
    add_routes_for_bidirectional_bgp_communication,
)
from vrouter_agent.vpp_utils import (
    UseCaseEnum,
    get_wg_info_for_frr,
    get_wg_ports,
    set_node_identification,
)


def get_vpp_pairs_to_connect_together():
    """
    Env file is filled with 4 node full mesh configuration for WG tunnels (VPP-to-VPP connection pairs (1, 2),
    (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)). This function returns the connection pairs relevant for this node (one
    from the pair is this node and the other one the node to connect from this node). The returned pairs fully
    reflect which topology/use case was choosen to setup.
    """
    match os.environ["USE_CASE"]:
        case UseCaseEnum.node4_fullmesh:
            return [(1, 2), (1, 3), (1, 4)]
        case UseCaseEnum.node4_star:
            return [(1, 2), (1, 3), (1, 4)]
        case _:  # UseCaseEnum.node2 or UseCaseEnum.node2_2links
            return [(1, 2)]


def get_redundant_link_count():
    return 2 if os.environ["USE_CASE"] == UseCaseEnum.node2_2links else 1


def add_proper_next_hop_route_for_second_redundant_wan_link():
    if os.environ["USE_CASE"] != UseCaseEnum.node2_2links:
        return

    # with just one WAN the Gateway (route's next hop) is defined as part of default route in bootstrap.vpp, but for
    # 2 WAN interfaces one WAN interface can't use default route (and the other still can) because default route can't
    # lead to 2 output interfaces (well it can but then it is loadbalancing and that is not what we want)
    # -> solution is to add non-default routes for one WAN interface (i choose the 2.WAN) and define the gateway (next
    # hop) there -> implication are that for the route construction we need the destination IP (for 1.WAN we had default
    # route so no need narrow destination) and need to do this for 2.WAN IP's of all other node -> adding node means to
    # add this kind of route to all other nodes (well, only for nodes that should have 2.WAN connection to that newly
    # added node)
    other_side_vpp = "VPP2"
    run_command(
        [
            "sudo",
            "vppctl",
            "ip",
            "route",
            "add",
            os.environ[other_side_vpp + "_WAN2_INTF_IP"] + "/32",
            "via",
            os.environ[os.environ["VPP"] + "_WAN2_INTF_GW_IP"],
            os.environ[os.environ["VPP"] + "_WAN2_INTF"],
        ]
    )


def run():
    print("Configuring VPP1 using VPP CLI...")
    load_env_variables()
    set_node_identification("NODE1", "CLIENT1", "VPP1")
    use_ebgp = False if os.environ.get("useEBGP") is None else True

    add_lcp_global_configuration()
    with ExtendedVPPAPIClient() as client:
        add_multiple_wireguard_tunnels(
            client,
            get_vpp_pairs_to_connect_together(),
            redundant_link_count=get_redundant_link_count(),
        )
    add_proper_next_hop_route_for_second_redundant_wan_link()
    add_bgp_loop_interface_with_lcp()
    add_ospf_lcp_fix()
    add_frr_configuration(
        get_wg_info_for_frr(
            get_vpp_pairs_to_connect_together(),
            redundant_link_count=get_redundant_link_count(),
        ),
        use_ebgp,
        # customer_filtering=get_customer_filtering(),
    )
    # TODO: add failover for client to internet (NAT) use case
    add_nat_configuration(
        get_wg_ports(
            get_vpp_pairs_to_connect_together(),
            redundant_link_count=get_redundant_link_count(),
        )
    )  # TODO this makes performance problems(client1-vpp1-vpp2-client1 path) -> without this the packets are handled in multiple threads but with this is one thread only!
    add_acl_configuration()
    add_client_neighbour_info()
    add_routes_for_bidirectional_bgp_communication()
    # add_dhcp_configuration()
    print("Done.")
