import asyncio
from sqlalchemy import text
from app.core.database import engine

async def enroll():
    """Enroll student 46 in the teacher's class so thinking_process test can work."""
    async with engine.begin() as conn:
        # Get teacher's class
        r = await conn.execute(text("""
            SELECT c.id FROM classes c
            JOIN teachers t ON t.id = c.teacher_id
            JOIN users u ON u.id = t.user_id
            WHERE u.email = 'profesor@test.com'
        """))
        row = r.fetchone()
        if not row:
            print("No class found for teacher")
            return
        class_id = row[0]
        print(f"Teacher class_id: {class_id}")

        # Enroll student 46 in that class
        try:
            await conn.execute(text("""
                INSERT INTO class_enrollments (class_id, student_id, enrolled_at)
                VALUES (:class_id, :student_id, NOW())
                ON CONFLICT DO NOTHING
            """), {"class_id": class_id, "student_id": 46})
            print(f"Enrolled student 46 in class {class_id}")
        except Exception as e:
            print(f"Enroll error: {e}")

asyncio.run(enroll())
