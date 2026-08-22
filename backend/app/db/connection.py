import asyncpg
from typing import Optional
from urllib.parse import unquote, urlsplit
from app.core.config import settings


def parse_postgres_url(database_url: Optional[str]) -> dict:
    """Parse a PostgreSQL URL without mistaking special password characters for host data."""
    if not database_url:
        raise RuntimeError("SUPABASE_DB_URL is not configured")
    if "://" not in database_url or "@" not in database_url:
        raise RuntimeError("SUPABASE_DB_URL must be a PostgreSQL connection URL")

    _, remainder = database_url.split("://", 1)
    credentials, address = remainder.rsplit("@", 1)
    if ":" not in credentials:
        raise RuntimeError("SUPABASE_DB_URL must include a username and password")
    username, password = credentials.split(":", 1)
    parsed = urlsplit(f"//{address}")
    if not parsed.hostname:
        raise RuntimeError("SUPABASE_DB_URL must include a database host")

    try:
        port = parsed.port or 5432
    except ValueError as exc:
        raise RuntimeError("SUPABASE_DB_URL has an invalid database port") from exc

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
            config = parse_postgres_url(settings.SUPABASE_DB_URL)
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
        async with self.pool.acquire() as connection:
            return await connection.fetch(query, *args)

    async def fetchrow(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.fetchrow(query, *args)

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as connection:
            return await connection.execute(query, *args)

# Global database instance
db = Database()

async def get_db() -> Database:
    if not db.pool:
        await db.connect()
    return db
