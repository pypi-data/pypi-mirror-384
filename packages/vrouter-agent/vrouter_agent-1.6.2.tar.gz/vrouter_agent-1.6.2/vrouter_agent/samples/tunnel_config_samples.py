"""
Sample tunnel configuration data for testing the VRouter stream processing system.
This demonstrates the JSON structure expected by the tunnel config processor.
"""

import json
from datetime import datetime
from typing import Dict, Any, List

# Sample tunnel configuration matching the schema structure
SAMPLE_TUNNEL_CONFIG_DATA = {
    "tag": "tunnel_config",
    "action": "provision",
    "order_id": "ORD-12345-ABCDE",
    "order_number": "TUN-2025-001",
    "topology": {
        "id": "topo-hub-spoke-001",
        "name": "Production Hub-Spoke Network",
        "type": "hub_spoke"
    },
    "tunnels": [
        {
            "interface_name": "wg-tunnel-001",
            "private_key": "YOur_PRiVaTe_Key_HeRe_32_ChArS_ExAmPlE=",
            "listen_port": 51820,
            "address": "10.100.1.2/24",
            "peer_public_key": "PeEr_PuBlIc_Key_HeRe_32_ChArS_ExAmPlE_123=",
            "allowed_ips": "10.100.0.0/16,192.168.100.0/24",
            "persistent_keepalive": 25,
            "peer_endpoint": "203.0.113.10:51820",
            "mtu": 1420,
            "peer_address": "10.100.1.1",
            "source_ip": "203.0.113.5",
            "gre_name": "gre1",
            "gre_local_tunnel_ip": "10.200.0.1",
            "gre_remote_tunnel_ip": "10.200.0.2"
        },
        {
            "interface_name": "wg-tunnel-002", 
            "private_key": "AnOtHeR_PRiVaTe_Key_HeRe_32_ChArS_ExAm=",
            "listen_port": 51821,
            "address": "10.100.2.2/24",
            "peer_public_key": "AnOtHeR_PuBlIc_Key_HeRe_32_ChArS_ExAm=",
            "allowed_ips": "10.101.0.0/16,192.168.101.0/24",
            "persistent_keepalive": 25,
            "peer_endpoint": "203.0.113.11:51821",
            "mtu": 1420,
            "peer_address": "10.100.2.1",
            "source_ip": "203.0.113.6",
            "gre_name": "gre2",
            "gre_local_tunnel_ip": "10.200.1.1",
            "gre_remote_tunnel_ip": "10.200.1.2"
        }
    ],
    "frr_config": {
        "zebra_config": "hostname hub-node\npassword zebra\nenable password zebra\n!\ninterface lo0\n ip address 10.100.1.2/32\n description Loopback interface\n no shutdown\n!\nline vty\n!",
        "ospf_config": "router ospf 1\n router-id 10.100.1.2\n ospf router-id 10.100.1.2\n network 10.100.1.0/24 area 0.0.0.0\n network 10.100.2.0/24 area 0.0.0.0\n redistribute connected\n redistribute static\n!",
        "bgp_config": "",
        "static_config": "",
        "full_config": "! FRR Configuration\n! Hub-Spoke Network\n!\nhostname hub-node\npassword zebra\nenable password zebra\n!\ninterface lo0\n ip address 10.100.1.2/32\n description Loopback interface\n no shutdown\n!\nline vty\n!\n!\nrouter ospf 1\n router-id 10.100.1.2\n ospf router-id 10.100.1.2\n network 10.100.1.0/24 area 0.0.0.0\n network 10.100.2.0/24 area 0.0.0.0\n redistribute connected\n redistribute static\n!",
        "config_hash": "e7f4c8b2a3d5f6e9c1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0"
    }
}

# Sample for point-to-point topology
SAMPLE_P2P_TUNNEL_CONFIG = {
    "tag": "tunnel_config",
    "action": "provision",
    "order_id": "ORD-67890-FGHIJ",
    "order_number": "TUN-2025-002",
    "topology": {
        "id": "topo-p2p-001",
        "name": "Site-to-Site Connection",
        "type": "point_to_point"
    },
    "tunnels": [
        {
            "interface_name": "wg-p2p-001",
            "private_key": "P2P_PRiVaTe_Key_HeRe_32_ChArS_ExAmPlE_=",
            "listen_port": 51822,
            "address": "172.16.1.1/30",
            "peer_public_key": "P2P_PuBlIc_Key_HeRe_32_ChArS_ExAmPlE_=",
            "allowed_ips": "172.16.0.0/16,10.200.0.0/16",
            "persistent_keepalive": 25,
            "peer_endpoint": "198.51.100.20:51822",
            "mtu": 1420,
            "peer_address": "172.16.1.2",
            "source_ip": "198.51.100.10",
            "gre_name": "gre-p2p1",
            "gre_local_tunnel_ip": "10.200.2.1",
            "gre_remote_tunnel_ip": "10.200.2.2"
        }
    ],
    "frr_config": {
        "zebra_config": "hostname p2p-node\npassword zebra\nenable password zebra\n!\ninterface lo0\n ip address 172.16.1.1/32\n description Loopback interface\n no shutdown\n!\nline vty\n!",
        "ospf_config": "router ospf 1\n router-id 172.16.1.1\n ospf router-id 172.16.1.1\n network 172.16.1.0/30 area 0.0.0.1\n redistribute connected\n!",
        "bgp_config": "",
        "static_config": "",
        "full_config": "! FRR Configuration\n! Point-to-Point Network\n!\nhostname p2p-node\npassword zebra\nenable password zebra\n!\ninterface lo0\n ip address 172.16.1.1/32\n description Loopback interface\n no shutdown\n!\nline vty\n!\n!\nrouter ospf 1\n router-id 172.16.1.1\n ospf router-id 172.16.1.1\n network 172.16.1.0/30 area 0.0.0.1\n redistribute connected\n!",
        "config_hash": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
    }
}

# Sample for decommission action
SAMPLE_DECOMMISSION_CONFIG = {
    "tag": "tunnel_config",
    "action": "decommission",
    "order_id": "ORD-11111-ZZZZZ",
    "order_number": "TUN-2025-003",
    "topology": {
        "id": "topo-legacy-001",
        "name": "Legacy Network to Remove",
        "type": "hub_spoke"
    },
    "tunnels": [
        {
            "interface_name": "wg-legacy-001",
            "private_key": "LegAcY_PRiVaTe_Key_HeRe_32_ChArS_ExAm=",
            "listen_port": 51823,
            "address": "10.99.1.1/24",
            "peer_public_key": "LegAcY_PuBlIc_Key_HeRe_32_ChArS_ExAm=",
            "allowed_ips": "10.99.0.0/16",
            "persistent_keepalive": 25,
            "peer_endpoint": "192.0.2.30:51823",
            "mtu": 1420,
            "peer_address": "10.99.1.2",
            "source_ip": "192.0.2.10",
            "gre_name": "gre-legacy1",
            "gre_local_tunnel_ip": "10.200.9.1",
            "gre_remote_tunnel_ip": "10.200.9.2"
        }
    ]
}

# Sample for full mesh topology
SAMPLE_FULL_MESH_CONFIG = {
    "tag": "tunnel_config",
    "action": "provision",
    "order_id": "ORD-MESH-54321",
    "order_number": "TUN-2025-004",
    "topology": {
        "id": "topo-mesh-001",
        "name": "Production Full Mesh",
        "type": "full_mesh"
    },
    "tunnels": [
        {
            "interface_name": "wg-mesh-node1",
            "private_key": "MeSh_N1_PRiVaTe_Key_HeRe_32_ChArS_Ex=",
            "listen_port": 51824,
            "address": "10.200.1.1/24",
            "peer_public_key": "MeSh_N2_PuBlIc_Key_HeRe_32_ChArS_Ex=",
            "allowed_ips": "10.200.2.0/24,10.250.0.0/16",
            "persistent_keepalive": 25,
            "peer_endpoint": "203.0.113.100:51824",
            "mtu": 1420,
            "peer_address": "10.200.2.1",
            "source_ip": "203.0.113.50",
            "gre_name": "gre-mesh1",
            "gre_local_tunnel_ip": "10.200.10.1",
            "gre_remote_tunnel_ip": "10.200.10.2"
        },
        {
            "interface_name": "wg-mesh-node2",
            "private_key": "MeSh_N1_PRiVaTe_Key_HeRe_32_ChArS_Ex=",
            "listen_port": 51825,
            "address": "10.200.1.1/24",
            "peer_public_key": "MeSh_N3_PuBlIc_Key_HeRe_32_ChArS_Ex=",
            "allowed_ips": "10.200.3.0/24,10.251.0.0/16",
            "persistent_keepalive": 25,
            "peer_endpoint": "203.0.113.101:51825",
            "mtu": 1420,
            "peer_address": "10.200.3.1",
            "source_ip": "203.0.113.51",
            "gre_name": "gre-mesh2",
            "gre_local_tunnel_ip": "10.200.11.1",
            "gre_remote_tunnel_ip": "10.200.11.2"
        }
    ],
    "frr_config": {
        "zebra_config": "hostname mesh-node1\npassword zebra\nenable password zebra\n!\ninterface lo0\n ip address 10.200.1.1/32\n description Loopback interface\n no shutdown\n!\nline vty\n!",
        "ospf_config": "router ospf 1\n router-id 10.200.1.1\n ospf router-id 10.200.1.1\n network 10.200.1.0/24 area 0.0.0.0\n network 10.250.0.0/16 area 0.0.0.0\n network 10.251.0.0/16 area 0.0.0.0\n redistribute connected\n redistribute static\n!",
        "bgp_config": "router bgp 65001\n bgp router-id 10.200.1.1\n bgp log-neighbor-changes\n neighbor mesh-group-1 peer-group\n neighbor mesh-group-1 remote-as 65001\n!",
        "static_config": "",
        "full_config": "! FRR Configuration\n! Full Mesh Network\n!\nhostname mesh-node1\npassword zebra\nenable password zebra\n!\ninterface lo0\n ip address 10.200.1.1/32\n description Loopback interface\n no shutdown\n!\nline vty\n!\n!\nrouter ospf 1\n router-id 10.200.1.1\n ospf router-id 10.200.1.1\n network 10.200.1.0/24 area 0.0.0.0\n network 10.250.0.0/16 area 0.0.0.0\n network 10.251.0.0/16 area 0.0.0.0\n redistribute connected\n redistribute static\n!\nrouter bgp 65001\n bgp router-id 10.200.1.1\n bgp log-neighbor-changes\n neighbor mesh-group-1 peer-group\n neighbor mesh-group-1 remote-as 65001\n!",
        "config_hash": "f1g2h3i4j5k6l7m8n9o0p1q2r3s4t5u6v7w8x9y0"
    }
}

def get_sample_configs() -> List[Dict[str, Any]]:
    """Return all sample tunnel configurations."""
    return [
        SAMPLE_TUNNEL_CONFIG_DATA,
        SAMPLE_P2P_TUNNEL_CONFIG,
        SAMPLE_DECOMMISSION_CONFIG,
        SAMPLE_FULL_MESH_CONFIG
    ]

def save_samples_to_files() -> None:
    """Save sample configurations to JSON files."""
    import os
    
    # Create samples directory
    samples_dir = "/srv/salt/base/vrouter-agent/files/vrouter-agent/samples/tunnel_configs"
    os.makedirs(samples_dir, exist_ok=True)
    
    samples = [
        (SAMPLE_TUNNEL_CONFIG_DATA, "hub_spoke_provision.json"),
        (SAMPLE_P2P_TUNNEL_CONFIG, "point_to_point_provision.json"),
        (SAMPLE_DECOMMISSION_CONFIG, "decommission_config.json"),
        (SAMPLE_FULL_MESH_CONFIG, "full_mesh_provision.json")
    ]
    
    for config, filename in samples:
        filepath = os.path.join(samples_dir, filename)
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=2)
        print(f"Saved sample config to {filepath}")

if __name__ == "__main__":
    # Print sample configurations
    print("=== Sample Tunnel Configuration Data ===\n")
    
    for i, config in enumerate(get_sample_configs(), 1):
        print(f"Sample {i}: {config['topology']['type']} - {config['action']}")
        print(f"Order ID: {config['order_id']}")
        print(f"Tunnels: {len(config['tunnels'])}")
        print(json.dumps(config, indent=2))
        print("-" * 60)
    
    # Save to files
    save_samples_to_files()
