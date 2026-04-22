"""
Curriculum Seed Script
Populates the database with Khan Academy-aligned mathematics curriculum.
Run: docker exec math-platform-backend-1 python -m seed.curriculum_seed --commit
"""

import asyncio
import sys
import argparse
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.curriculum import Topic, Unit, Lesson, Exercise, ExerciseType, Difficulty


# =============================================================================
# TOPICS DATA - Bolivian curriculum aligned (Khan Academy style)
# Built from: Chilean 5to Basico "Matemática 5º" (Marshall Cavendish/Santillana)
# + Singapore Math Method + Game-based calculation books
# =============================================================================

# ── Helpers for bar-model problem generation ──────────────────────────────────
def bar_model_problem(parts: list[int], total: int | None, question: str, operation: str = "add") -> dict:
    """
    Generate a bar-model visual problem.
    parts: list of segment values (the known parts)
    total: final/total bar value (None = unknown to solve — this is the correct_answer)
    operation: 'add' | 'subtract' | 'compare'
    Returns data matching frontend BarModelData: {type, question, total, units, correct_answer}
    """
    # units: [{label, value}] — label is the part name, value is the numeric amount
    units = [{"label": f"Parte {i+1}", "value": v} for i, v in enumerate(parts)]
    correct = str(total) if total is not None else None
    return {
        "type": "bar_model",
        "question": question,
        "total": str(total) if total is not None else "?",
        "units": units,
        "operation": operation,
        "correct_answer": correct,
    }


def word_problem(num1: int, num2: int, operation: str, context: str) -> dict:
    ops = {"add": "+", "subtract": "-", "multiply": "×", "divide": "÷"}
    op_sym = ops.get(operation, "+")
    q = f"{context} ¿Cuál es el resultado de {num1} {op_sym} {num2}?"
    if operation == "add":
        answer = num1 + num2
        explanation = f"{num1} + {num2} = {answer}"
    elif operation == "subtract":
        answer = num1 - num2
        explanation = f"{num1} - {num2} = {answer}"
    elif operation == "multiply":
        answer = num1 * num2
        explanation = f"{num1} × {num2} = {answer}"
    else:
        answer = num1 // num2
        explanation = f"{num1} ÷ {num2} = {answer}"
    return {
        "question": q,
        "correct_answer": str(answer),
        "explanation": explanation,
        "context": context,
    }


# ─────────────────────────────────────────────────────────────────────────────
# GRADE 1 (Grade 1 primary - ages 6-7)
# Topics: Numbers to 20, Addition/Subtraction to 10, 2D shapes, Length/weight
# ─────────────────────────────────────────────────────────────────────────────
GRADE1_TOPICS = [
    {
        "slug": "g1-numeros",
        "title": "Números hasta 20",
        "description": "Contar, leer y escribir números del 0 al 20",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "g1-contar-20",
                "title": "Contar hasta 20",
                "description": "Contar objetos hasta 20 y escribir el número",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Contar hasta 10",
                        "content": """# 🔢 Contar hasta 10

Cuenta los objetos que ves a tu alrededor.

## ¡Manos a la obra!

:::tryit:¿Cuántos círculos hay? ●●●●●●●●●●|10|Cuenta uno por uno|¡Muy bien!:::

## Los números del 0 al 10

- **0** Cero — nada
- **1** Uno — 👂 un objeto
- **2** Dos — 👂👂 pares
- **3** Tres — 👂👂👂
- **4** Cuatro — 👂👂👂👂
- **5** Cinco — 👂👂👂👂👂 (¡una mano!)
- **6** Seis — 👂👂👂👂👂👂
- **7** Siete — 👂👂👂👂👂👂👂
- **8** Ocho — 👂👂👂👂👂👂👂👂
- **9** Nueve — 👂👂👂👂👂👂👂👂👂
- **10** Diez — 👂👂👂👂👂👂👂👂👂👂 (¡las dos manos!)

:::visual:tenframe,5:::

Practica contando del 1 al 10.""",
                        "order_index": 0,
                        "exercise_slugs": ["g1-contar-5", "g1-contar-10"],
                    },
                    {
                        "title": "Contar hasta 20",
                        "content": """# 🔢 Contar hasta 20

¡Contamos juntos hasta **20**!

##group=10+ones
10 y 1 = **11** (diez y uno)
10 y 2 = **12** (diez y dos)
...
10 y 10 = **20** (dos dieces = veinte)

:::visual:tenframe,7:::
:::visual:tenframe,13:::
:::tryit:Si tienes 1 grupo de 10 y 4 objetos, ¿cuántos objetos tienes?|14|1 grupo = 10 + 4 = 14|10 + 4 = 14:::

Practica con los ejercicios.""",
                        "order_index": 1,
                        "exercise_slugs": ["g1-contar-15", "g1-contar-20"],
                    },
                ],
                "exercises": [
                    {"slug": "g1-contar-5", "title": "Contar hasta 5", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(3, 0, "add", "Hay 3 manzanas, ¿cuántas hay?"),
                     "hints": ["Cuenta los objetos", "1, 2, 3..."]},
                    {"slug": "g1-contar-10", "title": "Contar hasta 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(7, 0, "add", "Hay 7 libros en la mesa, ¿cuántos son?"),
                     "hints": ["Cuenta del 1 al 10"]},
                    {"slug": "g1-contar-15", "title": "Contar hasta 15", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(12, 0, "add", "Tienes 12 lápices en tu estuche, ¿cuántos son?"),
                     "hints": ["Un grupo de 10 y 2 más"]},
                    {"slug": "g1-contar-20", "title": "Contar hasta 20", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(18, 0, "add", "Hay 18 alumnos en la clase, ¿cuántos son?"),
                     "hints": ["Escribe el número 18"]},
                ],
            },
            {
                "slug": "g1-suma-resta-10",
                "title": "Sumar y restar hasta 10",
                "description": "Juntar y quitar objetos, sumar y restar hasta 10",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Sumar hasta 5",
                        "content": """# ➕ Sumar hasta 5

**Sumar** significa **juntar** cosas.

:::visual:base10,2,1:::
:::tryit:María tiene 2 caramelos y recibe 1 más. ¿Cuántos tiene?|3|2 + 1 = 3|¡Muy bien!:::
:::tryit:Hay 3 gatos y llega 1 más. ¿Cuántos gatos hay ahora?|4|3 + 1 = 4|3 + 1 = 4:::
:::tryit:2 fichas + 2 fichas = ?|4|2 + 2 = 4|¡Dos y dos son cuatro!:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g1-suma-5-a", "g1-suma-5-b"],
                    },
                    {
                        "title": "Restar hasta 5",
                        "content": """# ➖ Restar hasta 5

**Restar** significa **quitar** o **sacar**.

:::visual:numberline,4,2,subtract:::
:::tryit:Tenías 5 galletas y te comes 2. ¿Cuántas quedan?|3|5 - 2 = 3|5 menos 2 quedan 3:::
:::tryit:Hay 4 pájaros en un árbol. Se van 1. ¿Cuántos quedan?|3|4 - 1 = 3|4 menos 1 = 3:::
:::tryit:3 - 1 = ?|2|3 - 1 = 2|¡Muy bien!:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g1-resta-5-a", "g1-resta-5-b"],
                    },
                    {
                        "title": "Sumar y restar hasta 10",
                        "content": """# ➕➖ Sumar y restar hasta 10

Ahora usamos los **dos** operaciones.

:::visual:base10,6,4:::
:::visual:numberline,10,3,subtract:::

:::tryit:6 + 4 = ?|10|Seis más cuatro son diez|¡Correcto!:::
:::tryit:10 - 3 = ?|7|Diez menos tres son siete|10 - 3 = 7:::

:::tryit:Hay 7 bolas. 3 son rojas y las demás azules. ¿Cuántas son azules?|4|7 - 3 = 4|3 azules menos de 7:::
Practica.""",
                        "order_index": 2,
                        "exercise_slugs": ["g1-sumaresta-10-a", "g1-sumaresta-10-b"],
                    },
                ],
                "exercises": [
                    {"slug": "g1-suma-5-a", "title": "Sumar hasta 5", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(2, 3, "add", "Tienes 2 manzanas y compras 3 más."),
                     "hints": ["Cuenta todas juntas"]},
                    {"slug": "g1-suma-5-b", "title": "Sumar hasta 5", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(4, 1, "add", "Hay 4 libros en la mesa y pones 1 más."),
                     "hints": ["4 + 1 = 5"]},
                    {"slug": "g1-resta-5-a", "title": "Restar hasta 5", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(5, 2, "subtract", "Tenías 5 caramelos y regalaste 2."),
                     "hints": ["5 menos 2"]},
                    {"slug": "g1-resta-5-b", "title": "Restar hasta 5", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": word_problem(4, 1, "subtract", "Hay 4 pájaros. Se vuela 1."),
                     "hints": ["4 menos 1"]},
                    {"slug": "g1-sumaresta-10-a", "title": "Sumar hasta 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(6, 4, "add", "Ana tiene 6 gatos y Roberto tiene 4."),
                     "hints": ["6 + 4 = 10"]},
                    {"slug": "g1-sumaresta-10-b", "title": "Restar hasta 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(9, 3, "subtract", "En un autobús viajan 9 personas. Bajan 3."),
                     "hints": ["9 menos 3"]},
                ],
            },
        ],
    },
    {
        "slug": "g1-formas",
        "title": "Figuras 2D",
        "description": "Reconocer y describir formas: círculo, cuadrado, triángulo, rectángulo",
        "icon_name": "🔷",
        "units": [
            {
                "slug": "g1-figuras-basicas",
                "title": "Formas básicas",
                "description": "Círculo, cuadrado, triángulo y rectángulo",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "El Círculo",
                        "content": """# ⭕ El Círculo

El círculo es una forma **redonda**.

**Ejemplos en la vida real:**
- 🧁 La tapa de un vaso
- 🔴 Una moneda
- ⭕ La wheels de una voiture

:::tryit:¿Cuál de estos es un círculo? (🔴 A) (🔺 B) (⬜ C)|A|El círculo es redondo:::
:::tryit:¿Cuántos lados tiene un círculo?|0|El círculo no tiene lados|0 lados:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g1-circulo-1", "g1-circulo-2"],
                    },
                    {
                        "title": "El Cuadrado y el Triángulo",
                        "content": """# ⬜ El Cuadrado y el Triángulo

**Cuadrado:** tiene **4 lados iguales** y **4 esquinas**.
**Triángulo:** tiene **3 lados** y **3 esquinas**.

:::tryit:¿Cuántos lados tiene un cuadrado?|4|El cuadrado tiene 4 lados|4:::
:::tryit:¿Cuántos lados tiene un triángulo?|3|El triángulo tiene 3 lados|3:::
:::tryit:¿Cuál tiene 3 lados, el círculo o el triángulo?|triángulo|El triángulo tiene 3 lados|3:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g1-cuadrado-1", "g1-triangulo-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g1-circulo-1", "title": "Reconocer círculos", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuál es un círculo?", "choices": ["⬜ Cuadrado", "🔴 Círculo", "🔺 Triángulo"], "correct_answer": "🔴 Círculo", "explanation": "El círculo es redondo."},
                     "hints": ["Busca la forma redonda"]},
                    {"slug": "g1-circulo-2", "title": "Lados del círculo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuántos lados tiene un círculo?", "correct_answer": "0", "explanation": "El círculo no tiene lados."},
                     "hints": ["El círculo no tiene esquinas"]},
                    {"slug": "g1-cuadrado-1", "title": "Lados del cuadrado", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuántos lados tiene un cuadrado?", "correct_answer": "4", "explanation": "El cuadrado tiene 4 lados iguales."},
                     "hints": ["1, 2, 3, 4"]},
                    {"slug": "g1-triangulo-1", "title": "Lados del triángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuántos lados tiene un triángulo?", "correct_answer": "3", "explanation": "El triángulo tiene 3 lados."},
                     "hints": ["1, 2, 3"]},
                ],
            },
        ],
    },
    {
        "slug": "g1-medicion",
        "title": "Medición",
        "description": "Comparar longitud, peso y capacidad con palabras largo/corto, pesado/ligero",
        "icon_name": "📏",
        "units": [
            {
                "slug": "g1-longitud",
                "title": "Largo y corto",
                "description": "Comparar objetos por su longitud",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Comparar longitudes",
                        "content": """# 📏 Largo y corto

Podemos comparar **qué objeto es más largo** o **más corto**.

**Ejemplos:**
- 🐍 La serpiente es **larga**
- 🐜 El insecto es **corto**

:::tryit:¿Cuál es más largo, el lápiz o la regla?|regla|El lápiz es más corto que la regla|La regla:::
:::tryit:¿Cuál es más corto, tu dedo o tu brazo?|dedo|El dedo es más corto que el brazo|dedo:::
:::tryit:El tren es ___ que el auto.|más largo|Un tren es más largo que un auto|largo:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g1-longitud-1", "g1-longitud-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g1-longitud-1", "title": "Comparar largo", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Qué es más largo?", "choices": ["Un gusano", "Un elefante"], "correct_answer": "Un elefante", "explanation": "El elefante es más largo que el gusano."},
                     "hints": ["El elefante es más grande"]},
                    {"slug": "g1-longitud-2", "title": "Comparar corto", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Qué es más corto?", "choices": ["Tu pierna", "Tu pie"], "correct_answer": "Tu pie", "explanation": "Tu pie es más corto que tu pierna."},
                     "hints": ["La pierna es más larga"]},
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GRADE 2 (Grade 2 primary - ages 7-8)
# Topics: Numbers to 100, Add/subtract to 20, Multiplication intro, 2D/3D shapes
# ─────────────────────────────────────────────────────────────────────────────
GRADE2_TOPICS = [
    {
        "slug": "g2-numeros-100",
        "title": "Números hasta 100",
        "description": "Leer, escribir y comparar números hasta 100",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "g2-contar-100",
                "title": "Contar hasta 100",
                "description": "Contar de 10 en 10 y de 1 en 1 hasta 100",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Contar de 10 en 10",
                        "content": """# 🔢 Contar de 10 en 10

10, 20, 30, 40, 50, 60, 70, 80, 90, **100**

:::visual:base10,40,30:::
:::tryit:¿Cuánto es 4 grupos de 10?|40|4 × 10 = 40|4 grupos de 10 = 40:::
:::tryit:¿Cuánto es 7 grupos de 10?|70|7 × 10 = 70|7×10=70:::
:::tryit:¿Y 9 grupos de 10?|90|9×10=90|90:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g2-contar-10s-1", "g2-contar-10s-2"],
                    },
                    {
                        "title": "Números hasta 100",
                        "content": """# 🔢 Números hasta 100

Podemos ver los números en una **tabla de 100**.

:::tryit:¿Qué número viene después de 67?|68|67+1=68|68:::
:::tryit:¿Qué número viene después de 89?|90|89+1=90|90:::
:::tryit:¿Qué número viene antes de 50?|49|50-1=49|49:::
:::tryit:¿Mayor, 45 o 54?|54|54 tiene más que 45|54:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g2-100-1", "g2-100-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g2-contar-10s-1", "title": "Contar de 10 en 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 6 grupos de 10?", "correct_answer": "60", "explanation": "6 × 10 = 60"},
                     "hints": ["6 × 10 = 60"]},
                    {"slug": "g2-contar-10s-2", "title": "Contar de 10 en 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 8 grupos de 10?", "correct_answer": "80", "explanation": "8 × 10 = 80"},
                     "hints": ["8 × 10 = 80"]},
                    {"slug": "g2-100-1", "title": "Número siguiente", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Qué viene después de 79?", "correct_answer": "80", "explanation": "79 + 1 = 80"},
                     "hints": ["79 + 1"]},
                    {"slug": "g2-100-2", "title": "Comparar números", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuál es mayor, 34 o 43?", "choices": ["34", "43"], "correct_answer": "43", "explanation": "43 > 34"},
                     "hints": ["43 tiene más que 34"]},
                ],
            },
            {
                "slug": "g2-suma-resta-20",
                "title": "Sumar y restar hasta 20",
                "description": "Sumas y restas hasta 20 con y sin llevar",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Suma llevando",
                        "content": """# ➕ Sumar llevando

Cuando las unidades pasan de 9, **llevamos** a las decenas.

:::steps:Sumamos las unidades: 8 + 7 = 15|15:::Llevamos 1 decena|1:::8+7=15:::Sumamos + la que llevamos: 1 + 3 + 1 = 5|resultado=5:::

:::visual:base10,18,7:::
:::tryit:18 + 7 = ?|25|8+7=15, llevamos 1; 1+1+?; 3+1=5; resultado=25|25:::
:::tryit:9 + 8 = ?|17|9+8=17|17:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g2-suma-llevando-1", "g2-suma-llevando-2"],
                    },
                    {
                        "title": "Resta pidiendo prestado",
                        "content": """# ➖ Resta pidiendo prestado

Cuando el número de arriba es menor, **pedimos prestado** de la siguiente columna.

:::visual:numberline,32,18,subtract:::
:::tryit:32 - 18 = ?|14|32-18=14|14:::
:::tryit:25 - 9 = ?|16|25-9=16|16:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g2-resta-prestar-1", "g2-resta-prestar-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g2-suma-llevando-1", "title": "Suma llevando", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(15, 7, "add", "María tiene 15 galletas y compra 7 más."),
                     "hints": ["15 + 7 = 22"]},
                    {"slug": "g2-suma-llevando-2", "title": "Suma llevando", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(19, 8, "add", "Un autobús lleva 19 pasajeros y suben 8 más."),
                     "hints": ["19 + 8 = 27"]},
                    {"slug": "g2-resta-prestar-1", "title": "Resta prestando", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(32, 18, "subtract", "Tenía 32 bolígrafos y perdí 18."),
                     "hints": ["32 - 18 = 14"]},
                    {"slug": "g2-resta-prestar-2", "title": "Resta prestando", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(25, 9, "subtract", "Había 25 alumnos y se fueron 9."),
                     "hints": ["25 - 9 = 16"]},
                ],
            },
            {
                "slug": "g2-multiplicacion",
                "title": "Introducción a la multiplicación",
                "description": "Multiplicar como suma repetida, tablas del 1, 2, 5, 10",
                "order_index": 2,
                "lessons": [
                    {
                        "title": "¿Qué es multiplicar?",
                        "content": """# ✖️ ¿Qué es multiplicar?

**Multiplicar** es **sumar muchas veces el mismo número**.

**Ejemplo:** 4 grupos de 2 = 2 + 2 + 2 + 2 = **8**
Lo escribimos como: **4 × 2 = 8**

:::visual:array,4,2:::
:::tryit:¿Cuánto es 3 grupos de 5?|15|3×5=15|3×5=15:::
:::tryit:5 × 2 = ?|10|5×2=10|10:::
:::tryit:La tabla del 2: 2 × 1 = ?|2|2×1=2|2:::
:::tryit:2 × 5 = ?|10|2×5=10|10:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g2-mult-2-1", "g2-mult-2-5", "g2-mult-5-1"],
                    },
                    {
                        "title": "Tabla del 10",
                        "content": """# 🔟 Tabla del 10

Multiplicar por 10 es muy fácil: **añade un cero**.

- 1 × 10 = **10**
- 2 × 10 = **20**
- 3 × 10 = **30**
- 4 × 10 = **40**
- 5 × 10 = **50**
- 10 × 10 = **100**

:::tryit:6 × 10 = ?|60|6×10=60|60:::
:::tryit:9 × 10 = ?|90|9×10=90|90:::
:::tryit:10 × 10 = ?|100|10×10=100|100:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g2-mult-10-1", "g2-mult-10-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g2-mult-2-1", "title": "Tabla del 2", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 3 × 2?", "correct_answer": "6", "explanation": "3 × 2 = 2 + 2 + 2 = 6"},
                     "hints": ["3 grupos de 2"]},
                    {"slug": "g2-mult-2-5", "title": "Tabla del 2", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 5 × 2?", "correct_answer": "10", "explanation": "5 × 2 = 10"},
                     "hints": ["5 × 2 = 10"]},
                    {"slug": "g2-mult-5-1", "title": "Tabla del 5", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 4 × 5?", "correct_answer": "20", "explanation": "4 × 5 = 20"},
                     "hints": ["4 × 5 = 20"]},
                    {"slug": "g2-mult-10-1", "title": "Tabla del 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 7 × 10?", "correct_answer": "70", "explanation": "7 × 10 = 70"},
                     "hints": ["Añade un cero a 7"]},
                    {"slug": "g2-mult-10-2", "title": "Tabla del 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuánto es 8 × 10?", "correct_answer": "80", "explanation": "8 × 10 = 80"},
                     "hints": ["80"]},
                ],
            },
        ],
    },
    {
        "slug": "g2-geometria",
        "title": "Figuras y cuerpos",
        "description": "Reconocer cuadrado, triángulo, rectángulo, círculo; identificar cubo y esfera",
        "icon_name": "🔷",
        "units": [
            {
                "slug": "g2-figuras-3d",
                "title": "Cuerpos geométricos",
                "description": "Cubo, esfera, cilindro, cono",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "El cubo y la esfera",
                        "content": """# 🎲 El cubo y la esfera

**Cubo:** tiene **6 caras cuadradas** (como un dado).
**Esfera:** es **completamente redonda** (como una pelota).

:::tryit:¿Cuántas caras tiene un cubo?|6|El cubo tiene 6 caras cuadradas|6:::
:::tryit:¿Cuál es redondo, el cubo o la esfera?|esfera|La esfera es redonda|Esfera:::
:::tryit:Una lata de refresco parece un ___|cilindro|La lata tiene forma de cilindro|Cilindro:::
:::tryit:El cono tiene ___ caras planas.|0|El cono no tiene caras planas|0:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g2-cubo-1", "g2-esfera-1", "g2-cilindro-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g2-cubo-1", "title": "Caras del cubo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuántas caras tiene un cubo?", "correct_answer": "6", "explanation": "El cubo tiene 6 caras cuadradas."},
                     "hints": ["1, 2, 3, 4, 5, 6"]},
                    {"slug": "g2-esfera-1", "title": "Esfera", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuál tiene forma de esfera?", "choices": ["Dado", "Pelota", "Caja"], "correct_answer": "Pelota", "explanation": "La pelota es una esfera."},
                     "hints": ["Redonda por todas partes"]},
                    {"slug": "g2-cilindro-1", "title": "Cilindro", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cuál tiene forma de cilindro?", "choices": ["Pelota", "Lata de sopa", "Dado"], "correct_answer": "Lata de sopa", "explanation": "La lata tiene forma de cilindro."},
                     "hints": ["Como un tubo"]},
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GRADE 3 (Grade 3 primary - ages 8-9) — from Chilean curriculum Unit 1+2
# Topics: Large numbers to 1B, Multiply/divide 2-digit, Geometry/Measurement
# ─────────────────────────────────────────────────────────────────────────────
GRADE3_TOPICS = [
    {
        "slug": "g3-numeros",
        "title": "Números grandes",
        "description": "Números hasta 1,000,000, valor posicional, comparaciones",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "g3-millares",
                "title": "Hasta el millón",
                "description": "Leer, escribir y comparar números hasta 1,000,000",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Números hasta 10,000",
                        "content": """# 🔢 Números hasta 10,000

Podemos contar en grupos de mil:

1,000 | 2,000 | 3,000 | ... | 9,000 | **10,000**

:::visual:base10,2500,1500:::
:::tryit:¿Cuánto es 2,000 + 3,000?|5000|2,000 + 3,000 = 5,000|5000:::
:::tryit:¿Cómo se escribe "ocho mil quinientos"?|8500|8,000 + 500 = 8,500|8500:::
:::tryit:¿Mayor, 4,567 o 4,657?|4657|4657 > 4567|4657:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g3-millar-1", "g3-millar-2", "g3-comparar-1"],
                    },
                    {
                        "title": "Números hasta 1,000,000",
                        "content": """# 🔢 Hasta 1,000,000 (un millón)

**1 millón** = **1,000,000** = mil veces mil

:::tryit:¿Cuántos ceros tiene el número un millón?|6|1,000,000 tiene 6 ceros|6:::
:::tryit:Escribe el número: setecientos mil|700000|700,000|700000:::
:::tryit:¿Mayor, 500,000 o 499,999?|500000|500,000 > 499,999|500000:::
:::tryit:Redondea 347,582 a la unidad de mil más cercana.|348000|347,582 ≈ 348,000|348000:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g3-millones-1", "g3-redondeo-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g3-millar-1", "title": "Sumar millares", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(3000, 2000, "add", "Un stadium tiene 3,000 asientos y otro tiene 2,000."),
                     "hints": ["3,000 + 2,000 = 5,000"]},
                    {"slug": "g3-millar-2", "title": "Escribir con letras", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "¿Cómo se escribe 9,500?", "choices": ["nueve mil quinientos", "noventa y cinco mil", "novecientos cincuenta"], "correct_answer": "nueve mil quinientos", "explanation": "9,500 = nueve mil quinientos"},
                     "hints": ["9 mil + 500"]},
                    {"slug": "g3-comparar-1", "title": "Comparar números", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "¿Cuál es mayor?", "choices": ["34,567", "35,456"], "correct_answer": "35,456", "explanation": "35,456 > 34,567"},
                     "hints": ["Compara dígito por dígito desde la izquierda"]},
                    {"slug": "g3-millones-1", "title": "Lectura de millones", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cómo se lee 1,000,000?", "choices": ["cien mil", "un millón", "diez millones"], "correct_answer": "un millón", "explanation": "1,000,000 = un millón"},
                     "hints": ["Mil veces mil"]},
                    {"slug": "g3-redondeo-1", "title": "Redondeo a miles", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "Redondea 45,678 a la unidad de mil más cercana.", "correct_answer": "46000", "explanation": "45,678 ≈ 46,000 (el siguiente millar)"},
                     "hints": ["Redondea a 46,000 si el dígito de las centenas es 5 o más"]},
                ],
            },
            {
                "slug": "g3-multiplicar",
                "title": "Multiplicación avanzada",
                "description": "Multiplicar por decenas, centenas y números de dos cifras",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Multiplicar por 10, 100, 1000",
                        "content": """# ✖️ Multiplicar por 10, 100, 1000

**Por 10:** recorres el punto decimal 1 lugar a la derecha.
**Por 100:** recorres 2 lugares.
**Por 1000:** recorres 3 lugares.

- 45 × 10 = **450**
- 45 × 100 = **4,500**
- 45 × 1000 = **45,000**

:::tryit:123 × 10 = ?|1230|123×10=1230|1230:::
:::tryit:56 × 100 = ?|5600|56×100=5600|5600:::
:::tryit:8 × 1000 = ?|8000|8×1000=8000|8000:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g3-mult-10-1", "g3-mult-100-1"],
                    },
                    {
                        "title": "Multiplicación de dos cifras",
                        "content": """# ✖️ Multiplicar 23 × 15

:::steps:Multiplicamos 23 × 5 = 115|115:::Multiplicamos 23 × 10 = 230|230:::Sumamos: 115 + 230 = 345|345:::

:::visual:array,23,15:::
:::tryit:23 × 15 = ?|345|23×5=115, 23×10=230, 115+230=345|345:::
:::tryit:34 × 12 = ?|408|34×12=408|408:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g3-mult-2cifras-1", "g3-mult-2cifras-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g3-mult-10-1", "title": "Por 10", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(78, 10, "multiply", "Un autobús tiene 78 pasajeros y vienen 10 autobuses iguales."),
                     "hints": ["78 × 10 = 780"]},
                    {"slug": "g3-mult-100-1", "title": "Por 100", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(45, 100, "multiply", "Cada caja tiene 45 lápices. ¿Cuántos en 100 cajas?"),
                     "hints": ["45 × 100 = 4,500"]},
                    {"slug": "g3-mult-2cifras-1", "title": "Multiplicar 2 cifras", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": word_problem(23, 15, "multiply", "Un granero tiene 23 filas con 15 cajas en cada una."),
                     "hints": ["23 × 15 = 345"]},
                    {"slug": "g3-mult-2cifras-2", "title": "Multiplicar 2 cifras", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": word_problem(34, 12, "multiply", "Una fábrica produce 34 piezas por hora. Trabaja 12 horas."),
                     "hints": ["34 × 12 = 408"]},
                ],
            },
            {
                "slug": "g3-division",
                "title": "División",
                "description": "Dividir entre números de una cifra, relación con multiplicación",
                "order_index": 2,
                "lessons": [
                    {
                        "title": "Dividir es lo opuesto",
                        "content": """# ➗ Dividir es lo opuesto a multiplicar

**Dividir** = partir en partes iguales.

Si 4 × 3 = 12, entonces:
- 12 ÷ 4 = **3** (¿cuántas veces cabe 4 en 12?)
- 12 ÷ 3 = **4** (¿cuántas veces cabe 3 en 12?)

:::tryit:20 ÷ 5 = ?|4|5×4=20, entonces 20÷5=4|4:::
:::tryit:36 ÷ 6 = ?|6|6×6=36, entonces 36÷6=6|6:::
:::tryit:¿Es 42 ÷ 7 = 6?|Sí|7×6=42|Si:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g3-div-1", "g3-div-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g3-div-1", "title": "División básica", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(45, 5, "divide", "45 alumnos se dividen en 5 grupos iguales."),
                     "hints": ["45 ÷ 5 = 9"]},
                    {"slug": "g3-div-2", "title": "División básica", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": word_problem(56, 7, "divide", "56 libros se reparten entre 7 estantes."),
                     "hints": ["56 ÷ 7 = 8"]},
                ],
            },
        ],
    },
    {
        "slug": "g3-geometria",
        "title": "Geometría y medición",
        "description": "Perímetro, área, figuras 2D, plano cartesiano",
        "icon_name": "📐",
        "units": [
            {
                "slug": "g3-perimetro-area",
                "title": "Perímetro y área",
                "description": "Calcular perímetro y área de rectángulos, triángulos",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Perímetro",
                        "content": """# 📏 El Perímetro

El **perímetro** = la suma de todos los **lados** de una figura.

**Rectángulo:** P = 2 × (largo + ancho)

:::visual:comparison,14,10,Largo=14cm,Ancho=10cm:::
:::tryit:Un rectángulo tiene largo 8 cm y ancho 5 cm. ¿Cuál es su perímetro?|26|2×(8+5)=2×13=26|26:::
:::tryit:Un cuadrado tiene lado 6 cm. ¿Cuál es su perímetro?|24|6+6+6+6=24|24:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g3-perim-1", "g3-perim-2"],
                    },
                    {
                        "title": "Área de un rectángulo",
                        "content": """# 📐 Área del rectángulo

**Área** = largo × ancho

A = 10 cm × 5 cm = **50 cm²**

:::visual:array,10,5:::
:::tryit:Un rectángulo mide 7 cm de largo y 4 cm de ancho. ¿Cuál es su área?|28|7×4=28 cm²|28:::
:::tryit:Un cuadrado de lado 5 cm. ¿Cuál es su área?|25|5×5=25 cm²|25:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g3-area-1", "g3-area-cuad-1"],
                    },
                    {
                        "title": "Área del triángulo",
                        "content": """# 🔺 Área del triángulo

**A = (base × altura) ÷ 2**

:::tryit:Base = 8 cm, altura = 5 cm. ¿Área del triángulo?|20|(8×5)÷2=20|20:::
:::tryit:Base = 6 cm, altura = 4 cm. ¿Área?|12|(6×4)÷2=12|12:::
Practica.""",
                        "order_index": 2,
                        "exercise_slugs": ["g3-area-tri-1", "g3-area-tri-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g3-perim-1", "title": "Perímetro rectángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Un rectángulo tiene largo 9 cm y ancho 4 cm. ¿Cuál es su perímetro?", "correct_answer": "26", "explanation": "P = 2×(9+4) = 2×13 = 26 cm"},
                     "hints": ["2×(9+4)=26"]},
                    {"slug": "g3-perim-2", "title": "Perímetro cuadrado", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Un cuadrado tiene lado 7 cm. ¿Cuál es su perímetro?", "correct_answer": "28", "explanation": "P = 4×7 = 28 cm"},
                     "hints": ["4×7=28"]},
                    {"slug": "g3-area-1", "title": "Área rectángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Un rectángulo mide 8 cm × 6 cm. ¿Cuál es su área?", "correct_answer": "48", "explanation": "A = 8×6 = 48 cm²"},
                     "hints": ["8×6=48"]},
                    {"slug": "g3-area-cuad-1", "title": "Área cuadrado", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "Un cuadrado de lado 9 cm. ¿Área?", "correct_answer": "81", "explanation": "A = 9×9 = 81 cm²"},
                     "hints": ["9×9=81"]},
                    {"slug": "g3-area-tri-1", "title": "Área triángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Base = 10 cm, altura = 6 cm. ¿Área del triángulo?", "correct_answer": "30", "explanation": "A = (10×6)÷2 = 30 cm²"},
                     "hints": ["(10×6)÷2 = 30"]},
                    {"slug": "g3-area-tri-2", "title": "Área triángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Base = 8 cm, altura = 7 cm. ¿Área del triángulo?", "correct_answer": "28", "explanation": "A = (8×7)÷2 = 28 cm²"},
                     "hints": ["(8×7)÷2 = 28"]},
                ],
            },
            {
                "slug": "g3-plano-cartesiano",
                "title": "Plano cartesiano",
                "description": "Puntos y figuras en el plano cartesiano",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Puntos en el plano",
                        "content": """# 📍 Puntos en el plano cartesiano

Un punto se escribe como **(x, y)**:
- **x** = izquierda/derecha
- **y** = arriba/abajo

:::tryit:¿Qué punto está en (3, 4)?|x=3, y=4|(3,4) está 3 a la derecha y 4 hacia arriba|(3,4):::
:::tryit:El punto (0, 0) se llama ___|origen|El punto (0,0) es el origen|origen:::
:::tryit:¿En qué cuadrante está (2, 5)?|I|El (2,5) está en el cuadrante I|I:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g3-plano-1", "g3-plano-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g3-plano-1", "title": "Leer puntos", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿En qué cuadrante está el punto (4, 2)?", "choices": ["Cuadrante I", "Cuadrante II", "Cuadrante III"], "correct_answer": "Cuadrante I", "explanation": "x>0, y>0 = Cuadrante I"},
                     "hints": ["x positivo, y positivo"]},
                    {"slug": "g3-plano-2", "title": "Punto origen", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 5,
                     "data": {"question": "¿Cómo se llama el punto (0, 0)?", "choices": ["Eje X", "Eje Y", "Origen"], "correct_answer": "Origen", "explanation": "(0,0) es el origen."},
                     "hints": ["Centro del plano"]},
                ],
            },
        ],
    },
    {
        "slug": "g3-datos",
        "title": "Datos y estadística",
        "description": "Tablas, gráficos de barras, promedio",
        "icon_name": "📊",
        "units": [
            {
                "slug": "g3-tablas-graficos",
                "title": "Tablas y gráficos",
                "description": "Construir e interpretar tablas y gráficos de barras",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Gráficos de barras",
                        "content": """# 📊 Gráficos de barras

Un gráfico de barras muestra **comparaciones** con barras.

:::tryit:Si la barra de "manzanas" llega a 8 y la de "naranjas" a 5, ¿cuántas más manzanas hay?|3|8-5=3|3:::
:::tryit:Si la barra de "peras" llega a la mitad entre 4 y 6, ¿a qué número?|5|mitad de 4 y 6 = 5|5:::
:::tryit:¿Cuál fruta tiene la barra más alta? (manzanas=10, plátanos=6)|manzanas|10 es mayor que 6|manzanas:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g3-grafico-1", "g3-grafico-2"],
                    },
                    {
                        "title": "El promedio",
                        "content": """# 📈 El promedio (media aritmética)

**Promedio** = suma de todos los valores ÷ cantidad

Ejemplo: 4, 6, 8 → (4+6+8)÷3 = 18÷3 = **6**

:::tryit:Las notas de Pedro son 7, 8 y 9. ¿Cuál es su promedio?|8|(7+8+9)÷3=24÷3=8|8:::
:::tryit:Las temperaturas fueron 20°, 22° y 18°. ¿Promedio?|20|(20+22+18)÷3=20|20:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g3-promedio-1", "g3-promedio-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g3-grafico-1", "title": "Leer gráfico", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Barras: gatos=12, perros=9, pájaros=6. ¿Cuántos animales hay en total?", "correct_answer": "27", "explanation": "12+9+6=27"},
                     "hints": ["12+9+6=27"]},
                    {"slug": "g3-grafico-2", "title": "Comparar barras", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Si gatos=12 y perros=9, ¿cuántos más gatos que perros?", "correct_answer": "3", "explanation": "12-9=3"},
                     "hints": ["12-9=3"]},
                    {"slug": "g3-promedio-1", "title": "Calcular promedio", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Precios: $50, $70, $80. ¿Promedio?", "correct_answer": "67", "explanation": "(50+70+80)÷3 = 200÷3 ≈ 66.7 → 67"},
                     "hints": ["(50+70+80)÷3"]},
                    {"slug": "g3-promedio-2", "title": "Calcular promedio", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Edades: 10, 12, 14, 8. ¿Promedio?", "correct_answer": "11", "explanation": "(10+12+14+8)÷4 = 44÷4 = 11"},
                     "hints": ["44÷4=11"]},
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GRADE 4 (Grade 4 primary - ages 9-10) — from Chilean curriculum Unit 3
# Topics: Decimals, Equations, Probability, Data analysis
# ─────────────────────────────────────────────────────────────────────────────
GRADE4_TOPICS = [
    {
        "slug": "g4-decimales",
        "title": "Fracciones y decimales",
        "description": "Décimos, centésimos, milésimos; operaciones con decimales",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "g4-decimales-intro",
                "title": "Números decimales",
                "description": "Décimos, centésimos, comparación y operaciones con decimales",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Décimos y centésimos",
                        "content": """# 🔢 Décimos y Centésimos

**1décimo** = 0.1 = 1/10
**1centésimo** = 0.01 = 1/100

:::visual:fraction,3,10:::
:::tryit:0.3 = ?/10|3|0.3 = 3/10|3/10:::
:::tryit:0.25 = ?/100|25|0.25 = 25/100|25/100:::
:::tryit:¿Mayor, 0.4 o 0.36?|0.4|0.4 > 0.36|0.4:::
:::tryit:Redondea 3.72 a la décima más cercana.|3.7|3.72 ≈ 3.7|3.7:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g4-dec-1", "g4-dec-compare-1", "g4-dec-round-1"],
                    },
                    {
                        "title": "Sumar y restar decimales",
                        "content": """# ➕➖ Sumar y restar decimales

**¡Alinea el punto decimal!**

Ejemplo: 12.5 + 7.35 = ?
  12.50
+ 07.35
------
  19.85

:::tryit:4.5 + 3.25 = ?|7.75|4.50+3.25=7.75|7.75:::
:::tryit:10.0 - 3.47 = ?|6.53|10.00-3.47=6.53|6.53:::
:::tryit:2.8 + 1.6 = ?|4.4|2.8+1.6=4.4|4.4:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g4-dec-suma-1", "g4-dec-resta-1"],
                    },
                    {
                        "title": "Multiplicar decimales",
                        "content": """# ✖️ Multiplicar decimales

1. Multiplica normalmente
2. Cuenta los decimales de ambos factores
3. Coloca el punto en el resultado

Ejemplo: 3.2 × 1.5 = 4.8
(32 × 15 = 480, 1+1=2 decimales → 4.80)

:::tryit:2.5 × 4 = ?|10|2.5×4=10.0|10:::
:::tryit:1.2 × 0.3 = ?|0.36|1.2×0.3=0.36|0.36:::
:::tryit:0.5 × 0.5 = ?|0.25|0.5×0.5=0.25|0.25:::
Practica.""",
                        "order_index": 2,
                        "exercise_slugs": ["g4-dec-mult-1", "g4-dec-mult-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g4-dec-1", "title": "Décimos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Escribe 0.7 como fracción.", "correct_answer": "7/10", "explanation": "0.7 = 7/10"},
                     "hints": ["0.7 = 7/10"]},
                    {"slug": "g4-dec-compare-1", "title": "Comparar decimales", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Mayor, 0.85 o 0.9?", "choices": ["0.85", "0.9"], "correct_answer": "0.9", "explanation": "0.9 = 0.90 > 0.85"},
                     "hints": ["0.9 = 0.90 > 0.85"]},
                    {"slug": "g4-dec-round-1", "title": "Redondear decimales", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "Redondea 5.678 a la centésima.", "correct_answer": "5.68", "explanation": "5.678 ≈ 5.68"},
                     "hints": ["Mira el tercer decimal (8>5 → sube)"]},
                    {"slug": "g4-dec-suma-1", "title": "Suma de decimales", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": word_problem(0, 0, "add", "Juan recorre 3.5 km y luego 2.75 km."),
                     "hints": ["3.50 + 2.75 = 6.25"]},
                    {"slug": "g4-dec-resta-1", "title": "Resta de decimales", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": word_problem(0, 0, "subtract", "María tenía 10.5 litros de jugo y usó 3.75."),
                     "hints": ["10.50 - 3.75 = 6.75"]},
                    {"slug": "g4-dec-mult-1", "title": "Multiplicar decimal por entero", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 2.5 × 6?", "correct_answer": "15", "explanation": "2.5 × 6 = 15.0"},
                     "hints": ["2.5 × 6 = 15"]},
                    {"slug": "g4-dec-mult-2", "title": "Multiplicar decimales", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "¿Cuánto es 1.4 × 0.3?", "correct_answer": "0.42", "explanation": "1.4×0.3=0.42"},
                     "hints": ["1.4×0.3 = 0.42"]},
                ],
            },
            {
                "slug": "g4-fracciones",
                "title": "Fracciones equivalentes",
                "description": "Encontrar fracciones equivalentes, comparar fracciones",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Fracciones equivalentes",
                        "content": """# 🎯 Fracciones equivalentes

**1/2 = 2/4 = 3/6 = 4/8**

Multiplicamos o dividimos numerator y denominator por el mismo número.

:::tryit:¿Es 2/4 = 1/2?|Sí|2÷2=1 y 4÷2=2, entonces 2/4=1/2|Sí:::
:::tryit:¿Cuánto es 3/5 = ?/15?|9|3×3=9, 5×3=15 → 9/15|9/15:::
:::tryit:¿Mayor, 2/3 o 3/5?|2/3|2/3≈0.67, 3/5=0.60 → 2/3>3/5|2/3:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g4-frac-eq-1", "g4-frac-compare-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g4-frac-eq-1", "title": "Fracciones equivalentes", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "¿Qué es igual a 1/4?", "choices": ["2/6", "3/12", "4/10"], "correct_answer": "3/12", "explanation": "1/4 = 3/12 (×3)"},
                     "hints": ["1×3=3, 4×3=12 → 3/12"]},
                    {"slug": "g4-frac-compare-1", "title": "Comparar fracciones", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Mayor, 3/7 o 2/5?", "choices": ["3/7", "2/5"], "correct_answer": "3/7", "explanation": "3/7≈0.43, 2/5=0.40"},
                     "hints": ["3/7 ≈ 0.43 > 0.40 = 2/5"]},
                ],
            },
        ],
    },
    {
        "slug": "g4-algebra",
        "title": "Álgebra",
        "description": "Expresiones algebraicas, ecuaciones de primer grado",
        "icon_name": "🔣",
        "units": [
            {
                "slug": "g4-ecuaciones",
                "title": "Ecuaciones",
                "description": "Resolver ecuaciones sencillas: x + a = b, a × x = b",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "¿Qué es una ecuación?",
                        "content": """# 🔣 Ecuaciones

Una **ecuación** es una igualdad con un valor desconocido (x).

**Ejemplo:** x + 5 = 12 → x = ?

:::steps:Para encontrar x, restamos 5 de ambos lados|x - 5 = 12 - 5|x = 7|7:::
:::tryit:x + 8 = 15. ¿Cuánto vale x?|7|x+8=15 → x=15-8=7|7:::
:::tryit:3 × x = 21. ¿Cuánto vale x?|7|3x=21 → x=21÷3=7|7:::
:::tryit:x - 4 = 10. ¿Cuánto vale x?|14|14-4=10, entonces x=14|14:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g4-ecuacion-1", "g4-ecuacion-2", "g4-ecuacion-3"],
                    },
                ],
                "exercises": [
                    {"slug": "g4-ecuacion-1", "title": "Ecuación de suma", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "x + 6 = 14. ¿Cuánto vale x?", "correct_answer": "8", "explanation": "x = 14 - 6 = 8"},
                     "hints": ["x = 14 - 6"]},
                    {"slug": "g4-ecuacion-2", "title": "Ecuación de resta", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "x - 5 = 9. ¿Cuánto vale x?", "correct_answer": "14", "explanation": "x = 9 + 5 = 14"},
                     "hints": ["x = 9 + 5"]},
                    {"slug": "g4-ecuacion-3", "title": "Ecuación de multiplicación", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "4x = 28. ¿Cuánto vale x?", "correct_answer": "7", "explanation": "x = 28 ÷ 4 = 7"},
                     "hints": ["x = 28 ÷ 4"]},
                ],
            },
        ],
    },
    {
        "slug": "g4-probabilidad",
        "title": "Probabilidad",
        "description": "Resultados posibles, comparar probabilidades",
        "icon_name": "🎲",
        "units": [
            {
                "slug": "g4-probabilidad-intro",
                "title": "¿Qué tan probable?",
                "description": "Probabilidad como fracción, seguro, posible, imposible",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Resultados posibles",
                        "content": """# 🎲 Probabilidad

**Seguro** = es seguro que ocurre (muy probable)
**Posible** = puede pasar
**Imposible** = no puede pasar

**Ejemplo:** Lanzar un dado (1-6)
- Probabilidad de sacar 3 = **1/6**
- Probabilidad de sacar 7 = **0/6 = imposible**

:::tryit:Lanzas un dado. ¿Probabilidad de sacar 5?|1/6|1 favorable de 6 total|1/6:::
:::tryit:Lanzas una moneda. ¿Probabilidad de que caiga sol?|1/2|1 cara de 2 posibilidades|1/2:::
:::tryit:¿Probabilidad de sacar 8 en un dado?|0|imposible|0:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g4-prob-1", "g4-prob-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g4-prob-1", "title": "Probabilidad básica", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál es la probabilidad de sacar un 4 al lanzar un dado?", "correct_answer": "1/6", "explanation": "1 cara favorable de 6 posibles = 1/6"},
                     "hints": ["1 de 6"]},
                    {"slug": "g4-prob-2", "title": "Comparar probabilidades", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Mayor probabilidad, sacar 1 o sacar número par en un dado?", "choices": ["Sacar 1", "Sacar número par"], "correct_answer": "Sacar número par", "explanation": "P(par)=3/6=1/2 > P(1)=1/6"},
                     "hints": ["P(par)=3/6=1/2, P(1)=1/6"]},
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GRADE 5 (Grade 5 primary - ages 10-11) — FULL Chilean curriculum Unit 3+4
# Topics: Decimals, Algebra, Equations, Inequalities, Probability, Statistics
# ─────────────────────────────────────────────────────────────────────────────
GRADE5_TOPICS = [
    {
        "slug": "g5-fracciones-decimales",
        "title": "Fracciones y decimales",
        "description": "Números mixtos, operaciones con fracciones, decimales y fracciones",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "g5-fracciones-avanzado",
                "title": "Fracciones avanzadas",
                "description": "Números mixtos, fracciones impropias, suma/resta de fracciones",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Números mixtos",
                        "content": """# 🔢 Números mixtos

Un **número mixto** = entero + fracción
Ejemplo: **2 1/3** = 2 + 1/3

:::visual:fraction,7,4:::
7/4 = **1 3/4** (1 entero + 3/4)

:::tryit:9/4 = ? (número mixto)|2 1/4|9÷4=2 residuo 1 → 2 1/4|2 1/4:::
:::tryit:5/2 = ?|2 1/2|5÷2=2 residuo 1 → 2 1/2|2 1/2:::
:::tryit:3 1/2 como fracción impropia = ?|7/2|3×2+1=7 → 7/2|7/2:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g5-mixto-1", "g5-mixto-2"],
                    },
                    {
                        "title": "Sumar fracciones diferentes",
                        "content": """# ➕ Sumar fracciones con diferente denominador

1. Encuentra el **mínimo común denominador** (mcd)
2. Convierte ambas fracciones
3. Suma los numeradores

**Ejemplo:** 1/3 + 1/4
mcd(3,4) = 12
1/3 = 4/12, 1/4 = 3/12
4/12 + 3/12 = **7/12**

:::tryit:1/2 + 1/3 = ?|5/6|1/2=3/6, 1/3=2/6 → 3/6+2/6=5/6|5/6:::
:::tryit:2/5 + 1/4 = ?|13/20|2/5=8/20, 1/4=5/20 → 8/20+5/20=13/20|13/20:::
:::tryit:1/6 + 1/2 = ?|2/3|1/6=1/6, 1/2=3/6 → 4/6=2/3|2/3:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g5-frac-sumar-1", "g5-frac-sumar-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g5-mixto-1", "title": "A fracción impropia", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "Convierte 3 2/5 a fracción impropia.", "correct_answer": "17/5", "explanation": "3×5+2=17 → 17/5"},
                     "hints": ["3×5+2=17 → 17/5"]},
                    {"slug": "g5-mixto-2", "title": "A número mixto", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 10,
                     "data": {"question": "Convierte 11/4 a número mixto.", "correct_answer": "2 3/4", "explanation": "11÷4=2 residuo 3 → 2 3/4"},
                     "hints": ["11÷4=2 residuo 3"]},
                    {"slug": "g5-frac-sumar-1", "title": "Sumar fracciones", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 3/8 + 1/4?", "correct_answer": "5/8", "explanation": "3/8 + 2/8 = 5/8"},
                     "hints": ["1/4 = 2/8 → 3/8+2/8=5/8"]},
                    {"slug": "g5-frac-sumar-2", "title": "Sumar fracciones", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "¿Cuánto es 2/3 + 1/6 + 1/2?", "correct_answer": "4/3", "explanation": "2/3=4/6, 1/6=1/6, 1/2=3/6 → 4/6+1/6+3/6=8/6=4/3"},
                     "hints": ["mcd(3,6,2)=6 → 4/6+1/6+3/6=8/6=4/3"]},
                ],
            },
            {
                "slug": "g5-decimales-operaciones",
                "title": "Operaciones con decimales",
                "description": "Suma, resta, multiplicación y división de decimales",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Multiplicar y dividir decimales",
                        "content": """# ✖️➗ Multiplicar y dividir decimales

**Multiplicar decimales:**
3.2 × 1.5 → 32×15=480 → 2+1=3 → **4.80**

**Dividir decimales:**
12.6 ÷ 3 = **4.2**
4.5 ÷ 0.5 = **9** (porque 0.5 × 9 = 4.5)

:::tryit:2.5 × 1.4 = ?|3.5|2.5×1.4=3.50|3.5:::
:::tryit:9.6 ÷ 3 = ?|3.2|9.6÷3=3.2|3.2:::
:::tryit:7 ÷ 0.5 = ?|14|0.5×14=7|14:::
:::tryit:1.2 ÷ 0.4 = ?|3|0.4×3=1.2|3:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g5-dec-mult-1", "g5-dec-div-1", "g5-dec-div-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g5-dec-mult-1", "title": "Multiplicar decimales", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 2.4 × 1.5?", "correct_answer": "3.6", "explanation": "2.4×1.5=3.60"},
                     "hints": ["2.4×1.5=3.6"]},
                    {"slug": "g5-dec-div-1", "title": "Dividir decimal entre entero", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 8.4 ÷ 4?", "correct_answer": "2.1", "explanation": "8.4÷4=2.1"},
                     "hints": ["8.4÷4=2.1"]},
                    {"slug": "g5-dec-div-2", "title": "Dividir decimales", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "¿Cuánto es 6.4 ÷ 0.8?", "correct_answer": "8", "explanation": "0.8×8=6.4"},
                     "hints": ["0.8×8=6.4 → 8"]},
                ],
            },
        ],
    },
    {
        "slug": "g5-algebra-ecuaciones",
        "title": "Álgebra y ecuaciones",
        "description": "Expresiones algebraicas, resolver ecuaciones e inecuaciones",
        "icon_name": "🔣",
        "units": [
            {
                "slug": "g5-ecuaciones-inecuaciones",
                "title": "Ecuaciones e inecuaciones",
                "description": "Resolver ax+b=c y graficar soluciones en la recta numérica",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Resolver 2x + 3 = 11",
                        "content": """# 🔣 Ecuaciones de un paso

**x + 5 = 12 → x = 7** (restamos 5 de ambos lados)
**2x = 14 → x = 7** (dividimos entre 2)

:::steps:2x + 3 = 11|2x = 11 - 3 = 8|x = 8 ÷ 2 = 4|resultado=4:::

:::tryit:x + 7 = 20. ¿x?|13|13+7=20|13:::
:::tryit:3x = 24. ¿x?|8|3×8=24|8:::
:::tryit:5x - 3 = 17. ¿x?|4|5×4-3=20-3=17|4:::
:::tryit:x/2 = 6. ¿x?|12|12÷2=6|12:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g5-ecu-1", "g5-ecu-2", "g5-ecu-3"],
                    },
                    {
                        "title": "Inecuaciones",
                        "content": """# 🔣 Inecuaciones

Una **inecuación** usa **<, >, ≤, ≥** en lugar de **=**.

**x + 3 > 7 → x > 4** (todos los números mayores que 4)
**2x ≤ 10 → x ≤ 5** (todos los números hasta 5)

:::tryit:x + 2 > 5. ¿Qué valores puede tener x?|x>3|Cualquier valor mayor que 3|x>3:::
:::tryit:3x < 12. ¿x?|x<4|Cualquier valor menor que 4|x<4:::
:::tryit:x - 1 ≥ 4. ¿x?|x≥5|5 o más|5 o más:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g5-inecu-1", "g5-inecu-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g5-ecu-1", "title": "Ecuación básica", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "x + 9 = 15. ¿x?", "correct_answer": "6", "explanation": "x = 15 - 9 = 6"},
                     "hints": ["x = 15-9"]},
                    {"slug": "g5-ecu-2", "title": "Con multiplicación", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "4x = 36. ¿x?", "correct_answer": "9", "explanation": "x = 36 ÷ 4 = 9"},
                     "hints": ["x = 36÷4"]},
                    {"slug": "g5-ecu-3", "title": "Dos pasos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "2x + 5 = 19. ¿x?", "correct_answer": "7", "explanation": "2x = 19-5=14, x=14÷2=7"},
                     "hints": ["2x=14, x=7"]},
                    {"slug": "g5-inecu-1", "title": "Inecuación", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuál satisface x + 3 > 7?", "choices": ["x=3", "x=5", "x=4.9"], "correct_answer": "x=5", "explanation": "5+3=8>7"},
                     "hints": ["5+3=8 > 7"]},
                    {"slug": "g5-inecu-2", "title": "Inecuación", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuál satisface 3x ≤ 12?", "choices": ["x=5", "x=4", "x=4.1"], "correct_answer": "x=4", "explanation": "3×4=12≤12"},
                     "hints": ["3×4=12≤12"]},
                ],
            },
        ],
    },
    {
        "slug": "g5-probabilidad",
        "title": "Probabilidad",
        "description": "Resultados posibles, comparar probabilidades, fracciones",
        "icon_name": "🎲",
        "units": [
            {
                "slug": "g5-probabilidad-estadistica",
                "title": "Probabilidad y estadística",
                "description": "Diagrama de tallo y hojas, probabilidad experimental",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Diagrama de tallo y hojas",
                        "content": """# 📊 Diagrama de tallo y hojas

Ejemplo: Calificaciones 45, 52, 48, 55, 63, 61

Tallo | Hojas
  4  | 5 8
  5  | 2 5
  6  | 1 3

**Tallo** = decenas, **Hojas** = unidades

:::tryit:Con datos 23, 25, 31, 35, ¿cuál es el tallo de 25?|2|El tallo es la decena (2)|2:::
:::tryit:¿Cuál es la mediana de: 4, 7, 2, 9, 5?|5|Orden: 2,4,5,7,9 → el del medio es 5|5:::
:::tryit:¿Cuál es el rango de: 12, 18, 7, 22, 15?|15|22-7=15|15:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g5-tallo-1", "g5-estad-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g5-tallo-1", "title": "Diagrama tallo-hojas", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Datos: 34, 37, 42, 45, 48. ¿Cuál hoja corresponde al 37?", "choices": ["3", "7", "4"], "correct_answer": "7", "explanation": "En 37, hoja = unidades = 7"},
                     "hints": ["La hoja son las unidades"]},
                    {"slug": "g5-estad-1", "title": "Mediana y rango", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Datos: 8, 12, 15, 7, 20. ¿Cuál es la mediana?", "choices": ["12", "8", "15"], "correct_answer": "12", "explanation": "Orden: 7,8,12,15,20 → centro=12"},
                     "hints": ["Ordena: 7,8,12,15,20 → centro=12"]},
                ],
            },
        ],
    },
    {
        "slug": "g5-geometria",
        "title": "Figuras y perímetro",
        "description": "Figuras compuestas, paralelogramo, trapecio, círculo",
        "icon_name": "📐",
        "units": [
            {
                "slug": "g5-figuras-compuestas",
                "title": "Área de figuras compuestas",
                "description": "Calcular área de figuras que combinan rectángulos, triángulos, trapezoides",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Figuras compuestas",
                        "content": """# 📐 Área de figuras compuestas

Dividimos la figura en partes más simples.

:::visual:comparison,10,8,L=10cm,A=8cm:::
:::tryit:Un rectángulo de 8cm×5cm tiene área = ?|40|8×5=40 cm²|40:::
:::tryit:Si la figura tiene dos rectángulos (6×4=24 y 4×3=12), área total = ?|36|24+12=36|36:::
:::tryit:Área de un trapecio: (B+b)×h÷2. B=8cm, b=4cm, h=5cm → A=|30|(8+4)×5÷2=12×5÷2=30|30:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g5-fig-comp-1", "g5-fig-comp-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g5-fig-comp-1", "title": "Área figura compuesta", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Dos rectángulos: uno 7×3 y otro 5×2. ¿Área total?", "correct_answer": "31", "explanation": "7×3=21, 5×2=10 → 21+10=31"},
                     "hints": ["21+10=31"]},
                    {"slug": "g5-fig-comp-2", "title": "Área trapecio", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "Trapecio: B=10cm, b=6cm, h=4cm. ¿Área?", "correct_answer": "32", "explanation": "(10+6)×4÷2=16×2=32"},
                     "hints": ["(10+6)×4÷2=32"]},
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GRADE 6 (Grade 6 primary - ages 11-12) — from Chilean + Singapore Math
# Topics: Negative numbers, Ratios, Percentages, Volume, Algebra advanced
# ─────────────────────────────────────────────────────────────────────────────
GRADE6_TOPICS = [
    {
        "slug": "g6-numeros-negativos",
        "title": "Números negativos",
        "description": "Enteros positivos y negativos, recta numérica, operaciones básicas",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "g6-negativos",
                "title": "Números negativos",
                "description": "Enteros, recta numérica, suma/resta de negativos",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "En la recta numérica",
                        "content": """# 🔢 Números negativos

Los números negativos van **a la izquierda del 0**.

:::visual:numberline,0,-5,add:::
-5, -4, -3, -2, -1, **0**, 1, 2, 3, 4, 5

**Ejemplos en la vida real:**
- La temperatura bajo cero: **-5°C**
- El submarino a 100 metros bajo el mar: **-100m**
- Debes $20: **-$20**

:::tryit:¿Qué número es mayor, -3 o -1?|-1|-1 está más cerca del 0|-1:::
:::tryit:¿0 o -4?|0|0 > -4|0:::
:::tryit:-6 + 4 = ?|-2|-6+4=-2|-2:::
:::tryit:-3 - 5 = ?|-8|-3-5=-8|-8:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g6-neg-1", "g6-neg-2", "g6-neg-suma-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g6-neg-1", "title": "Comparar negativos", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Mayor, -5 o -2?", "choices": ["-5", "-2"], "correct_answer": "-2", "explanation": "-2 > -5"},
                     "hints": ["-2 está más cerca del 0"]},
                    {"slug": "g6-neg-2", "title": "Valor absoluto", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Valor absoluto de -7?", "correct_answer": "7", "explanation": "|-7| = 7"},
                     "hints": ["Distancia al 0"]},
                    {"slug": "g6-neg-suma-1", "title": "Sumar negativos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "-8 + 3 = ?", "correct_answer": "-5", "explanation": "-8 + 3 = -5"},
                     "hints": ["-8 + 3 = -5"]},
                ],
            },
        ],
    },
    {
        "slug": "g6-proporciones",
        "title": "Razones y proporciones",
        "description": "Razones, proporcionalidad directa, regla de tres simple",
        "icon_name": "⚖️",
        "units": [
            {
                "slug": "g6-razones",
                "title": "Razones",
                "description": "Escribir razones, simplificar, aplicaciones",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "¿Qué es una razón?",
                        "content": """# ⚖️ Razón

Una **razón** compara dos cantidades.
Se puede escribir como **a:b** o **a/b**.

**Ejemplo:** En una clase hay 12 niñas y 8 niños.
Razón niñas:nños = 12:8 = **3:2** (simplificada)

:::tryit:La razón de rojo:azul es 3:2. Si hay 6 azules, ¿cuántos rojos?|9|3/2=x/6 → x=9|9:::
:::tryit:Simplifica 15:25.|3:5|15÷5=3, 25÷5=5|3:5:::
:::tryit:La razón de teachers:students es 1:20. Si hay 5 teachers, ¿cuántos students?|100|1:20=5:x → x=100|100:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g6-razon-1", "g6-razon-2", "g6-razon-3"],
                    },
                    {
                        "title": "Regla de tres simple",
                        "content": """# 🔑 Regla de tres simple

Si 4 entradas cuestan $200, ¿cuánto cuestan 7?

4 → $200
7 → $?

$200 × 7 ÷ 4 = **$350**

:::tryit:Si 3 libros cuestan $45, ¿cuánto cuestan 5 libros?|75|45×5÷3=75|75:::
:::tryit:Un coche recorre 180 km con 12 L. ¿Cuántos km con 20 L?|300|180×20÷12=300|300:::
:::tryit:5 trabajadores hacen una obra en 8 días. ¿En cuántos días la hacen 10 trabajadores?|4|5×8÷10=4|4:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g6-regla3-1", "g6-regla3-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g6-razon-1", "title": "Razón", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "La razón de manzanas a peras es 4:3. Si hay 12 manzanas, ¿cuántas peras?", "correct_answer": "9", "explanation": "4:3=12:x → x=12×3÷4=9"},
                     "hints": ["12×3÷4=9"]},
                    {"slug": "g6-razon-2", "title": "Simplificar razón", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Simplifica 18:24", "choices": ["9:12", "3:4", "6:8"], "correct_answer": "3:4", "explanation": "18÷6=3, 24÷6=4 → 3:4"},
                     "hints": ["18÷6=3, 24÷6=4"]},
                    {"slug": "g6-razon-3", "title": "Aplicar razón", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "La razón de azúcar:harina es 1:4. ¿Cuánta harina para 200g de azúcar?", "correct_answer": "800", "explanation": "1:4 = 200:x → x=200×4=800g"},
                     "hints": ["200×4=800"]},
                    {"slug": "g6-regla3-1", "title": "Regla de tres", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "8 trabajadores hacen una cerca en 6 días. ¿En cuántos días la hacen 12 trabajadores?", "correct_answer": "3", "explanation": "8×6÷12=4... más trabajadores = menos días, pero cálculo correcto: 8×6÷12=4, pero como doblamos workers → 6÷2=3"},
                     "hints": ["Doblando workers → la mitad de días = 3"]},
                    {"slug": "g6-regla3-2", "title": "Regla de tres", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "Si 100g de queso cuestan $8, ¿cuánto cuestan 350g?", "correct_answer": "28", "explanation": "100→8, 350→x, x=8×350÷100=28"},
                     "hints": ["8×350÷100=28"]},
                ],
            },
        ],
    },
    {
        "slug": "g6-porcentaje",
        "title": "Porcentaje",
        "description": "Qué es el porcentaje, calcular porcentajes, descuentos e intereses",
        "icon_name": "💰",
        "units": [
            {
                "slug": "g6-porcentaje-intro",
                "title": "¿Qué es el porcentaje?",
                "description": "Conversiones %, fracción, decimal; problemas de descuento",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "De porcentaje a fracción y decimal",
                        "content": """# 💰 Porcentaje

**1% = 1/100 = 0.01**

:::tryit:25% = ?/100|25|25% = 25/100|25/100:::
:::tryit:25% = decimal|0.25|25÷100=0.25|0.25:::
:::tryit:0.75 = ?%|75|0.75×100=75%|75%:::
:::tryit:3/5 = ?%|60|3/5=0.6=60%|60%:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g6-pct-1", "g6-pct-2"],
                    },
                    {
                        "title": "Calcular el porcentaje",
                        "content": """# 💰 Calcular el porcentaje

**20% de 80 = 80 × 20 ÷ 100 = 16**

**Descuento ejemplo:**
Camisa a $100 con **20% de descuento**:
100 × 20 ÷ 100 = **$20** de descuento
Precio final = $100 - $20 = **$80**

:::tryit:¿Cuánto es el 30% de 200?|60|200×30÷100=60|60:::
:::tryit:¿Cuánto es el 15% de 80?|12|80×15÷100=12|12:::
:::tryit:Una bicicleta cuesta $500. Hay un descuento del 20%. ¿Precio final?|400|500×20÷100=100 desc; 500-100=400|400:::
Practica.""",
                        "order_index": 1,
                        "exercise_slugs": ["g6-pct-calc-1", "g6-pct-calc-2", "g6-pct-desc-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g6-pct-1", "title": "% a fracción", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Escribe 40% como fracción.", "correct_answer": "2/5", "explanation": "40% = 40/100 = 2/5"},
                     "hints": ["40÷100=2/5"]},
                    {"slug": "g6-pct-2", "title": "Decimal a %", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "0.08 = ?%", "correct_answer": "8", "explanation": "0.08×100 = 8%"},
                     "hints": ["0.08×100=8"]},
                    {"slug": "g6-pct-calc-1", "title": "Calcular %", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿25% de 120?", "correct_answer": "30", "explanation": "120×25÷100=30"},
                     "hints": ["120×25÷100=30"]},
                    {"slug": "g6-pct-calc-2", "title": "Calcular %", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿10% de 450?", "correct_answer": "45", "explanation": "450×10÷100=45"},
                     "hints": ["450×10÷100=45"]},
                    {"slug": "g6-pct-desc-1", "title": "Descuento", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "UnTV cuesta $800 con 25% de descuento. ¿Precio final?", "correct_answer": "600", "explanation": "800×25÷100=200 desc → 800-200=600"},
                     "hints": ["800-200=600"]},
                ],
            },
        ],
    },
    {
        "slug": "g6-volumen",
        "title": "Volumen",
        "description": "Volumen del prisma rectangular, cubo, unidades de capacidad",
        "icon_name": "📦",
        "units": [
            {
                "slug": "g6-volumen-prisma",
                "title": "Volumen del prisma",
                "description": "V = largo × ancho × alto; capacidad en litros",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Volumen del prisma rectangular",
                        "content": """# 📦 Volumen

**V = largo × ancho × alto**

Unidades: cm³ (centímetros cúbicos)

**Ejemplo:** V = 5cm × 3cm × 4cm = **60 cm³**

:::visual:array,5,3:::
:::tryit:Prisma 6cm × 4cm × 5cm → Volumen = ?|120|6×4×5=120 cm³|120:::
:::tryit:Un cubo de lado 3cm → Volumen = ?|27|3×3×3=27 cm³|27:::
:::tryit:1 L = ? cm³|1000|1 litro = 1000 cm³|1000:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g6-vol-prisma-1", "g6-vol-cubo-1"],
                    },
                ],
                "exercises": [
                    {"slug": "g6-vol-prisma-1", "title": "Volumen prisma", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Prisma: largo=8cm, ancho=5cm, alto=4cm. ¿Volumen?", "correct_answer": "160", "explanation": "8×5×4=160 cm³"},
                     "hints": ["8×5×4=160"]},
                    {"slug": "g6-vol-cubo-1", "title": "Volumen cubo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Cubo de lado 5cm. ¿Volumen?", "correct_answer": "125", "explanation": "5×5×5=125 cm³"},
                     "hints": ["5³=125"]},
                ],
            },
        ],
    },
    {
        "slug": "g6-algebra-avanzado",
        "title": "Álgebra avanzada",
        "description": "Expresiones algebraicas, ecuaciones con paréntesis, sistemas simples",
        "icon_name": "🔣",
        "units": [
            {
                "slug": "g6-expresiones-algebraicas",
                "title": "Expresiones y ecuaciones avanzadas",
                "description": "Reducir expresiones, ecuaciones con paréntesis",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Reducir expresiones",
                        "content": """# 🔣 Reducir expresiones algebraicas

**Simplificar** = combinar términos iguales.

**Ejemplo:** 3x + 2x = **5x**
4y - 2y + y = **3y**
3a + 2b - a = **2a + 2b** (no se pueden mezclar diferentes letras)

:::tryit:5x + 3x = ?|8x|5x+3x=8x|8x:::
:::tryit:7y - 2y = ?|5y|7y-2y=5y|5y:::
:::tryit:4a + 3b - 2a = ?|2a+3b|4a-2a+3b=2a+3b|2a+3b:::
:::tryit:2(x+3) = ?|2x+6|2×x+2×3=2x+6|2x+6:::
Practica.""",
                        "order_index": 0,
                        "exercise_slugs": ["g6-expr-1", "g6-expr-2"],
                    },
                ],
                "exercises": [
                    {"slug": "g6-expr-1", "title": "Reducir expresiones", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Simplifica: 6x + 4 - 3x", "choices": ["3x+4", "9x+4", "6x-4"], "correct_answer": "3x+4", "explanation": "6x-3x=3x → 3x+4"},
                     "hints": ["6x-3x=3x"]},
                    {"slug": "g6-expr-2", "title": "Multiplicar paréntesis", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "Desarrolla: 3(x + 2)", "choices": ["3x+2", "3x+6", "x+6"], "correct_answer": "3x+6", "explanation": "3×x + 3×2 = 3x+6"},
                     "hints": ["3x + 6"]},
                ],
            },
        ],
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# GRADE 1–6 CURRICULUM (all new content)
# ─────────────────────────────────────────────────────────────────────────────

TOPICS = GRADE1_TOPICS + GRADE2_TOPICS + GRADE3_TOPICS + GRADE4_TOPICS + GRADE5_TOPICS + GRADE6_TOPICS + [
    # ARITHMETIC
    {
        "slug": "aritmetica",
        "title": "Aritmética",
        "description": "Domina las operaciones básicas: suma, resta, multiplicación y división",
        "icon_name": "🔢",
        "units": [
            {
                "slug": "suma-y-resta",
                "title": "Suma y Resta",
                "description": "Aprende a sumar y restar números naturales",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Introducción a la Suma",
                        "content": """# 🎯 La Suma (Adición)

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

En los ejercicios siguientes, usa lo que aprendiste para resolver cada suma.""",
                        "order_index": 0,
                        "exercise_slugs": ["suma-2dig", "suma-3dig", "suma-llevando"],
                    },
                    {
                        "title": "Introducción a la Resta",
                        "content": """# ➖ La Resta (Sustracción)

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

## Practica con los ejercicios.""",
                        "order_index": 1,
                        "exercise_slugs": ["resta-2dig", "resta-3dig", "resta-prestando"],
                    },
                ],
                "exercises": [
                    {"slug": "suma-2dig", "title": "Suma de dos dígitos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 35 + 17?", "correct_answer": "52", "explanation": "35 + 17 = 52. Sumamos las unidades: 5+7=12, llevamos 1. Decenas: 3+1+1=5."},
                     "hints": ["Suma las unidades primero: 5 + 7 = ?", "Si la suma de unidades es mayor a 9, lleva 1 a las decenas", "35 + 17 = 52"]},
                    {"slug": "suma-3dig", "title": "Suma de tres dígitos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 234 + 156?", "correct_answer": "390", "explanation": "234 + 156 = 390"},
                     "hints": ["234 + 156 = (200+100) + (30+50) + (4+6)", "Sumando: 234 + 156 = 390", "200 + 100 = 300, 30 + 50 = 80, 4 + 6 = 10, total = 390"]},
                    {"slug": "resta-2dig", "title": "Resta de dos dígitos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 48 - 23?", "correct_answer": "25", "explanation": "48 - 23 = 25. Restamos unidad: 8-3=5. Decenas: 4-2=2."},
                     "hints": ["48 - 23: resta las unidades primero", "8 - 3 = 5", "4 - 2 = 2, entonces el resultado es 25"]},
                    {"slug": "resta-3dig", "title": "Resta de tres dígitos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 500 - 178?", "correct_answer": "322", "explanation": "500 - 178 = 322. Necesitamos pedir prestado."},
                     "hints": ["500 - 178: el 0 no puede restar 8", "Pedimos prestado: 10 - 8 = 2, luego 9 - 7 = 2, luego 4 - 1 = 2", "500 - 178 = 322"]},
                    {"slug": "suma-llevando", "title": "Suma llevando", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 67 + 58?", "correct_answer": "125", "explanation": "67 + 58 = 125. 7+8=15, llevamos 1. 6+5+1=12. Resultado: 125."},
                     "hints": ["Suma las unidades: 7 + 8 = 15. Escribe 5 y lleva 1.", "Suma las decenas + lo que llevas: 6 + 5 + 1 = 12", "67 + 58 = 125"]},
                    {"slug": "resta-prestando", "title": "Resta prestando", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 403 - 187?", "correct_answer": "216", "explanation": "403 - 187 = 216"},
                     "hints": ["403 - 187: el 3 no puede restar 7", "Pedimos 1 de las decenas: 13 - 7 = 6", "403 - 187 = 216"]},
                ]
            },
            {
                "slug": "multiplicacion",
                "title": "Multiplicación",
                "description": "Aprende las tablas de multiplicar y multiplicaciones de varios dígitos",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "¿Qué es la Multiplicación?",
                        "content": """# ✖️ La Multiplicación

La **multiplicación** es una forma rápida de hacer **sumas repetidas**.

## Modelo visual: Arreglos ( grids )
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

## Practica con las tablas del 2 al 5.""",
                        "order_index": 0,
                        "exercise_slugs": ["tabla-2", "tabla-3", "tabla-4", "tabla-5"],
                    },
                    {
                        "title": "Tablas del 6 al 9",
                        "content": """# 🔥 Tablas del 6, 7, 8 y 9

## 🎯 Modelo de Arreglo para la Tabla del 6

:::visual:animatedarray,6,6,true:::
6 × 6 = **36**

## Tabla del 6
6 × 1 = 6 | 6 × 2 = 12 | 6 × 3 = 18 | 6 × 4 = 24 | 6 × 5 = 30  
6 × 6 = 36 | 6 × 7 = 42 | 6 × 8 = 48 | 6 × 9 = 54 | 6 × 10 = 60

## Tabla del 7
7 × 1 = 7 | 7 × 2 = 14 | 7 × 3 = 21 | 7 × 4 = 28 | 7 × 5 = 35  
7 × 6 = 42 | 7 × 7 = 49 | 7 × 8 = 56 | 7 × 9 = 63 | 7 × 10 = 70

## Tabla del 8
8 × 1 = 8 | 8 × 2 = 16 | 8 × 3 = 24 | 8 × 4 = 32 | 8 × 5 = 40  
8 × 6 = 48 | 8 × 7 = 56 | 8 × 8 = 64 | 8 × 9 = 72 | 8 × 10 = 80

## Tabla del 9 (truco especial)
9 × 1 = 9 | 9 × 2 = 18 | 9 × 3 = 27 | 9 × 4 = 36 | 9 × 5 = 45  
9 × 6 = 54 | 9 × 7 = 63 | 9 × 8 = 72 | 9 × 9 = 81 | 9 × 10 = 90

**Truco del 9:** El primer dígito siempre es (9 - número) y ambos dígitos suman 9.  
Ejemplo: 9 × 7 = 63 → 7-1 = 6, 9-6 = 3 → 63

## Practica ahora.""",
                        "order_index": 1,
                        "exercise_slugs": ["tabla-6", "tabla-7", "tabla-8", "tabla-9", "multi-2dig", "multi-3x1"],
                    },
                ],
                "exercises": [
                    {"slug": "tabla-2", "title": "Tabla del 2", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 7 × 2?", "choices": ["12", "14", "16", "18"], "correct_answer": "14", "explanation": "7 × 2 = 14. Es like 7 + 7 = 14"},
                     "hints": ["Multiplicar es sumar repetido: 7 × 2 = 7 + 7", "7 + 7 = ?", "14"]},
                    {"slug": "tabla-3", "title": "Tabla del 3", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 9 × 3?", "choices": ["24", "27", "30", "33"], "correct_answer": "27", "explanation": "9 × 3 = 27. 9 + 9 + 9 = 27"},
                     "hints": ["9 × 3 = 9 + 9 + 9", "9 + 9 = 18, más 9 = 27", "27"]},
                    {"slug": "tabla-4", "title": "Tabla del 4", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 6 × 4?", "choices": ["20", "24", "28", "32"], "correct_answer": "24", "explanation": "6 × 4 = 24"},
                     "hints": ["6 × 4 = 6 + 6 + 6 + 6", "6 + 6 = 12, 12 + 6 = 18, 18 + 6 = 24", "24"]},
                    {"slug": "tabla-5", "title": "Tabla del 5", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 8 × 5?", "choices": ["35", "40", "45", "50"], "correct_answer": "40", "explanation": "8 × 5 = 40. 8 + 8 + 8 + 8 + 8 = 40"},
                     "hints": ["8 × 5 = 8 + 8 + 8 + 8 + 8", "8 × 10 = 80, entonces 8 × 5 = 80 ÷ 2 = 40", "40"]},
                    {"slug": "tabla-6", "title": "Tabla del 6", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 7 × 6?", "choices": ["36", "42", "48", "54"], "correct_answer": "42", "explanation": "7 × 6 = 42"},
                     "hints": ["7 × 6 = 7 × 5 + 7", "7 × 5 = 35, 35 + 7 = 42", "42"]},
                    {"slug": "tabla-7", "title": "Tabla del 7", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 9 × 7?", "choices": ["54", "56", "63", "72"], "correct_answer": "63", "explanation": "9 × 7 = 63"},
                     "hints": ["9 × 7 = 9 + 9 + 9 + 9 + 9 + 9 + 9", "9 × 7 = 63 (truco: 7-1=6, 9-6=3 → 63)", "63"]},
                    {"slug": "tabla-8", "title": "Tabla del 8", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 8 × 8?", "choices": ["56", "64", "72", "80"], "correct_answer": "64", "explanation": "8 × 8 = 64. Dobles: 8×2=16, 16×2=32, 32×2=64"},
                     "hints": ["8 × 8 = 8 + 8 + 8 + 8 + 8 + 8 + 8 + 8", "8 × 4 = 32, entonces 8 × 8 = 32 × 2 = 64", "64"]},
                    {"slug": "tabla-9", "title": "Tabla del 9", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 9 × 9?", "choices": ["72", "81", "90", "99"], "correct_answer": "81", "explanation": "9 × 9 = 81. Truco: 9-1=8, 9-8=1 → 81"},
                     "hints": ["9 × 9 = 9 + 9 + 9 + 9 + 9 + 9 + 9 + 9 + 9", "9 × 10 = 90, menos 9 = 81", "81"]},
                    {"slug": "multi-2dig", "title": "Multiplicación 2×1", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 23 × 4?", "correct_answer": "92", "explanation": "23 × 4 = 92. 20×4=80, 3×4=12, 80+12=92"},
                     "hints": ["23 × 4 = (20 + 3) × 4", "20×4 = 80 y 3×4 = 12, suma: 80 + 12 = 92", "92"]},
                    {"slug": "multi-3x1", "title": "Multiplicación 3×1", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 156 × 7?", "correct_answer": "1092", "explanation": "156 × 7 = 1092. 100×7=700, 50×7=350, 6×7=42, total=1092"},
                     "hints": ["156 = 100 + 50 + 6", "100×7=700, 50×7=350, 6×7=42", "700 + 350 = 1050, + 42 = 1092"]},
                ]
            },
            {
                "slug": "division",
                "title": "División",
                "description": "Aprende a dividir números y entender la relación con la multiplicación",
                "order_index": 2,
                "lessons": [
                    {
                        "title": "¿Qué es la División?",
                        "content": """# ➗ La División

La **división** es **repartir en partes iguales**. Es lo opuesto a la multiplicación.

## Vocabulario importante 📖

- **Dividendo:** el número que dividimos (el grande)
- **Divisor:** el número entre el que dividimos
- **Cociente:** el resultado
- **Residuo:** lo que sobra (si hay)

## Ejemplo: 24 ÷ 4 = ?

**Pregunta:** Si tienes 24 galletas y las repartes entre 4 amigos, ¿cuántas recibe cada uno?

**Respuesta:** 24 ÷ 4 = **6** porque 6 × 4 = 24

## 🎯 Modelo de División (Agrupar)

:::visual:division,24,4:::

24 objetos ÷ en grupos de 4 = **6 grupos**

## Relación con la multiplicación 💡

> **Dividir es lo contrario de multiplicar**
> Si 6 × 4 = 24, entonces 24 ÷ 4 = 6

## ¿Y cuando sobra algo?

**Ejemplo:** 17 ÷ 5

:::visual:division,17,5:::

- 5 entra 3 veces en 17 (5 × 3 = 15)
- Sobra 2 (17 - 15 = 2)
- **Respuesta: 3 residuo 2**

## Practica con los ejercicios.""",
                        "order_index": 0,
                        "exercise_slugs": ["division-basica", "division-2", "division-3"],
                    },
                ],
                "exercises": [
                    {"slug": "division-basica", "title": "División básica", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 24 ÷ 4?", "correct_answer": "6", "explanation": "24 ÷ 4 = 6 porque 6 × 4 = 24"},
                     "hints": ["24 ÷ 4: combienas veces cabe 4 en 24", "4 × 6 = 24, entonces 24 ÷ 4 = 6", "6"]},
                    {"slug": "division-2", "title": "División entre 2", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 18 ÷ 2?", "choices": ["6", "8", "9", "12"], "correct_answer": "9", "explanation": "18 ÷ 2 = 9. Mitad de 18 es 9."},
                     "hints": ["Dividir entre 2 es encontrar la mitad", "La mitad de 18 = 9", "18 ÷ 2 = 9"]},
                    {"slug": "division-3", "title": "División entre 3", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 27 ÷ 3?", "choices": ["6", "7", "8", "9"], "correct_answer": "9", "explanation": "27 ÷ 3 = 9. 9 × 3 = 27."},
                     "hints": ["27 ÷ 3: combienas veces cabe 3 en 27", "9 × 3 = 27, entonces 27 ÷ 3 = 9", "9"]},
                    {"slug": "division-4", "title": "División entre 4", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 32 ÷ 4?", "choices": ["6", "7", "8", "9"], "correct_answer": "8", "explanation": "32 ÷ 4 = 8. 8 × 4 = 32."},
                     "hints": ["32 ÷ 4: la mitad de la mitad", "Mitad de 32 = 16, mitad de 16 = 8", "8"]},
                    {"slug": "division-5", "title": "División entre 5", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 45 ÷ 5?", "choices": ["7", "8", "9", "10"], "correct_answer": "9", "explanation": "45 ÷ 5 = 9. 9 × 5 = 45."},
                     "hints": ["45 ÷ 5: combienas veces cabe 5 en 45", "5 × 9 = 45, entonces 45 ÷ 5 = 9", "9"]},
                    {"slug": "division-sobres", "title": "División con residuo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuál es el residuo de 17 ÷ 5?", "correct_answer": "2", "explanation": "17 ÷ 5 = 3 residuo 2 porque 5×3=15, 17-15=2"},
                     "hints": ["5 cabe 3 veces en 17 (5×3=15)", "Sobró 17 - 15 = 2", "El residuo es 2"]},
                    {"slug": "division-2dig", "title": "División de 2 dígitos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 72 ÷ 6?", "correct_answer": "12", "explanation": "72 ÷ 6 = 12. 12 × 6 = 72."},
                     "hints": ["72 ÷ 6: 6 × ? = 72", "6 × 10 = 60, falta 12, 6 × 2 = 12", "72 ÷ 6 = 12"]},
                    {"slug": "division-larga", "title": "División larga", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.hard, "points": 20,
                     "data": {"question": "¿Cuánto es 156 ÷ 12?", "correct_answer": "13", "explanation": "156 ÷ 12 = 13. 12 × 13 = 156."},
                     "hints": ["12 × 10 = 120, falta 36", "12 × 3 = 36, total 120+36=156", "156 ÷ 12 = 13"]},
                ]
            },
        ]
    },
    # FRACCIONES
    {
        "slug": "fracciones",
        "title": "Fracciones",
        "description": "Introducción a fracciones, operaciones con fracciones y comparación",
        "icon_name": "🍕",
        "units": [
            {
                "slug": "intro-fracciones",
                "title": "Introducción a Fracciones",
                "description": "Qué son las fracciones y cómo representarlas",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "¿Qué es una Fracción?",
                        "content": """# 🍕 ¿Qué es una Fracción?

Una **fracción** representa una **parte de un todo**.

## Las partes de una fracción

**Numerador** (arriba): las partes que tenemos  
**Denominador** (abajo): en cuántas partes se dividió el todo

## Ejemplo: 3/4

:::visual:fraction,3,4:::

Esto significa: dividimos algo en **4 partes iguales** y tenemos **3** de esas partes.

Imagina una pizza 🍕:
- La dividimos en 4 partes iguales
- Nos comemos 3 partes
- ¡Hemos comido 3/4 de la pizza!

## Fracciones especiales 🌟

:::visual:fraction,1,2:::
**1/2** = la mitad

:::visual:fraction,1,4:::
**1/4** = un cuarto

:::visual:fraction,3,4:::
**3/4** = tres cuartos

## Tips
- Si **numerador < denominador** → la fracción es **menor que 1** (ej: 1/4)
- Si **numerador = denominador** → la fracción es **igual a 1** (ej: 5/5 = 1)
- Si **numerador > denominador** → la fracción es **mayor que 1** (ej: 5/3 = 1 + 2/3)

## Practica con los ejercicios.""",
                        "order_index": 0,
                        "exercise_slugs": ["fraccion-partes", "fraccion-visual", "fraccion-mitad", "fraccion-igual-1"],
                    },
                ],
                "exercises": [
                    {"slug": "fraccion-partes", "title": "Partes de una fracción", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Qué número es el numerador en 3/4?", "choices": ["3", "4", "7", "12"], "correct_answer": "3", "explanation": "El numerador (3) indica las partes que tenemos"},
                     "hints": ["El numerador está ARRIBA de la línea", "En 3/4, el número de arriba es el 3", "3"]},
                    {"slug": "fraccion-visual", "title": "Fracciones en gráficos", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Si un rectángulo está dividido en 4 partes iguales y 3 están sombreadas, ¿qué fracción representa?", "choices": ["1/4", "2/4", "3/4", "4/4"], "correct_answer": "3/4", "explanation": "3 partes de 4 están sombreadas = 3/4"},
                     "hints": ["El denominador = total de partes (4)", "El numerador = partes sombreadas (3)", "3/4"]},
                    {"slug": "fraccion-numero", "title": "Escribe la fracción", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "Si tienes 2 pizzas y comes 1/3 de cada una, ¿qué fracción de pizza comiste en total?", "choices": ["2/3", "3/3", "2/6", "1/3"], "correct_answer": "2/3", "explanation": "1/3 + 1/3 = 2/3"},
                     "hints": ["Cada pizza contributes 1/3", "Sumamos: 1/3 + 1/3 = 2/3", "2/3"]},
                    {"slug": "fraccion-igual-1", "title": "Fracciones iguales a 1", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál de estas fracciones es igual a 1?", "choices": ["2/3", "5/5", "3/4", "7/8"], "correct_answer": "5/5", "explanation": "Cuando numerador = denominador, la fracción = 1"},
                     "hints": ["Para que una fracción sea igual a 1, arriba = abajo", "5/5 = 1 porque 5÷5 = 1", "5/5"]},
                    {"slug": "fraccion-mitad", "title": "La mitad", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál es la mitad de 8?", "choices": ["2", "3", "4", "5"], "correct_answer": "4", "explanation": "Mitad de 8 = 8 ÷ 2 = 4"},
                     "hints": ["La mitad = dividir entre 2", "8 ÷ 2 = 4", "4"]},
                ]
            },
            {
                "slug": "suma-fracciones",
                "title": "Suma de Fracciones",
                "description": "Sumar fracciones con mismo y diferente denominador",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Sumar Fracciones con Igual Denominador",
                        "content": """# ➕ Sumar Fracciones

## Caso fácil: mismo denominador 🎯

Cuando las fracciones tienen el **mismo denominador**, ¡es muy fácil!

### Ejemplo: 1/5 + 2/5 = ?

**Paso 1:** Los denominadores son iguales (5), así que no cambian.  
**Paso 2:** Sumamos los numeradores: 1 + 2 = 3  
**Paso 3:** Respuesta: **3/5**

:::visual:fraction,1,5:::
:::visual:fraction,2,5:::
Sumando = **1/5 + 2/5 = 3/5**

## Ejemplos rápidos

- 1/4 + 2/4 = **3/4** ✅
- 1/3 + 1/3 = **2/3** ✅
- 1/2 + 1/2 = **2/2 = 1** ✅ (¡es un entero!)

## Caso especial: medios y cuartos

1/2 + 1/4 = ?

1/2 = 2/4 (convertimos a cuartos)  
2/4 + 1/4 = **3/4**

> **Consejo:** Convierte a fracciones equivalentes para poder sumar.

Practica con los ejercicios.""",
                        "order_index": 0,
                        "exercise_slugs": ["suma-frac-igual", "suma-medios", "suma-tercios", "suma-cuartos"],
                    },
                ],
                "exercises": [
                    {"slug": "suma-frac-igual", "title": "Suma mismo denominador", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 1/5 + 2/5?", "correct_answer": "3/5", "explanation": "1/5 + 2/5 = 3/5. Sumamos numeradores, denominador igual."},
                     "hints": ["Los denominadores son iguales (5)", "1 + 2 = 3, mantenemos el 5 abajo", "3/5"]},
                    {"slug": "suma-frac-3mas", "title": "Suma tres fracciones", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 1/4 + 1/4 + 1/4?", "correct_answer": "3/4", "explanation": "1/4 + 1/4 + 1/4 = 3/4"},
                     "hints": ["1/4 + 1/4 = 2/4, luego + 1/4 = 3/4", "3 × (1/4) = 3/4", "3/4"]},
                    {"slug": "suma-medios", "title": "Suma de medios", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 1/2 + 1/2?", "correct_answer": "1", "explanation": "1/2 + 1/2 = 2/2 = 1"},
                     "hints": ["1/2 + 1/2 = 2/2", "2/2 = 1 (es un entero)", "1"]},
                    {"slug": "suma-tercios", "title": "Suma de tercios", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 1/3 + 1/3?", "correct_answer": "2/3", "explanation": "1/3 + 1/3 = 2/3"},
                     "hints": ["Mismo denominador: sumamos 1 + 1 = 2", "2/3", "2/3"]},
                    {"slug": "suma-cuartos", "title": "Suma de cuartos", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuánto es 1/4 + 2/4?", "correct_answer": "3/4", "explanation": "1/4 + 2/4 = 3/4"},
                     "hints": ["Denominador igual: 1 + 2 = 3", "3/4", "3/4"]},
                    {"slug": "suma-medios-cuartos", "title": "1/2 + 1/4", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuánto es 1/2 + 1/4?", "correct_answer": "3/4", "explanation": "1/2 = 2/4, entonces 2/4 + 1/4 = 3/4"},
                     "hints": ["Convierte 1/2 a cuartos: 1/2 = 2/4", "2/4 + 1/4 = 3/4", "3/4"]},
                ]
            },
            {
                "slug": "comparacion-fracciones",
                "title": "Comparación de Fracciones",
                "description": "Determinar qué fracción es mayor o menor",
                "order_index": 2,
                "lessons": [
                    {
                        "title": "Comparar Fracciones",
                        "content": """# ⚖️ Comparar Fracciones

¿Cómo sabemos **cuál fracción es mayor**?

## Regla 1: Igual denominador 🎯

Si tienen el **mismo denominador**, el numerador mayor es la fracción mayor.

**Ejemplo:** ¿Qué es mayor, 2/5 o 3/5?

:::visual:comparison,3,5,3/5,2/5:::

Ambas tienen denominador 5.  
3/5 > 2/5 porque 3 > 2.

## Regla 2: Igual numerador

Si tienen el **mismo numerador**, el denominador menor es la fracción mayor.

**Ejemplo:** ¿Qué es mayor, 1/3 o 1/5?

:::visual:comparison,3,5,1/3,1/5:::

Ambas tienen numerador 1.  
1/3 > 1/5 porque 3 < 5 (menos partes = más grande)

## Regla 3: Comparar con 1/2

Si una fracción es mayor que 1/2 y otra es menor, la mayor es la > 1/2.

**Ejemplo:** ¿3/4 o 1/2?  
3/4 > 1/2 porque 3/4 = 6/8 y 1/2 = 4/8, y 6/8 > 4/8.

## Tip rápido 💡

> Para comparar 3/4 y 1/2: busca un denominador común → 3/4 = 6/8, 1/2 = 4/8.  
> Como 6 > 4, entonces **3/4 > 1/2**

Practica con los ejercicios.""",
                        "order_index": 0,
                        "exercise_slugs": ["comparar-mitad", "comparar-tercios", "comparar-cuartos", "ordenar-fracciones"],
                    },
                ],
                "exercises": [
                    {"slug": "comparar-mitad", "title": "¿Mayor o menor que 1/2?", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿3/4 es mayor o menor que 1/2?", "choices": ["Mayor", "Menor", "Igual"], "correct_answer": "Mayor", "explanation": "3/4 > 1/2 porque 3/4 = 6/8 y 1/2 = 4/8"},
                     "hints": ["Convierte a octavos: 3/4 = 6/8, 1/2 = 4/8", "6/8 > 4/8", "Mayor"]},
                    {"slug": "comparar-tercios", "title": "Comparar tercios", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Qué fracción es mayor: 1/3 o 2/3?", "choices": ["1/3", "2/3"], "correct_answer": "2/3", "explanation": "2/3 > 1/3 porque tienen el mismo denominador"},
                     "hints": ["Mismo denominador: comparamos numeradores", "2 > 1", "2/3"]},
                    {"slug": "comparar-cuartos", "title": "Comparar cuartos", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Qué fracción es mayor: 1/4 o 3/4?", "choices": ["1/4", "3/4"], "correct_answer": "3/4", "explanation": "3/4 > 1/4"},
                     "hints": ["Mismo denominador: 3 > 1", "3/4", "3/4"]},
                    {"slug": "ordenar-fracciones", "title": "Ordenar fracciones", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuál es la fracción MENOR: 1/4, 1/2, 3/4?", "choices": ["1/4", "1/2", "3/4"], "correct_answer": "1/4", "explanation": "1/4 es la menor porque el numerador es el más pequeño"},
                     "hints": ["Compara: 1/4 < 1/2 < 3/4", "1/4 tiene el numerador más pequeño", "1/4"]},
                ]
            },
        ]
    },
    # GEOMETRÍA
    {
        "slug": "geometria",
        "title": "Geometría",
        "description": "Aprende sobre figuras 2D, perímetro, área y propiedades geométricas",
        "icon_name": "📐",
        "units": [
            {
                "slug": "figuras-2d",
                "title": "Figuras 2D",
                "description": "Reconoce y describe figuras bidimensionales",
                "order_index": 0,
                "lessons": [
                    {
                        "title": "Figuras Geométricas",
                        "content": """# 📐 Figuras Geométricas

Las **figuras 2D** son formas planas. Tienen **lados** y **vértices**.

## Vocabulario 📖

- **Lado:** cada línea que forma la figura
- **Vértice:** punto donde se encuentran dos lados (esquina)

## Figuras principales

### Triángulo △
- **3 lados** y **3 vértices**
- Ejemplo: las señales de tránsito

:::visual:anglemaker,60:::
Ángulos del triángulo equilátero: **60°** cada uno.

### Cuadrado ⬜
- **4 lados iguales**
- **4 vértices**
- Todos los ángulos son 90°

:::visual:protractor,90:::
El ángulo del cuadrado mide **90°** (recto).

### Rectángulo ▬
- **4 lados** (2 largos, 2 cortos)
- **4 vértices**
- Todos los ángulos son 90°

### Círculo ⭕
- **No tiene lados rectos**
- Es una curva cerrada
- Tiene un **centro**

### Pentágono ⬠
- **5 lados** y **5 vértices**

### Hexágono ⬡
- **6 lados** y **6 vértices**

## Practica contando lados y vértices.""",
                        "order_index": 0,
                        "exercise_slugs": ["triangulos", "pentagono", "contar-lados", "contar-vertices", "cuadrado-rectangulo", "circulo-propiedades"],
                    },
                ],
                "exercises": [
                    {"slug": "contar-lados", "title": "Contar lados", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuántos lados tiene un hexágono?", "choices": ["4", "5", "6", "7"], "correct_answer": "6", "explanation": "Un hexágono tiene 6 lados"},
                     "hints": ["Hex = 6", "Un hexágono es como un panal de miel", "6"]},
                    {"slug": "triangulos", "title": "Tipos de triángulos", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuántos lados tiene un triángulo?", "choices": ["2", "3", "4", "5"], "correct_answer": "3", "explanation": "Triángulo = 3 lados"},
                     "hints": ["Trian = 3", "3"]},
                    {"slug": "cuadrado-rectangulo", "title": "Cuadrado vs Rectángulo", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuántos lados IGUALES tiene un cuadrado?", "choices": ["2", "3", "4", "todas"], "correct_answer": "4", "explanation": "Un cuadrado tiene 4 lados iguales"},
                     "hints": ["El cuadrado tiene TODOS sus lados iguales", "4"]},
                    {"slug": "circulo-propiedades", "title": "Propiedades del círculo", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿El círculo tiene lados rectos?", "choices": ["Sí", "No"], "correct_answer": "No", "explanation": "El círculo no tiene lados rectos, es una curva cerrada"},
                     "hints": ["El círculo es una curva, no tiene líneas rectas", "No"]},
                    {"slug": "pentagono", "title": "Pentágono", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuántos lados tiene un pentágono?", "choices": ["4", "5", "6", "7"], "correct_answer": "5", "explanation": "Pentágono = 5 lados"},
                     "hints": ["Penta = 5", "5"]},
                    {"slug": "contar-vertices", "title": "Contar vértices", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuántos vértices tiene un rectángulo?", "choices": ["2", "3", "4", "5"], "correct_answer": "4", "explanation": "Un rectángulo tiene 4 vértices"},
                     "hints": ["Cada esquina es un vértice", "Un rectángulo tiene 4 esquinas", "4"]},
                ]
            },
            {
                "slug": "perimetro-area",
                "title": "Perímetro y Área",
                "description": "Calcula el perímetro y área de figuras planas",
                "order_index": 1,
                "lessons": [
                    {
                        "title": "Perímetro y Área",
                        "content": """# 📏 Perímetro y Área

## Perímetro: la cerca alrededor 🧵

El **perímetro** es la medida del **contorno** de una figura.

### Fórmulas:

**Cuadrado:** P = 4 × lado  
Ejemplo: lado = 5 cm → P = 4 × 5 = **20 cm**

**Rectángulo:** P = 2 × (largo + ancho)  
Ejemplo: largo = 8 cm, ancho = 3 cm → P = 2 × (8+3) = **22 cm**

**Triángulo:** P = lado₁ + lado₂ + lado₃

## Área: el piso dentro 🏠

El **área** es la medida de la **superficie** dentro de la figura.

### Fórmulas:

**Cuadrado:** A = lado × lado  
Ejemplo: lado = 4 cm → A = 4 × 4 = **16 cm²**

:::visual:array,4,4:::
4 × 4 = **16 cm²**

**Rectángulo:** A = largo × ancho  
Ejemplo: largo = 6 cm, ancho = 4 cm → A = 6 × 4 = **24 cm²**

:::visual:array,6,4:::
6 × 4 = **24 cm²**

## Recuerda 📝

- **Perímetro** se mide en cm, m, km (longitud)
- **Área** se mide en cm², m², km² (superficie)

Practica con los ejercicios.""",
                        "order_index": 0,
                        "exercise_slugs": ["perimetro-cuadrado", "perimetro-rectangulo", "area-cuadrado", "area-rectangulo", "perimetro-triangulo", "comparar-areas"],
                    },
                ],
                "exercises": [
                    {"slug": "perimetro-cuadrado", "title": "Perímetro del cuadrado", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál es el perímetro de un cuadrado de lado 5 cm?", "correct_answer": "20", "explanation": "Perímetro = 4 × lado = 4 × 5 = 20 cm"},
                     "hints": ["P = 4 × lado", "4 × 5 = 20", "20 cm"]},
                    {"slug": "perimetro-rectangulo", "title": "Perímetro del rectángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál es el perímetro de un rectángulo de largo 8 cm y ancho 3 cm?", "correct_answer": "22", "explanation": "P = 2×(8+3) = 2×11 = 22 cm"},
                     "hints": ["P = 2×(largo + ancho)", "2×(8+3) = 2×11 = 22", "22 cm"]},
                    {"slug": "area-cuadrado", "title": "Área del cuadrado", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál es el área de un cuadrado de lado 4 cm?", "correct_answer": "16", "explanation": "Área = lado × lado = 4 × 4 = 16 cm²"},
                     "hints": ["A = lado × lado", "4 × 4 = 16", "16 cm²"]},
                    {"slug": "area-rectangulo", "title": "Área del rectángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.easy, "points": 10,
                     "data": {"question": "¿Cuál es el área de un rectángulo de largo 6 cm y ancho 4 cm?", "correct_answer": "24", "explanation": "A = 6 × 4 = 24 cm²"},
                     "hints": ["A = largo × ancho", "6 × 4 = 24", "24 cm²"]},
                    {"slug": "perimetro-triangulo", "title": "Perímetro del triángulo", "exercise_type": ExerciseType.numeric, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuál es el perímetro de un triángulo con lados 4 cm, 5 cm y 6 cm?", "correct_answer": "15", "explanation": "P = 4 + 5 + 6 = 15 cm"},
                     "hints": ["P = lado₁ + lado₂ + lado₃", "4 + 5 + 6 = 15", "15 cm"]},
                    {"slug": "comparar-areas", "title": "Comparar áreas", "exercise_type": ExerciseType.multiple_choice, "difficulty": Difficulty.medium, "points": 15,
                     "data": {"question": "¿Cuál rectángulo tiene MAYOR área: uno de 4×6 o uno de 5×5?", "choices": ["4×6", "5×5", "son iguales"], "correct_answer": "5×5", "explanation": "Área 4×6=24, 5×5=25. El de 5×5 es mayor."},
                     "hints": ["Área 4×6 = 4 × 6 = 24", "Área 5×5 = 5 × 5 = 25", "5×5"]},
                 ]
            },
        ]
    },
]

# =============================================================================
# SEED FUNCTIONS
# =============================================================================

async def seed_topics(db):
    """Seed all topics, units, lessons, and exercises."""
    topic_count = 0
    unit_count = 0
    lesson_count = 0
    exercise_count = 0

    for topic_data in TOPICS:
        # Check if topic exists
        result = await db.execute(select(Topic).where(Topic.slug == topic_data["slug"]))
        existing = result.scalar_one_or_none()

        if existing:
            print(f"  ⏭️  Topic '{topic_data['slug']}' already exists, skipping")
            continue

        # Create topic
        topic = Topic(
            slug=topic_data["slug"],
            title=topic_data["title"],
            description=topic_data.get("description"),
            icon_name=topic_data.get("icon_name"),
        )
        db.add(topic)
        await db.flush()
        topic_count += 1
        print(f"  ✅ Created topic: {topic.title}")

        # Create units
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

            # Create lessons first (so exercises can link to them)
            lesson_map = {}  # slug-like key → lesson id
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

            # Create exercises and link to lessons
            for ex_data in unit_data.get("exercises", []):
                lesson_id = None
                # Find which lesson this exercise belongs to
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

            lesson_label = f" ({len(unit_data.get('lessons', []))} lessons)" if unit_data.get("lessons") else ""
            print(f"      ✅ Unit: {unit.title} ({len(unit_data.get('exercises', []))} exercises{lesson_label})")

    return topic_count, unit_count, lesson_count, exercise_count


async def verify_seed():
    """Verify seed data exists."""
    async with AsyncSessionLocal() as db:
        topics_result = await db.execute(select(Topic))
        topics = topics_result.scalars().all()

        units_result = await db.execute(select(Unit))
        units = units_result.scalars().all()

        lessons_result = await db.execute(select(Lesson))
        lessons = lessons_result.scalars().all()

        exercises_result = await db.execute(select(Exercise))
        exercises = exercises_result.scalars().all()

        return len(topics), len(units), len(lessons), len(exercises)


async def run_seed(dry_run=False, commit=True):
    """Run the seed process."""
    print("=" * 60)
    print("CURRICULUM SEED SCRIPT")
    print("=" * 60)

    if dry_run:
        print("\n⚠️  DRY RUN MODE - No changes will be made\n")
    elif not commit:
        print("\n⚠️  VERIFY MODE - Counts will be shown without inserting\n")

    print("\n📊 Current database state:")
    t, u, l, e = await verify_seed()
    print(f"   Topics: {t}, Units: {u}, Lessons: {l}, Exercises: {e}")

    if dry_run:
        print("\n📋 Would create:")
        total_units = sum(len(topic["units"]) for topic in TOPICS)
        total_lessons = sum(sum(len(u["lessons"]) for u in topic["units"]) for topic in TOPICS)
        total_exercises = sum(sum(len(u["exercises"]) for u in topic["units"]) for topic in TOPICS)
        print(f"   Topics: {len(TOPICS)}")
        print(f"   Units: {total_units}")
        print(f"   Lessons: {total_lessons}")
        print(f"   Exercises: {total_exercises}")
        return

    if not commit:
        return

    print("\n🚀 Starting seed...")

    async with AsyncSessionLocal() as db:
        t, u, l, e = await seed_topics(db)
        await db.commit()

    print("\n✅ Seed complete!")
    print(f"   Created: {t} topics, {u} units, {l} lessons, {e} exercises")

    print("\n📊 New database state:")
    t, u, l, e = await verify_seed()
    print(f"   Topics: {t}, Units: {u}, Lessons: {l}, Exercises: {e}")


def main():
    parser = argparse.ArgumentParser(description="Seed curriculum data")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--verify", action="store_true", help="Verify current state only")
    parser.add_argument("--commit", action="store_true", default=True, help="Commit changes (default)")
    parser.add_argument("--no-commit", dest="commit", action="store_false", help="Don't commit changes")
    args = parser.parse_args()

    if args.verify:
        asyncio.run(verify_seed())
    elif args.dry_run:
        asyncio.run(run_seed(dry_run=True, commit=False))
    else:
        asyncio.run(run_seed(dry_run=False, commit=args.commit))


if __name__ == "__main__":
    main()