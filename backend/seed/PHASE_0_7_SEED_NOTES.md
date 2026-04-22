# PHASE 0.7 — Seed Code Update Notes

**Status: NOT yet updated — requires manual delta from seed maintainer**

The seed file (`seed/curriculum_seed.py`) would reproduce the duplicates if run on a fresh DB.
Below is the authoritative delta needed to bring it in sync with the deduplicated DB state.

---

## Changes needed in `curriculum_seed.py`

### Topics to REMOVE (7 duplicates deleted)

| Removed Topic ID | Title | Canonical Topic ID |
|---|---|---|
| 78 | Fracciones | 98 |
| 85 | Estadística Avanzada | 95 |
| 113 | Probabilidad | 110 |
| 67 | Números hasta 100 | 103 |
| 118 | Volumen | 90 |
| 70 | Medición | 102 |
| 111 | Fracciones y decimales | 108 (kept as canonical) |

**Implementation:** Remove the dict entries for these topics from the `GRADEX_TOPICS` lists.
Any unit nested under these topics must either be moved to the canonical topic or removed.

### Units to REMOVE (1 duplicate)

| Removed Unit ID | Title | Topic | Canonical Unit ID |
|---|---|---|---|
| 169 | Fracciones equivalentes | 108 | 127 |

**Implementation:** Remove the unit dict with `slug: "g4-fracciones-equivalentes"` (or the duplicate one) from the topic 108's unit list.

### Lessons to RENAME (1 conflict resolved)

| Lesson ID | Old Title | New Title | Unit ID |
|---|---|---|---|
| 195 | Fracciones equivalentes | Práctica | 127 |

**Implementation:** In the unit that had two "Fracciones equivalentes" lessons, rename one to "Práctica".

### Unit.topic_id REMAPPING (FK fix — no content change)

These units were pointing to duplicate topics and were automatically remapped to the canonical topic:

| Unit ID | Old topic_id | New topic_id |
|---|---|---|
| (several) | 78 → 98 | (same units, different parent) |
| (several) | 85 → 95 | (same units, different parent) |
| (several) | 113 → 110 | (same units, different parent) |
| (several) | 67 → 103 | (same units, different parent) |
| (several) | 118 → 90 | (same units, different parent) |
| (several) | 70 → 102 | (same units, different parent) |
| (several) | 111 → 108 | (same units, different parent) |

**Implementation:** Update the `topic_id` references in the seed's unit dictionaries that reference the removed topic IDs.

---

## Final canonical state (after dedup)

```
Topics:   45  (was 53, removed 8 duplicates)
Units:    78  (was 79, removed 1 duplicate)
Lessons:  101 (unchanged — lesson from unit 169 moved to unit 127)
Exercises: 280 (unchanged)
```

## Recommended approach for seed update

Rather than editing the existing file line-by-line, the cleanest approach:

1. Dump the current canonical topic/unit/lesson structure from the DB into a new seed format
2. Replace the relevant `GRADEX_TOPICS` sections in `curriculum_seed.py`
3. Or: create a `seed/curriculum_dedup.py` migration that runs AFTER `curriculum_seed.py` to clean up any future duplicates automatically

**Priority:** MEDIUM — seed update only needed for **fresh DB deployments**. The current running platform is fully clean.