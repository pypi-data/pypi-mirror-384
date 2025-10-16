# VRouter Agent API Documentation

This document describes the available API endpoints for the VRouter Agent.

## Base URL
The API is served at: `http://localhost:8000` (default)

## Authentication
Currently, the API endpoints are open. Consider implementing authentication for production use.

## Available Endpoints

### Orders API (`/orders`)
- **GET** `/orders/` - List all orders
- **POST** `/orders/` - Create a new order  
- **GET** `/orders/{order_id}` - Get specific order

### Transactions API (`/transactions`)
- **GET** `/transactions/` - List all transactions
- **POST** `/transactions/` - Create a new transaction
- **GET** `/transactions/{transaction_id}` - Get specific transaction
- **GET** `/transactions/status` - Get basic system status

### Tunnel Configuration API (`/tunnel-config`)
- **GET** `/tunnel-config/` - Retrieve all tunnel configurations
  - Query params: `skip`, `limit`, `device_serial`, `status`, `tunnel_type`
- **GET** `/tunnel-config/{config_id}` - Get specific configuration by ID
- **GET** `/tunnel-config/by-tunnel/{tunnel_id}` - Get configuration by tunnel ID
  - Query params: `include_history` (boolean)
- **GET** `/tunnel-config/device/{device_serial}` - Get configurations for specific device
  - Query params: `skip`, `limit`, `status`
- **GET** `/tunnel-config/current-device/` - Get configurations for current device
  - Query params: `skip`, `limit`, `status`
- **GET** `/tunnel-config/stats/` - Get tunnel configuration statistics
- **GET** `/tunnel-config/health/` - Get tunnel config system health

### Telemetry API (`/telemetry`)
- **GET** `/telemetry/metrics/` - Enhanced system metrics with success/failure rates
- **GET** `/telemetry/status/` - System status with health indicators
- **GET** `/telemetry/health/` - Comprehensive health check with issue detection
- **GET** `/telemetry/performance/` - Detailed performance metrics and throughput
- **GET** `/telemetry/system-info/` - General system information and configuration
- **GET** `/telemetry/alerts/` - System alerts and warnings
  - Query params: `severity` (critical, high, medium, low)

#### Tunnel Telemetry Endpoints
- **GET** `/telemetry/tunnels/` - Get tunnel telemetry data with filtering
  - Query params: `status` (up, down, error, unknown), `tags` (comma-separated), `tunnel_id`, `include_metrics` (boolean)
- **GET** `/telemetry/tunnels/{tunnel_id}` - Get detailed telemetry for specific tunnel
- **GET** `/telemetry/tunnels/summary/` - Get summary overview of all tunnel telemetry
- **POST** `/telemetry/tunnels/cleanup/` - Clean up expired tunnel cache entries

## Response Formats

All endpoints return JSON responses with the following standard structure:

### Success Response
```json
{
  "success": true,
  "data": {...},
  "timestamp": "2025-06-05T10:30:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description",
  "timestamp": "2025-06-05T10:30:00Z"
}
```

### Pagination
List endpoints support pagination with `skip` and `limit` parameters:
- `skip`: Number of items to skip (default: 0)
- `limit`: Maximum number of items to return (default: 100, max: 1000)

## Health Monitoring

The telemetry endpoints provide comprehensive health monitoring:

### Health Status Levels
- **healthy**: All systems operating normally
- **warning**: Some issues detected but system is functional
- **critical**: Serious issues requiring immediate attention

### Alert Severity Levels
- **critical**: Immediate action required
- **high**: Action needed soon
- **medium**: Should be addressed
- **low**: Informational

## Example Usage

### Get System Health
```bash
curl http://localhost:8000/telemetry/health/
```

### Get Tunnel Configurations for Current Device
```bash
curl http://localhost:8000/tunnel-config/current-device/
```

### Get Critical Alerts
```bash
curl http://localhost:8000/telemetry/alerts/?severity=critical
```

### Get Performance Metrics
```bash
curl http://localhost:8000/telemetry/performance/
```

### Tunnel Telemetry Examples

#### Get All Tunnel Telemetry
```bash
curl http://localhost:8000/telemetry/tunnels/
```

#### Get Tunnels by Status
```bash
# Get only UP tunnels
curl http://localhost:8000/telemetry/tunnels/?status=up

# Get DOWN or ERROR tunnels
curl "http://localhost:8000/telemetry/tunnels/?status=down"
curl "http://localhost:8000/telemetry/tunnels/?status=error"
```

#### Filter Tunnels by Tags
```bash
# Get tunnels for specific order
curl "http://localhost:8000/telemetry/tunnels/?tags=order:12345"

# Get tunnels with multiple tags
curl "http://localhost:8000/telemetry/tunnels/?tags=tunnel_type:wireguard,vpp_verified"
```

#### Get Specific Tunnel Details
```bash
curl http://localhost:8000/telemetry/tunnels/wg0
```

#### Get Tunnel Summary
```bash
curl http://localhost:8000/telemetry/tunnels/summary/
```

#### Clean up Cache
```bash
curl -X POST http://localhost:8000/telemetry/tunnels/cleanup/
```

## Integration Notes

### Tunnel Telemetry Integration
- Tunnel telemetry is automatically collected during tunnel lifecycle events (provision, update, decommission)
- Status changes are logged in structured JSON format to `/var/log/vrouter-agent/tunnel-telemetry.log` for Splunk ingestion
- Telemetry data includes comprehensive tagging for easy filtering and search:
  - `tunnel_type:wireguard` - Tunnel technology type
  - `status:up` - Current operational status
  - `device:ABC123` - Device serial number
  - `order:12345` - Related order number
  - `topology:topo_1` - Topology identifier
  - `vpp_verified` - VPP verification completed
- In-memory caching provides fast API response times
- Cache cleanup automatically removes stale entries after 1 hour

### General Integration
- The tunnel configuration endpoints integrate with the enhanced stream processor
- Telemetry data is collected from the VRouter agent's internal metrics
- All timestamps are in ISO 8601 format (UTC)
- The API is designed to be stateless and can handle high-frequency polling

### Splunk Integration
Tunnel telemetry logs are structured for easy Splunk ingestion:

```json
{
  "event_type": "tunnel_status",
  "tunnel_id": "wg0",
  "tunnel_name": "wg0", 
  "tunnel_type": "wireguard",
  "status": "up",
  "previous_status": "down",
  "status_changed": true,
  "timestamp": 1693785600.123,
  "timestamp_iso": "2023-09-04T10:00:00.123",
  "network": {
    "local_ip": "10.1.1.1/24",
    "remote_ip": "10.1.1.2",
    "peer_endpoint": "203.0.113.1:51820"
  },
  "context": {
    "order_id": "abc123",
    "order_number": "12345",
    "topology_id": "topo_1"
  },
  "device": {
    "serial": "ABC123",
    "hostname": "node-1"
  },
  "tags": ["tunnel_type:wireguard", "status:up", "order:12345", "vpp_verified"]
}
```

#### Splunk Search Examples:
```splunk
# Find all tunnel status changes
index=vrouter event_type="tunnel_status" status_changed=true

# Find tunnels that went down
index=vrouter event_type="tunnel_status" status="down" 

# Find tunnels for specific order
index=vrouter event_type="tunnel_status" context.order_number="12345"

# Find VPP verification failures
index=vrouter event_type="tunnel_status" network.connectivity_test_passed=false
```

## Development

To start the API server:
```bash
cd /srv/salt/base/vrouter-agent/files/vrouter-agent
python -m vrouter_agent.main
```

Or using the start function:
```python
from vrouter_agent.main import start
start()
```
