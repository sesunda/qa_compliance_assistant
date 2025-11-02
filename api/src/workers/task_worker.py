"""
Background task worker for processing agent tasks asynchronously.

This worker polls the database for pending tasks and executes them in the background
without blocking API requests.
"""
import asyncio
import logging
from datetime import datetime
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
        
        try:
            while self.is_running:
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
        
        # Wait for running tasks to complete
        if self.running_tasks:
            logger.info(f"Waiting for {len(self.running_tasks)} tasks to complete...")
            await asyncio.gather(*self.running_tasks.values(), return_exceptions=True)
        
        logger.info("All tasks completed")
    
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
                return
            
            # Get pending tasks
            pending_tasks = db.query(AgentTask).filter(
                AgentTask.status == TaskStatus.PENDING.value
            ).order_by(AgentTask.created_at.asc()).limit(available_slots).all()
            
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
            task.started_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Executing task {task_id} (type: {task_type})")
            
            # Get the appropriate handler
            handler = self.task_handlers.get(task_type)
            if not handler:
                raise ValueError(f"No handler registered for task type: {task_type}")
            
            # Execute the handler
            result = await handler(task_id, payload, db)
            
            # Update task with success
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            task.status = TaskStatus.COMPLETED.value
            task.progress = 100
            task.result = result
            task.completed_at = datetime.utcnow()
            task.updated_at = datetime.utcnow()
            db.commit()
            
            logger.info(f"Task {task_id} completed successfully")
        
        except asyncio.CancelledError:
            # Task was cancelled
            logger.warning(f"Task {task_id} was cancelled")
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.status = TaskStatus.CANCELLED.value
                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                db.commit()
            raise
        
        except Exception as e:
            # Task failed
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
            if task:
                task.status = TaskStatus.FAILED.value
                task.error_message = str(e)
                task.completed_at = datetime.utcnow()
                task.updated_at = datetime.utcnow()
                db.commit()
        
        finally:
            db.close()
    
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
                task.updated_at = datetime.utcnow()
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
