import os

from vpp_vrouter.client import ExtendedVPPAPIClient

from vrouter_agent.utils import load_env_variables
from vrouter_agent.vpp.cli import add_client_neighbour_info
from vrouter_agent.vpp.vpp_api import (
    add_acl_configuration,
    add_bgp_loopback,
    add_frr_configuration,
    add_lcp_global_configuration,
    add_nat_configuration,
    add_node_part_of_client_to_node_frr_path,
    add_routes_for_bidirectional_bgp_communication_env,
)
from vrouter_agent.vpp.vpp_cli import (
    add_dhcp_configuration,
    add_multiple_wireguard_tunnels,
)
from vrouter_agent.vpp.vpp_utils import (
    UseCaseEnum,
    get_customer_filtering,
    get_ospf_zebra_filtering,
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
            return [(4, 1), (4, 2), (4, 3)]
        case UseCaseEnum.node4_star:
            return [(4, 1)]
        case _:  # UseCaseEnum.node2 or UseCaseEnum.node2_2links
            return []


def run():
    print("Configuring VPP4 using VPP CLI...")
    load_env_variables()
    set_node_identification("NODE4", "CLIENT4", "VPP4")
    use_ebgp = False if os.environ.get("useEBGP") is None else True

    with ExtendedVPPAPIClient() as client:
        add_lcp_global_configuration(client, os.environ["NODE_FRR_NETNS"])
        add_multiple_wireguard_tunnels(client, get_vpp_pairs_to_connect_together())
        add_bgp_loopback(client, os.environ["LAB_NODE4_BGP_LOOP_IP"])
        add_node_part_of_client_to_node_frr_path(client, use_ebgp)
        add_frr_configuration(
            get_wg_info_for_frr(get_vpp_pairs_to_connect_together()),
            use_ebgp,
            customer_filtering=get_customer_filtering(),
            # filtering below only for cases when node is not connected to all other nodes with direct connection
            ospf_zebra_filtering=get_ospf_zebra_filtering(
                get_vpp_pairs_to_connect_together()
            ),
        )
        add_nat_configuration(  # TODO need to add ports other stuff that goes through mgmt interface (SSH port 22 is added here so similary)
            client,
            os.environ["VPP4_LAN_INTF"],
            os.environ["VPP4_WAN_INTF"],
            os.environ["VPP4_WAN_INTF_IP"],
            get_wg_ports(get_vpp_pairs_to_connect_together()),
            ["22"],  # SSH port to NODE4
            [os.environ["LAB_NODE4_LINUX_WG_INTERFACE_PORT"]],
        )  # TODO this makes performance problems(client1-vpp1-vpp2-client1 path) -> without this the packets are handled in multiple threads but with this is one thread only!
        add_acl_configuration(
            client,
            os.environ["VPP4_LAN_INTF"],
            os.environ["VPP_ACL_DENIED_IP"] + "/32",
        )
        add_client_neighbour_info()
        add_routes_for_bidirectional_bgp_communication_env(client)
        add_dhcp_configuration()
    print("Done.")
