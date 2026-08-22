import asyncio
from app.db.connection import get_db

async def check():
    db = await get_db()
    res = await db.fetch("SELECT * FROM emergency_events ORDER BY triggered_at DESC LIMIT 1;")
    print(res)

asyncio.run(check())
