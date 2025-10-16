# from sqlmodel import Field, SQLModel, Relationship, Session, select
# from pydantic import BaseModel, PrivateAttr
# from uuid import UUID
# from uuid import uuid4

# from datetime import timezone, datetime
# from typing import Optional, List, Dict
# from .enums import (
#     TunnelType,
#     TunnelStatus,
#     OrderStatus,
# )

# class Transaction(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     txid: str
#     timestamp: datetime = Field(default=datetime.now(timezone.utc))
#     stream: str

#     def __str__(self) -> str:
#         return f"ID:{self.id}, TXID:{self.txid}, Timestamp:{self.timestamp}"

#     @classmethod
#     def is_processed(cls, session: Session, txid: str) -> bool:
#         statement = select(cls).where(cls.txid == txid)
#         result = session.exec(statement).first()
#         return result is not None

#     @classmethod
#     def create(cls, session: Session, txid: str) -> "Transaction":
#         processed_transaction = cls(txid=txid)
#         session.add(processed_transaction)
#         session.commit()
#         return processed_transaction


# class OSPFConfig(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     order_id: Optional[int] = Field(default=None, foreign_key="order.id")
#     enabled: Optional[bool] = Field(default=False)
#     router_id: Optional[str] = Field(default=None)
#     router_area: Optional[str] = Field(default=None)
#     as_number: Optional[str] = Field(default=None)
#     network: Optional[str] = Field(default=None)
#     wildcard: Optional[str] = Field(default=None)
#     priority: Optional[int] = Field(default=None)
#     auth: Optional[str] = Field(default=None)
#     auth_key: Optional[str] = Field(default=None)
#     retransmit: Optional[int] = Field(default=None)
#     whitelist: Optional[str] = Field(default=None)
#     client_enabled: Optional[bool] = Field(default=False)
#     client_router_id: Optional[str] = Field(default=None)
#     client_router_area: Optional[str] = Field(default=None)
#     lan_interface_name: Optional[str] = Field(default=None)
#     lan_ip_address: Optional[str] = Field(default=None)

#     lan_netmask: Optional[str] = Field(default=None)
#     lan_mac_address: Optional[str] = Field(default=None)
#     allowed_subnets: Optional[str] = Field(default=None)
#     cost: Optional[int] = Field(default=10)
#     hello: Optional[int] = Field(default=2)
#     dead: Optional[int] = Field(default=8)
#     device: Optional[int] = Field(default=None)
#     device_hostname: Optional[str] = Field(default=None)

#     order: Optional["Order"] = Relationship(back_populates="ospf_configs")

# class BGPConfig(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     order_id: Optional[int] = Field(default=None, foreign_key="order.id")
#     enabled: Optional[bool] = Field(default=False)
#     router_id: Optional[str] = Field(default=None)
#     as_number: Optional[str] = Field(default=None)
#     network: Optional[str] = Field(default=None)
#     prefix_list: Optional[str] = Field(default=None)
#     route_map: Optional[str] = Field(default=None)
#     redistribute: Optional[str] = Field(default=None)
#     device: Optional[int] = Field(default=None)
#     device_hostname: Optional[str] = Field(default=None)
    
#     order: Optional["Order"] = Relationship(back_populates="bgp_configs")
    
# class Wireguard(SQLModel, table=True):
#     id: Optional[int] = Field(default=None, primary_key=True)
#     device_id: Optional[int] = Field(default=None)
#     name: Optional[str] = Field(default=None, max_length=256)
#     ip_address: Optional[str] = Field(default=None, max_length=256)
#     listen_port: Optional[str] = Field(default=None, max_length=256)
#     mtu: Optional[str] = Field(default=None, max_length=256)
#     private_key: Optional[str] = Field(default=None, max_length=256)
#     public_key: Optional[str] = Field(default=None, max_length=256)
#     allowed_ips: Optional[str] = Field(default=None, max_length=256)
#     endpoint_ip: Optional[str] = Field(default=None, max_length=256)
#     source_ip: Optional[str] = Field(default=None, max_length=256)
#     persistent_keepalive: Optional[str] = Field(default=None, max_length=256)
#     device_hostname: Optional[str] = Field(default=None, max_length=256)

#     source: List["Tunnel"] = Relationship(
#         back_populates="source",
#         sa_relationship_kwargs={"foreign_keys": "[Tunnel.source_id]"},
#     )
#     destination: List["Tunnel"] = Relationship(
#         back_populates="destination",
#         sa_relationship_kwargs={"foreign_keys": "[Tunnel.destination_id]"},
#     )

#     def __str__(self) -> str:
#         return f"ID:{self.id}, IP:{self.ip_address}, Endpoint:{self.endpoint_ip}"


# class Tunnel(SQLModel, table=True):
#     uuid: Optional[UUID] = Field(  # type: ignore
#         default_factory=uuid4, index=True, unique=True
#     )
#     id: Optional[int] = Field(default=None, primary_key=True)
#     order_id: Optional[int] = Field(default=None, foreign_key="order.id")
#     source_id: Optional[int] = Field(default=None, foreign_key="wireguard.id")
#     destination_id: Optional[int] = Field(default=None, foreign_key="wireguard.id")
#     type: TunnelType = Field(default=TunnelType.UNKNOWN)
#     status: TunnelStatus = Field(default=TunnelStatus.PENDING)
#     failover: Optional[bool] = Field(default=False)
#     order: Optional["Order"] = Relationship(back_populates="tunnels")
#     source: Optional[Wireguard] = Relationship(
#         back_populates="source",
#         sa_relationship_kwargs={"foreign_keys": "[Tunnel.source_id]"},
#     )
#     destination: Optional[Wireguard] = Relationship(
#         back_populates="destination",
#         sa_relationship_kwargs={"foreign_keys": "[Tunnel.destination_id]"},
#     )
#     # Temporary fields (not in DB)
#     _source_on_host: Optional["Wireguard"] = PrivateAttr(default=None)
#     _destination_peer: Optional["Wireguard"] = PrivateAttr(default=None)
    
#     @property
#     def source_on_host(self):
#         return self._source_on_host

#     @source_on_host.setter
#     def source_on_host(self, val):
#         self._source_on_host = val

#     @property
#     def destination_peer(self):
#         return self._destination_peer

#     @destination_peer.setter
#     def destination_peer(self, val):
#         self._destination_peer = val
        
#     def __str__(self) -> str:
#         return f"ID:{self.id}, Source:{self.source.device_hostname}, Destination:{self.destination.device_hostname}, Status:{self.status}"

#     @classmethod
#     def in_scope(cls, host):
#         print("Source Hostname:", cls.source.device_hostname)
#         return (
#             cls.source.device_hostname == host
#             or cls.destination.device_hostname == host
#         )


# class Order(SQLModel, table=True):
#     """
#     Order model representing a network order.
    
#     """
#     uuid: Optional[UUID] = Field(  # type: ignore
#         default_factory=uuid4, index=True
#     )
#     id: Optional[int] = Field(default=None, primary_key=True)
#     organization: Optional[int]
#     connection_type: Optional[str] = Field(default=None, max_length=256)
#     order_number: Optional[str] = Field(default=None, max_length=256)
#     provision_txid: Optional[str] = Field(default=None, max_length=256, nullable=True)
#     decommission_txid: Optional[str] = Field(
#         default=None, max_length=256, nullable=True
#     )
#     status: OrderStatus = Field(default=OrderStatus.UNKNOWN)
#     type: Optional[str]
#     created_by: Optional[str]
#     updated_by: Optional[str]
#     created_at: Optional[str]
#     updated_at: Optional[str]
#     is_deleted: Optional[bool] = Field(default=False)
#     archived: Optional[bool] = Field(default=False)
#     routing_enabled: Optional[bool] = Field(default=False)
#     routing_protocol: Optional[str] = Field(default=None)
   
#     tunnels: List["Tunnel"] = Relationship(back_populates="order")
#     ospf_configs: List["OSPFConfig"] = Relationship(back_populates="order")
#     bgp_configs: List["BGPConfig"] = Relationship(back_populates="order")
    

#     @classmethod
#     def get_order_by_id(cls, session: Session, order_id: int) -> "Order":
#         """
#         Retrieve an order by its ID.

#         Args:
#             session (Session): The database session to use for the query.
#             order_id (int): The ID of the order to retrieve.

#         Returns:
#             Order: The order object with the specified ID, or None if not found.
#         """
#         statement = select(cls).where(cls.id == order_id)
#         return session.exec(statement).first()

#     @classmethod
#     def create_with_tunnels(cls, session: Session, order_data: dict) -> "Order":
#         """
#         Create an Order along with its Tunnels, Wireguards, and OSPFConfigs.
#         """
#         tunnels_data = order_data.pop("tunnels", [])
#         ospf_configs_data = order_data.pop("ospf_configs", [])

#         # Convert UUID string to UUID object if necessary
#         if "uuid" in order_data and isinstance(order_data["uuid"], str):
#             order_data["uuid"] = UUID(order_data["uuid"])

#         # Remove unwanted keys that aren't model fields
#         for field in ("id", "tunnel_count", "b2b_organization_names", "b2b_organizations"):
#             order_data.pop(field, None)

#         # Create the Order
#         order = cls(**order_data)
#         session.add(order)
#         session.flush()  # Get order.id without committing yet

#         # Prepare all Tunnels and Wireguards
#         tunnels = []
#         wireguards = []
#         for tunnel_data in tunnels_data:
#             source_data = tunnel_data.pop("source")
#             destination_data = tunnel_data.pop("destination")

#             for side_data in (source_data, destination_data):
#                 for k in ("id",):
#                     side_data.pop(k, None)

#             source = Wireguard(**source_data)
#             destination = Wireguard(**destination_data)
#             session.add_all([source, destination])
#             session.flush()  # Get source.id and destination.id

#             if "uuid" in tunnel_data and isinstance(tunnel_data["uuid"], str):
#                 tunnel_data["uuid"] = UUID(tunnel_data["uuid"])

#             for key in ("id", "order", "created_at", "updated_at"):
#                 tunnel_data.pop(key, None)

#             tunnel = Tunnel(
#                 **tunnel_data,
#                 order=order,
#                 source=source,
#                 destination=destination,
#             )
#             tunnels.append(tunnel)

#         session.add_all(tunnels)

#         # Prepare and add all OSPFConfigs
#         ospf_configs = []
#         for ospf_data in ospf_configs_data:
#             for field in ("id", "order"):
#                 ospf_data.pop(field, None)
#             ospf_config = OSPFConfig(**ospf_data, order=order)
#             ospf_configs.append(ospf_config)

#         session.add_all(ospf_configs)
#         session.commit()

#         return order

#     def __str__(self) -> str:
#         return f"ID:{self.id}, Order Number:{self.order_number}, Status:{self.status}"

#     def tunnels_in_scope_with_role(self, host: str) -> list[Tunnel]:
#         """
#         Retrieve tunnels in scope for a given host, including their roles.
#         Args:
#             host (str): The hostname of the device for which the tunnels are in scope.
#         Returns:
#             list[Tunnel]: A list of Tunnel objects that are in scope for the specified host.
#         """
#         # Check if the host is None or empty
#         if not host:
#             return []
#         result = []

#         for tunnel in self.tunnels:
#             if tunnel.source.device_hostname == host:
#                 tunnel.source_on_host = tunnel.source
#                 tunnel.destination_peer = tunnel.destination
#                 result.append(tunnel)
#             elif tunnel.destination.device_hostname == host:
#                 tunnel.source_on_host = tunnel.destination
#                 tunnel.destination_peer = tunnel.source
#                 result.append(tunnel)

#         return result


#     def get_host_ospf_config(self, host):
#         """
#         Retrieve the OSPF (Open Shortest Path First) configuration for a given host.

#         Args:
#             host (str): The hostname of the device for which the OSPF configuration is required.

#         Returns:
#             OSPFConfig: The OSPF configuration object for the specified host if found, otherwise None.
#         """

#         for ospf_config in self.ospf_configs:
#             if ospf_config.device_hostname == host:
#                 return ospf_config
#         return None
    
#     @classmethod
#     def get_or_create(cls,session: Session, order_data: Dict) -> "Order":
#         """
#         Retrieve an existing order by its ID or create a new one if it doesn't exist.

#         Args:
#             session (Session): The database session to use for the query.
#             order_data (dict): The data to create a new order if it doesn't exist.

#         Returns:
#             Order: The existing or newly created order object.
#         """
#         order_id = order_data.get("id")
#         order = cls.get_order_by_id(session, order_id) if order_id else None
#         if not order:
#             order = cls.create_with_tunnels(session, order_data)
#         return 
    
    