from fastapi import Depends, Form, BackgroundTasks
from loguru import logger
from sqlmodel import Session
from vrouter_agent.agent import VRouterAgent
from vrouter_agent.core.db import get_session
from vrouter_agent.services.chain import Chain
from vrouter_agent.models import Transaction
from vrouter_agent.core.config import settings 
from fastapi import APIRouter
from vrouter_agent.enhanced_stream_processor import get_stream_processor
from vrouter_agent.services.stream_listener import (
    get_stream_listener, 
    start_stream_listener, 
    stop_stream_listener,
    StreamListenerConfig
)
import time

router = APIRouter()

# Legacy route maintained for backwards compatibility
@router.post(
    "/",
)
async def transaction(
    background_tasks: BackgroundTasks,
    txid: str = Form(...),
    stream: str = Form(...),
    session: Session = Depends(get_session),
):
    """
    Legacy transaction endpoint maintained for backwards compatibility.
    
    Note: The system now primarily uses the stream listener service
    to automatically monitor and process transactions from the designated
    stream instead of relying on POST data.
    """
    logger.warning(f"Received transaction via legacy POST endpoint: {txid} on stream: {stream}")
    logger.info("Consider migrating to the stream listener service for automatic transaction processing")
    
    # Create transaction record
    new_transaction = Transaction(txid=txid, stream=stream)
    session.add(new_transaction)
    session.commit()
    logger.info(f"Transaction received: {new_transaction.id} on stream: {stream}")

    # Get the enhanced stream processor
    processor = await get_stream_processor()
        
    # Process transaction asynchronously using the enhanced processor
    success = await processor.process_transaction(new_transaction, stream, session)
    
    if success:
        logger.info(f"Transaction {new_transaction.id} queued for processing")
        return {
            "message": "Transaction queued for processing", 
            "id": new_transaction.id,
            "status": "queued"
        }
    else:
        logger.error(f"Failed to queue transaction {new_transaction.id}")
        return {
            "message": "Failed to queue transaction", 
            "id": new_transaction.id,
            "status": "error"
        }, 500

# Stream Listener Management Endpoints

# Endpoint to start the stream listener
@router.post("/stream-listener/start")
async def start_listener():
    """Start the stream listener service for monitoring the designated stream."""
    try:
        success = await start_stream_listener()
        
        if success:
            listener = await get_stream_listener()
            return {
                "message": "Stream listener started successfully",
                "stream_name": listener.config.stream_name,
                "hostname": listener.hostname,
                "status": "running"
            }
        else:
            return {
                "message": "Failed to start stream listener",
                "status": "error"
            }, 500
    except Exception as e:
        logger.error(f"Error starting stream listener: {e}")
        return {
            "message": f"Error starting stream listener: {str(e)}",
            "status": "error"
        }, 500

# Endpoint to stop the stream listener
@router.post("/stream-listener/stop")
async def stop_listener():
    """Stop the stream listener service."""
    try:
        await stop_stream_listener()
        return {
            "message": "Stream listener stopped successfully",
            "status": "stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping stream listener: {e}")
        return {
            "message": f"Error stopping stream listener: {str(e)}",
            "status": "error"
        }, 500

# Endpoint to get stream listener status
@router.get("/stream-listener/status")
async def get_listener_status():
    """Get current status of the stream listener."""
    try:
        listener = await get_stream_listener()
        status = listener.get_status()
        metrics = listener.get_metrics()
        
        return {
            "status": status,
            "metrics": metrics,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting stream listener status: {e}")
        return {
            "message": f"Error getting status: {str(e)}",
            "status": "error"
        }, 500

# Endpoint to get detailed processing statistics
@router.get("/stream-listener/stats")
async def get_listener_stats():
    """Get detailed processing statistics including database information."""
    try:
        listener = await get_stream_listener()
        stats = listener.get_processing_stats()
        
        return {
            "statistics": stats,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error getting stream listener statistics: {e}")
        return {
            "message": f"Error getting statistics: {str(e)}",
            "status": "error"
        }, 500

# Endpoint to check if a specific transaction is processed
@router.get("/stream-listener/transaction/{txid}/processed")
async def check_transaction_processed(txid: str):
    """Check if a specific transaction has been processed."""
    try:
        listener = await get_stream_listener()
        is_processed = listener.is_transaction_processed(txid)
        
        return {
            "txid": txid,
            "processed": is_processed,
            "timestamp": time.time()
        }
    except Exception as e:
        logger.error(f"Error checking transaction {txid}: {e}")
        return {
            "message": f"Error checking transaction: {str(e)}",
            "txid": txid,
            "status": "error"
        }, 500

# Endpoint to manually mark a transaction as processed
@router.post("/stream-listener/transaction/{txid}/mark-processed")
async def mark_transaction_processed(txid: str):
    """Manually mark a transaction as processed."""
    try:
        listener = await get_stream_listener()
        listener.mark_transaction_processed(txid)
        
        return {
            "message": f"Transaction {txid} marked as processed",
            "txid": txid,
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error marking transaction {txid} as processed: {e}")
        return {
            "message": f"Error marking transaction: {str(e)}",
            "txid": txid,
            "status": "error"
        }, 500

# Endpoint to reload processed transactions from database
@router.post("/stream-listener/reload-cache")
async def reload_processed_cache():
    """Reload processed transactions cache from database."""
    try:
        listener = await get_stream_listener()
        listener.reload_processed_transactions()
        
        return {
            "message": "Processed transactions cache reloaded from database",
            "status": "success"
        }
    except Exception as e:
        logger.error(f"Error reloading cache: {e}")
        return {
            "message": f"Error reloading cache: {str(e)}",
            "status": "error"
        }, 500

# Endpoint to configure stream listener
@router.post("/stream-listener/configure")
async def configure_listener(
    stream_name: str = Form(None),
    poll_interval: float = Form(5.0),
    batch_size: int = Form(50),
    max_retries: int = Form(3)
):
    """Configure stream listener settings."""
    try:
        # Get current listener
        current_listener = await get_stream_listener()
        is_running = current_listener.is_running
        
        # Stop if running
        if is_running:
            await stop_stream_listener()
        
        # Create new configuration
        config = StreamListenerConfig(
            stream_name=stream_name or current_listener.hostname,
            poll_interval=poll_interval,
            batch_size=batch_size,
            max_retries=max_retries
        )
        
        # Start with new config
        success = await start_stream_listener(config)
        
        return {
            "message": "Stream listener configured successfully",
            "config": {
                "stream_name": config.stream_name,
                "poll_interval": config.poll_interval,
                "batch_size": config.batch_size,
                "max_retries": config.max_retries
            },
            "status": "running" if success else "error"
        }
    except Exception as e:
        logger.error(f"Error configuring stream listener: {e}")
        return {
            "message": f"Error configuring listener: {str(e)}",
            "status": "error"
        }, 500
# Legacy processing status endpoint
@router.get("/status")
async def get_processing_status():
    """Get current stream processor status and metrics."""
    processor = await get_stream_processor()
    status = processor.get_status()
    metrics = processor.get_metrics()
    
    return {
        "processor_status": status,
        "metrics": metrics,
        "timestamp": time.time()
    }

# Legacy transaction status endpoint
@router.get("/{transaction_id}/status")
async def get_transaction_status(transaction_id: int, session: Session = Depends(get_session)):
    """Get status of a specific transaction."""
    transaction = session.get(Transaction, transaction_id)
    if not transaction:
        return {"error": "Transaction not found"}, 404
    
    return {
        "transaction_id": transaction.id,
        "txid": transaction.txid,
        "stream": transaction.stream,
        "created_at": transaction.created_at,
        "status": "completed"  # This could be enhanced with actual status tracking
    }


