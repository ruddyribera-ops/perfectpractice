"""
Content import + admin curriculum management router.

Handles:
- Viewing current curriculum state
- Seeding Bolivia-aligned curriculum
- Importing content from CSV/JSON uploads
- Khan Academy import (wired for future)
"""

import json
import re
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_user_required
from app.core.khan_client import KhanAcademyClient
from app.models.user import User
from app.models.curriculum import Topic, Unit, Lesson, Exercise
from app.models.classes import Class
from app.schemas.curriculum import TopicTreeResponse, UnitDetailResponse


router = APIRouter(prefix="/api/admin", tags=["admin"])


def _require_teacher_or_admin(user: User) -> None:
    if user.role not in ("teacher", "admin"):
        raise HTTPException(status_code=403, detail="Teacher or admin only")


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    return text


# -------------------------------------------------------------------------
# Curriculum status
# -------------------------------------------------------------------------

@router.get("/curriculum/status")
async def get_curriculum_status(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Return counts of all curriculum entities."""
    _require_teacher_or_admin(user)

    async def count(model):
        result = await db.execute(select(func.count(model.id)))
        return result.scalar() or 0

    return {
        "topics": await count(Topic),
        "units": await count(Unit),
        "lessons": await count(Lesson),
        "exercises": await count(Exercise),
    }


@router.get("/curriculum/topics", response_model=list[TopicTreeResponse])
async def list_all_topics(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """Return full topic tree (same as public /api/topics)."""
    _require_teacher_or_admin(user)
    result = await db.execute(
        select(Topic).where(Topic.parent_id == None).order_by(Topic.id)
    )
    topics = result.scalars().all()
    return [TopicTreeResponse.model_validate(t) for t in topics]


# -------------------------------------------------------------------------
# Seed Bolivia curriculum
# -------------------------------------------------------------------------

@router.post("/seed/bolivia")
async def seed_bolivia_curriculum(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Seed the full Bolivia curriculum (1°–6° primaria).

    Extends the existing curriculum_seed.py with grade-specific content
    aligned to Bolivian national curriculum standards.
    """
    _require_teacher_or_admin(user)

    created = {"topics": 0, "units": 0, "lessons": 0, "exercises": 0}

    BOLIVIA_CURRICULUM = _build_bolivia_curriculum()

    for grade, topics_data in BOLIVIA_CURRICULUM.items():
        for topic_data in topics_data:
            # Check if topic exists
            result = await db.execute(select(Topic).where(Topic.slug == topic_data["slug"]))
            if result.scalar_one_or_none():
                continue

            topic = Topic(
                slug=topic_data["slug"],
                title=topic_data["title"],
                description=topic_data.get("description"),
                icon_name=topic_data.get("icon_name"),
            )
            db.add(topic)
            await db.flush()
            created["topics"] += 1

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
                created["units"] += 1

                for lesson_data in unit_data.get("lessons", []):
                    lesson = Lesson(
                        unit_id=unit.id,
                        title=lesson_data["title"],
                        content=lesson_data["content"],
                        order_index=lesson_data.get("order_index", 0),
                    )
                    db.add(lesson)
                    await db.flush()
                    created["lessons"] += 1

                for ex_data in unit_data.get("exercises", []):
                    exercise = Exercise(
                        unit_id=unit.id,
                        lesson_id=None,
                        slug=ex_data["slug"],
                        title=ex_data["title"],
                        exercise_type=ex_data["exercise_type"],
                        difficulty=ex_data["difficulty"],
                        points_value=ex_data["points"],
                        data=ex_data["data"],
                        hints=ex_data.get("hints"),
                    )
                    db.add(exercise)
                    created["exercises"] += 1

    await db.commit()
    return {
        "message": "Bolivia curriculum seeded",
        "created": created,
        "total": {k: sum(1 for g in BOLIVIA_CURRICULUM.values() for t in g
                   for u in t.get("units", []) for _ in u.get("exercises", []))
                   for k in ["exercises"]},
    }


# -------------------------------------------------------------------------
# Run FULL curriculum seed (the big one with all grades + Bolivia bonus)
# -------------------------------------------------------------------------

@router.post("/seed/full")
async def seed_full_curriculum(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Run the FULL curriculum_seed.py — 53+ topics, 280+ exercises.

    This uses the TOPICS list from seed/curriculum_seed.py which includes:
    - GRADE1..GRADE6 (full G1-G6 Khan-aligned curriculum)
    - Bonus topics (Aritmética, etc.)

    Idempotent: skips topics/units/lessons/exercises that already exist.
    """
    _require_teacher_or_admin(user)

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from seed.curriculum_seed import seed_topics, verify_seed

    print(f"\n📊 Current DB state before seed:")
    before = await verify_seed()
    print(f"   Topics: {before[0]}, Units: {before[1]}, Lessons: {before[2]}, Exercises: {before[3]}")

    print("\n🚀 Running full seed (idempotent — skips existing topics/units/lessons)...")
    created = await seed_topics(db)
    await db.commit()

    print(f"\n✅ Full seed complete: {created[0]} topics, {created[1]} units, {created[2]} lessons, {created[3]} exercises")

    return {
        "message": "Full curriculum seeded",
        "created": {"topics": created[0], "units": created[1], "lessons": created[2], "exercises": created[3]},
        "total_after": {"topics": before[0] + created[0], "units": before[1] + created[1], "lessons": before[2] + created[2], "exercises": before[3] + created[3]},
    }


# -------------------------------------------------------------------------
# CSV/JSON import
# -------------------------------------------------------------------------

@router.post("/import/csv")
async def import_content_csv(
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
    file: UploadFile = File(...),
):
    """
    Import curriculum content from a CSV or JSON file.

    Expected JSON format:
    [
      {
        "type": "topic",
        "slug": "my-topic",
        "title": "My Topic",
        "description": "...",
        "icon_name": "📐"
      },
      {
        "type": "exercise",
        "topic_slug": "my-topic",
        "unit_slug": "my-unit",
        "slug": "my-ex",
        "title": "My Exercise",
        "exercise_type": "multiple_choice",
        "difficulty": "easy",
        "points": 10,
        "data": {
          "question": "...",
          "choices": ["A", "B", "C"],
          "correct_answer": "A"
        }
      }
    ]

    The importer auto-creates missing parent topics/units.
    """
    _require_teacher_or_admin(user)

    content = await file.read()
    try:
        items = json.loads(content.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file")

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="Expected a JSON array of items")

    created = {"topics": 0, "units": 0, "lessons": 0, "exercises": 0}
    topic_cache: dict[str, Topic] = {}
    unit_cache: dict[str, Unit] = {}

    for item in items:
        item_type = item.get("type", "")
        if item_type == "topic":
            slug = item["slug"]
            result = await db.execute(select(Topic).where(Topic.slug == slug))
            if result.scalar_one_or_none():
                continue
            topic = Topic(
                slug=slug,
                title=item["title"],
                description=item.get("description"),
                icon_name=item.get("icon_name"),
            )
            db.add(topic)
            await db.flush()
            topic_cache[slug] = topic
            created["topics"] += 1

        elif item_type == "unit":
            topic_slug = item["topic_slug"]
            unit_slug = item["slug"]
            cache_key = f"{topic_slug}::{unit_slug}"

            result = await db.execute(select(Unit).where(Unit.slug == unit_slug))
            if result.scalar_one_or_none():
                continue

            if topic_slug not in topic_cache:
                result = await db.execute(select(Topic).where(Topic.slug == topic_slug))
                t = result.scalar_one_or_none()
                if not t:
                    t = Topic(slug=topic_slug, title=item.get("topic_title", topic_slug))
                    db.add(t)
                    await db.flush()
                    created["topics"] += 1
                topic_cache[topic_slug] = t

            unit = Unit(
                topic_id=topic_cache[topic_slug].id,
                slug=unit_slug,
                title=item["title"],
                description=item.get("description"),
                order_index=item.get("order_index", 0),
            )
            db.add(unit)
            await db.flush()
            unit_cache[cache_key] = unit
            created["units"] += 1

        elif item_type == "lesson":
            unit_slug = item["unit_slug"]
            topic_slug = item.get("topic_slug", unit_slug.split("-")[0])
            cache_key = f"{topic_slug}::{unit_slug}"

            if cache_key not in unit_cache:
                result = await db.execute(select(Unit).where(Unit.slug == unit_slug))
                u = result.scalar_one_or_none()
                if not u:
                    continue
                unit_cache[cache_key] = u

            lesson = Lesson(
                unit_id=unit_cache[cache_key].id,
                title=item["title"],
                content=item.get("content", ""),
                content_type=item.get("content_type", "text"),
                order_index=item.get("order_index", 0),
            )
            db.add(lesson)
            await db.flush()
            created["lessons"] += 1

        elif item_type == "exercise":
            unit_slug = item["unit_slug"]
            topic_slug = item.get("topic_slug", unit_slug.split("-")[0])
            cache_key = f"{topic_slug}::{unit_slug}"

            if cache_key not in unit_cache:
                result = await db.execute(select(Unit).where(Unit.slug == unit_slug))
                u = result.scalar_one_or_none()
                if not u:
                    continue
                unit_cache[cache_key] = u

            from app.models.curriculum import ExerciseType, Difficulty
            ex_type = ExerciseType(item.get("exercise_type", "multiple_choice"))
            diff = Difficulty(item.get("difficulty", "medium"))

            exercise = Exercise(
                unit_id=unit_cache[cache_key].id,
                lesson_id=item.get("lesson_id"),
                slug=item["slug"],
                title=item["title"],
                exercise_type=ex_type,
                difficulty=diff,
                points_value=item.get("points", 10),
                data=item.get("data", {}),
                hints=item.get("hints"),
            )
            db.add(exercise)
            created["exercises"] += 1

    await db.commit()
    return {"message": "Import complete", "created": created}


# -------------------------------------------------------------------------
# Khan Academy import (wired for future)
# -------------------------------------------------------------------------

@router.post("/import/khan")
async def import_from_khan(
    api_key: str | None = None,
    user: User = Depends(get_current_user_required),
    db: AsyncSession = Depends(get_db),
):
    """
    Attempt to import content from Khan Academy API.

    Currently returns empty results — Khan Academy's public API is restricted.
    This endpoint is wired and ready; activates when they open API access.
    """
    _require_teacher_or_admin(user)

    client = KhanAcademyClient(api_key=api_key)
    courses = await client.get_courses()

    if not courses:
        return {
            "message": "No content retrieved from Khan Academy API",
            "note": "Khan Academy API is not publicly available. "
                    "Use /import/csv or /seed/bolivia to populate content.",
            "courses_retrieved": 0,
        }

    created = {"topics": 0, "units": 0, "lessons": 0, "exercises": 0}
    for course in courses:
        topic_data = client.transform_course(course)
        if not topic_data:
            continue

        result = await db.execute(select(Topic).where(Topic.slug == topic_data["slug"]))
        if result.scalar_one_or_none():
            continue

        topic = Topic(**topic_data)
        db.add(topic)
        await db.flush()
        created["topics"] += 1

    await db.commit()
    return {
        "message": "Khan Academy import complete",
        "created": created,
        "courses_retrieved": len(courses),
    }


# =============================================================================
# Bolivia Curriculum Data — 1° to 6° Primaria
# =============================================================================

def _build_bolivia_curriculum() -> dict[int, list[dict]]:
    """
    Full Bolivia-aligned math curriculum for grades 1–6.
    Based on Bolivian national curriculum (Ministerio de Educación).
    All content in Spanish. Topics → Units → Lessons → Exercises.
    """

    def ex(slug, title, etype, diff, pts, question, choices=None, correct=None, explanation="", hints=None):
        """Shorthand to build an exercise dict."""
        data = {"question": question, "explanation": explanation}
        if choices:
            data["choices"] = choices
            data["correct_answer"] = correct or choices[0]
        else:
            data["correct_answer"] = correct or ""
        return {
            "slug": slug,
            "title": title,
            "exercise_type": etype,
            "difficulty": diff,
            "points": pts,
            "data": data,
            "hints": hints or [],
        }

    from app.models.curriculum import ExerciseType, Difficulty

    return {
        1: [
            {
                "slug": "1-numeros",
                "title": "Números hasta 100",
                "description": "Contar, leer, escribir y ordenar números del 0 al 100",
                "icon_name": "🔢",
                "units": [
                    {
                        "slug": "1-numeros-contar",
                        "title": "Contar hasta 20",
                        "description": "Contar objetos hasta 20",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Contar hasta 10", "content": "# 🔢 Contar hasta 10\n\nCuenta los objetos que ves. Puedes usar tus dedos.\n\n## 🎯 Usa el Marco de Diez (Ten-Frame)\nEl Marco de Diez es una tabla de 2×5. ¡Nos ayuda a ver instantly cuántos hay!\n\n:::visual:tenframe,5:::\n\n**¿Cuántos ves?**\nHay **5** puntos coloreados. Las otras 5 casillas están vacías.\n\n## 🖐️ Cuenta con tus dedos\n\nCuenta uno por uno mientras señalas cada objeto. Luego mira el marco de arriba y verifica.\n\n:::tryit:¿Cuántos hay? (1, 2, 3...)|5|Cuenta los puntos coloreados:::", "order_index": 0},
                            {"title": "Contar hasta 20", "content": "# 🔢 Contar hasta 20\n\nPodemos contar más allá del 10. Mira cómo continuamos después del 10.\n\n## 🎯 Dos Marcos de Diez\n\nUn marco de diez muestra hasta 10. Para el 11 al 20, usamos **dos** marcos:\n\n:::visual:tenframe,10:::\n:::visual:tenframe,5:::\n\n**Primero** llenamos el primer marco (10). **Después** seguimos con el segundo.\n\n## 📝 Números del 11 al 20\n\n- 11 = 10 + 1 → **dieciuno**\n- 12 = 10 + 2 → **dieciséis**\n- 15 = 10 + 5 → **quince**\n- 20 = 10 + 10 → **veinte**\n\n:::tryit:¿Cuántos hay? (hasta 20)|15|Son 1 marco lleno + 5 más:::", "order_index": 1},
                        ],
                        "exercises": [
                            ex("1-contar-5", "¿Cuántos?", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuántos círculos hay? ●●●●●", correct="5", hints=["Cuenta uno por uno"]),
                            ex("1-contar-10", "Contar hasta 10", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuántos hay? ●●●●●●●●●●", choices=["8","9","10","11"], correct="10", hints=["Cuenta todos los puntos"]),
                            ex("1-contar-15", "Contar hasta 15", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuántos hay? ●●●●●●●●●●●●●●", correct="15", hints=["Cuenta de 5 en 5"]),
                        ],
                    },
                    {
                        "slug": "1-numeros-ordenar",
                        "title": "Ordenar números",
                        "description": "Mayor, menor e igual",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Mayor y menor", "content": "# ⚖️ Mayor y Menor\n\n3 < 5 se lee \"3 es menor que 5\"\n\n## 📊 Barras de Comparación\n\nLas barras nos muestran qué número es más grande:\n\n:::visual:comparison,3,5,Pequeño,Grande:::\n\nLa barra **Grande** es más larga porque 5 es mayor que 3.\n\n## 🔑 Reglas para comparar\n\n- El símbolo **<** significa \"es menor que\"\n- El símbolo **>** significa \"es mayor que\"\n- La boca siempre mira al número **mayor**\n\n> 3 < 5 → 3 es **menor** que 5\n> 7 > 2 → 7 es **mayor** que 2\n\n:::tryit:¿Qué número es mayor, 7 o 3?|7|El 7 es mayor que 3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("1-mayor-7-3", "¿Qué número es mayor?", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Qué número es mayor: 7 o 3?", choices=["7","3"], correct="7", hints=["Compara: 7 tiene más que 3"]),
                            ex("1-menor-2-9", "¿Qué número es menor?", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Qué número es menor: 2 o 9?", choices=["2","9"], correct="2", hints=["2 es más pequeño que 9"]),
                            ex("1-ordenar-1-5", "Ordena de menor a mayor", ExerciseType.multiple_choice, Difficulty.easy, 5, "Ordena: 1, 5, 3", choices=["1,3,5","5,3,1","3,1,5"], correct="1,3,5", hints=["El más pequeño primero"]),
                        ],
                    },
                ],
            },
            {
                "slug": "1-suma-resta",
                "title": "Suma y Resta hasta 20",
                "description": "Sumar y restar números con resultados hasta 20",
                "icon_name": "➕",
                "units": [
                    {
                        "slug": "1-suma-10",
                        "title": "Suma hasta 10",
                        "description": "Sumar números cuyo resultado sea 10 o menos",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Sumar hasta 5", "content": "# ➕ Sumar hasta 5\n\n2 + 3 = ?\n\n## 🎯 Modelo de Bloques Base-10\n\nLos bloques nos ayudan a ver los números:\n\n:::visual:base10,2,3:::\n\n**Primero** tenemos 2 (dos cuadritos).\n**Después** agregamos 3 más.\n**Resultado:** 2 + 3 = **5**\n\n## 📏 También puedes usar la Recta Numérica\n\n:::visual:numberline,0,2,add:::\n\nAvanzamos 2 lugares desde el 0. Estamos en el **2**.\n\n:::visual:numberline,2,3,add:::\n\nDesde el 2, avanzamos 3 más → **5**\n\n:::tryit:¿Cuánto es 1 + 2?|3|1 + 2 = 3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("1-suma-1-1", "1 + 1", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 1 + 1?", correct="2", hints=["1 más 1 es 2"]),
                            ex("1-suma-2-2", "2 + 2", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 2 + 2?", choices=["3","4","5","6"], correct="4", hints=["2 + 2 = 4"]),
                            ex("1-suma-3-1", "3 + 1", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 3 + 1?", correct="4", hints=["3 + 1 = 4"]),
                        ],
                    },
                    {
                        "slug": "1-suma-20",
                        "title": "Suma hasta 20",
                        "description": "Sumas un poco más grandes",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Sumar con 10", "content": "# ➕ Sumar con 10\n\n10 + 5 = ?\n\n## 🎯 Modelo de Bloques Base-10\n\n:::visual:base10,10,5:::\n\n10 = una barra de decenas. 5 = cinco cuadritos.\nJuntamos todo → **15**\n\n## 📏 Recta Numérica\n\n:::visual:numberline,0,10,add:::\n\nDesde el 0, avanzamos 10 → llegamos al **10**\n\n:::visual:numberline,10,5,add:::\n\nDesde el 10, avanzamos 5 más → **15**\n\n## 🧠 Truco\n\nCuando sumas **10 + un número**, solo cambia la cifra de las decenas.\n> 10 + 3 = **13**\n> 10 + 7 = **17**\n\n:::tryit:¿Cuánto es 10 + 7?|17|10 + 7 = 17:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("1-suma-10-5", "10 + 5", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 10 + 5?", correct="15", hints=["10 + 5 = 15"]),
                            ex("1-suma-8-6", "8 + 6", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 8 + 6?", correct="14", hints=["8 + 2 = 10, +4 = 14"]),
                            ex("1-suma-12-5", "12 + 5", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 12 + 5?", correct="17", hints=["12 + 3 = 15, +2 = 17"]),
                        ],
                    },
                    {
                        "slug": "1-resta-10",
                        "title": "Resta hasta 10",
                        "description": "Restar números hasta 10",
                        "order_index": 2,
                        "lessons": [
                            {"title": "Restar hasta 5", "content": "# ➖ Restar hasta 5\n\n4 - 2 = ?\n\n## 📏 Modelo de Recta Numérica\n\nRestar es **retroceder** en la recta numérica.\n\n:::visual:numberline,4,2,subtract:::\n\nDesde el **4**, retrocedemos 2 → llegamos al **2**.\n\n## 🖐️ También puedes verlo con tus dedos\n\nTienes 4 dedos. Cierras 2. ¿Cuántos quedan?\n**4 - 2 = 2**\n\n## 🔑 Recuerda\n\n- **Sumar** = avanzar = hacer más\n- **Restar** = retroceder = quitar\n\n:::tryit:¿Cuánto es 3 - 1?|2|Desde el 3 retrocedes 1:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("1-resta-5-2", "5 - 2", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 5 - 2?", correct="3", hints=["5 menos 2 = 3"]),
                            ex("1-resta-4-1", "4 - 1", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 4 - 1?", choices=["2","3","4","5"], correct="3", hints=["4 - 1 = 3"]),
                            ex("1-resta-3-2", "3 - 2", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 3 - 2?", correct="1", hints=["3 menos 2 = 1"]),
                        ],
                    },
                    {
                        "slug": "1-resta-20",
                        "title": "Resta hasta 20",
                        "description": "Restas un poco más grandes",
                        "order_index": 3,
                        "lessons": [
                            {"title": "Restar desde 10", "content": "# ➖ Restar desde 10\n\n10 - 4 = ?\n\n## 📏 Recta Numérica\n\n:::visual:numberline,10,4,subtract:::\n\nDesde el **10**, retrocedemos 4 → llegamos al **6**.\n\n## 📊 Otro ejemplo: 15 - 3\n\n:::visual:numberline,15,3,subtract:::\n\nDesde el **15**, retrocedemos 3 → llegamos al **12**.\n\n## 🧠 Consejo\n\nPara restar desde 10 o más, cuenta hacia atrás:\n> 10 - 4: 10, 9, 8, 7, 6 → **6** ✓\n> 15 - 3: 15, 14, 13, 12 → **12** ✓\n\n:::tryit:¿Cuánto es 15 - 3?|12|15 - 3 = 12:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("1-resta-10-4", "10 - 4", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 10 - 4?", correct="6", hints=["10 - 4 = 6"]),
                            ex("1-resta-18-5", "18 - 5", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 18 - 5?", correct="13", hints=["18 - 5 = 13"]),
                            ex("1-resta-16-7", "16 - 7", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 16 - 7?", correct="9", hints=["16 - 6 = 10, -1 = 9"]),
                        ],
                    },
                ],
            },
            {
                "slug": "1-formas",
                "title": "Formas Geométricas",
                "description": "Reconocer y nombrar círculos, cuadrados, triángulos y rectángulos",
                "icon_name": "📐",
                "units": [
                    {
                        "slug": "1-formas-basicas",
                        "title": "Figuras básicas",
                        "description": "Reconocer cuadrado, triángulo, círculo y rectángulo",
                        "order_index": 0,
                        "lessons": [
                            {"title": "El círculo", "content": "# ⭕ El Círculo\n\nEl círculo es redondo como una moneda. No tiene lados rectos.\n\n## 📐 Características del Círculo\n\n- 🔘 **No tiene lados rectos** — es una curva cerrada\n- 🎯 **Tiene un centro** — el punto en el medio\n- 📏 **No tiene vértices** — las esquinas son puntos en la curva\n\n## 🔎 Busca círculos en tu alrededor\n\n- 🪙 La moneda\n- ⭕ La pizza (a veces)\n- 🔵 La rueda de la bicicleta\n- 🏀 La pelota de fútbol\n\n:::visual:comparison,3,5,Círculo,Figura:::\n\n> Un círculo puede ser **pequeño** o **grande**, pero siempre tiene la misma forma.\n\n:::tryit:¿Cuántos lados tiene un círculo?|0|El círculo no tiene lados rectos:::", "order_index": 0},
                            {"title": "El triángulo", "content": "# △ El Triángulo\n\nEl triángulo tiene **3 lados** y **3 esquinas** (vértices).\n\n## 📐 Estructura del Triángulo\n\n:::visual:anglemaker,60:::\n\nEl ángulo de cada esquina de un triángulo equilátero mide **60°**.\n\n## 📏 Características\n\n- △ Tiene **3 lados** rectos\n- 📍 Tiene **3 vértices** (esquinas)\n- 🔺 Parece una **flecha** cuando lo apuntas\n\n## 🔎 Busca triángulos en tu alrededor\n\n- 🚸 Señal de tránsito\n- 📐 La forma de una pizza cuando cortas en cuartos\n- ⛺ La carpa de campaña\n\n:::tryit:¿Cuántos lados tiene?|3|3 lados rectos:::", "order_index": 1},
                        ],
                        "exercises": [
                            ex("1-circ-lados", "¿Cuántos lados?", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuántos lados tiene un círculo?", choices=["0","1","2","3"], correct="0", hints=["El círculo no tiene líneas rectas"]),
                            ex("1-triang-lados", "Lados del triángulo", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuántos lados tiene un triángulo?", choices=["2","3","4","5"], correct="3", hints=["Trian = 3"]),
                            ex("1-cuad-lados", "Lados del cuadrado", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuántos lados tiene un cuadrado?", choices=["3","4","5","6"], correct="4", hints=["Cuadrado = 4 lados iguales"]),
                        ],
                    },
                ],
            },
            {
                "slug": "1-medicion",
                "title": "Medición",
                "description": "Comparar tamaños: largo, corto, alto, bajo",
                "icon_name": "📏",
                "units": [
                    {
                        "slug": "1-medicion-basica",
                        "title": "Tamaño y longitud",
                        "description": "Comparar objetos por su tamaño",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Largo y corto", "content": "# 📏 Largo y Corto\n\nComparamos objetos por su longitud: ¿cuál es más largo?\n\n## 📏 Uso la Regla para Medir\n\n:::visual:ruler,0,10,cm,2,7:::\n\nLa zona **amarilla** mide **5 cm** (del 2 al 7).\n\n## 🔍 Comparación visual\n\n:::visual:comparison,7,3,Lápiz,Crayón:::\n\n**7** es mayor que **3**. El **Lápiz** es más largo.\n\n## 📝 Vocabulario\n\n- **Largo** = más centímetros, se extiende más\n- **Corto** = menos centímetros\n- **Alto** = mucha altura (arriba hacia abajo)\n- **Bajo** = poca altura\n\n:::tryit:¿Cuál es más largo?|el primero|Porque 7 > 3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("1-largo-corto", "¿Cuál es más largo?", ExerciseType.multiple_choice, Difficulty.easy, 5, "Lápiz vs. Clips", choices=["Lápiz","Clips","son iguales"], correct="Lápiz", hints=["El lápiz es más largo que el clips"]),
                            ex("1-alto-bajo", "¿Cuál es más alto?", ExerciseType.multiple_choice, Difficulty.easy, 5, "Árbol vs. Flor", choices=["Árbol","Flor","son iguales"], correct="Árbol", hints=["El árbol es más alto que la flor"]),
                        ],
                    },
                ],
            },
        ],
        2: [
            {
                "slug": "2-numeros",
                "title": "Números hasta 1000",
                "description": "Leer, escribir y comparar números hasta 1000",
                "icon_name": "🔢",
                "units": [
                    {
                        "slug": "2-valor-posicional",
                        "title": "Valor posicional",
                        "description": "Unidades, decenas y centenas",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Decenas", "content": "# 🔟 Decenas\n\n10, 20, 30, 40... cada grupo de 10 es una **decena**.\n\n## 🔢 Tabla de Valor Posicional\n\n:::visual:placevalue,60:::\n\nEl **6** está en las **decenas** → vale **60**.\n\n## 📊 Descomposición de números\n\n| Número | Decenas | Unidades |\n|--------|---------|----------|\n| 23 | 2 | 3 |\n| 45 | 4 | 5 |\n| 60 | 6 | 0 |\n| 87 | 8 | 7 |\n\n## 🧠 Recuerda\n\n- **10 unidades** = **1 decena**\n- **5 decenas** = **50**\n- **9 decenas** = **90**\n\n:::tryit:¿Cuántas decenas tiene 60?|6|60 = 6 decenas:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-decenas-50", "Decenas", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuántas decenas tiene el 50?", choices=["5","50","500"], correct="5", hints=["50 = 5 decenas"]),
                            ex("2-decenas-80", "Decenas 80", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuántas decenas tiene 80?", correct="8", hints=["80 = 8 decenas"]),
                            ex("2-valor-345", "Valor posicional", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Cuál es el valor del 3 en 345?", choices=["3","30","300"], correct="300", hints=["3 está en la posición de centenas"]),
                        ],
                    },
                ],
            },
            {
                "slug": "2-suma-resta",
                "title": "Suma y Resta hasta 1000",
                "description": "Operaciones con números hasta tres dígitos",
                "icon_name": "➕",
                "units": [
                    {
                        "slug": "2-suma-llevando",
                        "title": "Suma llevando",
                        "description": "Sumas donde las unidades pasan a decenas",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Sumar llevando", "content": "# ➕ Sumar Llevando\n\n45 + 7 = ?\n\n## 🎯 Modelo de Bloques Base-10 con Leva\n\n:::visual:base10,45,7:::\n\n**Paso 1:** Sumamos las unidades → 5 + 7 = 12\n**Paso 2:** El **12** = 2 unidades + **1 decena**\n**Paso 3:** Escribimos el **2**, llevamos **1** a las decenas\n**Paso 4:** 4 + 1 = 5 → Resultado: **52**\n\n## 📏 Recta Numérica (una forma alternativa)\n\n:::visual:numberline,45,7,add:::\n\nDesde **45**, avanzamos **7** → **52**\n\n## 🔑 Pasos para sumar llevando\n\n1. **Suma las unidades**\n2. Si el resultado es **mayor que 9**, lleva 1 a las decenas\n3. **Suma las decenas** (incluyendo lo que llevas)\n\n:::tryit:35 + 8 = ?|43|35 + 8 = 43, llevamos 1:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-suma-llevar-45-7", "45 + 7", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 45 + 7?", correct="52", hints=["5+7=12, llevamos 1, 4+1=5 → 52"]),
                            ex("2-suma-llevar-28-6", "28 + 6", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 28 + 6?", correct="34", hints=["8+6=14, llevamos 1, 2+1=3 → 34"]),
                            ex("2-suma-llevar-67-8", "67 + 8", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 67 + 8?", correct="75", hints=["7+8=15, llevamos 1, 6+1=7 → 75"]),
                            ex("2-suma-llevar-234-156", "234 + 156", ExerciseType.numeric, Difficulty.medium, 15, "¿Cuánto es 234 + 156?", correct="390", hints=["4+6=10, 3+5+1=9, 2+1=3 → 390"]),
                        ],
                    },
                    {
                        "slug": "2-resta-prestando",
                        "title": "Resta prestando",
                        "description": "Restas donde necesitamos pedir prestado",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Restar pidiendo prestado", "content": "# ➖ Resta Prestando\n\n52 - 27 = ?\n\n## 📏 Recta Numérica\n\n:::visual:numberline,52,27,subtract:::\n\nDesde **52**, retrocedemos **27** → **25**\n\n## 🔑 ¿Cuándo necesitamos pedir prestado?\n\nCuando las **unidades de arriba** son **menores** que las de abajo.\n\n**Ejemplo: 52 - 27**\n\n1. Las unidades: 2 - 7 → **no puede**\n2. Pedimos prestado **1 decena** (10 unidades)\n3. Ahora tenemos: 12 - 7 = **5** ✓\n4. Las decenas: 4 - 2 = **2** ✓\n5. Resultado: **25**\n\n## 🧠 Consejo\n\nPiensa en el préstamo como \"pedir ayuda a la decena\":\n> Tienes 2 manzanas pero necesitas 7. Pides prestada 1 decena = 10 manzanas más. Ahora tienes **12** manzanas. 12 - 7 = 5.\n\n:::tryit:403 - 187 = ?|216|403 - 187 = 216:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-resta-prestar-52-27", "52 - 27", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 52 - 27?", correct="25", hints=["2-7 no puede, pedimos 1 de las decenas"]),
                            ex("2-resta-prestar-81-34", "81 - 34", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 81 - 34?", correct="47", hints=["1-4 no puede, pedimos prestado"]),
                            ex("2-resta-prestar-500-178", "500 - 178", ExerciseType.numeric, Difficulty.medium, 15, "¿Cuánto es 500 - 178?", correct="322", hints=["500 es 5 centenas, necesitamos pedir prestado varias veces"]),
                        ],
                    },
                ],
            },
            {
                "slug": "2-multiplicacion",
                "title": "Introducción a la Multiplicación",
                "description": "Entender la multiplicación como suma repetida, tablas del 1 al 5",
                "icon_name": "✖️",
                "units": [
                    {
                        "slug": "2-multi-intro",
                        "title": "Multiplicación como suma repetida",
                        "description": "Entender qué significa multiplicar",
                        "order_index": 0,
                        "lessons": [
                            {"title": "¿Qué es multiplicar?", "content": "# ✖️ ¿Qué es la Multiplicación?\n\n3 × 4 significa **3 veces el 4** → 4 + 4 + 4\n\n## 🎯 Modelo de Arreglos (Matriz)\n\n:::visual:array,3,4:::\n\n**3 filas** de **4 columnas** = 3 × 4 = **12** puntos\n\n## 🔄 La multiplicación es suma repetida\n\n| Multiplicación | Suma repetida | Resultado |\n|----------------|---------------|-----------|\n| 2 × 3 | 3 + 3 | 6 |\n| 4 × 5 | 5 + 5 + 5 + 5 | 20 |\n| 3 × 4 | 4 + 4 + 4 | 12 |\n\n## 🧠 También funciona al revés\n\n4 × 3 = 3 + 3 + 3 + 3 = 12 (las dos responden el mismo problema)\n\n:::tryit:¿Cuánto es 2 × 3?|6|2 × 3 = 6:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-multi-2x3", "2 × 3", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 2 × 3?", correct="6", hints=["2×3 = 3+3 = 6"]),
                            ex("2-multi-4x2", "4 × 2", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 4 × 2?", correct="8", hints=["4×2 = 2+2+2+2 = 8"]),
                            ex("2-multi-3x5", "3 × 5", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es 3 × 5?", correct="15", hints=["3×5 = 5+5+5 = 15"]),
                        ],
                    },
                    {
                        "slug": "2-tablas-1-5",
                        "title": "Tablas del 1 al 5",
                        "description": "Memorizar las tablas de multiplicar",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Tabla del 1", "content": "# 1️⃣ Tabla del 1\n\n**Todo multiplicado por 1 es el mismo número.**\n\n1 × 1 = 1, 1 × 2 = 2, ..., 1 × 10 = 10\n\n## 🎯 Modelo de Arreglos\n\n:::visual:array,1,5:::\n\n**1 fila** de **5** = 1 × 5 = **5**\n\n## 📊 Tabla del 1 completa\n\n| Multiplicación | Resultado |\n|----------------|-----------|\n| 1 × 1 | 1 |\n| 1 × 2 | 2 |\n| 1 × 3 | 3 |\n| 1 × 4 | 4 |\n| 1 × 5 | 5 |\n| 1 × 6 | 6 |\n| 1 × 7 | 7 |\n| 1 × 8 | 8 |\n| 1 × 9 | 9 |\n| 1 × 10 | 10 |\n\n## 🧠 Truco\n\n> **1 × cualquier número = ese número**\n> 1 × 7 = 7, 1 × 100 = 100\n\n:::tryit:1 × 8|8|1 × 8 = 8:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-tabla1-6", "Tabla del 1", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 1 × 6?", choices=["1","6","60"], correct="6"),
                            ex("2-tabla2-3", "Tabla del 2", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 2 × 3?", choices=["5","6","8"], correct="6"),
                            ex("2-tabla3-4", "Tabla del 3", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 3 × 4?", choices=["10","11","12"], correct="12"),
                            ex("2-tabla4-5", "Tabla del 4", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 4 × 5?", choices=["18","20","24"], correct="20"),
                            ex("2-tabla5-3", "Tabla del 5", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 5 × 3?", choices=["10","15","20"], correct="15"),
                        ],
                    },
                ],
            },
            {
                "slug": "2-fracciones",
                "title": "Fracciones Simples",
                "description": "Mitad, cuarto, tercios",
                "icon_name": "🍕",
                "units": [
                    {
                        "slug": "2-fracciones-intro",
                        "title": "Mitad y cuarto",
                        "description": "Reconocer mitades y cuartos",
                        "order_index": 0,
                        "lessons": [
                            {"title": "¿Qué es la mitad?", "content": "# 🍕 La Mitad\n\nDividimos algo en **2 partes iguales**. Cada parte es la mitad.\n\n## 🎯 Modelo de Fracciones\n\n:::visual:fraction,1,2:::\n\n**Mitad** = **1 de 2** partes iguales → 1/2\n\n## 📊 Dividir en dos\n\n| Total | Mitad |\n|-------|-------|\n| 6 | 3 |\n| 10 | 5 |\n| 8 | 4 |\n| 4 | 2 |\n\n## 🧠 Cómo encontrar la mitad\n\nPara encontrar la mitad, **divide entre 2**.\n\n> Mitad de 6 → 6 ÷ 2 = **3** ✓\n> Mitad de 10 → 10 ÷ 2 = **5** ✓\n\n:::tryit:¿Cuánto es la mitad de 6?|3|6 ÷ 2 = 3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-mitad-6", "Mitad de 6", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es la mitad de 6?", correct="3", hints=["Divide entre 2: 6 ÷ 2 = 3"]),
                            ex("2-mitad-10", "Mitad de 10", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es la mitad de 10?", correct="5", hints=["10 ÷ 2 = 5"]),
                            ex("2-cuarto-8", "Cuarto de 8", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es un cuarto de 8?", correct="2", hints=["8 ÷ 4 = 2"]),
                            ex("2-tercio-9", "Tercio de 9", ExerciseType.numeric, Difficulty.easy, 5, "¿Cuánto es un tercio de 9?", correct="3", hints=["9 ÷ 3 = 3"]),
                        ],
                    },
                ],
            },
            {
                "slug": "2-datos",
                "title": "Datos y Gráficos",
                "description": "Recolectar y organizar datos en tablas y gráficos simples",
                "icon_name": "📊",
                "units": [
                    {
                        "slug": "2-graficos-intro",
                        "title": "Gráficos de barras",
                        "description": "Leer e interpretar gráficos de barras simples",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Leer un gráfico", "content": "# 📊 Leer un Gráfico de Barras\n\nEl gráfico muestra cuántos animales hay.\n\n## 📊 Barras de Comparación\n\n:::visual:comparison,3,5,Gatos,Perros:::\n\nLa barra de **Gatos** mide 3. La barra de **Perros** mide 5.\n\n## 📝 Cómo leer un gráfico de barras\n\n1. **Lee el título** — ¿de qué trata el gráfico?\n2. **Mira cada barra** — ¿a qué categoría pertenece?\n3. **Compara las alturas** — ¿cuál es mayor?\n4. **Lee los números** — cada barra tiene un número arriba\n\n## 🔍 Ejemplo: Animales en el zoológico\n\n| Animal | Cantidad |\n|--------|----------|\n| Gatos | 3 |\n| Perros | 5 |\n| Pájaros | 8 |\n\n- Los **pájaros** son los más numerosos (8)\n- Los **gatos** son los menos (3)\n\n:::tryit:¿Cuántos gatos hay?|3|La barra de gatos muestra 3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("2-grafico-mas", "¿Cuál es más?", ExerciseType.multiple_choice, Difficulty.easy, 5, "Gatos: 3, Perros: 5. ¿Qué hay más?", choices=["Gatos","Perros","son iguales"], correct="Perros", hints=["5 es más que 3"]),
                            ex("2-grafico-contar", "Contar del gráfico", ExerciseType.numeric, Difficulty.easy, 5, "Si el gráfico muestra: manzanas 4, naranjas 2. ¿Cuántas frutas en total?", correct="6", hints=["4 + 2 = 6"]),
                        ],
                    },
                ],
            },
        ],
        3: [
            {
                "slug": "3-multiplicacion",
                "title": "Multiplicación",
                "description": "Tablas del 6 al 10, multiplicación de 2 dígitos por 1 dígito",
                "icon_name": "✖️",
                "units": [
                    {
                        "slug": "3-tablas-6-10",
                        "title": "Tablas del 6 al 10",
                        "description": "Memorizar las tablas restantes",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Tabla del 6", "content": "# 6️⃣ Tabla del 6\n\n6 × 1 = 6, 6 × 2 = 12, ..., 6 × 10 = 60\n\n## 🎯 Modelo de Arreglo Animado\n\n:::visual:animatedarray,3,6,true:::\n\n**3 filas** de **6** = 3 × 6 = **18** puntos\n\n## 📊 Tabla del 6 completa\n\n| Multiplicación | Suma | Resultado |\n|----------------|------|-----------|\n| 6 × 1 | 6 | 6 |\n| 6 × 2 | 6 + 6 | 12 |\n| 6 × 3 | 6 + 6 + 6 | 18 |\n| 6 × 4 | 6 + 6 + 6 + 6 | 24 |\n| 6 × 5 | 6 × 5 | 30 |\n| 6 × 6 | 6 + 6 + 6 + 6 + 6 + 6 | 36 |\n| 6 × 7 | 6 + 6 + 6 + 6 + 6 + 6 + 6 | 42 |\n| 6 × 8 | 6 × 8 | 48 |\n| 6 × 9 | 6 × 9 | 54 |\n| 6 × 10 | 6 × 10 | 60 |\n\n## 🧠 Trucos para la tabla del 6\n\n> **6 × 8 = 48** → 6 × 10 = 60, - 6 × 2 = 12 → 60 - 12 = 48\n> **6 × 7 = 42** → 6 × 5 = 30 + 6 × 2 = 12 → 30 + 12 = 42\n\n:::tryit:6 × 7|42|6 × 7 = 42:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-tabla6-8", "Tabla del 6", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Cuánto es 6 × 8?", choices=["48","56","64"], correct="48"),
                            ex("3-tabla7-6", "Tabla del 7", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Cuánto es 7 × 6?", choices=["36","42","49"], correct="42"),
                            ex("3-tabla8-9", "Tabla del 8", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Cuánto es 8 × 9?", choices=["72","64","81"], correct="72"),
                            ex("3-tabla9-7", "Tabla del 9", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Cuánto es 9 × 7?", choices=["54","63","72"], correct="63"),
                            ex("3-tabla10-4", "Tabla del 10", ExerciseType.multiple_choice, Difficulty.easy, 5, "¿Cuánto es 10 × 4?", choices=["14","40","44"], correct="40"),
                        ],
                    },
                    {
                        "slug": "3-multi-2x1",
                        "title": "Multiplicación 2×1",
                        "description": "Multiplicar un número de 2 dígitos por uno de 1 dígito",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Multiplicar 2×1", "content": "# ✖️ Multiplicación 2 × 1\n\n23 × 4 = (20×4) + (3×4) = 80 + 12 = 92\n\n## 🎯 Modelo de Arreglos\n\n:::visual:array,4,23:::\n\n**4 filas** de **23** → desglosamos en:\n- 4 × 20 = **80**\n- 4 × 3 = **12**\n- Total: **92**\n\n## 🔑 Pasos para multiplicar 2×1\n\n1. **Multiplica las unidades** del número de 2 dígitos\n2. **Multiplica las decenas**\n3. **Suma** los dos resultados\n\n**Ejemplo: 15 × 3**\n- 3 × 5 = 15 (unidades)\n- 3 × 10 = 30 (decenas)\n- 15 + 30 = **45**\n\n:::tryit:15 × 3|45|15 × 3 = 45:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-multi-23x4", "23 × 4", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 23 × 4?", correct="92", hints=["20×4=80, 3×4=12, 80+12=92"]),
                            ex("3-multi-41x2", "41 × 2", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 41 × 2?", correct="82", hints=["40×2=80, 1×2=2, 80+2=82"]),
                            ex("3-multi-156x7", "156 × 7", ExerciseType.numeric, Difficulty.medium, 15, "¿Cuánto es 156 × 7?", correct="1092", hints=["100×7=700, 50×7=350, 6×7=42, 700+350+42=1092"]),
                        ],
                    },
                ],
            },
            {
                "slug": "3-division",
                "title": "División",
                "description": "Dividir usando tablas de multiplicar, división exacta y con residuo",
                "icon_name": "➗",
                "units": [
                    {
                        "slug": "3-division-intro",
                        "title": "Dividir con tablas",
                        "description": "Dividir usando lo que sabemos de multiplicar",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Dividir es lo opuesto", "content": "# ➗ Dividir es lo Opuesto de Multiplicar\n\nSi 4 × 6 = 24, entonces 24 ÷ 4 = 6\n\n## 🎯 Modelo de División (Agrupar)\n\n:::visual:division,24,4:::\n\n**24** dividido entre **4** = **6**\n\n24 objetos ÷ en grupos de 4 = **6 grupos**\n\n## 🔄 Relación entre multiplicar y dividir\n\n| Multiplicación | División |\n|----------------|----------|\n| 4 × 6 = 24 | 24 ÷ 4 = 6 |\n| 3 × 7 = 21 | 21 ÷ 3 = 7 |\n| 5 × 8 = 40 | 40 ÷ 5 = 8 |\n\n**Si sabes la multiplicación, ¡ya sabes la división!**\n\n## 🧠 ¿Cómo dividir?\n\n1. Piensa: \"¿4 × ? = 24?\"\n2. 4 × 6 = 24 → entonces 24 ÷ 4 = **6**\n\n:::tryit:36 ÷ 6|6|6 × 6 = 36:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-div-24-4", "24 ÷ 4", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 24 ÷ 4?", correct="6", hints=["4 × 6 = 24, entonces 24 ÷ 4 = 6"]),
                            ex("3-div-35-5", "35 ÷ 5", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 35 ÷ 5?", correct="7", hints=["5 × 7 = 35"]),
                            ex("3-div-48-6", "48 ÷ 6", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 48 ÷ 6?", correct="8", hints=["6 × 8 = 48"]),
                            ex("3-div-residuo-17-5", "17 ÷ 5 residuo", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 17 ÷ 5? ¿Cuál es el residuo?", correct="3", hints=["5×3=15, 17-15=2 de residuo"], explanation="17 ÷ 5 = 3 residuo 2"),
                        ],
                    },
                ],
            },
            {
                "slug": "3-fracciones",
                "title": "Fracciones",
                "description": "Sumar y restar fracciones con igual denominador, comparar fracciones",
                "icon_name": "🍕",
                "units": [
                    {
                        "slug": "3-fracciones-sumar",
                        "title": "Sumar fracciones",
                        "description": "Sumar fracciones con igual denominador",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Suma con mismo denominador", "content": "# ➕ Sumar Fracciones con Igual Denominador\n\n1/5 + 2/5 = 3/5\n\n## 🎯 Modelo de Fracciones\n\n:::visual:fraction,3,5:::\n\n**3/5** = 3 partes de 5 partes totales\n\n## 📝 ¿Cómo sumar fracciones?\n\n**Regla:** Cuando el denominador es igual, **solo suma los numeradores**.\n\n### Ejemplo: 1/5 + 2/5\n\n- **Paso 1:** Los denominadores son iguales → **5** (no cambian)\n- **Paso 2:** Sumamos los numeradores → 1 + 2 = **3**\n- **Paso 3:** Respuesta → **3/5**\n\n:::visual:fraction,1,5:::\n:::visual:fraction,2,5:::\nSumando = 1/5 + 2/5 = **3/5**\n\n## 🧠 Casos especiales\n\n- 1/2 + 1/2 = 2/2 = **1** (¡un entero completo!)\n- 1/4 + 2/4 = 3/4\n- 1/3 + 1/3 = 2/3\n\n:::tryit:2/5 + 1/5|3/5|2 + 1 = 3 sobre 5:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-frac-suma-1-4-2-4", "1/4 + 2/4", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Cuánto es 1/4 + 2/4?", choices=["3/4","3/8","1/4"], correct="3/4"),
                            ex("3-frac-suma-1-3-1-3", "1/3 + 1/3", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Cuánto es 1/3 + 1/3?", choices=["2/6","2/3","1/3"], correct="2/3"),
                            ex("3-frac-suma-1-2-1-2", "1/2 + 1/2", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Cuánto es 1/2 + 1/2?", choices=["2/4","1","2/2"], correct="1"),
                        ],
                    },
                    {
                        "slug": "3-fracciones-comparar",
                        "title": "Comparar fracciones",
                        "description": "Determinar cuál fracción es mayor",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Comparar con igual denominador", "content": "# ⚖️ Comparar Fracciones con Igual Denominador\n\nCon igual denominador: **mayor numerador = mayor fracción**.\n\n## 🎯 Modelo de Comparación\n\n:::visual:comparison,3,5,1/5,3/5:::\n\n**3/5** es mayor que **1/5**.\n\n## 📝 Reglas para comparar fracciones\n\n### Regla 1: Igual denominador\n\nSi tienen el **mismo denominador**, el numerador mayor es la fracción mayor.\n\n> 3/5 > 1/5 porque 3 > 1\n\n### Regla 2: Igual numerador\n\nSi tienen el **mismo numerador**, el denominador menor es la fracción mayor.\n\n> 1/3 > 1/5 porque 3 < 5 (menos partes = más grande)\n\n## 🔑 Recuerda\n\n- **Denominador igual** → compara **numeradores**\n- **Numerador igual** → compara **denominadores**\n\n:::tryit:¿Qué es mayor, 3/5 o 1/5?|3/5|3 > 1:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-frac-comp-3-4-1-4", "¿3/4 o 1/4?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Qué fracción es mayor: 3/4 o 1/4?", choices=["3/4","1/4","son iguales"], correct="3/4"),
                            ex("3-frac-comp-2-3-1-3", "¿2/3 o 1/3?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Qué fracción es mayor: 2/3 o 1/3?", choices=["2/3","1/3","son iguales"], correct="2/3"),
                            ex("3-frac-comp-3-8-5-8", "¿3/8 o 5/8?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Qué fracción es mayor: 3/8 o 5/8?", choices=["3/8","5/8","son iguales"], correct="5/8"),
                        ],
                    },
                ],
            },
            {
                "slug": "3-perimetro-area",
                "title": "Perímetro y Área",
                "description": "Calcular perímetro y área de cuadrado y rectángulo",
                "icon_name": "📏",
                "units": [
                    {
                        "slug": "3-perimetro",
                        "title": "Perímetro",
                        "description": "Calcular el contorno de figuras",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Calcular perímetro", "content": "# 📏 Perímetro\n\nEl **perímetro** es la medida del **contorno** de una figura.\n\n## 📐 Fórmulas\n\n- **Cuadrado:** P = lado + lado + lado + lado = 4 × lado\n- **Rectángulo:** P = 2 × (largo + ancho)\n\n## 🎯 Ejemplo: Cuadrado de lado 6cm\n\n:::visual:array,6,6:::\n\n**Perímetro** = 6 + 6 + 6 + 6 = **24 cm**\n\n## 📏 Ejemplo: Rectángulo 8cm × 3cm\n\n:::visual:comparison,8,3,Largo,Ancho:::\n\n**Perímetro** = 2 × (8 + 3) = 2 × 11 = **22 cm**\n\n## 🧠 Recuerda\n\n- **Perímetro** → suma de todos los lados\n- La unidad es **cm, m, km** (longitud)\n\n:::tryit:Perímetro de un cuadrado de lado 6cm|24cm|6 × 4 = 24:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-perim-cuad-5", "Perímetro cuadrado", ExerciseType.numeric, Difficulty.easy, 10, "¿Perímetro de un cuadrado de lado 5cm?", correct="20", hints=["P = 4 × 5 = 20"]),
                            ex("3-perim-rect-8-3", "Perímetro rectángulo", ExerciseType.numeric, Difficulty.easy, 10, "Perímetro de rectángulo largo 8cm, ancho 3cm", correct="22", hints=["P = 2×(8+3) = 2×11 = 22"]),
                            ex("3-perim-trian-4-5-6", "Perímetro triángulo", ExerciseType.numeric, Difficulty.medium, 10, "Perímetro triángulo lados 4cm, 5cm, 6cm", correct="15", hints=["P = 4+5+6 = 15"]),
                        ],
                    },
                    {
                        "slug": "3-area",
                        "title": "Área",
                        "description": "Calcular la superficie interior",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Calcular área", "content": "# 🏠 Área\n\nEl **área** es la medida de la **superficie** dentro de una figura.\n\n## 📐 Fórmulas\n\n- **Cuadrado:** A = lado × lado\n- **Rectángulo:** A = largo × ancho\n\n## 🎯 Ejemplo: Cuadrado de lado 4cm\n\n:::visual:array,4,4:::\n\n4 × 4 = **16 cm²**\n\n## 📏 Ejemplo: Rectángulo 6cm × 3cm\n\n:::visual:array,6,3:::\n\n6 × 3 = **18 cm²**\n\n## 🔑 Diferencia entre Perímetro y Área\n\n| Concepto | Mide | Unidad |\n|----------|------|--------|\n| **Perímetro** | El contorno | cm, m |\n| **Área** | La superficie dentro | **cm², m²** |\n\n:::tryit:Área de un cuadrado de lado 4cm|16cm²|4 × 4 = 16:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-area-cuad-4", "Área cuadrado", ExerciseType.numeric, Difficulty.easy, 10, "Área de un cuadrado de lado 4cm", correct="16", hints=["A = 4 × 4 = 16"]),
                            ex("3-area-rect-6-3", "Área rectángulo", ExerciseType.numeric, Difficulty.easy, 10, "Área rectángulo largo 6cm, ancho 3cm", correct="18", hints=["A = 6 × 3 = 18"]),
                            ex("3-area-comp-4x4-vs-5x3", "Comparar áreas", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Qué área es mayor: 4×4 o 5×3?", choices=["4×4","5×3","son iguales"], correct="5×3", hints=["16 vs 15"]),
                        ],
                    },
                ],
            },
            {
                "slug": "3-datos",
                "title": "Estadística y Datos",
                "description": "Media, moda, tablas de frecuencia",
                "icon_name": "📊",
                "units": [
                    {
                        "slug": "3-media-moda",
                        "title": "Media y moda",
                        "description": "Calcular el promedio y la moda de un conjunto de datos",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Calcular la media", "content": "# 📊 La Media (Promedio)\n\n**Media** = suma de todos los valores ÷ cantidad de valores\n\n## 📏 Recta Numérica para entender\n\n:::visual:numberline,0,18,add:::\n\n## 🎯 Ejemplo: Calcular la media de 4, 6, 8\n\n**Paso 1:** Suma todos → 4 + 6 + 8 = **18**\n**Paso 2:** Cuenta cuántos números → son **3**\n**Paso 3:** Divide → 18 ÷ 3 = **6**\n\n:::visual:placevalue,6:::\n\nLa media es **6**.\n\n## 📝 Otro ejemplo\n\nCalificaciones: 7, 8, 9, 6\n- Suma: 7 + 8 + 9 + 6 = **30**\n- Cantidad: **4**\n- Media: 30 ÷ 4 = **7.5**\n\n## 🧠 Consejo\n\n> La media es el valor \"equitativo\" — si todos tuvieran lo mismo, ¿cuánto tendría cada uno?\n\n:::tryit:Media de 4, 6, 8|6|(4+6+8)÷3 = 18÷3 = 6:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("3-media-2-4-6", "Media de 3 números", ExerciseType.numeric, Difficulty.easy, 10, "Calcula la media: 2, 4, 6", correct="4", hints=["(2+4+6) ÷ 3 = 12 ÷ 3 = 4"]),
                            ex("3-media-5-10-15-20", "Media de 4 números", ExerciseType.numeric, Difficulty.medium, 10, "Calcula la media: 5, 10, 15, 20", correct="12.5", hints=["(5+10+15+20) ÷ 4 = 50 ÷ 4 = 12.5"]),
                            ex("3-moda-2-3-2-5-2", "Moda", ExerciseType.multiple_choice, Difficulty.easy, 10, "Datos: 2, 3, 2, 5, 2. ¿Cuál es la moda?", choices=["2","3","5"], correct="2", hints=["La moda es el valor que más se repite"]),
                        ],
                    },
                ],
            },
        ],
        4: [
            {
                "slug": "4-numeros-grandes",
                "title": "Números hasta Millions",
                "description": "Leer, escribir y comparar números hasta el millón",
                "icon_name": "🔢",
                "units": [
                    {
                        "slug": "4-millares",
                        "title": "Miles y millones",
                        "description": "Valor posicional hasta millones",
                        "order_index": 0,
                        "lessons": [
                            {"title": "El millón", "content": "# 🔢 El Millón\n\n1,000,000 = un millón\n\n## 🔢 Tabla de Valor Posicional\n\n:::visual:placevalue,1234567:::\n\n| Posición | Millones | Miles | Miles | Centenas | Decenas | Unidades |\n|----------|----------|-------|-------|----------|---------|----------|\n| Valor | 1,000,000 | 200,000 | 30,000 | 400 | 50 | 6 |\n\n## 📊 Comparación de tamaños\n\n:::visual:comparison,1,1000000,1,Millon:::\n\nUn millón es **1,000,000 veces más** que 1.\n\n## 🧠 Números grandes\n\n| Nombre | Cantidad de ceros | Ejemplo |\n|--------|-------------------|---------|\n| Decena | 1 | 10 |\n| Centena | 2 | 100 |\n| Millar | 3 | 1,000 |\n| Decena de millar | 4 | 10,000 |\n| **Millón** | **6** | **1,000,000** |\n\n:::tryit:¿Cuántas decenas de mil hay en 50,000?|5|50,000 ÷ 10,000 = 5:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("4-millares-4532", "Valor posicional", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Qué valor tiene el 5 en 453,200?", choices=["5,000","50,000","500,000"], correct="50,000"),
                            ex("4-millares-comparar", "Comparar números", ExerciseType.multiple_choice, Difficulty.medium, 10, "¿Cuál es mayor: 456,789 o 465,789?", choices=["456,789","465,789","son iguales"], correct="465,789"),
                        ],
                    },
                ],
            },
            {
                "slug": "4-fracciones-decimales",
                "title": "Fracciones y Decimales",
                "description": "Fracciones equivalentes, decimales hasta centésimas",
                "icon_name": "🍕",
                "units": [
                    {
                        "slug": "4-fracciones-equivalentes",
                        "title": "Fracciones equivalentes",
                        "description": "Encontrar y crear fracciones equivalentes",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Fracciones equivalentes", "content": "# 🔄 Fracciones Equivalentes\n\n**1/2 = 2/4 = 4/8** — Son fracciones que representan el mismo valor.\n\n## 🎯 Modelo de Fracciones\n\n:::visual:fraction,1,2:::\n**1/2** — la mitad\n:::visual:fraction,2,4:::\n**2/4** — también la mitad\n:::visual:fraction,4,8:::\n**4/8** — también la mitad\n\n¡Todas son **equivalentes** (iguales)!\n\n## 📝 Cómo encontrar fracciones equivalentes\n\n**Método 1:** Multiplica numerador y denominador por el mismo número.\n\n> 1/2 × 2/2 = **2/4**\n> 1/2 × 4/4 = **4/8**\n\n**Método 2:** Divide numerador y denominador por el mismo número.\n\n> 4/8 ÷ 2/2 = **2/4**\n> 2/4 ÷ 2/2 = **1/2**\n\n## 🔑 Regla de oro\n\n> **Lo que haces arriba (numerador), hazlo abajo (denominador).**\n\n:::tryit:¿Es 3/6 = 1/2?|Sí|3÷3=1, 6÷3=2 → 1/2:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("4-frac-equiv-1-2-2-4", "¿1/2 = 2/4?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Son equivalentes 1/2 y 2/4?", choices=["Sí","No"], correct="Sí"),
                            ex("4-frac-equiv-2-3-4-6", "¿2/3 = 4/6?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Son equivalentes 2/3 y 4/6?", choices=["Sí","No"], correct="Sí"),
                            ex("4-frac-equiv-3-5-6-10", "¿3/5 = 6/10?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Son equivalentes 3/5 y 6/10?", choices=["Sí","No"], correct="Sí"),
                        ],
                    },
                    {
                        "slug": "4-decimales-intro",
                        "title": "Introducción a decimales",
                        "description": "Décimas y centésimas, leer y escribir decimales",
                        "order_index": 1,
                        "lessons": [
                            {"title": "¿Qué es un decimal?", "content": "# 🔢 Decimales\n\n0.1 = una décima = 1/10\n0.01 = una centésima = 1/100\n\n## 🔢 Tabla de Valor Posicional\n\n:::visual:placevalue,354:::\n\nEl **3** vale 300. El **5** vale 50. El **4** vale 4.\n\n## 🎯 Décimas y Centésimas\n\n:::visual:fraction,5,10:::\n\n**0.5** = cinco décimas = **5/10** = **1/2**\n\n## 📝 Conversiones\n\n| Decimal | Fracción | Significado |\n|---------|-----------|-------------|\n| 0.1 | 1/10 | una décima |\n| 0.5 | 5/10 | cinco décimas |\n| 0.01 | 1/100 | una centésima |\n| 0.25 | 25/100 | veinticinco centésimas |\n\n## 🧠 Recuerda\n\n> El **punto decimal** (.) separa las unidades de las décimas.\n> 3.5 = 3 unidades y 5 décimas\n\n:::tryit:0.5 en fracción|1/2|0.5 = 5/10 = 1/2:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("4-dec-0-3-frac", "Decimal a fracción", ExerciseType.multiple_choice, Difficulty.easy, 10, "0.3 =", choices=["3/10","3/100","30/10"], correct="3/10"),
                            ex("4-dec-0-75-frac", "0.75 en fracción", ExerciseType.multiple_choice, Difficulty.medium, 10, "0.75 =", choices=["75/100","75/1000","7/5"], correct="75/100"),
                            ex("4-dec-comparar-0-4-0-6", "Comparar decimales", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Cuál es mayor: 0.4 o 0.6?", choices=["0.4","0.6","son iguales"], correct="0.6"),
                        ],
                    },
                ],
            },
            {
                "slug": "4-operaciones",
                "title": "Operaciones Combinadas",
                "description": "Suma, resta, multiplicación y división combinadas, reglas de prioridad",
                "icon_name": "🧮",
                "units": [
                    {
                        "slug": "4-orden-operaciones",
                        "title": "Orden de operaciones",
                        "description": "PEMDAS: paréntesis, exponentes, multiplicación, división, suma, resta",
                        "order_index": 0,
                        "lessons": [
                            {"title": "PEMDAS", "content": "# 🧮 Orden de Operaciones (PEMDAS)\n\n**P**aréntesis → **E**xponentes → **M**ultiplicación → **D**ivisión → **A**dición → **S**ustracción\n\n## 📝 ¿Por qué es importante el orden?\n\n3 + 4 × 2 = ?\n\n- ❌ Si sumas primero: (3 + 4) × 2 = 7 × 2 = **14**\n- ✅ Si multiplicas primero: 3 + (4 × 2) = 3 + 8 = **11**\n\n## 🎯 Ejemplo con pasos animados\n\n:::steps:Primero paréntesis|No hay paréntesis aquí:::Multiplicación: 4 × 2|4 × 2 = 8:::Suma: 3 + 8|3 + 8 = 11:::\n\n## 🧠记忆 **PEMDAS**\n\n> **P**lease **E**xcuse **M**y **D**ear **A**unt **S**ally\n\nCada letra = un paso en orden.\n\n:::tryit:5 + 3 × 2|11|3 × 2 = 6, luego 5 + 6 = 11:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("4-orden-3-4x2", "3 + 4 × 2", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 3 + 4 × 2?", correct="11", hints=["Primero 4×2=8, luego 3+8=11"]),
                            ex("4-orden-parentesis", "(3+4)×2", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es (3 + 4) × 2?", correct="14", hints=["Primero paréntesis: 3+4=7, luego 7×2=14"]),
                            ex("4-orden-2-3x4-1", "2 + 3 × 4 - 1", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 2 + 3 × 4 - 1?", correct="13", hints=["3×4=12, 2+12-1=13"]),
                        ],
                    },
                ],
            },
            {
                "slug": "4-angulos",
                "title": "Ángulos",
                "description": "Medir y clasificar ángulos: agudo, recto, obtuso",
                "icon_name": "📐",
                "units": [
                    {
                        "slug": "4-angulos-intro",
                        "title": "Clasificación de ángulos",
                        "description": "Ángulos agudos, rectos y obtusos",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Tipos de ángulos", "content": "# 📐 Tipos de Ángulos\n\n**Agudo** < 90° | **Recto** = 90° | **Obtuso** > 90°\n\n## 🎯 Usa el Transportador\n\n:::visual:protractor,45:::\n**45°** → **Agudo** (menos de 90°)\n\n## 📐 Clasificación visual\n\n### Ángulo Agudo (< 90°)\n:::visual:anglemaker,45:::\n**45°** — es agudo\n\n### Ángulo Recto (= 90°)\n:::visual:anglemaker,90:::\n**90°** — ángulo recto\n\n### Ángulo Obtuso (> 90°)\n:::visual:anglemaker,120:::\n**120°** — obtuso\n\n## 🔑 Recuerda\n\n| Tipo | Medida | Ejemplo |\n|------|--------|---------|\n| **Agudo** | < 90° | 30°, 45°, 60° |\n| **Recto** | = 90° | 90° |\n| **Obtuso** | > 90° | 120°, 150° |\n\n:::tryit:¿Qué tipo es 45°?|Agudo|45° < 90°:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("4-angulo-45", "Ángulo de 45°", ExerciseType.multiple_choice, Difficulty.easy, 10, "45° es un ángulo:", choices=["Agudo","Recto","Obtuso"], correct="Agudo"),
                            ex("4-angulo-90", "Ángulo de 90°", ExerciseType.multiple_choice, Difficulty.easy, 10, "90° es un ángulo:", choices=["Agudo","Recto","Obtuso"], correct="Recto"),
                            ex("4-angulo-120", "Ángulo de 120°", ExerciseType.multiple_choice, Difficulty.easy, 10, "120° es un ángulo:", choices=["Agudo","Recto","Obtuso"], correct="Obtuso"),
                            ex("4-angulo-complementario", "Complementario", ExerciseType.multiple_choice, Difficulty.medium, 10, "Si un ángulo mide 30°, ¿cuál es su complementario?", choices=["30°","60°","90°"], correct="60°", explanation="30° + 60° = 90°"),
                        ],
                    },
                ],
            },
            {
                "slug": "4-datos-avanzado",
                "title": "Estadística Avanzada",
                "description": "Rango, mediana, diagrams de línea",
                "icon_name": "📊",
                "units": [
                    {
                        "slug": "4-rango-mediana",
                        "title": "Rango y mediana",
                        "description": "Calcular rango y mediana de un conjunto de datos",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Rango y mediana", "content": "# 📊 Rango y Mediana\n\n**Rango** = mayor - menor\n**Mediana** = valor del medio (ordenado de menor a mayor)\n\n## 📏 Recta Numérica para entender el rango\n\n:::visual:numberline,0,9,add:::\n\n## 🎯 Ejemplo: Datos 3, 8, 2, 9, 1\n\n### Mediana (valor del medio)\n\n**Paso 1:** Ordenar de menor a mayor → 1, 2, **3**, 8, 9\n**Paso 2:** El valor del medio es → **3**\n\n### Rango (diferencia)\n\n**Paso 1:** El mayor = **9**\n**Paso 2:** El menor = **1**\n**Paso 3:** 9 - 1 = **8**\n\n## 📝 Fórmulas\n\n| Concepto | Fórmula | Ejemplo |\n|----------|---------|---------|\n| **Rango** | mayor - menor | 9 - 1 = 8 |\n| **Mediana** | valor del medio | 3 |\n\n## 🧠 Consejo\n\n> Para la **mediana**: cuenta el mismo número de valores a la izquierda y derecha del centro.\n\n:::tryit:Mediana de 3, 8, 2, 9, 1|3|Ordena: 1,2,3,8,9 → el del medio es 3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("4-rango-3-5-8-2-9", "Rango", ExerciseType.numeric, Difficulty.easy, 10, "Calcula el rango: 3, 5, 8, 2, 9", correct="7", hints=["Mayor=9, menor=2, 9-2=7"]),
                            ex("4-mediana-ord-1-3-7-9", "Mediana (impar)", ExerciseType.numeric, Difficulty.easy, 10, "Datos ordenados: 1, 3, 7, 9. ¿Mediana?", correct="5", hints=["Mediana = (3+7)÷2 = 5"], explanation="Hay 4 datos, la mediana es el promedio de los dos del medio"),
                        ],
                    },
                ],
            },
        ],
        5: [
            {
                "slug": "5-decimales",
                "title": "Decimales",
                "description": "Operaciones con decimales: suma, resta, multiplicación, división",
                "icon_name": "🔢",
                "units": [
                    {
                        "slug": "5-decimales-op",
                        "title": "Operaciones con decimales",
                        "description": "Sumar, restar, multiplicar y dividir decimales",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Sumar decimales", "content": "# ➕ Sumar Decimales\n\n3.5 + 2.3 = 5.8\n\n## 🔑 Regla más importante\n\n**Alinea los puntos decimales** antes de sumar.\n\n## 📏 Recta Numérica para decimales\n\n:::visual:numberline,0,35,add:::\n\n## 🎯 Ejemplo: 3.5 + 2.3\n\n```\n  3 . 5\n+ 2 . 3\n--------\n  5 . 8\n```\n\n**Paso 1:** Suma las décimas → 5 + 3 = **8**\n**Paso 2:** Suma las unidades → 3 + 2 = **5**\n**Paso 3:** El punto decimal queda **entre** 5 y 8\n\n## 📝 Otro ejemplo: 12.4 + 5.2\n\n```\n  12 . 4\n+  5 . 2\n---------\n  17 . 6\n```\n\n:::tryit:4.2 + 3.1|7.3|4.2 + 3.1 = 7.3:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("5-dec-suma-3-5-2-3", "3.5 + 2.3", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 3.5 + 2.3?", correct="5.8", hints=["5 + 2 = 7, 0.5 + 0.3 = 0.8"]),
                            ex("5-dec-suma-12-4-5-2", "12.4 + 5.2", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 12.4 + 5.2?", correct="17.6", hints=["12+5=17, 0.4+0.2=0.6"]),
                            ex("5-dec-resta-9-5-3-2", "9.5 - 3.2", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es 9.5 - 3.2?", correct="6.3", hints=["9-3=6, 0.5-0.2=0.3"]),
                            ex("5-dec-multi-2-5-x-3", "2.5 × 3", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 2.5 × 3?", correct="7.5", hints=["2.5 × 3 = 7.5"]),
                        ],
                    },
                ],
            },
            {
                "slug": "5-porcentajes",
                "title": "Porcentajes",
                "description": "Calcular porcentajes, equivalencia con fracciones y decimales",
                "icon_name": "📈",
                "units": [
                    {
                        "slug": "5-porcentaje-intro",
                        "title": "¿Qué es el porcentaje?",
                        "description": " Relacionar porcentajes con fracciones y decimales",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Porcentaje a fracción", "content": "# 📈 Porcentajes\n\n**50% = 50/100 = 1/2**\n**25% = 25/100 = 1/4**\n\n## 🎯 Modelo de Fracciones\n\n:::visual:fraction,1,2:::\n**50%** = 1/2 = la mitad\n\n:::visual:fraction,1,4:::\n**25%** = 1/4 = un cuarto\n\n## 📝 Cómo convertir porcentaje a fracción\n\n| Porcentaje | División | Fracción simplificada |\n|------------|-----------|----------------------|\n| 50% | 50/100 | 1/2 |\n| 25% | 25/100 | 1/4 |\n| 10% | 10/100 | 1/10 |\n| 75% | 75/100 | 3/4 |\n\n## 🧠 Consejo\n\n> **%** significa \"entre 100\"\n> 50% = 50/100 = divide numerator y denominador por 50 → **1/2**\n\n:::tryit:¿Qué fracción es 25%?|1/4|25÷25=1, 100÷25=4:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("5-pct-50-frac", "50% a fracción", ExerciseType.multiple_choice, Difficulty.easy, 10, "50% =", choices=["1/2","1/4","1/5"], correct="1/2"),
                            ex("5-pct-25-frac", "25% a fracción", ExerciseType.multiple_choice, Difficulty.easy, 10, "25% =", choices=["1/4","1/3","1/5"], correct="1/4"),
                            ex("5-pct-10-frac", "10% a fracción", ExerciseType.multiple_choice, Difficulty.easy, 10, "10% =", choices=["1/10","1/5","1/8"], correct="1/10"),
                            ex("5-pct-30-200", "30% de 200", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es el 30% de 200?", correct="60", hints=["200 × 0.30 = 60"]),
                        ],
                    },
                ],
            },
            {
                "slug": "5-proporciones",
                "title": "Proporciones y Razones",
                "description": "Razones, proporciones, regla de tres simple",
                "icon_name": "⚖️",
                "units": [
                    {
                        "slug": "5-razones",
                        "title": "Razones",
                        "description": "Expresar relaciones como razones",
                        "order_index": 0,
                        "lessons": [
                            {"title": "¿Qué es una razón?", "content": "# ⚖️ Razones\n\nLa **razón** expresa una relación entre dos cantidades.\n\n## 📊 Barras de Comparación\n\n:::visual:comparison,3,2,Azules,Rojos:::\n\n**3:2** → 3 azules por cada 2 rojos\n\n## 📝 ¿Cómo se escribe una razón?\n\nSe escribe con **dos puntos**:\n- **3:2** significa \"3 a 2\"\n- Azul:Rojo = 3:2\n\n## 🔄 Simplificar razones\n\n**Ejemplo:** 6 azules y 4 rojos\n\n6:4 = dividimos entre 2 → **3:2**\n\n| Original | Simplificada |\n|----------|-------------|\n| 6:4 | 3:2 |\n| 8:12 | 2:3 |\n| 10:5 | 2:1 |\n\n## 🧠 Consejo\n\n> Las razones son como **fracciones** — puedes simplificarlas dividiendo por el mismo número.\n\n:::tryit:Si hay 6 azules y 4 rojos, ¿cuál es la razón?|3:2|6÷2=3, 4÷2=2:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("5-razon-6-4", "Razón simplificada", ExerciseType.multiple_choice, Difficulty.easy, 10, "Si hay 6 azules y 4 rojos, la razón azules:rojos simplificada es:", choices=["3:2","6:4","2:3"], correct="3:2"),
                            ex("5-razon-8-12", "Razón simplificada 8:12", ExerciseType.multiple_choice, Difficulty.easy, 10, "Simplifica la razón 8:12", choices=["2:3","4:6","1:2"], correct="2:3"),
                        ],
                    },
                    {
                        "slug": "5-regla-tres",
                        "title": "Regla de tres simple",
                        "description": "Resolver problemas de proporcionalidad",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Regla de tres", "content": "# ⚖️ Regla de Tres\n\nSi 4 lápices cuestan 12 bs, ¿cuánto cuestan 6?\n\n## 📊 Barras de Comparación\n\n:::visual:comparison,4,6,4 lápices,6 lápices:::\n\n## 📝 Cómo aplicar la Regla de Tres\n\n**Paso 1:** Identifica la proporción\n> Si 4 lápices → 12 bs\n> Entonces 6 lápices → ? bs\n\n**Paso 2:** Calcula el precio por unidad\n> 12 bs ÷ 4 lápices = **3 bs por lápiz**\n\n**Paso 3:** Multiplica\n> 6 lápices × 3 bs = **18 bs**\n\n## 🧠 Fórmula\n\n> **?** = (6 × 12) ÷ 4 = 72 ÷ 4 = **18**\n\n## 📊 Tabla de proporción\n\n| Lápices | Precio (bs) |\n|---------|-------------|\n| 4 | 12 |\n| 6 | 18 |\n| 8 | 24 |\n| 10 | 30 |\n\n:::tryit:Si 5 libros cuestan 100 bs, ¿cuánto cuestan 8?|160 bs|100÷5=20, 20×8=160:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("5-regla-3-4-12-6", "Regla de tres", ExerciseType.numeric, Difficulty.medium, 15, "Si 4 lpices cuestan 12 bs, ¿cuánto cuestan 6?", correct="18", hints=["? = 6 × 12 ÷ 4 = 18"]),
                            ex("5-regla-3-5-100-8", "Regla de tres libros", ExerciseType.numeric, Difficulty.medium, 15, "Si 5 libros cuestan 100 bs, ¿cuánto cuestan 8?", correct="160", hints=["8 × 100 ÷ 5 = 160"]),
                        ],
                    },
                ],
            },
            {
                "slug": "5-areas-triangulos",
                "title": "Área de Triángulos",
                "description": "Fórmula del área de triángulos",
                "icon_name": "📐",
                "units": [
                    {
                        "slug": "5-area-triangulo",
                        "title": "Área del triángulo",
                        "description": "Calcular área usando (base × altura) / 2",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Fórmula del área", "content": "# 📐 Área del Triángulo\n\n**A = (base × altura) ÷ 2**\n\n## 📐 Modelo del Triángulo\n\n:::visual:anglemaker,60:::\n\nLa **altura** es perpendicular a la base.\n\n## 🎯 Ejemplo: Base = 8cm, Altura = 5cm\n\n**Paso 1:** Multiplica base × altura\n> 8 × 5 = **40**\n\n**Paso 2:** Divide entre 2\n> 40 ÷ 2 = **20 cm²**\n\n## 📝 Fórmula paso a paso\n\n| Paso | Operación | Resultado |\n|------|-----------|-----------|\n| 1 | 8 × 5 | 40 |\n| 2 | 40 ÷ 2 | **20 cm²** |\n\n## 🧠 ¿Por qué se divide entre 2?\n\nPorque un triángulo es **mitad de un rectángulo**.\n\n:::tryit:Base 8cm, altura 5cm|20cm²|(8×5)÷2 = 20:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("5-area-tri-8-5", "Triángulo 8×5", ExerciseType.numeric, Difficulty.easy, 10, "Base 8cm, altura 5cm. ¿Área?", correct="20", hints=["(8×5)÷2 = 40÷2 = 20"]),
                            ex("5-area-tri-10-6", "Triángulo 10×6", ExerciseType.numeric, Difficulty.easy, 10, "Base 10cm, altura 6cm. ¿Área?", correct="30", hints=["(10×6)÷2 = 60÷2 = 30"]),
                            ex("5-area-tri-12-9", "Triángulo 12×9", ExerciseType.numeric, Difficulty.medium, 10, "Base 12cm, altura 9cm. ¿Área?", correct="54", hints=["(12×9)÷2 = 108÷2 = 54"]),
                        ],
                    },
                ],
            },
            {
                "slug": "5-volumen",
                "title": "Volumen",
                "description": "Calcular volumen de prismas rectangulares",
                "icon_name": "📦",
                "units": [
                    {
                        "slug": "5-volumen-prisma",
                        "title": "Volumen del prisma rectangular",
                        "description": "V = largo × ancho × alto",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Volumen", "content": "# 📦 Volumen\n\n**V = largo × ancho × alto**\n\n## 📦 ¿Qué es el volumen?\n\nEl volumen mide **cuánto cabe** dentro de un objeto 3D.\n\n## 🎯 Ejemplo: Prisma de 3cm × 4cm × 5cm\n\n**Paso 1:** 3 × 4 = **12** (área de la base)\n**Paso 2:** 12 × 5 = **60 cm³**\n\n## 📊 Capas del prisma\n\n:::visual:array,3,4:::\n\n**Base** = 3 × 4 = **12 cm²**\n\nMultiplicamos por 5 capas → **12 × 5 = 60 cm³**\n\n## 🧠 Unidades de volumen\n\n| Unidad | Significado |\n|--------|-------------|\n| cm³ | centímetro cúbico |\n| m³ | metro cúbico |\n| km³ | kilómetro cúbico |\n\n## 📝 Fórmula resumen\n\n> **V = largo × ancho × alto**\n\n:::tryit:3cm × 4cm × 5cm|60cm³|3×4×5 = 60:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("5-vol-prisma-3-4-5", "Prisma 3×4×5", ExerciseType.numeric, Difficulty.easy, 10, "Largo 3cm, ancho 4cm, alto 5cm. ¿Volumen?", correct="60", hints=["3×4×5 = 60"]),
                        ],
                    },
                ],
            },
        ],
        6: [
            {
                "slug": "6-negativos",
                "title": "Números Negativos",
                "description": "Introducción a enteros negativos, compararlos y operarlos",
                "icon_name": "🔢",
                "units": [
                    {
                        "slug": "6-negativos-intro",
                        "title": "Números negativos",
                        "description": "Entender la recta numérica con negativos",
                        "order_index": 0,
                        "lessons": [
                            {"title": "En la recta numérica", "content": "# 🔢 Números Negativos\n\nLos negativos están a la **izquierda del 0**.\n-5, -4, -3, -2, -1, **0**, 1, 2...\n\n## 📏 Recta Numérica con Negativos\n\n:::visual:numberline,0,-5,add:::\n\nDesde **0**, retrocedemos 5 → llegamos a **-5**\n\n## 🔑 Reglas para comparar negativos\n\n| Comparación | Significado |\n|-------------|-------------|\n| -3 > -5 | -3 está más a la derecha (es mayor) |\n| -1 > -3 | -1 está más cerca del 0 |\n| -5 < -1 | -5 es menor (más a la izquierda) |\n\n## 📝 Orden en la recta numérica\n\n**De menor a mayor:**\n> -5 < -3 < -1 < 0 < 1 < 3 < 5\n\n**De mayor a menor:**\n> 5 > 3 > 1 > 0 > -1 > -3 > -5\n\n:::tryit:¿Qué número es mayor, -3 o -1?|-1|-1 está más cerca del 0:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-neg-mayor-3-1", "¿Qué es mayor -3 o -1?", ExerciseType.multiple_choice, Difficulty.easy, 10, "¿Qué número es mayor: -3 o -1?", choices=["-3","-1","son iguales"], correct="-1", hints=["-1 está más cerca del 0"]),
                            ex("6-neg-ordenar", "Ordenar negativos", ExerciseType.multiple_choice, Difficulty.easy, 10, "Ordena de menor a mayor: -5, 2, -1, 0", choices=["-5,-1,0,2","2,0,-1,-5","-1,-5,0,2"], correct="-5,-1,0,2"),
                            ex("6-neg-suma-5-neg3", "-5 + (-3)", ExerciseType.numeric, Difficulty.easy, 10, "¿Cuánto es -5 + (-3)?", correct="-8", hints=["-5 + -3 = -8"]),
                            ex("6-neg-resta-2-neg5", "2 - (-5)", ExerciseType.numeric, Difficulty.medium, 10, "¿Cuánto es 2 - (-5)?", correct="7", hints=["Restar negativo = sumar"]),
                        ],
                    },
                ],
            },
            {
                "slug": "6-razones-velocidad",
                "title": "Razones, Tasas y Velocidad",
                "description": "Razones complejas, tasas unitarias, velocidad = distancia/tiempo",
                "icon_name": "⚖️",
                "units": [
                    {
                        "slug": "6-velocidad",
                        "title": "Velocidad",
                        "description": "Velocidad = distancia ÷ tiempo",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Velocidad constante", "content": "# 🚗 Velocidad\n\n**Velocidad = Distancia ÷ Tiempo**\n\n## 📊 Barras de Comparación\n\n:::visual:comparison,120,60,Distancia (km),Velocidad (km/h):::\n\n## 🎯 Ejemplo: 120km en 2 horas\n\n**Fórmula:** Velocidad = Distancia ÷ Tiempo\n\n> 120 km ÷ 2 h = **60 km/h**\n\n## 📝 Tabla de velocidad\n\n| Distancia | Tiempo | Velocidad |\n|-----------|--------|-----------|\n| 120 km | 2 h | 60 km/h |\n| 150 km | 3 h | 50 km/h |\n| 200 km | 4 h | 50 km/h |\n| 80 km | 1 h | 80 km/h |\n\n## 🧠 Consejo\n\n> **Velocidad constante** = la velocidad no cambia.\n> Si vas a 60 km/h, cada hora recorres 60 km.\n\n:::tryit:150km en 3h|50km/h|150÷3 = 50:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-velocidad-120-2", "120km en 2h", ExerciseType.multiple_choice, Difficulty.easy, 10, "Un auto viaja 120km en 2h. ¿Velocidad?", choices=["50 km/h","60 km/h","120 km/h"], correct="60 km/h", hints=["120 ÷ 2 = 60"]),
                            ex("6-velocidad-200-4", "200km en 4h", ExerciseType.numeric, Difficulty.easy, 10, "Un auto viaja 200km en 4h. ¿Velocidad?", correct="50", hints=["200 ÷ 4 = 50"]),
                            ex("6-velocidad-dist-tiempo", "Distancia", ExerciseType.numeric, Difficulty.medium, 10, "Un tren a 80 km/h viaja 3h. ¿Distancia?", correct="240", hints=["80 × 3 = 240 km"]),
                        ],
                    },
                ],
            },
            {
                "slug": "6-proporcionalidad",
                "title": "Proporcionalidad Compleja",
                "description": "Proporciones directas e inversas, problemas de proporcionalidad",
                "icon_name": "⚖️",
                "units": [
                    {
                        "slug": "6-prop-inversa",
                        "title": "Proporcionalidad inversa",
                        "description": "Cuando al aumentar una magnitud la otra disminuye",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Relación inversa", "content": "# ⚖️ Proporcionalidad Inversa\n\nCuando **aumenta** una magnitud, la otra **disminuye**.\n\n## 📊 Comparación: Trabajadores vs Días\n\n:::visual:comparison,3,6,3 trabajadores,6 trabajadores:::\n\n**3 trabajadores** → 6 días\n**6 trabajadores** → 3 días\n\n## 🎯 Ejemplo: 3 trabajadores en 6 días\n\n**Regla:** 3 × 6 = trabajo total\n\n| Trabajadores | Días | Comprobación |\n|-------------|------|-------------|\n| 3 | 6 | 3 × 6 = 18 |\n| 6 | 3 | 6 × 3 = 18 |\n| 9 | 2 | 9 × 2 = 18 |\n\n## 🔑 Fórmula de proporcionalidad inversa\n\n> **Trabajo total = trabajadores × días**\n> Si 4 × 8 = 32, entonces 8 trabajadores → 32 ÷ 8 = **4 días**\n\n:::tryit:Si 4 trabajadores hacen obra en 8 días, ¿en cuántos días la hacen 8 trabajadores?|4 días|4×8=32, 32÷8=4:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-prop-inv-4-8-8", "4→8 días, 8→?", ExerciseType.numeric, Difficulty.medium, 15, "Si 4 trabajadores hacen una obra en 8 días, ¿en cuántos días la hacen 8 trabajadores?", correct="4", hints=["Trabajo total = 4×8=32, 32÷8=4"]),
                        ],
                    },
                ],
            },
            {
                "slug": "6-areas-poligonos",
                "title": "Áreas de Polígonos",
                "description": "Área de paralelogramo, rombo, trapecio",
                "icon_name": "📐",
                "units": [
                    {
                        "slug": "6-area-paralelogramo",
                        "title": "Área del paralelogramo",
                        "description": "A = base × altura",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Paralelogramo", "content": "# 📐 Área del Paralelogramo\n\n**A = base × altura**\n\n## 📐 Modelo de Paralelogramo\n\n:::visual:anglemaker,60:::\n\nLa **altura** es perpendicular (forma 90°) a la base.\n\n## 🎯 Ejemplo: Base = 10cm, Altura = 6cm\n\n**Fórmula:** A = base × altura\n> 10 × 6 = **60 cm²**\n\n## 📝 ¿Por qué es igual que el rectángulo?\n\nSi cortas un triángulo de un lado del paralelogramo y lo pones en el otro, ¡se convierte en un rectángulo!\n\n:::visual:array,6,10:::\n\n**Base × Altura** = 10 × 6 = **60 cm²**\n\n:::tryit:Base 10cm, altura 6cm|60cm²|10 × 6 = 60:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-area-par-10-6", "Paralelogramo 10×6", ExerciseType.numeric, Difficulty.easy, 10, "Base 10cm, altura 6cm. ¿Área?", correct="60", hints=["10×6 = 60"]),
                            ex("6-area-par-8-5", "Paralelogramo 8×5", ExerciseType.numeric, Difficulty.easy, 10, "Base 8cm, altura 5cm. ¿Área?", correct="40", hints=["8×5 = 40"]),
                        ],
                    },
                    {
                        "slug": "6-area-trapecio",
                        "title": "Área del trapecio",
                        "description": "A = ((b1 + b2) × h) ÷ 2",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Trapecio", "content": "# 📐 Área del Trapecio\n\n**A = ((base₁ + base₂) × altura) ÷ 2**\n\n## 📐 Modelo de Trapecio\n\n:::visual:anglemaker,60:::\n\nUn trapecio tiene **2 bases** (paralelas) y **1 altura**.\n\n## 🎯 Ejemplo: Base₁ = 8cm, Base₂ = 4cm, Altura = 5cm\n\n**Paso 1:** Suma las bases → 8 + 4 = **12**\n**Paso 2:** Multiplica por la altura → 12 × 5 = **60**\n**Paso 3:** Divide entre 2 → 60 ÷ 2 = **30 cm²**\n\n## 📝 Tabla resumen\n\n| Paso | Operación | Resultado |\n|------|-----------|-----------|\n| 1 | 8 + 4 | 12 |\n| 2 | 12 × 5 | 60 |\n| 3 | 60 ÷ 2 | **30 cm²** |\n\n## 🧠 Recuerda\n\n> Un trapecio es como dos rectángulos pegados.\n> Por eso dividimos entre 2.\n\n:::tryit:b1=8, b2=4, h=5|(8+4)×5÷2 = 30cm²|(12×5)÷2 = 30:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-area-trap-8-4-5", "Trapecio 8-4-5", ExerciseType.numeric, Difficulty.medium, 10, "Bases 8cm y 4cm, altura 5cm. ¿Área?", correct="30", hints=["((8+4)×5)÷2 = 60÷2 = 30"]),
                        ],
                    },
                ],
            },
            {
                "slug": "6-estadistica",
                "title": "Estadística Avanzada",
                "description": "Desviación estándar intro, diagramas de caja, probabilidad básica",
                "icon_name": "📊",
                "units": [
                    {
                        "slug": "6-probabilidad",
                        "title": "Probabilidad básica",
                        "description": "Espacio muestral, eventos, probabilidad simple",
                        "order_index": 0,
                        "lessons": [
                            {"title": "¿Qué es la probabilidad?", "content": "# 🎲 Probabilidad\n\n**P = casos favorables ÷ casos posibles**\n\n## 🎯 Modelo de Fracciones para Probabilidad\n\n:::visual:fraction,1,6:::\n\n**P(5)** = 1 caso favorable ÷ 6 casos posibles = **1/6**\n\n## 📝 Ejemplos\n\n### Lanzar un dado (6 caras)\n\n| Evento | Casos favorables | Casos posibles | Probabilidad |\n|--------|-----------------|----------------|-------------|\n| Sacar 5 | 1 | 6 | 1/6 |\n| Sacar número par | 3 | 6 | 3/6 = 1/2 |\n| Sacar 7 | 0 | 6 | 0 |\n\n### Lanzar una moneda (2 caras)\n\n:::visual:division,1,2:::\n\n**P(cara)** = 1 ÷ 2 = **1/2**\n\n## 🧠 Reglas de la probabilidad\n\n> - La probabilidad siempre está entre **0 y 1**\n> **0** = imposible | **1** = seguro\n> P = 0.5 = 1/2 = 50%\n\n:::tryit:Moneda: P(cara)|1/2|1÷2 = 1/2:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-prob-dado-4", "P(4) en dado", ExerciseType.multiple_choice, Difficulty.easy, 10, "Al lanzar un dado, ¿cuál es la probabilidad de sacar 4?", choices=["1/6","1/4","1/2"], correct="1/6"),
                            ex("6-prob-esfera-3-8", "Esfera 3 de 8", ExerciseType.multiple_choice, Difficulty.easy, 10, "Urna con 8 esferas, 3 rojas. ¿P(roja)?", choices=["3/8","3/5","5/8"], correct="3/8"),
                            ex("6-prob-cara-sello", "Moneda cara", ExerciseType.multiple_choice, Difficulty.easy, 10, "Lanzar moneda. ¿P(cara)?", choices=["1/2","1/3","1/4"], correct="1/2"),
                        ],
                    },
                ],
            },
            {
                "slug": "6-algebra-intro",
                "title": "Introducción al Álgebra",
                "description": "Expresiones algebraicas, resolver ecuaciones simples",
                "icon_name": "🔢",
                "units": [
                    {
                        "slug": "6-expresiones",
                        "title": "Expresiones algebraicas",
                        "description": "Variables, términos, simplificar expresiones",
                        "order_index": 0,
                        "lessons": [
                            {"title": "Variables y expresiones", "content": "# 🔢 Expresiones Algebraicas\n\n**x + 5** significa \"un número más 5\"\n\n## 🔢 La variable es como una caja\n\n:::visual:placevalue,5:::\n\nLa **x** es como una caja que puede contener cualquier número.\n\n## 📝 ¿Qué significa x + 5?\n\n| Si x = ... | Entonces x + 5 = ... |\n|------------|----------------------|\n| x = 1 | 1 + 5 = 6 |\n| x = 3 | 3 + 5 = 8 |\n| x = 10 | 10 + 5 = 15 |\n\n## 🔑 Expresiones comunes\n\n| Expresión | Significado |\n|-----------|-------------|\n| x + 5 | x más 5 |\n| 2x | 2 veces x |\n| x - 3 | x menos 3 |\n| x ÷ 2 | x entre 2 |\n\n:::tryit:Si x = 3, ¿cuánto es x + 5?|8|3 + 5 = 8:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-alge-x-3-mas-5", "x + 5 si x=3", ExerciseType.numeric, Difficulty.easy, 10, "Si x = 3, ¿cuánto es x + 5?", correct="8", hints=["3 + 5 = 8"]),
                            ex("6-alge-2x-menos-1-x-4", "2x - 1 si x=4", ExerciseType.numeric, Difficulty.easy, 10, "Si x = 4, ¿cuánto es 2x - 1?", correct="7", hints=["2×4 - 1 = 8 - 1 = 7"]),
                            ex("6-alge-simplificar", "Simplificar 3x + 2x", ExerciseType.multiple_choice, Difficulty.easy, 10, "Simplifica: 3x + 2x", choices=["5x","6x","5x²"], correct="5x", hints=["3x + 2x = 5x"]),
                        ],
                    },
                    {
                        "slug": "6-ecuaciones-1",
                        "title": "Ecuaciones de primer grado",
                        "description": "Resolver x + a = b y ax = b",
                        "order_index": 1,
                        "lessons": [
                            {"title": "Resolver x + a = b", "content": "# 🔢 Resolver Ecuaciones: x + a = b\n\n**x + 7 = 12**\n**x = 12 - 7**\n**x = 5**\n\n## 📏 En la Recta Numérica\n\n:::visual:numberline,0,12,add:::\n\nPara encontrar x, pensamos: \"¿desde dónde partimos para llegar a 12?\"\n\n## 🔑 Pasos para resolver\n\n**Regla de oro:** Lo que haces a un lado, hazlo al otro.\n\n### Ejemplo: x + 3 = 10\n\n**Paso 1:** Identifica la operación → **+3**\n**Paso 2:** Haz la operación inversa → **-3**\n**Paso 3:** Aplica a ambos lados:\n> x + 3 - 3 = 10 - 3\n> **x = 7**\n\n## 📝 Verificación\n\n> x + 3 = 10 → 7 + 3 = 10 ✅\n\n:::tryit:x + 3 = 10|x = 7|x = 10 - 3 = 7:::", "order_index": 0},
                        ],
                        "exercises": [
                            ex("6-ecuacion-x-mas-3-10", "x + 3 = 10", ExerciseType.multiple_choice, Difficulty.easy, 10, "Resuelve: x + 3 = 10", choices=["x=5","x=6","x=7"], correct="x=7"),
                            ex("6-ecuacion-3x-12", "3x = 12", ExerciseType.multiple_choice, Difficulty.easy, 10, "Resuelve: 3x = 12", choices=["x=2","x=3","x=4"], correct="x=4"),
                            ex("6-ecuacion-x-5-8", "x - 5 = 8", ExerciseType.multiple_choice, Difficulty.easy, 10, "Resuelve: x - 5 = 8", choices=["x=11","x=12","x=13"], correct="x=13", hints=["x = 8 + 5 = 13"]),
                        ],
                    },
                ],
            },
        ],
    }