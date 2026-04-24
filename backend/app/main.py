from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio

from app.core.database import engine, Base
from app.routers import auth, topics, units, exercises, students, teachers, leaderboard, classes_router, assignments, lessons, notifications, parents, classroom, content_import


async def _startup_db():
    """Connect to DB and run all setup + migrations in background with retries."""
    for attempt in range(10):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            print("DB connected and tables ready.")
            break
        except Exception as e:
            print(f"DB startup attempt {attempt + 1}/10 failed: {e}")
            await asyncio.sleep(3)
    await run_migrations()


async def run_migrations():
    """Run DB migrations in the background so startup doesn't block the healthcheck."""

    # Migration: add assignment_id to exercise_attempts if not exists
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'exercise_attempts' AND column_name = 'assignment_id'
            """))
            if not result.fetchone():
                await conn.execute(text("""
                    ALTER TABLE exercise_attempts
                    ADD COLUMN assignment_id INTEGER REFERENCES assignments(id)
                """))
                print("Migration: added assignment_id to exercise_attempts")
    except Exception as e:
        print(f"Migration check skipped: {e}")

    # Migration: rename notifications.student_id to user_id if student_id exists
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'notifications' AND column_name = 'student_id'
            """))
            if result.fetchone():
                has_user = await conn.execute(text("""
                    SELECT column_name FROM information_schema.columns
                    WHERE table_name = 'notifications' AND column_name = 'user_id'
                """))
                if not has_user.fetchone():
                    await conn.execute(text("""
                        ALTER TABLE notifications ADD COLUMN user_id INTEGER REFERENCES users(id)
                    """))
                await conn.execute(text("""
                    UPDATE notifications
                    SET user_id = subq.user_id
                    FROM (SELECT students.id as student_id, students.user_id as user_id FROM students) AS subq
                    WHERE notifications.student_id = subq.student_id
                """))
                await conn.execute(text("ALTER TABLE notifications DROP COLUMN student_id"))
                print("Migration: renamed notifications.student_id to user_id")
    except Exception as e:
        print(f"Migration notifications rename skipped: {e}")

    # Migration: add 'parent' to userrole enum if not exists
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT enumlabel FROM pg_enum WHERE enumtypid = 'userrole'::regtype AND enumlabel = 'parent'
            """))
            if not result.fetchone():
                await conn.execute(text("ALTER TYPE userrole ADD VALUE 'parent'"))
                print("Migration: added 'parent' to userrole enum")
    except Exception as e:
        print(f"Migration userrole enum skipped: {e}")

    # Migration: fix parent_student_links.student_id - change 0 to NULL and allow NULL
    try:
        async with engine.begin() as conn:
            await conn.execute(text("UPDATE parent_student_links SET student_id = NULL WHERE student_id = 0"))
            await conn.execute(text("ALTER TABLE parent_student_links ALTER COLUMN student_id DROP NOT NULL"))
            print("Migration: fixed parent_student_links.student_id (0->NULL, drop NOT NULL)")
    except Exception as e:
        print(f"Migration parent_student_links skipped: {e}")

    # Migration: update lesson content with visual blocks
    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                UPDATE lessons SET content = :content
                WHERE title = 'Introducción a la Suma'
            """), {"content": """# 🎯 La Suma (Adición)

La **suma** es juntar dos o más cantidades. Piensa en ello como **agregar** cosas.

## Modelo visual: Bloques de Base-10

:::visual:base10,35,17:::

## ¿Cómo sumamos?

**Ejemplo:** 35 + 17 = ?

### Paso a paso animado:
:::steps:Sumamos las unidades: 5 + 7 = 12|12:::Escribimos 2, llevamos 1 a las decenas|+1 a decenas:::Sumamos las decenas (más lo que llevamos): 3 + 1 + 1 = 5|resultado=5:::

## Modelo en la recta numérica:
:::visual:numberline,0,35,add:::

:::tryit:¿Cuánto es 35 + 17?|52|35 + 17 = 52|35 + 17 = 52. ¡Sumamos las unidades y llevamos 1!:::

## Un truco útil 💡
Si sumas un número con 0, el resultado es el mismo número.
> 45 + 0 = 45

## Practica:
:::tryit:¿Cuánto es 12 + 5?|17|12 + 5 = 17|¡Muy bien!:::

En los ejercicios siguientes, usa lo que aprendiste para resolver cada suma."""})
            print("Migration: updated lesson content (suma)")
    except Exception as e:
        print(f"Migration lesson content (suma) skipped: {e}")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                UPDATE lessons SET content = :content
                WHERE title = 'Introducción a la Resta'
            """), {"content": """# ➖ La Resta (Sustracción)

La **resta** es **quitar** una cantidad de otra. Piensa en ello como **restar** o **comparar**.

## Modelo visual: Recta numérica
:::visual:numberline,48,23,subtract:::

## ¿Cómo restamos?

**Ejemplo:** 48 - 23 = ?

### Paso a paso:
:::steps:Restamos las unidades: 8 - 3 = 5|resultado=5:::Restamos las decenas: 4 - 2 = 2|resultado=2::::

## ¿Y cuando necesitamos "pedir prestado"?

**Ejemplo:** 52 - 27

:::visual:numberline,52,27,subtract:::

:::tryit:¿Cuánto es 52 - 27?|25|52 - 27 = 25|52 - 27 = 25. ¡Primero restamos las unidades!:::

> 2 no puede restar 7, entonces pedimos 1 decena (que se convierte en 10 unidades): 12 - 7 = 5
> Luego 4 (que ahora es 3, porque dimos 1) - 2 = 1 → Resultado: **25**

## Practica con los ejercicios."""})
            print("Migration: updated lesson content (resta)")
    except Exception as e:
        print(f"Migration lesson content (resta) skipped: {e}")

    try:
        async with engine.begin() as conn:
            await conn.execute(text("""
                UPDATE lessons SET content = :content
                WHERE title = '¿Qué es la Multiplicación?'
            """), {"content": """# ✖️ La Multiplicación

La **multiplicación** es una forma rápida de hacer **sumas repetidas**.

## Modelo visual: Arreglos (grids)
:::visual:array,3,4:::

## ¿Qué significa 7 × 3?

Significa **sumar 7 tres veces**: 7 + 7 + 7 = 21

O también **sumar 3 siete veces**: 3 + 3 + 3 + 3 + 3 + 3 + 3 = 21

:::tryit:Si tienes 4 filas de 5 bolas, ¿cuántas bolas tienes en total?|20|4 × 5 = 20|4 filas × 5 bolas = 20 bolas!:::

## Las tablas de multiplicar

Memorizar las tablas te hará más rápido. Aquí va la tabla del 2:

| × | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|
| **2** | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 20 |

## Truco para la tabla del 9 🧙‍♂️
El resultado siempre suma 9:
> 9 × 1 = 9 → 0 + 9 = 9
> 9 × 2 = 18 → 1 + 8 = 9
> 9 × 3 = 27 → 2 + 7 = 9
> etc.

:::tryit:¿Cuánto es 6 × 8?|48|6 × 8 = 48|6 × 8 = 48. ¡60 - 12 = 48!:::

## Practica con las tablas del 2 al 5."""})
            print("Migration: updated lesson content (multiplicación)")
    except Exception as e:
        print(f"Migration lesson content (multiplicación) skipped: {e}")

    # Migration: add content_type to lessons if not exists
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = 'lessons' AND column_name = 'content_type'
            """))
            if not result.fetchone():
                await conn.execute(text("""
                    ALTER TABLE lessons ADD COLUMN content_type VARCHAR(20) DEFAULT 'text' NOT NULL
                """))
                print("Migration: added content_type to lessons")
    except Exception as e:
        print(f"Migration lessons.content_type skipped: {e}")

    # Migration: assign lesson_id to exercises that have unit_id but lesson_id=NULL
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text(
                "SELECT COUNT(*) FROM exercises WHERE lesson_id IS NULL AND unit_id IS NOT NULL"
            ))
            count = result.scalar()
            if count:
                await conn.execute(text("""
                    UPDATE exercises e
                    SET lesson_id = (
                        SELECT l.id FROM lessons l
                        WHERE l.unit_id = e.unit_id
                        ORDER BY l.order_index, l.id
                        LIMIT 1
                    )
                    WHERE e.lesson_id IS NULL AND e.unit_id IS NOT NULL
                """))
                print(f"Migration: assigned lesson_id to {count} exercises that had unit_id but lesson_id=NULL")
    except Exception as e:
        print(f"Migration exercises lesson_id skipped: {e}")

    print("Background migrations complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # All DB work runs in background — app is ready for healthcheck immediately
    asyncio.create_task(_startup_db())
    yield
    await engine.dispose()


app = FastAPI(
    title="Math Platform API",
    description="Khan Academy-style learning platform — Bolivian curriculum",
    version="1.0.2",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(topics.router, prefix="/api/topics", tags=["topics"])
app.include_router(units.router, prefix="/api/units", tags=["units"])
app.include_router(exercises.router, prefix="/api/exercises", tags=["exercises"])
app.include_router(students.router, prefix="/api/me", tags=["students"])
app.include_router(teachers.router, prefix="/api", tags=["teachers"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(classes_router.router, prefix="/api/classes", tags=["classes"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["assignments"])
app.include_router(lessons.router, prefix="/api/lessons", tags=["lessons"])
app.include_router(notifications.router, prefix="/api/me/notifications", tags=["notifications"])
app.include_router(parents.router, prefix="/api/parents", tags=["parents"])
app.include_router(classroom.router, tags=["classroom"])
app.include_router(content_import.router)

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "version": "1.0.2"}

@app.get("/health")
async def root_health():
    return {"status": "healthy"}

@app.get("/debug/db")
async def debug_db():
    import os
    from app.core.config import settings
    from sqlalchemy import text as sa_text
    db_url_masked = settings.DATABASE_URL[:40] + "***" if settings.DATABASE_URL else "NOT SET"
    # Show all DB-related env vars available
    db_env_vars = {k: v[:20] + "..." for k, v in os.environ.items()
                   if any(x in k.upper() for x in ["DATABASE", "POSTGRES", "PG", "DB_"])}
    try:
        async with engine.begin() as conn:
            result = await conn.execute(sa_text("SELECT COUNT(*) FROM users"))
            user_count = result.scalar()
        return {"db": "ok", "users": user_count, "url_prefix": db_url_masked, "env_keys": db_env_vars}
    except Exception as e:
        return {"db": "error", "error": str(e), "url_prefix": db_url_masked, "env_keys": db_env_vars}
