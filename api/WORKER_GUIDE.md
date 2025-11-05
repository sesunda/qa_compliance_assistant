# Background Task Worker Guide

## Overview

The QCA Compliance Assistant uses an asyncio-based background task worker to process long-running agent tasks without blocking API requests. Tasks are stored in the database and executed asynchronously with progress tracking.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   API Request   │────▶│  Create Task     │────▶│   Database      │
│  (User/Agent)   │     │  (Status: pending)│     │  (agent_tasks)  │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                                           │
                                                           ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Task Result   │◀────│  Update Status   │◀────│  Task Worker    │
│   (JSONB)       │     │  (Running/Done)  │     │  (Polling Loop) │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

## Components

### 1. TaskWorker (`api/src/workers/task_worker.py`)

Core worker class that:
- Polls database every 5 seconds for pending tasks
- Executes up to 3 tasks concurrently
- Updates task status and progress
- Handles errors and cancellation
- Starts on FastAPI startup, stops on shutdown

**Key Methods:**
```python
worker = get_worker()
worker.register_handler("task_type", handler_function)
await worker.start()  # Runs continuously
await worker.stop()   # Graceful shutdown
```

### 2. Task Handlers (`api/src/workers/task_handlers.py`)

Handler functions for different task types:

```python
async def handle_test_task(task_id: int, payload: Dict, db: Session) -> Dict:
    """
    Handler function signature:
    - task_id: Database ID of the task
    - payload: Task parameters (from JSONB)
    - db: SQLAlchemy session
    - Returns: Result data (stored as JSONB)
    """
    # Update progress
    await update_progress(task_id, 50, "Half way done")
    
    # Do work...
    
    return {"status": "success", "data": "..."}
```

**Built-in Handlers:**
- `test` - Demo handler with progress tracking
- `fetch_evidence` - Auto-fetch evidence (placeholder)
- `generate_report` - Auto-generate reports (placeholder)
- `analyze_compliance` - Compliance analysis (placeholder)

### 3. Integration (`api/src/main.py`)

Worker lifecycle managed via FastAPI lifespan:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start worker
    worker = get_worker()
    for task_type, handler in TASK_HANDLERS.items():
        worker.register_handler(task_type, handler)
    worker_task = asyncio.create_task(worker.start())
    
    yield
    
    # Shutdown: Stop worker gracefully
    await worker.stop()
    worker_task.cancel()
```

## Task Lifecycle

1. **Created** (`POST /agent-tasks/`)
   - Status: `pending`
   - Progress: 0
   - Stored in database

2. **Picked Up** (Worker polls every 5s)
   - Status: `running`
   - `started_at` timestamp set
   - Handler function called

3. **Executing** (Handler running)
   - Progress: 0-100 (updated via `update_progress()`)
   - Result: Building incrementally

4. **Completed** (Handler returns)
   - Status: `completed` (or `failed`)
   - Progress: 100
   - `completed_at` timestamp set
   - Result stored in JSONB field

## Usage Examples

### Create a Task

```bash
curl -X POST http://localhost:8000/agent-tasks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "test",
    "title": "My Test Task",
    "description": "Testing the worker",
    "payload": {"steps": 5}
  }'
```

### Monitor Progress

```bash
# Get task details
curl http://localhost:8000/agent-tasks/2 \
  -H "Authorization: Bearer $TOKEN"

# Check stats
curl http://localhost:8000/agent-tasks/stats \
  -H "Authorization: Bearer $TOKEN"
```

### Watch Worker Logs

```bash
docker logs -f qca_api | grep -E "worker|Task"
```

## Adding New Task Types

1. **Create Handler Function** (`task_handlers.py`)

```python
async def handle_my_custom_task(task_id: int, payload: Dict, db: Session) -> Dict:
    """Custom task handler"""
    # Extract parameters
    param1 = payload.get("param1")
    
    # Update progress
    await update_progress(task_id, 25, "Step 1 complete")
    
    # Do work...
    result = do_something(param1)
    
    await update_progress(task_id, 100, "Finished")
    
    return {"result": result, "status": "success"}
```

2. **Register in TASK_HANDLERS** (`task_handlers.py`)

```python
TASK_HANDLERS = {
    "test": handle_test_task,
    "my_custom": handle_my_custom_task,  # Add here
    # ...
}
```

3. **Add to TaskType Enum** (Optional, `agent_schemas.py`)

```python
class TaskType(str, Enum):
    MY_CUSTOM = "my_custom"
```

4. **Restart API**

```bash
docker restart qca_api
```

## Configuration

Worker settings in `TaskWorker.__init__()`:

```python
TaskWorker(
    poll_interval=5,        # Seconds between polls
    max_concurrent_tasks=3  # Max parallel tasks
)
```

## Error Handling

- **Handler Exception**: Task marked as `failed`, error stored in `error_message`
- **Task Cancellation**: Status set to `cancelled` (via `PUT /agent-tasks/{id}/cancel`)
- **Worker Crash**: Tasks remain in `running` state (manual recovery needed)

## Best Practices

1. **Use Progress Updates**: Keep users informed
   ```python
   await update_progress(task_id, percent, "Status message")
   ```

2. **Handle Cancellation**: Check task status periodically for long operations
   ```python
   task = db.query(AgentTask).filter(AgentTask.id == task_id).first()
   if task.status == TaskStatus.CANCELLED.value:
       return {"cancelled": True}
   ```

3. **Store Detailed Results**: Use JSONB for structured output
   ```python
   return {
       "status": "success",
       "items_processed": 42,
       "errors": [],
       "metadata": {...}
   }
   ```

4. **Database Sessions**: Always use the provided `db` session, don't create new ones

5. **Logging**: Use the logger for debugging
   ```python
   logger.info(f"Processing task {task_id}")
   logger.error(f"Error: {e}", exc_info=True)
   ```

## Testing

### Unit Test Handler
```python
import asyncio
from api.src.workers.task_handlers import handle_test_task

async def test():
    result = await handle_test_task(
        task_id=999,
        payload={"steps": 3},
        db=mock_session
    )
    assert result["status"] == "success"

asyncio.run(test())
```

### Integration Test
```bash
# Create task
TASK_ID=$(curl -s -X POST http://localhost:8000/agent-tasks/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"task_type":"test","title":"Test"}' | jq -r '.id')

# Wait for completion
sleep 10

# Verify
curl http://localhost:8000/agent-tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.status'
# Should return: "completed"
```

## Troubleshooting

### Worker Not Starting
```bash
# Check logs
docker logs qca_api | grep "worker"

# Should see:
# "Starting background task worker..."
# "Registered handler for task type: ..."
# "Task worker started"
```

### Tasks Stuck in Pending
```bash
# Check worker is running
docker logs qca_api --tail 20 | grep "worker"

# Check database connection
docker exec qca_api python3 -c "from api.src.database import SessionLocal; db=SessionLocal(); print('OK')"
```

### Tasks Failing
```bash
# Check task error message
curl http://localhost:8000/agent-tasks/$TASK_ID \
  -H "Authorization: Bearer $TOKEN" | jq '.error_message'

# Check worker logs
docker logs qca_api | grep "Task.*failed"
```

## Performance

- **Throughput**: Up to 3 tasks concurrently
- **Latency**: Tasks picked up within 5 seconds
- **Scalability**: Can adjust `max_concurrent_tasks` and `poll_interval`

For higher throughput, consider:
- Increasing `max_concurrent_tasks`
- Decreasing `poll_interval` (increases DB load)
- Running multiple worker instances (requires distributed locking)

## Future Enhancements

- [ ] Distributed task queue (Redis/RabbitMQ)
- [ ] Task priority levels
- [ ] Retry logic for failed tasks
- [ ] Task scheduling (cron-like)
- [ ] WebSocket notifications for real-time updates
- [ ] Task dependencies (DAG execution)
