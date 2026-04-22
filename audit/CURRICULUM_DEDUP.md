# PHASE 0 — Curriculum Deduplication Report

**Date:** April 2026
**Status:** PHASE 0.1 COMPLETE — awaiting merge decisions

---

## FINDINGS SUMMARY

### Database Totals
| Entity | Count |
|--------|-------|
| Topics | 53 |
| Units | 79 |
| Lessons | 101 |
| Exercises | 280 |

---

## DUPLICATE UNITS (7 pairs = 14 units)

| Canonical Keep | Duplicate Eliminate | Rationale |
|---|---|---|
| Unit(id=132) `Operaciones con decimales` — topic=Decimales, 1 lesson, 4 exercises | Unit(id=173) `Operaciones con decimales` — topic=Fracciones y decimales, 1 lesson, 3 exercises | El de Decimales tiene más exercises y belong al topic "Decimales" que es más específico |
| Unit(id=154) `Contar hasta 20` — topic=Números hasta 20, 2 lessons, 4 exercises | Unit(id=103) `Contar hasta 20` — topic=Números hasta 100, 2 lessons, 3 exercises | Mismo contenido, mantener el que está en su topic correcto (Números hasta 20) |
| Unit(id=127) `Fracciones equivalentes` — topic=Fracciones y Decimales, 1 lesson, 3 exercises | Unit(id=169) `Fracciones equivalentes` — topic=Fracciones y decimales, 1 lesson, 2 exercises | Mismo contenido, mantener el que está en "Fracciones y Decimales" (capitalización diferente, mismo topic) |
| Unit(id=178) `Razones` — topic=Razones y proporciones, 2 lessons, 5 exercises | Unit(id=134) `Razones` — topic=Proporciones y Razones, 1 lesson, 2 exercises | "Razones y proporciones" es el topic correcto (más claro), más exercises |
| Unit(id=148) `División` — topic=Aritmética, 1 lesson, 8 exercises | Unit(id=164) `División` — topic=Números grandes, 1 lesson, 2 exercises | Same title, "División" como contenido de "Aritmética" es más natural |
| Unit(id=179) `¿Qué es el porcentaje?` — topic=Porcentaje, 2 lessons, 5 exercises | Unit(id=133) `¿Qué es el porcentaje?` — topic=Porcentajes, 1 lesson, 4 exercises | El topic "Porcentaje" es singular y correcto; "Porcentajes" plural es redundante |
| Unit(id=138) `Números negativos` — topic=Números Negativos, 1 lesson, 4 exercises | Unit(id=177) `Números negativos` — topic=Números negativos, 1 lesson, 3 exercises | Mismo topic (difieren solo en capitalización: "Negativos" vs "negativos"), mantener id=138 por más exercises |

**Merge actions:**
- Lessons from eliminated units → reassign to canonical unit
- Exercises from eliminated units → reassign to canonical unit
- Then DELETE eliminated units

---

## DUPLICATE TOPICS (7 pairs + 1 triplet)

### TOPIC TRIPLET: `Fracciones y decimales` (3 instances!)
| Topic ID | Units | Lessons | Decision |
|---|---|---|---|
| 82 — `Fracciones y Decimales` | 2 | 2 | KEEP (capital D — but check if same content as 111) |
| 108 — `Fracciones y decimales` | 2 | 4 | KEEP — most lessons, consolidate others INTO THIS ONE |
| 111 — `Fracciones y decimales` | 2 | 3 | MERGE INTO 108 |

**Issue:** Topics 82, 108, 111 all have the same name with minor capital differences. They need to be ONE topic.
**Decision:** Keep id=108 (highest lesson count), merge 82 and 111 into 108.

### TOPIC PAIRS:

| Canonical Keep | Duplicate Eliminate | Rationale |
|---|---|---|
| Topic(id=98) `Fracciones` — units=3, lessons=3 | Topic(id=78) `Fracciones` — units=2, lessons=2 | Keep id=98 (more content) |
| Topic(id=95) `Estadística Avanzada` — units=1, lessons=1 | Topic(id=85) `Estadística Avanzada` — units=1, lessons=1 | Same content, keep id=95 (lower ID = created first, more likely canonical) |
| Topic(id=110) `Probabilidad` — units=1, lessons=1 | Topic(id=113) `Probabilidad` — units=1, lessons=1 | Same content, keep id=110 |
| Topic(id=67) `Números hasta 100` — units=2, lessons=3 | Topic(id=103) `Números hasta 100` — units=3, lessons=6 | Keep id=103 (MORE content — this is the richer duplicate!) |
| Topic(id=90) `Volumen` — units=1, lessons=1 | Topic(id=118) `Volumen` — units=1, lessons=1 | Same content, keep id=90 |
| Topic(id=70) `Medición` — units=1, lessons=1 | Topic(id=102) `Medición` — units=1, lessons=1 | Same content, keep id=70 |
| Topic(id=108) `Fracciones y decimales` — units=2, lessons=4 | Topic(id=82) `Fracciones y Decimales` — units=2, lessons=2 | Merge 82 INTO 108 (see triplet note above) |
| Topic(id=108) `Fracciones y decimales` | Topic(id=111) `Fracciones y decimales` | Merge 111 INTO 108 |

**Note about id=103:** Topic id=103 `Números hasta 100` (units=3, lessons=6) is being KEPT as canonical for "Números hasta 100" over id=67. But note that Unit id=103 `Contar hasta 20` (from the unit deduplication above) currently belongs to topic id=103. After we delete unit id=103, that unit's lessons/exercises will be reassigned to unit id=154. This does NOT affect the topic decision.

### TOPIC NEAR-DUPLICATE: 'Perímetro y Área' (id=79, appears in 2 topic groups)
Actually checking this — topic id=79 `Perímetro y Área` appears once in the list. It's not a near-duplicate in terms of topics table, it's that topic id=79 has units that might also appear elsewhere. This is a WAIT — need to verify if 'Perímetro y Área' as a topic name is a real duplicate or just similar to 'Figuras y perímetro' (id=114).

---

## DUPLICATE LESSONS WITHIN SAME UNIT

**Count: 0** ✅

No lessons with duplicate titles in the same unit. This means we don't need to handle lesson deduplication at this stage.

---

## MERGE DECISION SUMMARY

### Units to DELETE after reassigning content:
- id=173 (Operaciones con decimales → keep 132)
- id=103 (Contar hasta 20 → keep 154)
- id=169 (Fracciones equivalentes → keep 127)
- id=134 (Razones → keep 178)
- id=164 (División → keep 148)
- id=133 (¿Qué es el porcentaje? → keep 179)
- id=177 (Números negativos → keep 138)

### Topics to DELETE after reassigning content:
- id=78 (Fracciones → keep 98)
- id=85 (Estadística Avanzada → keep 95)
- id=113 (Probabilidad → keep 110)
- id=67 (Números hasta 100 → keep 103)
- id=90 (Volumen → keep 118) ⚠️ WAIT — keep 90 actually (lower ID, same content)
- id=70 (Medición → keep 102) ⚠️ WAIT — keep 70 actually (lower ID, same content)
- id=82 (Fracciones y Decimales → keep 108)
- id=111 (Fracciones y decimales → keep 108)
- id=118 (Volumen → keep 90) — wait this is circular... let's fix: keep id=90

### Corrected topic keep list:
| Keep | Eliminate | Note |
|---|---|---|
| id=98 | id=78 | |
| id=95 | id=85 | |
| id=110 | id=113 | |
| id=103 | id=67 | id=103 wins (more content) |
| id=90 | id=118 | keep lower ID (90) |
| id=70 | id=102 | keep lower ID (70) |
| id=108 | id=82, id=111 | triplet merge |

---

## VERIFICATION QUERIES (to run after merge)

```sql
-- No duplicate unit titles
SELECT title, COUNT(*) FROM units GROUP BY title HAVING COUNT(*) > 1;

-- No duplicate topic titles
SELECT title, COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1;

-- No orphan lessons
SELECT * FROM lessons WHERE unit_id NOT IN (SELECT id FROM units);

-- No orphan exercises
SELECT * FROM exercises WHERE unit_id NOT IN (SELECT id FROM units) AND lesson_id NOT IN (SELECT id FROM lessons);

-- No orphan units
SELECT * FROM units WHERE topic_id NOT IN (SELECT id FROM topics);
```

---

## ROLLBACK SCRIPT (execute BEFORE merge)
```sql
-- This script would restore the state. Save as backup before executing.
-- TO BE WRITTEN in Phase 0.3 before merge execution.
```
