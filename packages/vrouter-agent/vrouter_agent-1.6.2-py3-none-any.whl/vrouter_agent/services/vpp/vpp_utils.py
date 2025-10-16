import os
from enum import Enum
from typing import List, Tuple

WG_TUNNELS_PER_CONNECTION = 4


# Note: can't use StrEnum due to Python3.10 (it is Python3.11+ feature)
class UseCaseEnum(str, Enum):
    node4_fullmesh = "4nodefullmesh"
    node4_star = "4nodestar"
    node2 = "2node"
    node2_2links = "2node2links"


def set_node_identification(node, client, vpp: str):
    os.environ["NODE"] = node
    os.environ["CLIENT"] = client
    os.environ["VPP"] = vpp


def get_wg_info_for_frr(
    vpp_pairs_to_connect_together, redundant_link_count=1
) -> List[Tuple[str, str, int]]:
    wg_counter = 0
    info = []
    for _, (src_vpp, dst_vpp) in enumerate(vpp_pairs_to_connect_together):
        for link_index in range(redundant_link_count):
            for i in range(WG_TUNNELS_PER_CONNECTION):
                info.append(
                    (
                        "wg" + str(wg_counter),
                        os.environ[
                            f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{link_index * WG_TUNNELS_PER_CONNECTION + i}_GRE_INTERFACE_IP_ADDRESS"
                        ]
                        + "/"
                        + os.environ[
                            f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{link_index * WG_TUNNELS_PER_CONNECTION + i}_GRE_INTERFACE_IP_ADDRESS_MASK"
                        ],
                        link_index + 1,
                    )
                )
                wg_counter += 1

    return info


def get_wg_ports(vpp_pairs_to_connect_together, redundant_link_count=1):
    return [
        os.environ[
            f"VPP{src_vpp}_TO_VPP{dst_vpp}_WG{link_index * WG_TUNNELS_PER_CONNECTION + i}_PORT"
        ]
        for _, (src_vpp, dst_vpp) in enumerate(vpp_pairs_to_connect_together)
        for link_index in range(redundant_link_count)
        for i in range(WG_TUNNELS_PER_CONNECTION)
    ]


def get_customer_filtering():
    if os.environ["USE_CASE"] != UseCaseEnum.node4_star:
        return ""
    return f"""
ip prefix-list customer-underlay seq 5 permit {os.environ['CLIENT1_VPP_INTF_IP_NETWORK']} le 32
ip prefix-list customer-underlay seq 10 permit {os.environ['CLIENT2_VPP_INTF_IP_NETWORK']} le 32
ip prefix-list customer-underlay seq 15 permit {os.environ['CLIENT3_VPP_INTF_IP_NETWORK']} le 32
ip prefix-list customer-underlay seq 20 permit {os.environ['CLIENT4_VPP_INTF_IP_NETWORK']} le 32"""
    # NOTE: this could be simplified to something generic(no need to change this filtering when adding new nodes)
    # like this:
    # "ip prefix-list customer-underlay seq 5 permit 10.0.0.0/16 le 32"
    # if also 4th node's client vpp interface would be in the same subset (10.0.x.x/16), but it isn't


def get_ospf_zebra_filtering(vpp_pairs_to_connect_together):
    if os.environ["USE_CASE"] != UseCaseEnum.node4_star:
        return ""
    wg_bgp_needed_prefix_list = ""
    seq_index = 5
    dst_indexes = set()
    for wg_index in range(WG_TUNNELS_PER_CONNECTION):
        for _, (src_vpp, dst_vpp) in enumerate(vpp_pairs_to_connect_together):
            wg_bgp_needed_prefix_list += (
                f"ip prefix-list wg-and-bgp-loopbacks-needed seq {seq_index} permit "
                f"{os.environ[f'VPP{src_vpp}_TO_VPP{dst_vpp}_WG{wg_index}_INTERFACE_IP_NETWORK']} le 32\n"
            )
            dst_indexes.add(dst_vpp)
            seq_index += 5
    for dst_index in dst_indexes:
        wg_bgp_needed_prefix_list += (
            f"ip prefix-list wg-and-bgp-loopbacks-needed seq {seq_index} permit "
            f"{os.environ['LAB_NODE' + str(dst_index) + '_BGP_LOOP_IP']}/32\n"
        )
    all_wg_and_bgp_loopbacks = f"""ip prefix-list all-wg-and-bgp-loopbacks seq 5 permit {os.environ['VPP_ALL_WG_NETWORK']} le 32
ip prefix-list all-wg-and-bgp-loopbacks seq 10 permit {os.environ['ALL_BGP_LOOPBACKS_NETWORK']} le 32"""
    return wg_bgp_needed_prefix_list + all_wg_and_bgp_loopbacks
