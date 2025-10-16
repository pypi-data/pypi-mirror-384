import subprocess
import time
import os

from vrouter_agent.utils import run_command, load_env_variables
from vrouter_agent.vpp_utils import UseCaseEnum


def add_frr_configuration():
    def get_router_neighbor_config_block(node_index):
        return f""" neighbor {os.environ[f"LAB_NODE{node_index}_BGP_LOOP_IP"]} remote-as internal
 neighbor {os.environ[f"LAB_NODE{node_index}_BGP_LOOP_IP"]} update-source lo
 # in case of peer connection failure, retry connection every X seconds
 neighbor {os.environ[f"LAB_NODE{node_index}_BGP_LOOP_IP"]} timers connect {os.environ["BGP_PEER_CONNECTION_RETRY_INTERVAL"]}"""

    def get_af_neighbor_config_block(node_index):
        return f"  neighbor {os.environ[f'LAB_NODE{node_index}_BGP_LOOP_IP']} route-reflector-client"

    router_neighbors = ""
    fix_route_maps = ""
    af_bgp_filtering = ""
    bgp_filtering = ""
    match os.environ["USE_CASE"]:
        case str(UseCaseEnum.node4_fullmesh):
            router_neighbor = (
                get_router_neighbor_config_block(1)
                + "\n"
                + get_router_neighbor_config_block(2)
                + "\n"
                + get_router_neighbor_config_block(3)
                + "\n"
                + get_router_neighbor_config_block(4)
            )
            af_neighbor = (
                get_af_neighbor_config_block(1)
                + "\n"
                + get_af_neighbor_config_block(2)
                + "\n"
                + get_af_neighbor_config_block(3)
                + "\n"
                + get_af_neighbor_config_block(4)
            )
        case UseCaseEnum.node4_star:
            router_neighbor = (
                get_router_neighbor_config_block(1)
                + "\n"
                + get_router_neighbor_config_block(2)
                + "\n"
                + get_router_neighbor_config_block(3)
                + "\n"
                + get_router_neighbor_config_block(4)
            )
            af_neighbor = (
                get_af_neighbor_config_block(1)
                + "\n"
                + get_af_neighbor_config_block(2)
                + "\n"
                + get_af_neighbor_config_block(3)
                + "\n"
                + get_af_neighbor_config_block(4)
            )
            fix_route_maps = """
 # for a route reflector to apply a route-map to reflected routes
 bgp route-reflector allow-outbound-policy"""
            af_bgp_filtering = f"""
  neighbor {os.environ["LAB_NODE2_BGP_LOOP_IP"]} prefix-list bgp2-filter out
  neighbor {os.environ["LAB_NODE3_BGP_LOOP_IP"]} prefix-list bgp3-filter out
  neighbor {os.environ["LAB_NODE4_BGP_LOOP_IP"]} prefix-list bgp4-filter out"""
            start_index = int(os.environ["CLIENT1_SIMULATION_SUBNET_INDEX_START"])
            bgp_filtering = f"""
ip prefix-list bgp2-filter seq 5 permit {os.environ["CLIENT1_VPP_INTF_IP_NETWORK"]}
ip prefix-list bgp2-filter seq 10 permit {os.environ["CLIENT1_SIMULATION_SUBNET_PREFIX"]}{str(start_index)}{os.environ["CLIENT1_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ["CLIENT1_SIMULATION_VETH_INF_IP_MASK"]}
ip prefix-list bgp2-filter seq 15 permit {os.environ["CLIENT1_SIMULATION_SUBNET_PREFIX"]}{str(start_index+1)}{os.environ["CLIENT1_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ["CLIENT1_SIMULATION_VETH_INF_IP_MASK"]}
ip prefix-list bgp2-filter seq 20 deny any
!
ip prefix-list bgp3-filter seq 5 permit {os.environ["CLIENT1_VPP_INTF_IP_NETWORK"]}
ip prefix-list bgp3-filter seq 10 permit {os.environ["CLIENT1_SIMULATION_SUBNET_PREFIX"]}{str(start_index+2)}{os.environ["CLIENT1_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ["CLIENT1_SIMULATION_VETH_INF_IP_MASK"]}
ip prefix-list bgp3-filter seq 15 permit {os.environ["CLIENT1_SIMULATION_SUBNET_PREFIX"]}{str(start_index+3)}{os.environ["CLIENT1_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ["CLIENT1_SIMULATION_VETH_INF_IP_MASK"]}
ip prefix-list bgp3-filter seq 20 deny any
!
ip prefix-list bgp4-filter seq 5 permit {os.environ["CLIENT1_VPP_INTF_IP_NETWORK"]}
ip prefix-list bgp4-filter seq 10 permit {os.environ["CLIENT1_SIMULATION_SUBNET_PREFIX"]}{str(start_index+4)}{os.environ["CLIENT1_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ["CLIENT1_SIMULATION_VETH_INF_IP_MASK"]}
ip prefix-list bgp4-filter seq 15 permit {os.environ["CLIENT1_SIMULATION_SUBNET_PREFIX"]}{str(start_index+5)}{os.environ["CLIENT1_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ["CLIENT1_SIMULATION_VETH_INF_IP_MASK"]}
ip prefix-list bgp4-filter seq 20 deny any"""
        case _:  # UseCaseEnum.node2 or UseCaseEnum.node2_2links
            router_neighbor = (
                get_router_neighbor_config_block(1)
                + "\n"
                + get_router_neighbor_config_block(2)
            )
            af_neighbor = (
                get_af_neighbor_config_block(1) + "\n" + get_af_neighbor_config_block(2)
            )

    config_str = f"""!
frr version 8.1
frr defaults traditional
hostname rr
service integrated-vtysh-config
! there is problem with applying logging to file like this:
!log file /var/log/frr/debug.log
! => using syslog instead that logs to /var/log/frr/frr.log
log syslog debugging
!log syslog informational
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
debug static events
debug static route
!
# BGP ASN is the same for all BGP nodes -> 64512 is static ASN
router bgp 64512
 bgp router-id {os.environ["LAB_RR_BGP_LOOP_IP"]}{fix_route_maps}
# no bgp ebgp-requires-policy
# no bgp suppress-duplicates
# no bgp network import-check
{router_neighbor}
 !
 address-family ipv4 unicast
{af_neighbor}{af_bgp_filtering}
 exit-address-family
!{bgp_filtering}
line vty
!
"""
    # clean previous configuration (the vtysh -b just adds stuff, but can delete it -> need to wipe out everything)
    subprocess.run(
        "sudo sh -c \"echo '' > /etc/frr/frr.conf\"", shell=True, capture_output=True
    )
    subprocess.run("sudo vtysh -b", shell=True, capture_output=True)
    subprocess.run("sudo systemctl restart frr", shell=True, capture_output=True)
    time.sleep(2)

    # add new configuration
    with open(r"/etc/frr/frr.conf", "w") as frr_config:
        frr_config.write(config_str)
    subprocess.run("sudo vtysh -b", shell=True, capture_output=True)
    # subprocess.run("sudo systemctl restart frr", shell=True, capture_output=True)


def add_bgp_loop():
    try:
        run_command(
            ["sudo", "ip", "addr", "add", os.environ["LAB_RR_BGP_LOOP_IP"], "dev", "lo"]
        )
    except subprocess.CalledProcessError as e:
        print(f"Error adding loopback address: {e}")
        pass
    except RuntimeError as e:
        print(f"Error adding loopback address: {e}")
        pass


def run():
    print("Configuring RR using linux commands...")
    load_env_variables()
    add_frr_configuration()
    add_bgp_loop()
    print("Done.")
