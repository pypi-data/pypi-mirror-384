from contextlib import asynccontextmanager
import sys
import argparse
from fastapi import FastAPI
from loguru import logger
import logging
import uvicorn

from vrouter_agent.core.db import init_db
from vrouter_agent.api import orders, transactions, tunnel_config, telemetry, root
from vrouter_agent.services.chain import Chain
from vrouter_agent.services.startup import initialize_services, shutdown_services
from vrouter_agent.utils.logger import InterceptHandler, format_record
import os
from vrouter_agent.core.config import settings


# Default configuration values
DEFAULT_LOG_FILE = "/var/log/vrouter-agent/vrouter-agent.log"
DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
DEFAULT_LOG_LEVEL = "INFO"

# Dynamically get version from pyproject.toml
def get_version():
    try:
        import toml
        import pathlib
        pyproject_path = pathlib.Path(__file__).parent / "pyproject.toml"
        if pyproject_path.exists():
            data = toml.load(pyproject_path)
            # Try both [tool.poetry] and [project] tables
            if "tool" in data and "poetry" in data["tool"] and "version" in data["tool"]["poetry"]:
                return data["tool"]["poetry"]["version"]
            elif "project" in data and "version" in data["project"]:
                return data["project"]["version"]
    except Exception:
        pass
    return "unknown"

VERSION = get_version()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure logging in the child process (when uvicorn reloads)
    # Get configuration from environment variables set by parent process
    log_file = os.getenv("VRouterAgentLogFile", DEFAULT_LOG_FILE)
    log_level = os.getenv("VRouterAgentLogLevel", DEFAULT_LOG_LEVEL)
    setup_logging(log_file, log_level)
    
    # Startup
    logger.debug("Initializing database")
    init_db()
    
    # Initialize application services (stream listener, processor, etc.)
    logger.info("Initializing application services...")
    success = await initialize_services()
    if not success:
        logger.error("Failed to initialize application services")
        sys.exit(1)
    
    for route in app.routes:
        logger.info(f"Route: {route.path} - {route.name}")

    yield
    
    # Shutdown
    logger.info("Shutting down application services...")
    await shutdown_services()

app = FastAPI(
    title="VRouter Agent API",
    description="API for VRouter tunnel configuration and telemetry monitoring",
    version="1.0.0",
    contact={
        "name": "USDN vRouter Agent Server",
        "email": "support@usdatanetworks.com",
    },
    license_info={
        "name": "Private License",
    },
    lifespan=lifespan
)
app.include_router(root.router, tags=["root"])
app.include_router(orders.router, prefix="/orders", tags=["orders"])
app.include_router(transactions.router, prefix="/transactions", tags=["transactions"])
app.include_router(tunnel_config.router, tags=["tunnel-config"])
app.include_router(telemetry.router, tags=["telemetry"])


def setup_logging(log_file: str, log_level: str):
    """Configure logging with the specified log file and level."""
    # Intercept standard logging and redirect to loguru
    logging.getLogger().handlers = [InterceptHandler()]
    logging.getLogger().setLevel(logging.DEBUG)  # Capture all levels, filtering happens in loguru
    
    # Ensure log directory exists
    import os
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    # Normalize log level to uppercase string
    log_level_str = log_level.upper()
    
    # Remove default handler and configure loguru with both console and file handlers
    logger.remove()  # Remove default handler
    
    # Add console handler (for stdout/stderr)
    logger.add(
        sys.stderr,
        format=format_record,
        level=log_level_str,
        backtrace=True,
        diagnose=True,
        enqueue=True,
    )
    
    # Add file handler with rotation
    logger.add(
        log_file,
        format=format_record,
        level=log_level_str,
        rotation="50 MB",  # Rotate log file after it reaches 50 MB -for testing purposes
        retention="90 days",  # Keep logs for 90 days
        compression=None,  # No compression for Splunk compatibility
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )




def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="VRouter Agent Server - API for VRouter tunnel configuration and telemetry monitoring",
        prog="vrouter-agent",
        epilog="For more information, visit: https://github.com/Unified-Sentinel-Data-Networks"
    )
    
    # Version option
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show version and exit"
    )
    
    # Server configuration options
    parser.add_argument(
        "--host",
        default=os.getenv("VRouterAgentHost", DEFAULT_HOST),
        help=f"Host to bind to (default: {DEFAULT_HOST}). Can also be set via VRouterAgentHost environment variable."
    )
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=int(os.getenv("VRouterAgentPort", DEFAULT_PORT)),
        help=f"Port to bind to (default: {DEFAULT_PORT}). Can also be set via VRouterAgentPort environment variable."
    )
    
    # Logging configuration options
    parser.add_argument(
        "--log-file", "-l",
        default=os.getenv("VRouterAgentLogFile", DEFAULT_LOG_FILE),
        help=f"Log file path (default: {DEFAULT_LOG_FILE}). Can also be set via VRouterAgentLogFile environment variable."
    )
    parser.add_argument(
        "--log-level",
        default=os.getenv("VRouterAgentLogLevel", DEFAULT_LOG_LEVEL),
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help=f"Log level (default: {DEFAULT_LOG_LEVEL}). Can also be set via VRouterAgentLogLevel environment variable."
    )
    return parser.parse_args()


def start():
    """Start the VRouter Agent Server with command-line configuration."""
    args = parse_args()
    
    # Set environment variables so child process can access them
    os.environ["VRouterAgentLogFile"] = args.log_file
    os.environ["VRouterAgentLogLevel"] = args.log_level
    
    # Setup logging with the specified configuration
    setup_logging(args.log_file, args.log_level)

    logger.info("Starting vRouter Agent Server...")
    logger.info("************************")

    logger.info(f"Log file is saved to {args.log_file}")
    logger.info(f"Log level set to {args.log_level}")
    logger.info(f"Starting server on {args.host}:{args.port}")
    logger.info("************************")
    logger.info(settings.config.interfaces)
    logger.info(settings.config.multichain)
    
    # Basic multichain connectivity check - stream subscription for hostname and order_update is handled by startup services
    chain = Chain(chain=settings.config.multichain.chain, user=settings.config.global_.user)
    if not chain.is_running():
        logger.error(f"Multichain daemon for chain {settings.config.multichain.chain} is not running.")
        sys.exit(1)
    logger.info("Multichain daemon is running")
    
    # Configure uvicorn logging to use loguru
    logging.getLogger("uvicorn").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]
    logging.getLogger("fastapi").handlers = [InterceptHandler()]
    
    uvicorn.run(
        "vrouter_agent.main:app", 
        host=args.host,
        port=args.port,
        reload=True,
        log_level=args.log_level.lower(),
        log_config=None,  # Disable uvicorn's default logging config to use our loguru setup
    )


if __name__ == "__main__":
    start()
