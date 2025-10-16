import os
import json
from typing import Optional, Dict, List, Any, Union
from contextlib import contextmanager
from dataclasses import dataclass
from vrouter_agent.utils import run_command
import mcrpc
import re
import time
from datetime import datetime
from cryptography.fernet import Fernet
from vrouter_agent.core.config import settings

from loguru import logger as log


def get_multichain_client(chain_name: str, user: str):
    """Multichain client using secure directory structure

    Args:
        chain_name (str): chain_name
        user (str): user (maintained for compatibility but uses secure location)

    Raises:
        OSError: File error

    Returns:
        client: multichain_client
    """
    try:
        # Use the secure multichain directory
        multichain_dir = f"/var/lib/multichain/.multichain/{chain_name}"
        if not os.path.exists(multichain_dir):
            raise OSError(
                f"Multichain {chain_name} is not connected to this node. Please try again."
            )
        rpcuser = None
        rpcpasswd = None

        with open(
            os.path.join(multichain_dir, "multichain.conf"),
            "r",
            encoding="utf-8",
        ) as blockchain_file:
            for line in blockchain_file.readlines():
                if line.startswith("rpcuser"):
                    rpcuser = line.split("=")[1].strip()
                if line.startswith("rpcpassword"):
                    rpcpasswd = line.split("=")[1].strip()
        with open(
            os.path.join(multichain_dir, "params.dat"),
            "r",
            encoding="utf-8",
        ) as blockchain_file:
            for line in blockchain_file.readlines():
                if line.startswith("default-rpc-port"):
                    rpcport = re.findall(r"\d+", line)[0]


        client = mcrpc.RpcClient("localhost", rpcport, rpcuser, rpcpasswd, False)
        return client

    except IOError as error:
        log.exception("Error occurred: " + str(error))

    except KeyError as error:
        log.exception(str(error))

    return None


@dataclass
class MultichainConfig:
    """Configuration for multichain connection."""
    chain_name: str
    user: str
    rpc_host: str = "localhost"
    max_retries: int = 3
    retry_delay: float = 5.0
    timeout: float = 30.0


@dataclass
class StreamItem:
    """Represents a stream item from multichain."""
    txid: str
    data: str

    publishers: Optional[List[str]] = None
    keys: Optional[List[str]] = None
    offchain: Optional[bool] = False
    available: Optional[bool] = True
    confirmations: Optional[int] = 0
    blocktime: Optional[int] = None
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamItem':
        """Create StreamItem from dictionary."""
        return cls(
            txid=data.get('txid', ''),
            publishers=data.get('publishers', []),
            keys=data.get('keys', []),
            data=data.get('data', {}),
            confirmations=data.get('confirmations', 0),
            blocktime=data.get('blocktime'),
            offchain=data.get('offchain', False),
            available=data.get('available', True)
        )
    @classmethod
    def get_decrypted_data(self) -> str:
        """Decrypt the data using the private key"""
        # convert data to bytes
        data = bytes.fromhex(self.data)
        # decrypt the data
        key = Fernet(settings.config.global_.secret_key.encode("utf-8"))
        
        decrypted_data = key.decrypt(data)
        return decrypted_data.decode("utf-8")




class MultichainConnectionError(Exception):
    """Exception raised when multichain connection fails."""
    pass


class StreamNotFoundError(Exception):
    """Exception raised when stream is not found."""
    pass


@contextmanager
def multichain_client_context(config: MultichainConfig):
    """Context manager for multichain client connections."""
    client = None
    try:
        client = get_multichain_client_enhanced(config)
        if not client:
            raise MultichainConnectionError(f"Failed to connect to chain: {config.chain_name}")
        yield client
    finally:
        # Cleanup if needed
        if client:
            log.debug(f"Closed multichain client connection for {config.chain_name}")


def get_multichain_client_enhanced(config: MultichainConfig) -> Optional[mcrpc.RpcClient]:
    """Enhanced multichain client with better error handling and configuration.
    
    Args:
        config: Multichain configuration
        
    Returns:
        Optional[mcrpc.RpcClient]: Multichain client or None if failed
        
    Raises:
        MultichainConnectionError: If connection fails after retries
    """
    for attempt in range(config.max_retries):
        try:
            log.info(f"Attempting to connect to multichain {config.chain_name} (attempt {attempt + 1}/{config.max_retries})")
            
            # Use the secure multichain directory
            multichain_dir = f"/var/lib/multichain/.multichain/{config.chain_name}"
            if not os.path.exists(multichain_dir):
                raise OSError(
                    f"Multichain {config.chain_name} is not connected to this node. Please try again."
                )
            
            # Read RPC credentials
            rpc_config = _read_rpc_config(multichain_dir)
            
            # Test connection with getinfo
            _test_multichain_connection(config.chain_name, config.user)
            
            # Create client
            client = mcrpc.RpcClient(
                config.rpc_host, 
                rpc_config['rpcport'], 
                rpc_config['rpcuser'], 
                rpc_config['rpcpasswd'], 
                False
            )
            
            # Test client connection
            try:
                client.getinfo()
                log.info(f"Successfully connected to multichain {config.chain_name}")
                return client
            except Exception as e:
                log.warning(f"Client connection test failed: {e}")
                raise
                
        except Exception as error:
            log.warning(f"Connection attempt {attempt + 1} failed: {error}")
            if attempt < config.max_retries - 1:
                log.info(f"Retrying in {config.retry_delay} seconds...")
                time.sleep(config.retry_delay)
            else:
                log.error(f"All connection attempts failed for {config.chain_name}")
                raise MultichainConnectionError(f"Failed to connect after {config.max_retries} attempts")
    
    return None


def _read_rpc_config(multichain_dir: str) -> Dict[str, str]:
    """Read RPC configuration from multichain directory."""
    rpcuser = None
    rpcpasswd = None
    rpcport = None
    
    # Read multichain.conf
    conf_file = os.path.join(multichain_dir, "multichain.conf")
    if os.path.exists(conf_file):
        with open(conf_file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                line = line.strip()
                if line.startswith("rpcuser"):
                    rpcuser = line.split("=", 1)[1].strip()
                elif line.startswith("rpcpassword"):
                    rpcpasswd = line.split("=", 1)[1].strip()
    
    # Read params.dat for port
    params_file = os.path.join(multichain_dir, "params.dat")
    if os.path.exists(params_file):
        with open(params_file, "r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.startswith("default-rpc-port"):
                    rpcport = re.findall(r"\d+", line)[0]
    
    if not all([rpcuser, rpcpasswd, rpcport]):
        raise ValueError("Missing RPC configuration parameters")
    
    return {
        'rpcuser': rpcuser,
        'rpcpasswd': rpcpasswd,
        'rpcport': rpcport
    }


def _test_multichain_connection(chain_name: str, user: str) -> None:
    """Test multichain connection using direct RPC instead of CLI.
    
    This method uses direct RPC connection to test multichain availability,
    avoiding sudo requirements and working with the secure multichain setup.
    """
    try:
        # Use the secure multichain directory
        multichain_dir = f"/var/lib/multichain/.multichain/{chain_name}"
        
        if not os.path.exists(multichain_dir):
            raise MultichainConnectionError(
                f"Multichain {chain_name} directory not found at {multichain_dir}"
            )
        
        # Read RPC configuration from secure location
        rpc_config = _read_rpc_config(multichain_dir)
        
        # Test direct RPC connection instead of CLI
        client = mcrpc.RpcClient(
            "localhost",
            rpc_config['rpcport'],
            rpc_config['rpcuser'],
            rpc_config['rpcpasswd'],
            False
        )
        
        # Test the connection with a simple getinfo call
        info = client.getinfo()
        log.debug(f"MultiChain connection test successful for {chain_name}: {info.get('version', 'unknown version')}")
        
    except Exception as e:
        raise MultichainConnectionError(f"RPC connection test failed for {chain_name}: {str(e)}")


def list_stream_items_enhanced(
    config: MultichainConfig,
    stream_name: str,
    start: Optional[str] = None,
    count: int = 100,
    verbose: bool = True,
    skip_txids: Optional[List[str]] = None
) -> List[StreamItem]:
    """Enhanced function to list stream items with better filtering and pagination.
    
    Args:
        config: Multichain configuration
        stream_name: Name of the stream
        start: Starting point for pagination
        count: Maximum number of items to return
        verbose: Whether to include verbose information
        skip_txids: List of transaction IDs to skip
        
    Returns:
        List[StreamItem]: List of stream items
        
    Raises:
        StreamNotFoundError: If stream doesn't exist
        MultichainConnectionError: If connection fails
    """
    skip_txids = skip_txids or []
    
    with multichain_client_context(config) as client:
        # Ensure stream subscription
        ensure_stream_subscription(client, stream_name)
        
        # Get stream items
        try:
            raw_items = client.liststreamitems(stream_name, verbose, count, start)
        except Exception as e:
            if "stream not found" in str(e).lower():
                raise StreamNotFoundError(f"Stream '{stream_name}' not found")
            raise MultichainConnectionError(f"Failed to list stream items: {e}")
        
        # Convert to StreamItem objects and filter
        items = []
        for raw_item in raw_items:
            if raw_item.get('txid') not in skip_txids:
                try:
                    item = StreamItem.from_dict(raw_item)
                    items.append(item)
                except Exception as e:
                    log.warning(f"Failed to parse stream item: {e}")
                    continue
        
        log.info(f"Retrieved {len(items)} items from stream '{stream_name}'")
        return items


def ensure_stream_subscription(client: mcrpc.RpcClient, stream_name: str) -> bool:
    """Ensure a stream is subscribed.
    
    Args:
        client: Multichain RPC client
        stream_name: Name of the stream
        
    Returns:
        bool: True if subscribed successfully
        
    Raises:
        StreamNotFoundError: If stream doesn't exist
    """
    try:
        streams = client.liststreams(stream_name)
        
        if not streams:
            raise StreamNotFoundError(f"Stream '{stream_name}' not found")
        
        for stream in streams:
            if not stream.get("subscribed", False):
                log.info(f"Subscribing to stream: {stream['name']}")
                client.subscribe(stream["name"])
                return True
        
        log.debug(f"Already subscribed to stream: {stream_name}")
        return True
        
    except Exception as e:
        if "stream not found" in str(e).lower():
            raise StreamNotFoundError(f"Stream '{stream_name}' not found")
        raise


def publish_to_stream(
    config: MultichainConfig,
    stream_name: str,
    key: str,
    data: Union[str, Dict[str, Any]],
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Publish data to a multichain stream.
    
    Args:
        config: Multichain configuration
        stream_name: Name of the stream
        key: Key for the data
        data: Data to publish (string or dictionary)
        options: Additional options for publishing
        
    Returns:
        str: Transaction ID of the published item
        
    Raises:
        StreamNotFoundError: If stream doesn't exist
        MultichainConnectionError: If connection fails
    """
    with multichain_client_context(config) as client:
        # Ensure stream exists and we're subscribed
        ensure_stream_subscription(client, stream_name)
        
        # Convert data to hex if it's a dictionary
        if isinstance(data, dict):
            data_str = json.dumps(data)
            data_hex = data_str.encode('utf-8').hex()
        else:
            data_hex = data.encode('utf-8').hex()
        
        try:
            # Publish to stream
            if options:
                txid = client.publishfrom(
                    client.getaddresses()[0],  # Use first address
                    stream_name,
                    key,
                    data_hex,
                    options
                )
            else:
                txid = client.publish(stream_name, key, data_hex)
            
            log.info(f"Published to stream '{stream_name}' with key '{key}', txid: {txid}")
            return txid
            
        except Exception as e:
            if "stream not found" in str(e).lower():
                raise StreamNotFoundError(f"Stream '{stream_name}' not found")
            raise MultichainConnectionError(f"Failed to publish to stream: {e}")


def get_stream_info(config: MultichainConfig, stream_name: str) -> Dict[str, Any]:
    """Get information about a stream.
    
    Args:
        config: Multichain configuration
        stream_name: Name of the stream
        
    Returns:
        Dict[str, Any]: Stream information
        
    Raises:
        StreamNotFoundError: If stream doesn't exist
    """
    with multichain_client_context(config) as client:
        try:
            streams = client.liststreams(stream_name, True)  # verbose=True
            
            if not streams:
                raise StreamNotFoundError(f"Stream '{stream_name}' not found")
            
            return streams[0]
            
        except Exception as e:
            if "stream not found" in str(e).lower():
                raise StreamNotFoundError(f"Stream '{stream_name}' not found")
            raise MultichainConnectionError(f"Failed to get stream info: {e}")


def list_all_streams(config: MultichainConfig) -> List[Dict[str, Any]]:
    """List all streams on the multichain.
    
    Args:
        config: Multichain configuration
        
    Returns:
        List[Dict[str, Any]]: List of stream information
    """
    with multichain_client_context(config) as client:
        try:
            return client.liststreams("*", True)  # All streams, verbose=True
        except Exception as e:
            raise MultichainConnectionError(f"Failed to list streams: {e}")


def create_stream(
    config: MultichainConfig,
    stream_name: str,
    open_flag: bool = True,
    options: Optional[Dict[str, Any]] = None
) -> str:
    """Create a new stream on the multichain.
    
    Args:
        config: Multichain configuration
        stream_name: Name of the new stream
        open_flag: Whether the stream is open for writing
        options: Additional stream options
        
    Returns:
        str: Transaction ID of the stream creation
    """
    with multichain_client_context(config) as client:
        try:
            if options:
                txid = client.create("stream", stream_name, open_flag, options)
            else:
                txid = client.create("stream", stream_name, open_flag)
            
            log.info(f"Created stream '{stream_name}' with txid: {txid}")
            return txid
            
        except Exception as e:
            raise MultichainConnectionError(f"Failed to create stream: {e}")


def list_stream_items(
    config: MultichainConfig,
    stream_name: str,
    start: Optional[str] = None,
    count: int = 100,
    verbose: bool = True
) -> List[StreamItem]:
    """Compatibility wrapper for list_stream_items_enhanced.
    
    This function provides backward compatibility for existing code that expects
    the list_stream_items function. It calls list_stream_items_enhanced with
    default parameters.
    
    Args:
        config: Multichain configuration
        stream_name: Name of the stream
        start: Starting point for pagination
        count: Maximum number of items to return
        verbose: Whether to include verbose information
        
    Returns:
        List[StreamItem]: List of stream items
        
    Raises:
        StreamNotFoundError: If stream doesn't exist
        MultichainConnectionError: If connection fails
    """
    return list_stream_items_enhanced(
        config=config,
        stream_name=stream_name,
        start=start,
        count=count,
        verbose=verbose
    )


def get_multichain_status(config: MultichainConfig) -> Dict[str, Any]:
    """Get comprehensive status of the multichain node.
    
    Args:
        config: Multichain configuration
        
    Returns:
        Dict[str, Any]: Status information
    """
    with multichain_client_context(config) as client:
        try:
            info = client.getinfo()
            
            # Get additional information
            peer_info = client.getpeerinfo()
            blockchain_info = client.getblockchaininfo()
            
            return {
                "node_info": info,
                "peer_count": len(peer_info),
                "peers": peer_info,
                "blockchain": blockchain_info,
                "timestamp": datetime.now().isoformat(),
                "chain_name": config.chain_name
            }
            
        except Exception as e:
            raise MultichainConnectionError(f"Failed to get multichain status: {e}")
