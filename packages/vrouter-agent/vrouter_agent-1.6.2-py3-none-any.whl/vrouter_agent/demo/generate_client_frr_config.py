import os
import sys

from vrouter_agent.utils import load_env_variables


def run():
    client_number = sys.argv[1]
    use_ebgp = True if sys.argv[2] == "1" else False
    load_env_variables(silent=True)

    if use_ebgp:
        return get_ebgp_frr_config(client_number)
    return get_ospf_frr_config(client_number)


def get_ebgp_frr_config(client_number):
    client = "CLIENT" + str(client_number)
    start = int(os.environ[client + "_SIMULATION_SUBNET_INDEX_START"])
    end = int(os.environ[client + "_SIMULATION_SUBNET_INDEX_END"])
    subnets = get_subnets(end, start, client)

    config = f"""!
frr version 8.1
frr defaults traditional
hostname usdn-client-0{client_number}
! there is problem with applying logging to file like this:
!log file /var/log/frr/debug.log
! => using syslog instead that logs to /var/log/frr/frr.log
log syslog debugging
!log syslog informational
log stdout
log commands
no ipv6 forwarding
service integrated-vtysh-config
!
debug zebra events
debug static events
! cant debug static routes in FRR 7.5.1, almalinux client machine
!debug static route
interface lo
 ip address {os.environ[client + "_BGP_LOOP_IP"]}/32
!
router bgp {str(client_number)}
 bgp router-id {os.environ[client + "_BGP_LOOP_IP"]}
 no bgp ebgp-requires-policy
 neighbor {os.environ["LAB_NODE"+str(client_number)+"_BGP_LOOP_IP"]} remote-as external
 neighbor {os.environ["LAB_NODE"+str(client_number)+"_BGP_LOOP_IP"]} update-source lo
 neighbor {os.environ["LAB_NODE"+str(client_number)+"_BGP_LOOP_IP"]} ebgp-multihop 20
 !
 address-family ipv4 unicast
  network {os.environ[client + "_VPP_INTF_IP_NETWORK"]}{subnets}
 exit-address-family
line vty
!
""".replace(
        "\n", "\\n"
    )
    print(config)


def get_subnets(end, start, client):
    subnets = ""
    for i in range(start, end + 1):
        subnets += f"""\n  network {os.environ[client + "_SIMULATION_SUBNET_PREFIX"]}{i}{os.environ[client + "_SIMULATION_SUBNET_MASK_SUFFIX"]}/{os.environ[client + "_SIMULATION_VETH_INF_IP_MASK"]}"""
    return subnets


def get_ospf_frr_config(client_number):
    client = "CLIENT" + str(client_number)
    vpp = "VPP" + str(client_number)
    start = int(os.environ[client + "_SIMULATION_SUBNET_INDEX_START"])
    end = int(os.environ[client + "_SIMULATION_SUBNET_INDEX_END"])
    subnet_interfaces = get_subnet_interfaces(end, start, client, vpp)

    config = f"""!
frr version 8.1
frr defaults traditional
hostname usdn-client-0{client_number}
! there is problem with applying logging to file like this:
!log file /var/log/frr/debug.log
! => using syslog instead that logs to /var/log/frr/frr.log
log syslog debugging
!log syslog informational
log stdout
log commands
no ipv6 forwarding
service integrated-vtysh-config
!
debug zebra events
debug static events
! cant debug static routes in FRR 7.5.1, almalinux client machine
!debug static route
{subnet_interfaces}
!
interface {os.environ[client + "_VPP_INTF"]}
 ip address {os.environ[client + "_VPP_INTF_IP"]}/{os.environ[client + "_VPP_INTF_IP_MASK"]}
 ip ospf area {os.environ[vpp + "_CUSTOMER_OSPF_AREA"]}
 ip ospf network point-to-point
 ip ospf hello-interval {os.environ["VPP_CUSTOMER_OSPF_HELLO_INTERVAL"]}
 ip ospf dead-interval {os.environ["VPP_CUSTOMER_OSPF_DEAD_INTERVAL"]}
!
router ospf
 ospf router-id {os.environ[client + "_OSPF_ROUTER_ID"]}
!
line vty
!
""".replace(
        "\n", "\\n"
    )
    print(config)


def get_subnet_interfaces(end, start, client, vpp):
    subnet_interfaces = ""
    for i in range(start, end + 1):
        subnet_interfaces += f"""!
interface {os.environ[client + "_SIMULATION_VETH_INF_NAME_PREFIX"]}{i}
 ip address {os.environ[client + "_SIMULATION_SUBNET_PREFIX"]}{i}{os.environ[client + "_SIMULATION_VETH_INF_IP_SUFFIX"]}/{os.environ[client + "_SIMULATION_VETH_INF_IP_MASK"]}
 ip ospf area {os.environ[vpp + "_CUSTOMER_OSPF_AREA"]}
"""
    return subnet_interfaces
