"""
Task Stream API - Server-Sent Events for real-time task updates
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.orm import Session
import asyncio
import json
import logging
from typing import AsyncGenerator, Dict, Any, Optional

from api.src.database import get_db
from api.src.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/task-stream", tags=["task-stream"])

# Global queue for broadcasting task updates to all connected clients
# Each user will have their own queue filtered by user_id
task_broadcast_queues: Dict[int, asyncio.Queue] = {}


async def broadcast_task_update(task_update: Dict[str, Any]):
    """
    Broadcast task update to all connected clients for the specific user.
    
    Args:
        task_update: Task update dictionary with task_id, status, result, created_by
    """
    user_id = task_update.get("created_by")
    if not user_id:
        logger.warning(f"Task update missing created_by field: {task_update}")
        return
    
    if user_id in task_broadcast_queues:
        try:
            await task_broadcast_queues[user_id].put(task_update)
            logger.info(f"Broadcasted task {task_update.get('task_id')} to user {user_id}")
        except Exception as e:
            logger.error(f"Failed to broadcast task update to user {user_id}: {e}")


@router.get("/")
async def stream_task_updates(
    token: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """
    SSE endpoint for streaming real-time task updates to the client.
    Accepts token as query parameter since EventSource doesn't support custom headers.
    
    Returns:
        EventSourceResponse with task update events
    """
    # Authenticate using token from query param
    if not token:
        raise HTTPException(status_code=401, detail="Authentication token required")
    
    try:
        # Verify JWT token
        from api.src.auth import verify_token
        payload = verify_token(token)
        
        if not payload:
            logger.error(f"SSE authentication failed: Invalid token")
            raise HTTPException(status_code=401, detail="Invalid token")
        
        user_id = payload.get("sub")
        
        if not user_id:
            logger.error(f"SSE authentication failed: No sub in payload")
            raise HTTPException(status_code=401, detail="Invalid token - no user ID")
            
        # Get user from database
        from api.src.models import User
        user = db.query(User).filter(User.id == int(user_id)).first()
        if not user:
            logger.error(f"SSE authentication failed: User {user_id} not found in database")
            raise HTTPException(status_code=401, detail="User not found")
        
        current_user = {"id": user.id, "email": user.email, "role": user.role}
        logger.info(f"User {user_id} ({user.email}) authenticated for SSE stream")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"SSE authentication failed with exception: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    logger.info(f"User {user_id} connected to task stream")
    
    async def event_generator() -> AsyncGenerator[Dict[str, str], None]:
        # Create a queue for this user's connection
        queue = asyncio.Queue()
        task_broadcast_queues[user_id] = queue
        
        try:
            # Send initial connection event
            yield {
                "event": "connected",
                "data": json.dumps({"message": "Connected to task stream", "user_id": user_id})
            }
            
            # Keep connection alive and send updates
            while True:
                try:
                    # Wait for task update with timeout for keepalive
                    task_update = await asyncio.wait_for(queue.get(), timeout=30.0)
                    
                    # Send task update event
                    yield {
                        "event": "task_update",
                        "data": json.dumps({
                            "task_id": task_update.get("task_id"),
                            "task_type": task_update.get("task_type"),
                            "status": task_update.get("status"),
                            "result": task_update.get("result"),
                            "error_message": task_update.get("error_message"),
                            "progress": task_update.get("progress", 100)
                        })
                    }
                    
                except asyncio.TimeoutError:
                    # Send keepalive comment every 30 seconds
                    yield {
                        "event": "keepalive",
                        "data": json.dumps({"timestamp": asyncio.get_event_loop().time()})
                    }
                    
        except asyncio.CancelledError:
            logger.info(f"User {user_id} disconnected from task stream")
        finally:
            # Clean up queue when connection closes
            if user_id in task_broadcast_queues:
                del task_broadcast_queues[user_id]
                logger.info(f"Cleaned up task stream queue for user {user_id}")
    
    return EventSourceResponse(event_generator())
