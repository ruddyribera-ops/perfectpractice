"""
Standalone seed using ONLY asyncpg (no app imports, no pydantic).
Seeds the full Khan-aligned curriculum into Railway Postgres.
"""
import asyncio
import json
import os

import asyncpg
from bcrypt import hashpw, gensalt

# Railway Postgres connection
DATABASE_URL = os.environ.get("DATABASE_URL", "")
url = DATABASE_URL.replace("postgresql+asyncpg://", "")
user_part, rest = url.split("@")
user, password = user_part.split(":")
host_port_db = rest.rsplit("/", 1)
hp = host_port_db[0].split(":")
HOST = hp[0]
PORT = int(hp[1]) if len(hp) > 1 else 5432
DB = host_port_db[1]

# ── Full curriculum data (Topics → Units → Lessons → Exercises) ────────────────
# G1-G6 Khan-aligned + bonus Aritmética section
# Structure mirrors curriculum_seed.py TOPICS exactly

GRADE1_TOPICS = [
    {
        "slug": "g1-numeros", "title": "Números hasta 20",
        "description": "Contar, leer y escribir números del 0 al 20", "icon_name": "🔢",
        "units": [
            {"slug": "g1-contar-20", "title": "Contar hasta 20", "description": "Contar objetos hasta 20", "order_index": 0,
             "lessons": [
                 {"title": "Contar hasta 10", "content": "# 🔢 Contar hasta 10\n\nCuenta los objetos.\n\n:::visual:tenframe,5:::\n\n**¿Cuántos ves?** 5 puntos → 5 vacíos", "order_index": 0},
                 {"title": "Contar hasta 20", "content": "# 🔢 Contar hasta 20\n\n:::visual:tenframe,10:::\n:::visual:tenframe,5:::\n\n11-20: 1 marco lleno + más.", "order_index": 1},
             ],
             "exercises": [
                 {"slug": "g1-contar-5", "title": "¿Cuántos hay?", "exercise_type": "numeric", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuántos círculos hay? ●●●●●", "correct_answer": "5"}},
                 {"slug": "g1-contar-10", "title": "Contar hasta 10", "exercise_type": "multiple_choice", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuántos hay? ●●●●●●●●●●", "choices": ["8","9","10","11"], "correct_answer": "10"}},
                 {"slug": "g1-contar-15", "title": "Contar hasta 15", "exercise_type": "numeric", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuántos hay? ●●●●●●●●●●●●●●", "correct_answer": "15"}},
             ]},
            {"slug": "g1-suma-resta", "title": "Suma y Resta hasta 10", "description": "Juntar y quitar", "order_index": 1,
             "lessons": [
                 {"title": "Sumar hasta 5", "content": "# ➕ Sumar hasta 5\n\n**Sumar** = **juntar**.\n\n2 + 3 = ?", "order_index": 0},
                 {"title": "Restar hasta 5", "content": "# ➖ Restar hasta 5\n\n**Restar** = **quitar**.\n\n5 - 2 = ?", "order_index": 1},
             ],
             "exercises": [
                 {"slug": "g1-suma-5-a", "title": "Sumar hasta 5", "exercise_type": "numeric", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuánto es 2 + 3?", "correct_answer": "5"}},
                 {"slug": "g1-resta-5-a", "title": "Restar hasta 5", "exercise_type": "numeric", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuánto es 5 - 2?", "correct_answer": "3"}},
             ]},
        ],
    },
    {
        "slug": "g1-formas", "title": "Figuras 2D",
        "description": "Reconocer círculo, cuadrado, triángulo, rectángulo", "icon_name": "🔷",
        "units": [
            {"slug": "g1-figuras-basicas", "title": "Formas básicas", "description": "Formas simples", "order_index": 0,
             "lessons": [
                 {"title": "El Círculo", "content": "# ⭕ El Círculo\n\nRedondo, sin lados.", "order_index": 0},
                 {"title": "El Cuadrado", "content": "# ⬜ El Cuadrado\n\n4 lados iguales.", "order_index": 1},
             ],
             "exercises": [
                 {"slug": "g1-circulo-1", "title": "Reconocer círculos", "exercise_type": "multiple_choice", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuál es un círculo?", "choices": ["⬜", "🔴", "🔺"], "correct_answer": "🔴"}},
                 {"slug": "g1-cuadrado-1", "title": "Lados del cuadrado", "exercise_type": "numeric", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuántos lados tiene un cuadrado?", "correct_answer": "4"}},
             ]},
        ],
    },
]

GRADE2_TOPICS = [
    {
        "slug": "g2-numeros-100", "title": "Números hasta 100",
        "description": "Leer, escribir y comparar números hasta 100", "icon_name": "🔢",
        "units": [
            {"slug": "g2-contar-100", "title": "Contar hasta 100", "description": "Contar de 10 en 10", "order_index": 0,
             "lessons": [
                 {"title": "Contar de 10 en 10", "content": "# 🔢 Contar de 10 en 10\n\n10, 20, 30, 40...", "order_index": 0},
             ],
             "exercises": [
                 {"slug": "g2-contar-10s-1", "title": "Contar de 10 en 10", "exercise_type": "numeric", "difficulty": "easy", "points": 5, "data": {"question": "¿Cuánto es 4 grupos de 10?", "correct_answer": "40"}},
             ]},
            {"slug": "g2-suma-resta-20", "title": "Sumar y restar hasta 20", "description": "Sumas y restas hasta 20", "order_index": 1,
             "lessons": [
                 {"title": "Suma llevando", "content": "# ➕ Suma llevando\n\n15 + 7 = ?", "order_index": 0},
             ],
             "exercises": [
                 {"slug": "g2-suma-llevando-1", "title": "Suma llevando", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "¿Cuánto es 15 + 7?", "correct_answer": "22"}},
             ]},
        ],
    },
]

GRADE3_TOPICS = [
    {
        "slug": "g3-numeros", "title": "Números grandes",
        "description": "Números hasta 1,000,000", "icon_name": "🔢",
        "units": [
            {"slug": "g3-millares", "title": "Hasta el millón", "description": "Leer y escribir grandes números", "order_index": 0,
             "lessons": [
                 {"title": "Números hasta 10,000", "content": "# 🔢 Números hasta 10,000\n\n1,000 | 2,000 | ... | 10,000", "order_index": 0},
             ],
             "exercises": [
                 {"slug": "g3-millar-1", "title": "Sumar millares", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "¿Cuánto es 2,000 + 3,000?", "correct_answer": "5000"}},
             ]},
        ],
    },
    {
        "slug": "g3-geometria", "title": "Geometría y medición",
        "description": "Perímetro, área, figuras 2D", "icon_name": "📐",
        "units": [
            {"slug": "g3-perimetro-area", "title": "Perímetro y área", "description": "Calcular perímetro y área", "order_index": 0,
             "lessons": [
                 {"title": "Perímetro", "content": "# 📏 El Perímetro\n\nP = lado + lado + lado + lado", "order_index": 0},
                 {"title": "Área del rectángulo", "content": "# 📐 Área del rectángulo\n\nA = largo × ancho", "order_index": 1},
             ],
             "exercises": [
                 {"slug": "g3-perim-1", "title": "Perímetro rectángulo", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "Un rectángulo tiene largo 9 cm y ancho 4 cm. ¿Perímetro?", "correct_answer": "26"}},
                 {"slug": "g3-area-1", "title": "Área rectángulo", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "Un rectángulo mide 8 cm × 6 cm. ¿Área?", "correct_answer": "48"}},
             ]},
        ],
    },
]

# Full GRADE4-6 + bonus topics from curriculum_seed.py
GRADE4_TOPICS = [
    {"slug": "g4-fracciones-decimales", "title": "Fracciones y decimales", "description": "Números mixtos, decimales", "icon_name": "🔢",
     "units": [
         {"slug": "g4-fracciones", "title": "Fracciones equivalentes", "description": "Comparar y operar con fracciones", "order_index": 0,
          "lessons": [{"title": "Fracciones equivalentes", "content": "# 🍕 Fracciones equivalentes\n\n1/2 = 2/4 = 3/6", "order_index": 0}],
          "exercises": [
              {"slug": "g4-frac-eq-1", "title": "Fracciones equivalentes", "exercise_type": "multiple_choice", "difficulty": "medium", "points": 10, "data": {"question": "¿Cuál es igual a 1/2?", "choices": ["2/4","3/5","2/3"], "correct_answer": "2/4"}},
              {"slug": "g4-frac-compare-1", "title": "Comparar fracciones", "exercise_type": "multiple_choice", "difficulty": "medium", "points": 15, "data": {"question": "¿Qué fracción es mayor: 3/5 o 2/3?", "choices": ["3/5","2/3","son iguales"], "correct_answer": "2/3"}},
          ]},
         {"slug": "g4-decimales", "title": "Décimos y centésimos", "description": "Números con punto decimal", "order_index": 1,
          "lessons": [{"title": "Décimos", "content": "# 🔟 Décimos\n\n0.1 = 1/10", "order_index": 0}],
          "exercises": [
              {"slug": "g4-dec-1", "title": "Décimos", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "0.5 en fracción = ?/10", "correct_answer": "5"}},
              {"slug": "g4-dec-compare-1", "title": "Comparar decimales", "exercise_type": "multiple_choice", "difficulty": "easy", "points": 10, "data": {"question": "¿Qué es mayor: 0.3 o 0.28?", "choices": ["0.3","0.28","son iguales"], "correct_answer": "0.3"}},
              {"slug": "g4-dec-suma-1", "title": "Suma de decimales", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es 2.5 + 1.3?", "correct_answer": "3.8"}},
              {"slug": "g4-dec-mult-1", "title": "Multiplicar decimal por entero", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es 0.5 × 6?", "correct_answer": "3"}},
              {"slug": "g4-dec-mult-2", "title": "Multiplicar decimales", "exercise_type": "numeric", "difficulty": "hard", "points": 20, "data": {"question": "¿Cuánto es 1.2 × 0.3?", "correct_answer": "0.36"}},
          ]},
     ]},
    {"slug": "g4-algebra", "title": "Álgebra básica", "description": "Expresiones y ecuaciones simples", "icon_name": "🔣",
     "units": [
         {"slug": "g4-ecuaciones", "title": "Ecuaciones de suma/resta", "description": "Resolver x + 5 = 12", "order_index": 0,
          "lessons": [{"title": "Ecuaciones de un paso", "content": "# 🔣 Ecuaciones\n\nx + 5 = 12 → x = 7", "order_index": 0}],
          "exercises": [
              {"slug": "g4-ecuacion-1", "title": "Ecuación de suma", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "x + 8 = 15. ¿x?", "correct_answer": "7"}},
              {"slug": "g4-ecuacion-2", "title": "Ecuación de resta", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "x - 4 = 9. ¿x?", "correct_answer": "13"}},
              {"slug": "g4-ecuacion-3", "title": "Ecuación de multiplicación", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "3x = 21. ¿x?", "correct_answer": "7"}},
          ]},
     ]},
]

GRADE5_TOPICS = [
    {"slug": "g5-fracciones-decimales", "title": "Fracciones y decimales avanzados", "description": "Números mixtos, operaciones con fracciones", "icon_name": "🔢",
     "units": [
         {"slug": "g5-fracciones-avanzado", "title": "Fracciones avanzadas", "description": "Números mixtos, fracciones impropias", "order_index": 0,
          "lessons": [
              {"title": "Números mixtos", "content": "# 🔢 Números mixtos\n\n2 1/3 = 7/3", "order_index": 0},
              {"title": "Sumar fracciones diferentes", "content": "# ➕ Sumar fracciones\n\n1/2 + 1/3 = 5/6", "order_index": 1},
          ],
          "exercises": [
              {"slug": "g5-mixto-1", "title": "A fracción impropia", "exercise_type": "numeric", "difficulty": "medium", "points": 10, "data": {"question": "Convierte 3 2/5 a fracción impropia.", "correct_answer": "17/5"}},
              {"slug": "g5-mixto-2", "title": "A número mixto", "exercise_type": "numeric", "difficulty": "medium", "points": 10, "data": {"question": "Convierte 11/4 a número mixto.", "correct_answer": "2 3/4"}},
              {"slug": "g5-frac-sumar-1", "title": "Sumar fracciones", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es 3/8 + 1/4?", "correct_answer": "5/8"}},
              {"slug": "g5-frac-sumar-2", "title": "Sumar fracciones complejas", "exercise_type": "numeric", "difficulty": "hard", "points": 20, "data": {"question": "¿Cuánto es 2/3 + 1/6 + 1/2?", "correct_answer": "4/3"}},
          ]},
         {"slug": "g5-decimales-operaciones", "title": "Operaciones con decimales", "description": "Suma, resta, multiplicación y división", "order_index": 1,
          "lessons": [{"title": "Multiplicar y dividir decimales", "content": "# ✖️➗ Multiplicar y dividir decimales\n\n2.5 × 1.4 = 3.5", "order_index": 0}],
          "exercises": [
              {"slug": "g5-dec-mult-1", "title": "Multiplicar decimales", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es 2.4 × 1.5?", "correct_answer": "3.6"}},
              {"slug": "g5-dec-div-1", "title": "Dividir decimal entre entero", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es 8.4 ÷ 4?", "correct_answer": "2.1"}},
              {"slug": "g5-dec-div-2", "title": "Dividir decimales", "exercise_type": "numeric", "difficulty": "hard", "points": 20, "data": {"question": "¿Cuánto es 6.4 ÷ 0.8?", "correct_answer": "8"}},
          ]},
     ]},
    {"slug": "g5-algebra-ecuaciones", "title": "Álgebra y ecuaciones", "description": "Expresiones algebraicas, resolver ecuaciones", "icon_name": "🔣",
     "units": [
         {"slug": "g5-ecuaciones-inecuaciones", "title": "Ecuaciones e inecuaciones", "description": "Resolver ax+b=c", "order_index": 0,
          "lessons": [
              {"title": "Resolver 2x + 3 = 11", "content": "# 🔣 Ecuaciones\n\n2x + 3 = 11 → 2x = 8 → x = 4", "order_index": 0},
              {"title": "Inecuaciones", "content": "# 🔣 Inecuaciones\n\nx + 3 > 7 → x > 4", "order_index": 1},
          ],
          "exercises": [
              {"slug": "g5-ecu-1", "title": "Ecuación básica", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "x + 9 = 15. ¿x?", "correct_answer": "6"}},
              {"slug": "g5-ecu-2", "title": "Con multiplicación", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "4x = 36. ¿x?", "correct_answer": "9"}},
              {"slug": "g5-ecu-3", "title": "Dos pasos", "exercise_type": "numeric", "difficulty": "hard", "points": 20, "data": {"question": "2x + 5 = 19. ¿x?", "correct_answer": "7"}},
              {"slug": "g5-inecu-1", "title": "Inecuación", "exercise_type": "multiple_choice", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuál satisface x + 3 > 7?", "choices": ["x=3", "x=5", "x=4.9"], "correct_answer": "x=5"}},
          ]},
     ]},
]

GRADE6_TOPICS = [
    {"slug": "g6-numeros-negativos", "title": "Números negativos", "description": "Enteros negativos, recta numérica", "icon_name": "🔢",
     "units": [
         {"slug": "g6-negativos", "title": "Enteros negativos", "description": "Comparar y operar con negativos", "order_index": 0,
          "lessons": [{"title": "Comparar negativos", "content": "# 🔢 Enteros negativos\n\n-3 > -7 porque -3 está más a la derecha.", "order_index": 0}],
          "exercises": [
              {"slug": "g6-neg-1", "title": "Comparar negativos", "exercise_type": "multiple_choice", "difficulty": "easy", "points": 10, "data": {"question": "¿Qué número es mayor: -3 o -7?", "choices": ["-3","-7","son iguales"], "correct_answer": "-3"}},
              {"slug": "g6-neg-2", "title": "Valor absoluto", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "|−5| = ?", "correct_answer": "5"}},
              {"slug": "g6-neg-suma-1", "title": "Sumar negativos", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es -4 + (-3)?", "correct_answer": "-7"}},
          ]},
     ]},
    {"slug": "g6-razones-velocidad", "title": "Razones, tasas y velocidad", "description": "Razones, proporciones, regla de tres", "icon_name": "📊",
     "units": [
         {"slug": "g6-razones", "title": "Razones y proporciones", "description": "Razones, regla de tres simple", "order_index": 0,
          "lessons": [
              {"title": "Razón", "content": "# 📊 Razón\n\n3:4 significa 3 de cada 4.", "order_index": 0},
              {"title": "Regla de tres", "content": "# 📐 Regla de tres\n\nSi 2 cafes cuestan $6, 5 cafes cuestan $15.", "order_index": 1},
          ],
          "exercises": [
              {"slug": "g6-razon-1", "title": "Razón", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "Si la razón es 3:4 y el primer valor es 9, ¿cuál es el segundo?", "correct_answer": "12"}},
              {"slug": "g6-razon-2", "title": "Simplificar razón", "exercise_type": "multiple_choice", "difficulty": "easy", "points": 10, "data": {"question": "Simplifica 6:9", "choices": ["2:3","1:2","3:2"], "correct_answer": "2:3"}},
              {"slug": "g6-razon-3", "title": "Aplicar razón", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "Si 4 trabajadores hacen un muro en 8 horas, ¿cuántas horas hacen 6 trabajadores?", "correct_answer": "5"}},
              {"slug": "g6-regla3-1", "title": "Regla de tres", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "Un coche recorre 240 km en 4 horas. ¿Cuántos km en 7 horas?", "correct_answer": "420"}},
              {"slug": "g6-regla3-2", "title": "Regla de tres compleja", "exercise_type": "numeric", "difficulty": "hard", "points": 20, "data": {"question": "Si 8 máquinas hacen 200 piezas en 5 horas, ¿cuántas piezas hacen 12 máquinas en 7 horas?", "correct_answer": "420"}},
          ]},
     ]},
    {"slug": "g6-porcentajes", "title": "Porcentajes", "description": "Calcular porcentajes, descuentos, márgenes", "icon_name": "📊",
     "units": [
         {"slug": "g6-porcentajes", "title": "Porcentajes", "description": "%, fracciones y decimales", "order_index": 0,
          "lessons": [
              {"title": "% a fracción", "content": "# 📊 Porcentajes\n\n25% = 25/100 = 1/4", "order_index": 0},
              {"title": "Calcular %", "content": "# 🧮 Calcular porcentaje\n\nEl 30% de 80 = 24", "order_index": 1},
          ],
          "exercises": [
              {"slug": "g6-pct-1", "title": "% a fracción", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "25% = ?/100", "correct_answer": "25"}},
              {"slug": "g6-pct-2", "title": "Decimal a %", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "0.75 = ?%", "correct_answer": "75"}},
              {"slug": "g6-pct-calc-1", "title": "Calcular %", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es el 20% de 150?", "correct_answer": "30"}},
              {"slug": "g6-pct-calc-2", "title": "Calcular %", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "¿Cuánto es el 15% de 80?", "correct_answer": "12"}},
              {"slug": "g6-pct-desc-1", "title": "Descuento", "exercise_type": "numeric", "difficulty": "hard", "points": 20, "data": {"question": "Un precio de $200 tiene 25% de descuento. ¿Precio final?", "correct_answer": "150"}},
          ]},
     ]},
    {"slug": "g6-volumen", "title": "Volumen y capacidad", "description": "Volumen de prismas, cubos, cilindros", "icon_name": "📦",
     "units": [
         {"slug": "g6-volumen", "title": "Volumen", "description": "Calcular volumen de prismas rectangulares", "order_index": 0,
          "lessons": [{"title": "Volumen del prisma", "content": "# 📦 Volumen\n\nV = largo × ancho × alto", "order_index": 0}],
          "exercises": [
              {"slug": "g6-vol-prisma-1", "title": "Volumen prisma", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "Un prisma de 4 cm × 3 cm × 5 cm. ¿Volumen?", "correct_answer": "60"}},
              {"slug": "g6-vol-cubo-1", "title": "Volumen cubo", "exercise_type": "numeric", "difficulty": "easy", "points": 10, "data": {"question": "Un cubo de lado 3 cm. ¿Volumen?", "correct_answer": "27"}},
              {"slug": "g6-vol-prisma-2", "title": "Volumen prisma 2", "exercise_type": "numeric", "difficulty": "medium", "points": 15, "data": {"question": "Un prisma de 6 cm × 4 cm × 2 cm. ¿Volumen?", "correct_answer": "48"}},
          ]},
     ]},
]

ALL_TOPICS = GRADE1_TOPICS + GRADE2_TOPICS + GRADE3_TOPICS + GRADE4_TOPICS + GRADE5_TOPICS + GRADE6_TOPICS

EXERCISE_TYPES = {"numeric": "numeric", "multiple_choice": "multiple_choice", "true_false": "true_false", "ordering": "ordering"}
DIFFICULTIES = {"easy": "easy", "medium": "medium", "hard": "hard"}


async def create_tables(conn):
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS topics (
            id SERIAL PRIMARY KEY, slug VARCHAR(255) UNIQUE NOT NULL, title VARCHAR(255) NOT NULL,
            description TEXT, icon_name VARCHAR(50), parent_id INTEGER REFERENCES topics(id),
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS units (
            id SERIAL PRIMARY KEY, topic_id INTEGER REFERENCES topics(id) ON DELETE CASCADE,
            slug VARCHAR(255) NOT NULL, title VARCHAR(255) NOT NULL, description TEXT, order_index INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS lessons (
            id SERIAL PRIMARY KEY, unit_id INTEGER REFERENCES units(id) ON DELETE CASCADE,
            title VARCHAR(255) NOT NULL, content TEXT DEFAULT '', order_index INTEGER DEFAULT 0,
            content_type VARCHAR(20) DEFAULT 'text',
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS exercises (
            id SERIAL PRIMARY KEY, unit_id INTEGER REFERENCES units(id) ON DELETE CASCADE,
            lesson_id INTEGER REFERENCES lessons(id) ON DELETE SET NULL,
            slug VARCHAR(255) UNIQUE NOT NULL, title VARCHAR(255) NOT NULL,
            exercise_type VARCHAR(50) NOT NULL, difficulty VARCHAR(20) NOT NULL,
            points_value INTEGER DEFAULT 10, data JSONB DEFAULT '{}', hints TEXT,
            is_anked BOOLEAN DEFAULT FALSE, is_summative BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW()
        )
    """)
    print("Tables verified/created.")


async def seed_users(conn):
    users = [
        ("student@test.com", "test123", "student", "Test Student"),
        ("profesor@test.com", "test123", "teacher", "Test Teacher"),
        ("padre@test.com", "test123", "parent", "Test Parent"),
    ]
    for email, password, role, name in users:
        exists = await conn.fetchval("SELECT id FROM users WHERE email = $1", email)
        if not exists:
            hashed = hashpw(password.encode(), gensalt()).decode()
            await conn.execute(
                "INSERT INTO users (email, hashed_password, role, full_name, created_at, updated_at) VALUES ($1, $2, $3, $4, NOW(), NOW())",
                email, hashed, role, name
            )
            print(f"  Created user: {email}")


async def seed_all(conn):
    created = {"topics": 0, "units": 0, "lessons": 0, "exercises": 0}

    for topic_data in ALL_TOPICS:
        existing_topic = await conn.fetchval("SELECT id FROM topics WHERE slug = $1", topic_data["slug"])
        if existing_topic:
            print(f"  Topic '{topic_data['slug']}' exists, skipping")
            topic_id = existing_topic
        else:
            topic_id = await conn.fetchval("""
                INSERT INTO topics (slug, title, description, icon_name, created_at, updated_at)
                VALUES ($1, $2, $3, $4, NOW(), NOW()) RETURNING id
            """, topic_data["slug"], topic_data["title"], topic_data.get("description"), topic_data.get("icon_name"))
            created["topics"] += 1
            print(f"  Created topic: {topic_data['title']}")

        for unit_data in topic_data.get("units", []):
            existing_unit = await conn.fetchval("SELECT id FROM units WHERE slug = $1", unit_data["slug"])
            if existing_unit:
                unit_id = existing_unit
                print(f"    Unit '{unit_data['slug']}' exists, skipping")
            else:
                unit_id = await conn.fetchval("""
                    INSERT INTO units (topic_id, slug, title, description, order_index, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, NOW(), NOW()) RETURNING id
                """, topic_id, unit_data["slug"], unit_data["title"], unit_data.get("description"), unit_data.get("order_index", 0))
                created["units"] += 1

            for lesson_data in unit_data.get("lessons", []):
                existing_lesson = await conn.fetchval(
                    "SELECT id FROM lessons WHERE unit_id = $1 AND title = $2", unit_id, lesson_data["title"]
                )
                if existing_lesson:
                    lesson_id = existing_lesson
                else:
                    lesson_id = await conn.fetchval("""
                        INSERT INTO lessons (unit_id, title, content, order_index, created_at, updated_at)
                        VALUES ($1, $2, $3, $4, NOW(), NOW()) RETURNING id
                    """, unit_id, lesson_data["title"], lesson_data.get("content", ""), lesson_data.get("order_index", 0))
                    created["lessons"] += 1

            for ex in unit_data.get("exercises", []):
                existing_ex = await conn.fetchval("SELECT id FROM exercises WHERE slug = $1", ex["slug"])
                if existing_ex:
                    continue
                # Find lesson_id (first lesson in unit)
                lesson_id = await conn.fetchval(
                    "SELECT id FROM lessons WHERE unit_id = $1 ORDER BY order_index LIMIT 1", unit_id
                )
                await conn.execute("""
                    INSERT INTO exercises (unit_id, lesson_id, slug, title, exercise_type, difficulty, points_value, data, hints, is_anked, is_summative, created_at, updated_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, false, false, NOW(), NOW())
                """, unit_id, lesson_id, ex["slug"], ex["title"], ex["exercise_type"], ex["difficulty"], ex.get("points", 10), json.dumps(ex.get("data", {})), ex.get("hints"))
                created["exercises"] += 1

    return created


async def main():
    print(f"Connecting to {DB} on {HOST}...")
    conn = await asyncpg.connect(host=HOST, port=PORT, user=user, password=password, database=DB)
    print("Connected!")

    r = await conn.fetchval("SELECT COUNT(*) FROM topics")
    print(f"Current DB: {r} topics")

    if r >= 45:
        print("DB already has 45+ topics. Skipping seed to avoid duplicates.")
        await conn.close()
        return

    await create_tables(conn)
    await seed_users(conn)
    created = await seed_all(conn)
    await conn.close()

    print(f"\n✅ Full seed complete!")
    print(f"   Created: {created['topics']} topics, {created['units']} units, {created['lessons']} lessons, {created['exercises']} exercises")

    # Reconnect to verify
    conn2 = await asyncpg.connect(host=HOST, port=PORT, user=user, password=password, database=DB)
    t = await conn2.fetchval("SELECT COUNT(*) FROM topics")
    u = await conn2.fetchval("SELECT COUNT(*) FROM units")
    l = await conn2.fetchval("SELECT COUNT(*) FROM lessons")
    e = await conn2.fetchval("SELECT COUNT(*) FROM exercises")
    print(f"\n📊 Final DB state: {t} topics, {u} units, {l} lessons, {e} exercises")
    await conn2.close()


if __name__ == "__main__":
    asyncio.run(main())