# vRouter-agent
[![Build and Sync Package to S3](https://github.com/Unified-Sentinel-Data-Networks/vrouter-agent/actions/workflows/publish-vrouter-agent-s3.yml/badge.svg)](https://github.com/Unified-Sentinel-Data-Networks/vrouter-agent/actions/workflows/publish-vrouter-agent-s3.yml)


# Overview 
vrouter-agent is a custom pip module built by USDN to handle and execute transaction from customer portal to each node. 


# Requirements

- [python][python] >= 3.10
- [vpp][vpp] >= v20.06
- [multichain][multichain] > v2.3.1
- [Fast API][fastapi] > v0.115
- [FRR][frr] > v8.3
- [vrouter][vrouter] > v1.0.6
- [poetry][poetry] > v1.6.1

# Development
This project is managed by poetry. Use poetry to install and run script.
 
```bash
curl -sSL https://install.python-poetry.org | python3 -
poetry install 
poetry run server
```

# Deployment 

## Building RPM Package

To build an RPM package for AlmaLinux/RHEL deployment:

```bash
# Quick build (from project root)
./build-package.sh

# Or use the build system directly
./build/build.sh
```

The build system automatically:
- Creates a source tarball
- Builds the RPM package
- Handles Python 3.10+ requirements
- Sets up virtual environment for dependencies
- Configures systemd service integration

For detailed build documentation, see [`build/README.md`](build/README.md).

## Installation

```bash
# Install the RPM package
sudo dnf install ./dist/RPMS/noarch/vrouter-agent-*.rpm

# Enable and start the service
sudo systemctl enable vrouter-agent
sudo systemctl start vrouter-agent
```

### Run vrouter-agent as a service

vRouter depends on different services. In order to run vrouter-agent, these services must be up and running:
- VPP
- vRouter
- multichaind@{{chain}}. Chain is what defined in the nodecontrol 
- FRR

#### Create service file: 

```bash
sudo nano /etc/systemd/system/vrouter_agent.service
```

```ini
[Unit]
Description=VRouter Agent Server - API for VRouter tunnel configuration and telemetry monitoring
Requires=multichaind@{{chain}}
After=network.target multichaind@{{chain}} vpp.service vrouter.service

[Service]
Type=simple
ExecStartPre=/usr/local/bin/poetry/bin/poetry install 
ExecStart=/usr/local/bin/poetry/bin/poetry run server 
Restart=on-failure
RestartSec=30
WorkingDirectory=/opt/vrouter-agent/bin

# Optional: Set environment variables for configuration
# Environment=VRouterAgentHost=0.0.0.0
# Environment=VRouterAgentPort=8000
# Environment=VRouterAgentLogLevel=INFO
# Environment=VRouterAgentLogFile=/var/log/vrouter-agent.log

[Install]
WantedBy=multi-user.target
```

**Note**: You can configure the service by:
1. Setting environment variables in the service file (as shown above)
2. Modifying the `ExecStart` line to include command-line arguments:
   ```ini
   ExecStart=/usr/local/bin/poetry/bin/poetry run server --host 0.0.0.0 --port 9000 --log-level DEBUG
   ```

#### Enable service at boot and start service:

```bash
sudo systemctl enable vrouter-agent && sudo systemctl start vrouter-agent 
```

# Usage

## Command Line Options

The vrouter-agent supports various command-line options for configuration:

```bash
usage: vrouter-agent [-h] [--version] [--host HOST] [--port PORT] 
                     [--log-file LOG_FILE] [--log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}]

VRouter Agent Server - API for VRouter tunnel configuration and telemetry monitoring

options:
  -h, --help            show this help message and exit
  --version, -v         Show version and exit
  --host HOST           Host to bind to (default: 127.0.0.1)
  --port PORT, -p PORT  Port to bind to (default: 8000)
  --log-file LOG_FILE, -l LOG_FILE
                        Log file path (default: /var/log/vrouter-agent.log)
  --log-level {DEBUG,INFO,WARNING,ERROR,CRITICAL}
                        Log level (default: INFO)
```

### Configuration Options

The vrouter-agent can be configured through:
1. **Command-line arguments** (highest priority)
2. **Environment variables** (medium priority)
3. **Default values** (lowest priority)

#### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `VRouterAgentHost` | Server host address | `127.0.0.1` |
| `VRouterAgentPort` | Server port number | `8000` |
| `VRouterAgentLogFile` | Log file path | `/var/log/vrouter-agent.log` |
| `VRouterAgentLogLevel` | Log level | `INFO` |

### Examples

#### Basic Usage

```bash
# Run with default settings
vrouter-agent

# Show version
vrouter-agent --version
vrouter-agent -v

# Show help
vrouter-agent --help
vrouter-agent -h
```

#### Custom Configuration

```bash
# Run on specific host and port
vrouter-agent --host 0.0.0.0 --port 9000

# Enable debug logging with custom log file
vrouter-agent --log-level DEBUG --log-file /tmp/vrouter-debug.log

# Combine multiple options
vrouter-agent --host 192.168.1.100 --port 8080 --log-level WARNING --log-file /var/log/custom-vrouter.log

# Using short options
vrouter-agent -p 9000 -l /tmp/vrouter.log
```

#### Using Environment Variables

```bash
# Set environment variables
export VRouterAgentHost="0.0.0.0"
export VRouterAgentPort="9000"
export VRouterAgentLogLevel="DEBUG"
export VRouterAgentLogFile="/var/log/vrouter-debug.log"

# Run with environment configuration
vrouter-agent

# Override specific settings with command-line args
vrouter-agent --port 8080  # Uses env vars for other settings, but port 8080
```

### Logging

The vrouter-agent uses structured logging with the following features:

- **Dual output**: Logs to both console (stdout) and file simultaneously
- **Log rotation**: Automatic log file rotation at 1MB with compression
- **Configurable levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Structured format**: JSON-like format with timestamps, levels, and context

#### Log Levels

| Level | Description | When to Use |
|-------|-------------|-------------|
| `DEBUG` | Detailed diagnostic information | Development and troubleshooting |
| `INFO` | General operational messages | Production monitoring (default) |
| `WARNING` | Warning messages for unusual situations | Production monitoring |
| `ERROR` | Error messages for handled failures | Production monitoring |
| `CRITICAL` | Critical errors that may cause shutdown | Production monitoring |

#### Log File Management

- **Default location**: `/var/log/vrouter-agent.log`
- **Rotation**: Automatic at 1MB file size
- **Compression**: Old logs are compressed as `.zip` files
- **Retention**: Managed by the logging system
- **Permissions**: Ensure the user running vrouter-agent has write access to the log directory

### Run manually

```bash
/usr/local/bin/vrouter-agent
```

## Troubleshooting

### Common Issues

1. **Permission denied for log file**:
   ```bash
   # Ensure log directory exists and has proper permissions
   sudo mkdir -p /var/log
   sudo chown $(whoami):$(whoami) /var/log/vrouter-agent.log
   
   # Or use a different log file location
   vrouter-agent --log-file /tmp/vrouter-agent.log
   ```

2. **Port already in use**:
   ```bash
   # Check what's using the port
   sudo netstat -tulpn | grep :8000
   
   # Use a different port
   vrouter-agent --port 8080
   ```

3. **Service dependencies not running**:
   ```bash
   # Check required services status
   sudo systemctl status vpp
   sudo systemctl status vrouter
   sudo systemctl status multichaind@<chain-name>
   
   # Check logs for more details
   vrouter-agent --log-level DEBUG
   ```

4. **Configuration issues**:
   ```bash
   # Verify configuration with debug logging
   vrouter-agent --log-level DEBUG --log-file /tmp/debug.log
   
   # Check environment variables
   env | grep VRouterAgent
   ```

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[US Data Networks](https://usdatanetworks.com)

[python]: https://www.python.org/downloads/release/python-380/
[pip]: https://pip.pypa.io/en/stable/installation/
[vpp]: https://s3-docs.fd.io/vpp/22.06/
[multichain]: https://www.multichain.com/download-community/
[fastapi]: https://fastapi.tiangolo.com/
[frr]: https://gallery.ecr.aws/p6l6k3o9/frr
[vrouter]: https://github.com/Unified-Sentinel-Data-Networks/vrouter-pantheon
[poetry]: https://install.python-poetry.org