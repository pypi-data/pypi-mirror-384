import subprocess


def generate_wireguard_keys():
    """
    Generate a WireGuard private & public key
    Requires that the 'wg' command is available on PATH
    Returns (private_key, public_key), both strings
    """
    privkey = subprocess.check_output("wg genkey", shell=True).decode("utf-8").strip()
    pubkey = (
        subprocess.check_output(f"echo '{privkey}' | wg pubkey", shell=True)
        .decode("utf-8")
        .strip()
    )
    return (privkey, pubkey)


wg_count_per_connection = 4
global_counter = 1
counter_per_node = {1: 0, 2: 0, 3: 0, 4: 0}

for _, (src, dst) in enumerate([(1, 2), (1, 3), (1, 4), (2, 3), (2, 4), (3, 4)]):
    # print(f"Handling WG links from VPP{src}->VPP{dst}")
    for link_index in range(2):
        if link_index == 1 and not (src == 1 and dst == 2):
            continue  # make 2 link only between node1 and node2
        for wg_group_index in range(wg_count_per_connection):
            # print(f"Handling {wg_group_index+1}.WG in WG group")
            private_key1, public_key1 = generate_wireguard_keys()
            private_key2, public_key2 = generate_wireguard_keys()
            # print(private_key1, public_key1)
            print(
                f"""
# VPP{src}<->VPP{dst}, {link_index+1}.link, {wg_group_index+1}.wg
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_NAME=wg{counter_per_node[src]}
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_IP=192.168.{100+global_counter}.1
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_IP_MASK=24
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_IP_NETWORK=192.168.{100+global_counter}.0/24
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_PORT={50000+global_counter}
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_PUBLIC_KEY={public_key1}
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_PRIVATE_KEY={private_key1}
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_GRE_INTERFACE_NAME=gre{counter_per_node[src]}
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_GRE_INTERFACE_IP_ADDRESS=192.168.{200+global_counter}.1
VPP{src}_TO_VPP{dst}_WG{link_index * wg_count_per_connection + wg_group_index}_GRE_INTERFACE_IP_ADDRESS_MASK=24

VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_NAME=wg{counter_per_node[dst]}
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_IP=192.168.{100+global_counter}.2
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_IP_MASK=24
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_INTERFACE_IP_NETWORK=192.168.{100+global_counter}.0/24
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_PORT={50000+global_counter}
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_PUBLIC_KEY={public_key2}
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_PRIVATE_KEY={private_key2}
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_GRE_INTERFACE_NAME=gre{counter_per_node[dst]}
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_GRE_INTERFACE_IP_ADDRESS=192.168.{200+global_counter}.2
VPP{dst}_TO_VPP{src}_WG{link_index * wg_count_per_connection + wg_group_index}_GRE_INTERFACE_IP_ADDRESS_MASK=24"""
            )
            global_counter += 1
            counter_per_node[src] += 1
            counter_per_node[dst] += 1
