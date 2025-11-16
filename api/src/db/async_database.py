"""
Async PostgreSQL database manager for NOTIFY/LISTEN and async operations.
"""
import asyncpg
import logging
from typing import Optional
from api.src.config import settings

logger = logging.getLogger(__name__)


class AsyncDatabaseManager:
    """Manages async PostgreSQL connections for NOTIFY/LISTEN"""
    
    def __init__(self, database_url: str):
        self.pool: Optional[asyncpg.Pool] = None
        self.database_url = database_url
        self.notify_connection: Optional[asyncpg.Connection] = None
    
    async def connect(self):
        """Initialize connection pool"""
        try:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=2,
                max_size=10,
                command_timeout=60,
                max_inactive_connection_lifetime=300
            )
            logger.info("Async database pool created")
        except Exception as e:
            logger.error(f"Failed to create async database pool: {e}")
            raise
    
    async def disconnect(self):
        """Close all connections"""
        try:
            if self.notify_connection:
                await self.notify_connection.close()
                self.notify_connection = None
                logger.info("NOTIFY connection closed")
            
            if self.pool:
                await self.pool.close()
                self.pool = None
                logger.info("Async database pool closed")
        except Exception as e:
            logger.error(f"Error during disconnect: {e}")
    
    async def get_listen_connection(self) -> asyncpg.Connection:
        """Get or create dedicated connection for LISTEN"""
        if not self.notify_connection or self.notify_connection.is_closed():
            self.notify_connection = await asyncpg.connect(self.database_url)
            logger.info("Created new NOTIFY connection")
        return self.notify_connection
    
    async def execute(self, query: str, *args):
        """Execute a query using the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)
    
    async def fetch(self, query: str, *args):
        """Fetch results using the pool"""
        if not self.pool:
            raise RuntimeError("Database pool not initialized")
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)


# Global instance
async_db = AsyncDatabaseManager(settings.DATABASE_URL)
