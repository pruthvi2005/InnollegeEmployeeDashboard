import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from sqlalchemy import select

from app.database import SessionLocal
from app.models.user import User
from app.core.security import decode_token
from app.core.redis_client import is_blacklisted
from app.core.websocket_manager import ws_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSockets"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
):
    """Real-time event streaming WebSocket connection authenticated by JWT query param."""
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008)  # Policy violation / unauthorized
        return

    jti = payload.get("jti")
    if jti and is_blacklisted(jti):
        await websocket.close(code=1008)
        return

    user_id = payload.get("sub")
    if not user_id:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.id == user_id)).scalar_one_or_none()
        if not user or not user.is_active:
            await websocket.close(code=1008)
            return

        role_str = user.role.value if hasattr(user.role, "value") else str(user.role)
    finally:
        db.close()

    await ws_manager.connect(websocket, user_id=user_id, role=role_str)
    try:
        # Acknowledge connection
        await websocket.send_text(
            ws_manager._format_message("connected", {"user_id": user_id, "role": role_str})
        )
        while True:
            # Keep alive and listen for client pings/messages
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("action") == "ping":
                    await websocket.send_text(
                        ws_manager._format_message("pong", {"status": "ok"})
                    )
            except Exception:
                pass
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, user_id)
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
        ws_manager.disconnect(websocket, user_id)
