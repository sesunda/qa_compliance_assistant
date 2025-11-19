"""
Background task worker for processing agent tasks asynchronously.

This worker polls the database for pending tasks and executes them in the background
without blocking API requests.
"""
import asyncio
import logging
import time
from datetime import datetime
from api.src.utils.datetime_utils import now_sgt, SGT
from typing import Dict, Any, Callable, Optional
from sqlalchemy.orm import Session

from api.src.database import SessionLocal
from api.src.models import AgentTask
from api.src.agent_schemas import TaskStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskWorker:
    """Background worker for processing agent tasks"""
    
    def __init__(self, poll_interval: int = 5, max_concurrent_tasks: int = 3):
        """
        Initialize the task worker.
        
        Args:
            poll_interval: Seconds between database polls for new tasks
            max_concurrent_tasks: Maximum number of tasks to run concurrently
        """
        self.poll_interval = poll_interval
        self.max_concurrent_tasks = max_concurrent_tasks
        self.task_handlers: Dict[str, Callable] = {}
        self.running_tasks: Dict[int, asyncio.Task] = {}
        self.is_running = False
        self.listen_task = None
        self.notification_queue = asyncio.Queue()
        
    def register_handler(self, task_type: str, handler: Callable):
        """
        Register a handler function for a specific task type.
        
        Args:
            task_type: The type of task this handler processes
            handler: Async function that takes (task_id, payload) and returns result
        """
        self.task_handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")
    
    async def start(self):
        """Start the background worker"""
        self.is_running = True
        logger.info("Task worker started")
        
        # Start NOTIFY listener in background
        self.listen_task = asyncio.create_task(self._listen_for_notifications())
        
        try:
            while self.is_running:
                # Check for notifications first (immediate processing)
                try:
                    while not self.notification_queue.empty():
                        task_id = await asyncio.wait_for(self.notification_queue.get(), timeout=0.1)
                        logger.info(f"Processing notified task {task_id}")
                        await self._process_pending_tasks()
                except asyncio.TimeoutError:
                    pass
                
                # Then do regular polling (fallback)
                await self._process_pending_tasks()
                await asyncio.sleep(self.poll_interval)
        except Exception as e:
            logger.error(f"Worker error: {e}", exc_info=True)
        finally:
            logger.info("Task worker stopped")
    
    async def stop(self):
        """Stop the background worker gracefully"""
        logger.info("Stopping task worker...")
        self.is_running = False
        
        # Cancel listener task
        if self.listen_task:
            self.listen_task.cancel()
            try:
                await self.listen_task
            except asyncio.CancelledError:
                pass
        
        # Wait for running tasks to complete
        if self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} tasks to complete...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("All tasks completed")
    
    async def _listen_for_notifications(self):
        """Listen for PostgreSQL NOTIFY events using asyncpg with auto-reconnect"""
        from api.src.db.async_database import async_db
        
        while self.is_running:
            try:
                conn = await async_db.get_listen_connection()
                
                async def notification_handler(connection, pid, channel, payload):
                    logger.info(f"Received NOTIFY on '{channel}': task {payload}")
                    await self.notification_queue.put(payload)
                
                await conn.add_listener('new_task', notification_handler)
                logger.info("Started listening for PostgreSQL NOTIFY on 'new_task' channel")
                
                # Keep connection alive with minimal sleep to allow immediate event processing
                # Changed from sleep(30) to sleep(0.1) to eliminate 60s NOTIFY delay
                while self.is_running:
                    await asyncio.sleep(0.1)  # Minimal sleep - allows instant notification processing
                    # Note: asyncpg handles connection health automatically
                    # Removed explicit health checks that were blocking notifications
            except asyncio.CancelledError:
                logger.info("NOTIFY listener cancelled")
                break
            except Exception as e:
                logger.error(f"NOTIFY listener error: {e}. Reconnecting in 5s...", exc_info=True)
                await asyncio.sleep(5)
        
        logger.info("NOTIFY listener stopped")
    
    async def _process_pending_tasks(self):
        """Poll database for pending tasks and start processing them"""
        db = SessionLocal()
        try:
            # Clean up completed tasks from tracking
            completed_task_ids = [
                task_id for task_id, task in self.running_tasks.items()
                if task.done()
            ]
            for task_id in completed_task_ids:
                del self.running_tasks[task_id]
            
            # Check if we can take on more tasks
            available_slots = self.max_concurrent_tasks - len(self.running_tasks)
            if available_slots <= 0:
                logger.debug(f"Worker at capacity: {len(self.running_tasks)}/{self.max_concurrent_tasks} tasks running")
                return
            
            # Get pending tasks
            query_start = time.time()
            pending_tasks = db.query(AgentTask).filter(
                AgentTask.status == TaskStatus.PENDING.value
            ).order_by(AgentTask.created_at.asc()).limit(available_slots).all()
            query_time = time.time() - query_start
            
            # Log polling activity with query performance
            if pending_tasks:
                logger.info(f"Polling: Found {len(pending_tasks)} pending task(s), {len(self.running_tasks)} currently running (query: {query_time:.3f}s)")
                for task in pending_tasks:
                    # Both datetimes must be naive for subtraction
                    task_created = task.created_at.replace(tzinfo=None) if task.created_at.tzinfo else task.created_at
                    current_time = now_sgt()  # This returns naive datetime
                    age = (current_time - task_created).total_seconds()
                    logger.info(f"  - Task {task.id} created {age:.1f}s ago, status={task.status}")
            else:
                logger.debug(f"Polling: No pending tasks, {len(self.running_tasks)} currently running (query: {query_time:.3f}s)")
            
            # Start processing each pending task
            for task in pending_tasks:
                if task.id not in self.running_tasks:
                    logger.info(f"Starting task {task.id}: {task.title}")
                    
                    # Create async task to process this agent task
                    async_task = asyncio.create_task(
                        self._execute_task(task.id, task.task_type, task.payload or {})
                    )
                    self.running_tasks[task.id] = async_task
        
        except Exception as e:
            logger.error(f"Error processing pending tasks: {e}", exc_info=True)
        finally:
            db.close()
    
    async def _execute_task(self, task_id: int, task_type: str, payload: Dict[str, Any]):
        """
        Execute a single task.
        
        Args:
            task_id: ID of the agent task
            task_type: Type of task to execute
            payload: Task parameters
        """
        db = SessionLocal()
        try:
            # Update task status to running
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            task.status = TaskStatus.RUNNING.value
            task.started_at = now_sgt()
            task.updated_at = now_sgt()
            db.commit()
            
            logger.info(f"Executing task {task_id} (type: {task_type})")
            
            # Get the appropriate handler
            handler = self.task_handlers.get(task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task_type}")
            
            # Execute the handler
            result = await handler(task_id, payload, db)
            
            # Update task based on result status
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            
            # Check if handler returned an error status
            result_status = result.get("status", "success") if isinstance(result, dict) else "success"
            
            if result_status == "error":
                # Handler returned error - mark as FAILED
                task.status = TaskStatus.FAILED.value
                task.error_message = result.get("message", "Task failed")
                logger.error(f"Task {task_id} failed: {task.error_message}")
            else:
                # Handler succeeded or partially succeeded
                task.status = TaskStatus.COMPLETED.value
                logger.info(f"Task {task_id} completed successfully")
            
            task.progress = 100
            task.result = result
            task.completed_at = now_sgt()
            task.updated_at = now_sgt()
            db.commit()
            
            # Broadcast task completion to SSE clients
            await self._broadcast_task_completion(task)
        
        except asyncio.CancelledError:
            # Task was cancelled
            logger.warning(f"Task {task_id} was cancelled")
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.status = TaskStatus.CANCELLED.value
                task.completed_at = now_sgt()
                task.updated_at = now_sgt()
                db.commit()
            raise
        
        except Exception as e:
            # Task failed
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = now_sgt()
                task.updated_at = now_sgt()
                db.commit()
                
                # Broadcast task failure to SSE clients
                await self._broadcast_task_completion(task)
        
        finally:
            db.close()
    
    async def _broadcast_task_completion(self, task: AgentTask):
        """
        Broadcast task completion/failure to SSE clients and add result to conversation.
        
        Args:
            task: Completed or failed AgentTask instance
        """
        try:
            from api.src.routers.task_stream import broadcast_task_update
            
            task_update = {
                "task_id": task.id,
                "task_type": task.task_type,
                "status": task.status,
                "result": task.result,
                "error_message": task.error_message,
                "progress": task.progress,
                "created_by": task.created_by
            }
            
            await broadcast_task_update(task_update)
            logger.info(f"Broadcasted task {task.id} completion to SSE clients")
            
            # Add task result to conversation if session_id is available
            if task.payload and isinstance(task.payload, dict) and "session_id" in task.payload:
                await self._add_result_to_conversation(task)
            
        except Exception as e:
            logger.error(f"Failed to broadcast task {task.id} to SSE: {e}")
    
    async def _add_result_to_conversation(self, task: AgentTask):
        """
        Add task result to the conversation history.
        
        Args:
            task: Completed AgentTask instance with session_id in payload
        """
        from api.src.database import SessionLocal
        db = None
        try:
            from api.src.services.conversation_manager import ConversationManager
            import json
            
            session_id = task.payload.get("session_id")
            if not session_id:
                logger.warning(f"Task {task.id} has no session_id in payload, skipping conversation update")
                return
            
            user_id = task.payload.get("current_user_id")
            if not user_id:
                logger.warning(f"Task {task.id} has no current_user_id in payload, skipping conversation update")
                return
            
            # Format result message based on task status
            if task.status == "completed":
                # Format successful result
                result_message = self._format_task_result(task)
            else:
                # Format error message
                result_message = f"Task failed: {task.error_message or 'Unknown error'}"
            
            # Create new DB session for conversation update
            db = SessionLocal()
            
            # Add assistant message to conversation
            conv_manager = ConversationManager(db=db, user_id=user_id)
            conv_manager.add_message(
                session_id=session_id,
                role="assistant",
                content=result_message
            )
            
            logger.info(f"Added task {task.id} result to conversation {session_id}")
            
        except Exception as e:
            logger.error(f"Failed to add task {task.id} result to conversation: {e}", exc_info=True)
        finally:
            if db:
                db.close()
    
    def _format_task_result(self, task: AgentTask) -> str:
        """Format task result as human-readable message."""
        import json
        
        result = task.result
        if not result:
            return f"Task completed with no result."
        
        # Extract message if available
        if isinstance(result, dict):
            if "message" in result:
                return result["message"]
            
            # Format analysis results
            if "analysis" in result:
                analysis = result["analysis"]
                if isinstance(analysis, dict):
                    score = analysis.get("overall_score", 0)
                    passed = analysis.get("passed", False)
                    status_emoji = "✅" if passed else "❌"
                    
                    msg = f"{status_emoji} Evidence Analysis Complete\\n\\n"
                    msg += f"**Overall Score:** {score}%\\n"
                    msg += f"**Status:** {'Passed' if passed else 'Failed'}\\n\\n"
                    
                    if "validation_results" in analysis:
                        msg += "**Validation Results:**\\n"
                        for val in analysis["validation_results"]:
                            criterion = val.get("criterion", "Unknown")
                            passed_check = val.get("passed", False)
                            check_emoji = "✅" if passed_check else "❌"
                            msg += f"{check_emoji} {criterion}\\n"
                    
                    if "recommendations" in analysis and analysis["recommendations"]:
                        msg += "\\n**Recommendations:**\\n"
                        for rec in analysis["recommendations"]:
                            msg += f"• {rec}\\n"
                    
                    return msg
            
            # Fallback to JSON string
            return json.dumps(result, indent=2)
        
        return str(result)
    
    async def update_task_progress(self, task_id: int, progress: int, message: Optional[str] = None):
        """
        Update the progress of a running task.
        
        Args:
            task_id: ID of the task
            progress: Progress percentage (0-100)
            message: Optional status message
        """
        db = SessionLocal()
        try:
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.progress = max(0, min(100, progress))
                task.updated_at = now_sgt()
                if message and task.result:
                    # Add progress message to result
                    if isinstance(task.result, dict):
                        task.result["progress_message"] = message
                db.commit()
                logger.debug(f"Task {task_id} progress: {progress}%")
        except Exception as e:
            logger.error(f"Error updating task progress: {e}")
        finally:
            db.close()


# Global worker instance
_worker_instance: Optional[TaskWorker] = None


def get_worker() -> TaskWorker:
    """Get the global worker instance"""
    global _worker_instance
    if _worker_instance is None:
        _worker_instance = TaskWorker()
    return _worker_instance


async def update_progress(task_id: int, progress: int, message: Optional[str] = None):
    """
    Convenience function to update task progress from within handlers.
    
    Args:
        task_id: ID of the task
        progress: Progress percentage (0-100)
        message: Optional status message
    """
    worker = get_worker()
    await worker.update_task_progress(task_id, progress, message)
