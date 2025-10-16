import json
from loguru import logger as log
from sqlmodel import Session
from vrouter_agent.core.enums import OrderStatus, StreamItemTag, StreamItemAction
from vrouter_agent.core.config import settings
from vrouter_agent.services.chain import Chain, StreamItem
from vrouter_agent.services.client import VRouterClient
from vrouter_agent.models import Transaction, Order
from vrouter_agent.enhanced_stream_processor import get_stream_processor
from .utils import (
    get_device_serial_number,
)

class VRouterAgent:

    async def process_transaction_async(self, transaction, stream, session):
        processor = await get_stream_processor()
        return await processor.process_transaction(transaction, stream, session)
    

    
    
    
    # FRR_CONTAINER_NAME = "frr"

    # def __init__(self):
    #     self.serial_number = get_device_serial_number()


    # def notify_transaction(
    #     self,
    #     transaction: Transaction,
    #     stream: str,
    #     session: Session,
    # ):
    #     log.info(f"Received transaction {transaction.txid} on stream {stream}")
    #     chain = Chain(
    #         chain=settings.config.multichain.chain,
    #         user=settings.config.global_.user,
    #     )
      
    #     stream = chain.get_stream_item(stream,transaction.txid)
    #     if not stream:
    #         log.error(f"Transaction {transaction.txid} not found in the stream.")
    #         return

    #     stream_item = StreamItem(
    #         data=stream["data"],
    #         txid=stream["txid"],
    #     )
    #     decrypted_data = stream_item.get_decrypted_data()
    #     decrypted_data = json.loads(decrypted_data)
        
    #     # decrypt_data = {"tag": "order", "action": "create", "data": serialized_data}
    #     if decrypted_data["tag"] == StreamItemTag.ORDER:
    #         # save order if it doesn't exist
    #         order_data = decrypted_data["data"]
    #         # check if order already exists
    #         order = Order.get_or_create(session,order_data)
    #         tunnels = order.tunnels_in_scope_with_role(self.serial_number)
    #         if len(tunnels) == 0:
    #             log.debug("No tunnels found for this host. Skipping order processing.")
    #             return
    #         # process the order
    #         if decrypted_data["action"] == StreamItemAction.CREATE:
    #             log.info(f"Processing order {decrypted_data['data']} action {decrypted_data['action']}")
    #             log.debug(f"Tunnels data: {tunnels}")
    #             ospf_config = order.get_host_ospf_config(self.serial_number) if order.ospf_enabled else None
    #             vrouter = VRouterClient(tunnels=tunnels,ospf_config=ospf_config)
    #             if not vrouter.is_connected():
    #                 log.error("VRouter client is not connected. Exiting...")
    #                 return
    #             created = vrouter.create_wireguard_tunnels()
    #             if ospf_config:
    #                 vrouter.create_ospf_configuration()
                
                
    #         elif decrypted_data["action"] == StreamItemAction.UPDATE:
    #             log.info(f"Updating order {decrypted_data['data']}")
    #             vrouter.update_wireguard_tunnels()
    #             if order.ospf_enabled:
    #                 vrouter.update_ospf_configuration()
    #         elif decrypted_data["action"] == StreamItemAction.DELETE:
    #             log.info(f"Deleting order {decrypted_data['data']}")
    #             vrouter.delete_wireguard_tunnels()
    #             if order.ospf_enabled:
    #                 vrouter.delete_ospf_configuration()
                    
    #         # update order status
    #         order.status = OrderStatus.COMPLETED if created else OrderStatus.FAILED
    #         # update order status
    #         session.add(order)
    #         session.commit()
    #         log.info(f"Order {order.id} status updated to {order.status}")
                
    #     elif decrypted_data["tag"] == StreamItemTag.NETWORK:
    #         pass 
    #     # vpp = VPP()
    #     # tunnels = list(order.tunnels_in_scope(self.serial_number))
    #     # if len(tunnels) == 0:
    #     #     log.debug("No tunnels found for this host. Skipping order processing.")
    #     #     return
    #     # if order.status == OrderStatus.DECOMMISSION_REQUESTED:
    #     #     log.info(f"Decommissioning order {order.id} ...")
    #     #     vpp.delete_lcp_global_configuration("frr")
    #     #     wg_interfaces = []
    #     #     for tunnel in tunnels:
    #     #         source, destination = order.get_tunnel_data(tunnel, self.serial_number)
    #     #         if vpp.delete_wireguard_tunnel(
    #     #             source,
    #     #             destination,
    #     #             order.ospf_enabled,
    #     #             settings.config.interfaces["lan_primary"],
    #     #         ):
    #     #             tunnel.status = TunnelStatus.DELETED
    #     #         else:
    #     #             tunnel.status = TunnelStatus.UNKNOWN
    #     #         wg_interfaces.append(
    #     #             {
    #     #                 "name": source.name,
    #     #                 "ip_address": source.ip_address,
    #     #                 "port": source.listen_port,
    #     #             }
    #     #         )
    #     #         log.info(f"Tunnel {tunnel.uuid} is {tunnel.status}.")
    #     #     if order.ospf_enabled:
    #     #         ospf = order.get_host_ospf_config(self.serial_number)
    #     #         lan_intf = settings.config.interfaces["lan_primary"]
    #     #         frr = FRR(
    #     #             ospf,
    #     #             settings.config.route_reflector,
    #     #             settings.config.route_reflector_controller,
    #     #             lan_intf,
    #     #             wg_interfaces,
    #     #         )
    #     #         # frr.delete_all_configs()
    #     #         run_command(["sudo", "systemctl", "restart", self.FRR_CONTAINER_NAME])
    #     #         vpp.delete_nat_configuration(
    #     #             settings.config.interfaces["lan_primary"],
    #     #             settings.config.interfaces["wan_primary"],
    #     #             list(set([x["port"] for x in wg_interfaces])),
    #     #             [22, 2206, 2205],
    #     #         )
    #     #         vpp.delete_acl_configuration(settings.config.interfaces["lan_primary"])

    #     #         # Restart VPP to apply the changes - Hacking around the issue
    #     #         run_command(["sudo", "systemctl", "restart", "vpp"])

    #     #     order.status = OrderStatus.DECOMMISSION_COMPLETE
    #     #     session.add_all(tunnels)
    #     #     session.add(order)
    #     #     session.commit()
    #     #     log.info(f"Decommissioning order {order.id} completed.")
    #     #     asyncio.create_task(self.send_telemetry(str(order.tunnels[0].uuid))) # TODO: Send telemetry for all tunnels
    #     # if order.status == OrderStatus.PROVISION_REQUESTED:
    #     #     log.info(f"Provisioning order {order.id} ...")
    #     #     created_wg_interfaces = []
    #     #     vpp.add_lcp_global_configuration("frr")
    #     #     ospf_neighbors = get_ospf_neighbors()
    #     #     log.debug("Current OSPF neighbors: ", ospf_neighbors)

    #     #     for count, tunnel in enumerate(tunnels):
    #     #         log.info(
    #     #             f"Processing tunnel ID:{tunnel.id}, source:{tunnel.source}, destination:{tunnel.destination}"
    #     #         )
    #     #         source, destination = order.get_tunnel_data(tunnel, self.serial_number)

    #     #         name, ip_address = vpp.add_wireguard_tunnel(
    #     #             source,
    #     #             destination,
    #     #             count,
    #     #             ospf_enabled=order.ospf_enabled,
    #     #             ospf_neighbors=ospf_neighbors,
    #     #         )
    #     #         if tunnel.failover:
    #     #             log.info(
    #     #                 "Failover tunnel detected. Adding routes for failover link ..."
    #     #             )
    #     #             secondary_route = vpp.add_vpp_route(
    #     #                 destination.source_ip + "/32",
    #     #                 settings.config.interfaces["wan_secondary"].gateway,
    #     #                 settings.config.interfaces["wan_secondary"].interface_name,
    #     #             )
    #     #             if secondary_route:
    #     #                 log.info("Secondary route added successfully.")

    #     #         created_wg_interfaces.append(
    #     #             {
    #     #                 "name": name,
    #     #                 "ip_address": ip_address,
    #     #                 "port": source.listen_port,
    #     #             }
    #     #         )

    #     #     if order.ospf_enabled:
    #     #         # if ospf is already enabled, skip
    #     #         if ospf_neighbors:
    #     #             log.info("OSPF neighbors found. Skipping...")
    #     #         else:
    #     #             ospf = order.get_host_ospf_config(self.serial_number)
    #     #             if not ospf:
    #     #                 log.error("No OSPF configuration found for the host.")
    #     #             lan_intf = settings.config.interfaces["lan_primary"]

    #     #             vpp.expose_lan_interface_to_frr_container(
    #     #                 lan_intf.interface_name,
    #     #                 lan_intf.ip_address,
    #     #                 lan_intf.prefix_len,
    #     #             )

    #     #             vpp.add_bgp_loopback(settings.config.route_reflector.loopback)

    #     #             if ospf.client_enabled:
    #     #                 vpp.add_ospf_lcp_fix(
    #     #                     client_vpp_intf_address=ospf.lan_ip_address,
    #     #                     vpp_lan_intf=lan_intf.interface_name,
    #     #                 )
    #     #                 vpp.add_client_neighbour_info(
    #     #                     lan_intf.interface_name,
    #     #                     ospf.lan_ip_address,
    #     #                     ospf.lan_mac_address,
    #     #                 )
    #     #             frr = FRR(
    #     #                 ospf,
    #     #                 settings.config.route_reflector,
    #     #                 settings.config.route_reflector_controller,
    #     #                 lan_intf,
    #     #                 created_wg_interfaces,
    #     #             )
    #     #             frr.apply_all_configs()

    #     #             vpp.add_routes_for_bidirectional_bgp_communication(
    #     #                 "frr",
    #     #                 settings.config.route_reflector.loopback,
    #     #                 settings.config.route_reflector_controller.loopback.split("/")[
    #     #                     0
    #     #                 ],
    #     #                 settings.config.route_reflector_controller.address,
    #     #             )

    #     #             if ospf.allowed_subnets:
    #     #                 pillar = {
    #     #                     "allowed_routes": ospf.allowed_subnets,
    #     #                     "loopback": settings.config.route_reflector.loopback,
    #     #                     "lan_ip_address": ospf.lan_ip_address,
    #     #                     "lan_netmask": ospf.lan_netmask,
    #     #                 }
    #     #                 log.debug("BGP Filtering found. Applying the configuration")
    #     #                 log.debug(f"Pillar: {json.dumps(pillar)}")
    #     #                 cmd = run_command(
    #     #                     [
    #     #                         "sudo",
    #     #                         "salt-call",
    #     #                         "state.apply",
    #     #                         "frr.change",
    #     #                         "pillar=" + json.dumps({"frr_config": pillar}),
    #     #                     ]
    #     #                 )
    #     #                 log.debug(cmd)
    #     #             vpp.add_nat_configuration(
    #     #                 lan_iface=settings.config.interfaces["lan_primary"],
    #     #                 wan_iface=settings.config.interfaces["wan_primary"],
    #     #                 wg_ports_to_open=list(
    #     #                     set([x["port"] for x in created_wg_interfaces])
    #     #                 ),
    #     #                 tcp_ports=[
    #     #                     22,
    #     #                     2206,
    #     #                     2205,
    #     #                 ],  # TODO: Add the ports from the order
    #     #                 udp_ports=[settings.config.route_reflector.port],
    #     #             )
    #     #             vpp.add_acl_configuration(
    #     #                 ingress_iface=settings.config.interfaces["lan_primary"],
    #     #                 deny_network="8.8.4.4/32",
    #     #             )

    #     #     log.info("Now testing connectivity for the tunnels ...")

    #     #     # Check initial tunnel statuses
    #     #     for tunnel in tunnels:
    #     #         source, destination = order.get_tunnel_data(tunnel, self.serial_number)
    #     #         log.info(f"Testing connectivity for tunnel: {tunnel.uuid}")
    #     #         log.info(f"Source Device: {source.device_hostname}")
    #     #         log.info(f"Destination Device: {destination.device_hostname}")
    #     #         tunnel.status = self.check_tunnel_status(vpp, destination.ip_address)

    #     #     MAX_RETRIES = 5
    #     #     SLEEP_DURATION = 30  # seconds

    #     #     # Retry logic for pending tunnels
    #     #     for _ in range(MAX_RETRIES):
    #     #         tunnel_statuses = [tunnel.status for tunnel in tunnels]
    #     #         log.debug(f"Tunnel statuses: {tunnel_statuses}")

    #     #         if all(status == TunnelStatus.ACTIVE for status in tunnel_statuses):
    #     #             order.status = OrderStatus.PROVISION_COMPLETE
    #     #             asyncio.create_task(self.send_telemetry(str(tunnel.uuid)))
    #     #             log.info(
    #     #                 f"Order {order.id} status updated to {OrderStatus.PROVISION_COMPLETE}"
    #     #             )
    #     #             break

    #     #         elif all(status == TunnelStatus.INACTIVE for status in tunnel_statuses):
    #     #             order.status = OrderStatus.PROVISION_FAILED
    #     #             log.info(
    #     #                 f"Order {order.id} status updated to {OrderStatus.PROVISION_FAILED}"
    #     #             )
    #     #             break

    #     #         elif any(status == TunnelStatus.PENDING for status in tunnel_statuses):
    #     #             log.info(
    #     #                 f"Order {order.id} has pending tunnels. Retrying in {SLEEP_DURATION} seconds..."
    #     #             )
    #     #             time.sleep(SLEEP_DURATION)

    #     #             # Recheck only pending tunnels
    #     #             for tunnel in tunnels:
    #     #                 if tunnel.status == TunnelStatus.PENDING:
    #     #                     source, destination = order.get_tunnel_data(
    #     #                         tunnel, self.serial_number
    #     #                     )
    #     #                     log.info(
    #     #                         f"Re-testing connectivity for tunnel: {tunnel.uuid}"
    #     #                     )
    #     #                     tunnel.status = self.check_tunnel_status(
    #     #                         vpp, destination.ip_address
    #     #                     )

    #     #         else:
    #     #             order.status = OrderStatus.PROVISION_INCOMPLETE
    #     #             log.info(
    #     #                 f"Order {order.id} status updated to {OrderStatus.PROVISION_INCOMPLETE}"
    #     #             )
    #     #             break

    #     #     # Batch update tunnels and order
    #     #     session.add_all(tunnels)
    #     #     session.add(order)
    #     #     session.commit()
    #     #     log.info("Order processing completed.")
    #     #     return order

