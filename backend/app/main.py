from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from sqlalchemy import text
import asyncio
import os

from app.core.database import engine, Base
from app.core.config import settings
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

_frontend = os.environ.get("RAILWAY_ENVIRONMENT") \
    and settings.RAILWAY_FRONTEND_URL \
    or settings.FRONTEND_URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend],
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

@app.get("/debug/login-test")
async def debug_login():
    from sqlalchemy import text as sa_text
    results = {}
    try:
        async with engine.begin() as conn:
            for table in ["users", "sessions", "students", "teachers"]:
                try:
                    r = await conn.execute(sa_text(f"SELECT COUNT(*) FROM {table}"))
                    results[table] = r.scalar()
                except Exception as e:
                    results[table] = f"ERROR: {str(e)[:60]}"
    except Exception as e:
        return {"connection": f"FAILED: {str(e)[:100]}"}
    return {"connection": "ok", "tables": results}

@app.get("/health")
async def root_health():
    return {"status": "healthy"}

@app.post("/api/admin/cleanup-content")
async def cleanup_content_endpoint():
    """Fix content issues across all exercises and lessons."""
    from sqlalchemy import text as sa_text

    # Map of (search_pattern, replacement) for content cleanup
    replacements = [
        ("combienas veces", "cuántas veces"),
        ("combien", "cuánto"),
        ("voiture", "auto"),
        (" wheels ", " ruedas "),
        ("La wheels", "Las ruedas"),
        ("ver instantly", "ver inmediatamente"),
        (" instantly ", " inmediatamente "),
        ("UnTV cuesta", "Un TV cuesta"),
        ("##group=10+ones", "## Un grupo de 10 más unidades"),
        ("teachers:students", "profesores:estudiantes"),
        ("5 teachers", "5 profesores"),
        ("100 students", "100 estudiantes"),
        ("la razón de teachers", "la razón de profesores"),
        ("razón niñas:nños", "razón niñas:niños"),
        # Bad comparison visual usage that produced "+-60" badge
        (":::visual:comparison,120,60,Distancia (km),Velocidad (km/h):::\n\n", ""),
        (":::visual:comparison,1,1000000,1,Millon:::\n\n", ""),
        (":::visual:comparison,3,5,Círculo,Figura:::\n\n", ""),
        (":::visual:comparison,8,3,Largo,Ancho:::\n\n", ""),
        (":::visual:comparison,7,3,Lápiz,Crayón:::", ":::visual:comparison,3,7,Crayón (3cm),Lápiz (7cm):::"),
        (":::visual:comparison,3,2,Azules,Rojos:::", ":::visual:comparison,2,3,Rojas (2),Azules (3):::"),
    ]

    results = {"exercises_updated": 0, "lessons_updated": 0, "explanations_filled": 0, "details": []}

    # Process each replacement in its own transaction so partial failure doesn't kill all
    for search, replace in replacements:
        try:
            async with engine.begin() as conn:
                # Fix exercise data (JSON column)
                r = await conn.execute(sa_text(
                    "UPDATE exercises SET data = REPLACE(data::text, :s, :r)::json WHERE data::text LIKE :p"
                ), {"s": search, "r": replace, "p": f"%{search}%"})
                if r.rowcount > 0:
                    results["details"].append(f"exercises.data '{search[:40]}': {r.rowcount}")
                    results["exercises_updated"] += r.rowcount

                # Fix hints (JSON array column)
                r2 = await conn.execute(sa_text(
                    "UPDATE exercises SET hints = REPLACE(hints::text, :s, :r)::json WHERE hints IS NOT NULL AND hints::text LIKE :p"
                ), {"s": search, "r": replace, "p": f"%{search}%"})
                if r2.rowcount > 0:
                    results["details"].append(f"exercises.hints '{search[:40]}': {r2.rowcount}")
                    results["exercises_updated"] += r2.rowcount

                # Fix lesson content (TEXT)
                r3 = await conn.execute(sa_text(
                    "UPDATE lessons SET content = REPLACE(content, :s, :r) WHERE content LIKE :p"
                ), {"s": search, "r": replace, "p": f"%{search}%"})
                if r3.rowcount > 0:
                    results["details"].append(f"lessons.content '{search[:40]}': {r3.rowcount}")
                    results["lessons_updated"] += r3.rowcount
        except Exception as e:
            results["details"].append(f"ERROR on '{search[:40]}': {str(e)[:120]}")

    # Fill empty explanations using last hint when available
    # data and hints are JSON columns (not JSONB), so cast to jsonb for manipulation
    try:
        async with engine.begin() as conn:
            r4a = await conn.execute(sa_text("""
                UPDATE exercises
                SET data = jsonb_set(data::jsonb, '{explanation}',
                    to_jsonb((hints::jsonb)->>(jsonb_array_length(hints::jsonb)-1)))::json
                WHERE (data->>'explanation' = '' OR data->>'explanation' IS NULL)
                  AND hints IS NOT NULL
                  AND jsonb_typeof(hints::jsonb) = 'array'
                  AND jsonb_array_length(hints::jsonb) > 0
            """))
            r4b = await conn.execute(sa_text("""
                UPDATE exercises
                SET data = jsonb_set(data::jsonb, '{explanation}', '"¡Bien hecho!"'::jsonb)::json
                WHERE data->>'explanation' = '' OR data->>'explanation' IS NULL
            """))
            results["explanations_filled"] = (r4a.rowcount or 0) + (r4b.rowcount or 0)
            results["details"].append(f"Filled {r4a.rowcount or 0} from hints, {r4b.rowcount or 0} default")
    except Exception as e:
        results["details"].append(f"ERROR filling explanations: {str(e)[:200]}")

    return results


@app.post("/api/admin/seed-curriculum")
async def seed_curriculum_endpoint():
    """Seed full curriculum (G1-G6) into database. Admin only."""
    from app.core.database import AsyncSessionLocal
    from app.models.curriculum import Topic, Unit, Lesson, Exercise
    from seed.curriculum_seed import TOPICS

    async with AsyncSessionLocal() as db:
        topic_count = unit_count = lesson_count = exercise_count = 0

        for topic_data in TOPICS:
            topic = Topic(
                slug=topic_data["slug"],
                title=topic_data["title"],
                description=topic_data.get("description"),
                icon_name=topic_data.get("icon_name"),
            )
            db.add(topic)
            await db.flush()
            topic_count += 1

            for unit_data in topic_data.get("units", []):
                unit = Unit(
                    topic_id=topic.id,
                    slug=unit_data["slug"],
                    title=unit_data["title"],
                    description=unit_data.get("description"),
                    order_index=unit_data.get("order_index", 0),
                )
                db.add(unit)
                await db.flush()
                unit_count += 1

                lesson_map = {}
                for lesson_data in unit_data.get("lessons", []):
                    lesson = Lesson(
                        unit_id=unit.id,
                        title=lesson_data["title"],
                        content=lesson_data["content"],
                        order_index=lesson_data.get("order_index", 0),
                    )
                    db.add(lesson)
                    await db.flush()
                    lesson_count += 1
                    lesson_map[lesson_data["title"]] = lesson.id

                for ex_data in unit_data.get("exercises", []):
                    lesson_id = None
                    for lesson_data in unit_data.get("lessons", []):
                        if ex_data["slug"] in lesson_data.get("exercise_slugs", []):
                            lesson_id = lesson_map.get(lesson_data["title"])
                            break

                    exercise = Exercise(
                        unit_id=unit.id,
                        lesson_id=lesson_id,
                        slug=ex_data["slug"],
                        title=ex_data["title"],
                        exercise_type=ex_data["exercise_type"],
                        difficulty=ex_data["difficulty"],
                        points_value=ex_data["points"],
                        data=ex_data["data"],
                        hints=ex_data.get("hints"),
                        is_anked=ex_data.get("is_anked", False),
                        is_summative=ex_data.get("is_summative", False),
                    )
                    db.add(exercise)
                    exercise_count += 1

        await db.commit()

        return {
            "status": "seeded",
            "topics": topic_count,
            "units": unit_count,
            "lessons": lesson_count,
            "exercises": exercise_count,
        }

