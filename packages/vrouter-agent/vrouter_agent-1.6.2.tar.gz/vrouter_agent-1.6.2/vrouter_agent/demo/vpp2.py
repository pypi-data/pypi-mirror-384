import ipaddress
import time

from vpp_vrouter.client import ExtendedVPPAPIClient
from vpp_vrouter.common import models

from vrouter_agent import utils
from vrouter_agent.utils import run_command

logger = utils.setup_logger(__name__, save_dir="/var/log")


def configure_dpdk_interfaces(
    client,
    wan_intf_name: str,
    lan_intf_name: str,
    wan_intf_net: list[str] = [],
    lan_intf_net: list[str] = [],
):
    wan_intf_config = models.InterfaceConfigurationItem(
        name=wan_intf_name,
        type=models.InterfaceType.DPDK,
        enabled=True,
        ip_addresses=[wan_intf_net],
        mtu=8500,
    )
    lan_intf_config = models.InterfaceConfigurationItem(
        name=lan_intf_name,
        type=models.InterfaceType.DPDK,
        enabled=True,
        ip_addresses=[lan_intf_net],
        mtu=8500,
    )
    # Configure DPDK interfaces with 10.0.x.1/24 IP addresses
    for item in client.get_configuration().items:
        # Make sure the interfaces are configured
        if (
            isinstance(item.config, models.InterfaceConfigurationItem)
            and item.config.name == wan_intf_name
            and not item.config.enabled
        ):
            logger.info("Enabling WAN interface %s" % wan_intf_name)
            reply = client.update_configuration(
                item.config,
                wan_intf_config,
            )
            if reply.all_updated_items_applied_to_vpp:
                logger.info(f"WAN interface {item.config.name} configured")

        if (
            isinstance(item.config, models.InterfaceConfigurationItem)
            and item.config.name == lan_intf_name
            and not item.config.enabled
        ):
            logger.info("Enabling LAN interface %s" % lan_intf_name)
            reply = client.update_configuration(
                item.config,
                lan_intf_config,
            )
            if reply.all_updated_items_applied_to_vpp:
                logger.info(f"LAN interface {item.config.name} configured")


def configure_wg_interfaces(
    client,
    wg_name: str,
    wg_net: list[str],
    mtu: int,
    src_addr: str,
    src_port: int,
    dst_port: int,
    private_key: str,
    dst_addr: str,
    peer_public_key: str,
    peer_endpoint: str,
    peer_allowed_ips: list[str],
):
    logger.info("Configuring Wireguard")
    wireguard_interface_config = models.InterfaceConfigurationItem(
        name=wg_name,
        enabled=True,
        ip_addresses=wg_net,
        type=models.InterfaceType.WIREGUARD_TUNNEL,
        mtu=mtu,  # leaving some room for encryption encapsulation so that packet don't break into segments
        link=models.WireguardInterfaceLink(
            private_key=private_key,  # encoded in base64
            port=src_port,
            src_addr=ipaddress.IPv4Address(src_addr),
        ),
    )
    wireguard_peer_config = models.WireguardPeerConfigurationItem(
        public_key=peer_public_key,  # encoded in base64
        port=dst_port,
        endpoint=ipaddress.IPv4Address(dst_addr),
        allowed_ips=peer_allowed_ips,
        wg_if_name=wireguard_interface_config.name,
    )
    wireguard_router_config = models.RouteConfigurationItem(
        destination_network=peer_endpoint,
        outgoing_interface=wireguard_interface_config.name,
    )
    reply = client.add_configuration(
        wireguard_interface_config, wireguard_peer_config, wireguard_router_config
    )
    if reply.vpp_apply_success:
        logger.info("Wireguard configured. Now wait 30s for the tunnel to come up")
        time.sleep(30)
        logger.info("Testing connectivity")
        output = run_command(["sudo", "vppctl", "ping", peer_endpoint.split("/")[0]])
        logger.info(output)
    else:
        logger.info("Wireguard configuration failed")


def configure_nat(client, wan_intf_name, lan_intf_name):
    logger.info("Configuring NAT")
    # NAT INSIDE
    nat44_in_config = models.Nat44InterfaceConfigurationItem(
        name=lan_intf_name, nat_inside=True
    )
    # NAT OUTSIDE
    nat44_out_config = models.Nat44InterfaceConfigurationItem(
        name=wan_intf_name, nat_outside=True
    )
    # IDENTITY NAT
    indentity_nat_config = models.DNat44ConfigurationItem(
        label="identity_nat",
        identity_mappings=[models.IdentityMapping(interface=wan_intf_name, port=50000)],
    )

    # ADDRESS POOL
    # address_pool_config = models.Nat44AddressPoolConfigurationItem(
    #     first_ip="10.0.1.1",
    #     last_ip="10.0.2.1",
    # )

    # Create temp cli command for NAT
    run_command(["sudo", "vppctl", "nat44" "add", "10.0.2.1"])
    run_command(["sudo", "vppctl", "nat44", "add", "10.0.1.1"])

    reply = client.add_configuration(
        nat44_in_config, nat44_out_config, indentity_nat_config
    )
    logger.info(reply)

    logger.info("NAT configured. Now wait 30s for the tunnel to come up")
    time.sleep(10)

    logger.info("Testing connectivity")
    output = run_command(["sudo", "vppctl", "ping", "172.32.0.10"])
    logger.info(output)


def configure_lcp(client, wan_intf_name, lan_intf_name):
    # Configuring LCP
    logger.info("Configuring LCP")

    lcp_globals_config = models.LCPGlobalsConfigurationItem(
        default_namespace="dataplane",
        lcp_sync=True,  # Enables copying of changes made in VPP into their Linux counterpart
        # sub-interface creation in VPP automatically creates a Linux Interface Pair(LIP) and its companion Linux
        # network interface
        lcp_auto_subint=True,
    )
    lcp_pair_wan_config = models.LCPPairConfigurationItem(
        interface=wan_intf_name,
        mirror_interface_host_name=f"host-wan-vpp",
        mirror_interface_type=models.LCPHostInterfaceTypeEnum.TUN,
        host_namespace="dataplane",  # current/default linux namespace
    )
    lcp_pair_lan_config = models.LCPPairConfigurationItem(
        interface=lan_intf_name,
        mirror_interface_host_name=f"host-lan-vpp",
        mirror_interface_type=models.LCPHostInterfaceTypeEnum.TUN,
        host_namespace="dataplane",  # current/default linux namespace
    )

    reply = client.add_configuration(
        lcp_globals_config, lcp_pair_wan_config, lcp_pair_lan_config
    )
    print(reply)


def configure_frr(client):
    # Testing FRR

    logger.info("Configuring FRR")

    frr_init_config = [
        config_detail.config
        for config_detail in client.get_configuration().items
        if isinstance(config_detail.config, models.FRRConfigurationItem)
    ][0]
    print(frr_init_config)

    # appending some bgp configuration to initial FRR config
    # (FRR config is updated, but that means just means delete of old config and add of new one. In case of FRR,
    # the delete does nothing because FRR need to have always some configuration. That means that only addition of
    # FRR configuration matters.)
    append_to_frr_config = (
        """ 
hostname ospfd
password zebra
log stdout
!
router ospf
 network 172.16.0.2/32 area 0
 network 10.0.10.2/24 area 0
 network 10.0.20.2/24 area 0
! 
    """.strip(
            "\n "
        )
        + "\n"
    )

    reply = client.update_configuration(
        frr_init_config,
        models.FRRConfigurationItem(
            config=frr_init_config.config + append_to_frr_config
        ),
    )

    print(reply)


def run():
    with ExtendedVPPAPIClient() as client:
        # DPDK interfaces
        wan_intf_name = "GigabitEthernet0/9/0"
        lan_intf_name = "GigabitEthernet0/8/0"
        wan_intf_net = "10.0.1.2/24"
        lan_intf_net = "10.0.2.2/24"

        # WG Interface
        wg_name = "wg0"
        wg_net = ["172.32.0.9/30"]
        mtu = 1420
        src_port = 50000
        dst_port = 50000
        private_key = "YIBI+xgvhGiTwwblC9DA4Xy3jAyMP2eVVtvst6Z7lmA="
        src_addr = "10.0.1.2"

        # WG Peers
        dst_addr = "10.0.1.1"
        peer_allowed_ips = ["0.0.0.0/0"]
        peer_public_key = "slDc60lMEXVJs2E4MILoSqdqs7DYkrFkGoon8dkqtzI="
        peer_endpoint = "172.32.0.10/30"

        configure_dpdk_interfaces(
            client, wan_intf_name, lan_intf_name, wan_intf_net, lan_intf_net
        )
        configure_wg_interfaces(
            client,
            wg_name=wg_name,
            wg_net=wg_net,
            mtu=mtu,
            src_port=src_port,
            dst_port=dst_port,
            private_key=private_key,
            src_addr=src_addr,
            dst_addr=dst_addr,
            peer_allowed_ips=peer_allowed_ips,
            peer_public_key=peer_public_key,
            peer_endpoint=peer_endpoint,
        )
        # configure_nat(client, wan_intf_name, lan_intf_name)
        configure_lcp(client, wan_intf_name, lan_intf_name)
        configure_frr(client)
