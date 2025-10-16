
from fastapi import Depends, HTTPException
from sqlmodel import Session, select
from vrouter_agent.core.db import get_session
from vrouter_agent.utils.config import get_device_serial_number
from vrouter_agent.models import Order

from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def get_orders(
    session: Session = Depends(get_session),
    offset: int = 0,
    limit: int = 10,
):
    items = session.exec(select(Order).offset(offset).limit(limit)).all()
    # Check if any orders exist
    if not items:
        return HTTPException(status_code=404, detail="No orders found")
    host = get_device_serial_number()

    return [
        {
            "id": item.id,
            "order_number": item.order_number,
            "type": item.type,
            "status": item.status,
            "tunnels": item.tunnels_in_scope(
                host
            ),  # only return the tunnels in scope for the host
        }
        for item in items
    ]


@router.get("/{order_id}")
async def get_order_by_id(
    order_id: int,
    session: Session = Depends(get_session),
):
    item = session.get(Order, order_id)
    if not item:
        return HTTPException(status_code=404, detail="Order not found")
    host = get_device_serial_number()

    return {
        "id": item.id,
        "order_number": item.order_number,
        "type": item.type,
        "status": item.status,
        "tunnels": item.tunnels_in_scope(
            host
        ),  # only return the tunnels in scope for the host
    }




