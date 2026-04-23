import asyncio
from app.core.database import engine
from sqlalchemy import text

async def migrate():
    async with engine.begin() as conn:
        # Add helped_peer_id column to exercise_attempts
        result = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'exercise_attempts' AND column_name = 'helped_peer_id'
        """))
        if result.fetchone():
            print('helped_peer_id already exists')
        else:
            await conn.execute(text("""
                ALTER TABLE exercise_attempts
                ADD COLUMN helped_peer_id INTEGER REFERENCES students(id)
            """))
            print('Added helped_peer_id column')

        # Verify
        result2 = await conn.execute(text("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'exercise_attempts' AND column_name = 'helped_peer_id'
        """))
        print(f'helped_peer_id verified: {result2.fetchone() is not None}')

asyncio.run(migrate())
