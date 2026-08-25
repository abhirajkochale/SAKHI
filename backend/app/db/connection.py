import asyncpg
from typing import Optional
from urllib.parse import unquote, urlsplit
from app.core.config import settings


def parse_postgres_url(database_url: Optional[str]) -> dict:
    """Parse a PostgreSQL URL without mistaking special password characters for host data."""
    if not database_url:
        raise RuntimeError("DATABASE_URL is not configured")
    if "://" not in database_url or "@" not in database_url:
        raise RuntimeError("DATABASE_URL must be a PostgreSQL connection URL")

    _, remainder = database_url.split("://", 1)
    credentials, address = remainder.rsplit("@", 1)
    if ":" not in credentials:
        raise RuntimeError("DATABASE_URL must include a username and password")
    username, password = credentials.split(":", 1)
    parsed = urlsplit(f"//{address}")
    if not parsed.hostname:
        raise RuntimeError("DATABASE_URL must include a database host")

    try:
        port = parsed.port or 5432
    except ValueError as exc:
        raise RuntimeError("DATABASE_URL has an invalid database port") from exc

    return {
        "user": unquote(username),
        "password": unquote(password),
        "host": parsed.hostname,
        "port": port,
        "database": parsed.path.lstrip("/"),
    }

class Database:
    def __init__(self):
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        if not self.pool:
            if not settings.DATABASE_URL or "sqlite" in settings.DATABASE_URL:
                print("[DB] asyncpg disabled: DATABASE_URL is set to SQLite")
                return
                
            # If postgresql format like postgresql+asyncpg:// or postgresql://
            url = settings.DATABASE_URL
            if url.startswith("postgresql+"):
                url = url.replace("postgresql+", "", 1)
                
            config = parse_postgres_url(url)
            self.pool = await asyncpg.create_pool(
                **config,
                min_size=1,
                max_size=10,
                command_timeout=60
            )

    async def disconnect(self):
        if self.pool:
            await self.pool.close()
            self.pool = None

    async def fetch(self, query: str, *args):
        if not self.pool:
            return []
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        if not self.pool:
            return None
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        if not self.pool:
            return None
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

# Global database instance
db = Database()

async def get_db() -> Database:
    if not db.pool:
        await db.connect()
    return db
