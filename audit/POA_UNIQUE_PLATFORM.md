# Math Platform — POA: De Khan Academy Clone a Plataforma Única

**North Star Goal:** Crear una plataforma de matemáticas Boliviana que prioriza al padre como co-enseñante, usa el Modelo de Barras interactivamente como ventana al proceso de pensamiento del estudiante, y se siente culturalmente conectada a Bolivia — no genérica.

**Auditoría previa:** 10 fases completadas. Hallazgos críticos y altos corregidos. Ver `audit/AUDIT_CONSOLIDATED.md` y `audit/FIXES_APPLIED.md`.

---

## FASE 0 — Consolidación Curricular (Data Deduplication)

**Objetivo:** Consolidar topics y units duplicados antes de cualquier feature nueva. Existían múltiples "Fracciones" y "Medidas" dispersos en el seed — esto causa experiencias confusas para el estudiante y datos inconsistent.

**Multisteps:**

**0.1 — Scout: Identificar duplicados exactos y near-duplicates**
- [ ] 0.1.1 — Query DB: `SELECT title, COUNT(*) FROM units GROUP BY title HAVING COUNT(*) > 1` — listar todos los units con nombres duplicados
- [ ] 0.1.2 — Query DB: `SELECT title, COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1` — mismo para topics
- [ ] 0.1.3 — Buscar near-duplicates: units con nombres casi-identicos (ej: "Fracciones", "Fracciones equivalent", "Fracciones equivalentes" sin consolidar)
- [ ] 0.1.4 — Generar reporte en `audit/CURRICULUM_DEDUP.md` con lista completa: canonical unit/topic vs duplicate, cantidad de exercises/lessons en cada uno

**0.2 — Plan de Merge: Decidir cuál es el canonical**
- [ ] 0.2.1 — Para cada set de duplicados, decidir cuál GUARDA y cuál ELIMINA (criterio: más exercises, más lessons, nombre más claro/correcto)
- [ ] 0.2.2 — Para cada duplicate, listar todos los exercises y lessons que lo referencian
- [ ] 0.2.3 — Mapear todos los `lesson.unit_id` de duplicados → canonical unit_id
- [ ] 0.2.4 — Mapear todos los `exercise.unit_id` de duplicados → canonical unit_id
- [ ] 0.2.5 — Mapear todos los `topic.parent_id` de duplicados → canonical topic_id (si hay topics duplicados también)
- [ ] 0.2.6 — Verificar que no haya orphan rows después del remapping

**0.3 — Ejecutar merge en DB**
- [ ] 0.3.1 — UPDATE todos los `lesson.unit_id` de duplicados → canonical unit_id
- [ ] 0.3.2 — UPDATE todos los `exercise.unit_id` de duplicados → canonical unit_id
- [ ] 0.3.3 — UPDATE todos los `topic.parent_id` de duplicados → canonical topic_id
- [ ] 0.3.4 — DELETE los units duplicados (después de verificar que todos los FK fueron remapeados)
- [ ] 0.3.5 — DELETE los topics duplicados (después de verificar que todos los child topics fueron movidos)
- [ ] 0.3.6 — Vacuum/verify DB consistency: `SELECT * FROM lessons WHERE unit_id NOT IN (SELECT id FROM units)` → debe ser 0

**0.4 — Consolidar lessons duplicadas dentro del mismo unit**
- [ ] 0.4.1 — Buscar lessons con el mismo `title` dentro del mismo unit: `SELECT title, unit_id, COUNT(*) FROM lessons GROUP BY title, unit_id HAVING COUNT(*) > 1`
- [ ] 0.4.2 — Para cada lesson duplicada: si una tiene exercises y la otra no, eliminar la vacía y mantener la que tiene contenido
- [ ] 0.4.3 — Si ambas tienen exercises, revisar cuál tiene más/better quality content, eliminar la weaker
- [ ] 0.4.4 — Verificar que el ordering (`order_index`) de las lessons restantes sea sequencial y sin gaps dentro de cada unit

**0.5 — Re-indexar order_index de todo**
- [ ] 0.5.1 — Dentro de cada unit, re-enumerar `order_index` de lessons de 0 a N secuencialmente
- [ ] 0.5.2 — Dentro de cada topic, re-enumerar `order_index` de units de 0 a N
- [ ] 0.5.3 — Dentro de cada grade/topic tree, re-enumerar `order_index` de topics de 0 a N
- [ ] 0.5.4 — Documentar en `audit/CURRICULUM_DEDUP.md` exactamente qué se eliminó y por qué (decisión auditable)

**0.6 — Verificación post-merge**
- [ ] 0.6.1 — Confirmar: `SELECT COUNT(*) FROM units GROUP BY title HAVING COUNT(*) > 1` → 0 rows
- [ ] 0.6.2 — Confirmar: `SELECT COUNT(*) FROM topics GROUP BY title HAVING COUNT(*) > 1` → 0 rows
- [ ] 0.6.3 — Confirmar: total exercises se mantiene (no se perdió ninguno en el merge)
- [ ] 0.6.4 — Confirmar: todos los students con `student_topic_progress` siguen encontrando sus topics (no orphan progress)
- [ ] 0.6.5 — Smoke test: como estudiante@test.com, navegar por topic tree completo sin errores 404

**0.7 — Actualizar source code de seed**
- [ ] 0.7.1 — Actualizar `curriculum_seed.py` para reflejar el nuevo schema consolidado (eliminar entries duplicadas)
- [ ] 0.7.2 — Actualizar `FIXES_APPLIED.md` con nota de que Phase 0 de deduplicación fue ejecutada
- [ ] 0.7.3 — Marcar `audit/CURRICULUM_DEDUP.md` como completado con evidencia de los queries

**Guardrails:**
- NUNCA eliminar exercises — solo reasignarlos al unit correcto
- NUNCA eliminar lessons con exercises — si hay conflicto, conservar ambas con `order_index` diferente
- Hacer rollback script ANTES de ejecutar updates (guardar estado previo)
- Si hay uncertainty sobre cuál es el canonical, NO eliminar — marcar como "needs review"
- Tiempo máximo: 1 sesión. Si encuentra más de 20 duplicados que requieren decisión manual, pausar y reportar antes de proceder.

---

## FASE 1 — Limpieza de Contenido (Foundation)

**Objetivo:** Eliminar todo contenido garbled (caracteres chinos, traducciones automáticas) y reemplazar contextos genéricos con contextos Bolivianos reales. Sin esto, nada más importa.

**Multisteps:**
- [ ] 1.1 — Escribir script Python que escanee TODOS los archivos de lección en `backend/seed/curriculum_seed.py` buscando chars no-españoles (`那`, `你`, etc.) y reportar ubicaciones exactas
- [ ] 1.2 — Reemplazar todos los contextos genéricos (ejercicios con "Alice bought apples", "John went to the store") con contextos Bolivianos (mercado de La Paz, productos Bolivianos, moneda local)
- [ ] 1.3 — Verificar que todos los `:::tryit:::` blocks tengan texto legible en español Boliviano
- [ ] 1.4 — Auditar que los emojis y caracteres especiales no rompen ningún rendering
- [ ] 1.5 — Verificar que el contenido se renderiza correctamente en frontend (smoke test visual)

**Guardrails:**
- SOLO texto de lección/seed — no modificar lógica de negocio ni estructuras de datos
- Cada reemplazo de contexto documentado en `audit/CONTENT_CLEANUP.md` con antes/después
- No re-seedear la base de datos todavía — guardar cambios en scripts primero

---

## FASE 2 — Modelo de Barras Interactivo (Core Differentiator)

**Objetivo:** Convertir el bar model de display widget a herramienta de construcción interactiva drag-and-drop donde el estudiante arrastra segmentos y construye el modelo, y el teacher puede ver el proceso de construcción.

**Multisteps:**
- [ ] 2.1 — Leer el componente actual `BarModel` en `LessonVisuals.tsx` y documentar su interface (props, eventos, estado)
- [ ] 2.2 — Diseñar nuevo schema de datos para `BarModelAttempt`: `{segments_built: [{label, value, order, timestamp}], final_answer: string, time_spent: int}`
- [ ] 2.3 — Rebuild `BarModel` component con drag-and-drop usando HTML5 drag events o pointer events (no dependencia de librería externa)
- [ ] 2.4 — Añadir `process_tracking` al enviar ejercicio: guardar el JSON de construcción en `exercise_attempts.answer_json` como `{"type": "bar_model_construction", "segments": [...]}`
- [ ] 2.5 — Verificar que `submit_attempt` en backend acepte y guarde el JSON de construcción
- [ ] 2.6 — Test: crear un bar_model exercise, construir el modelo interactivamente, enviar, verificar en DB que el proceso fue guardado

**Guardrails:**
- NO cambiar la estructura de datos del `Exercise` model — usar `answer_json` que ya existe
- Mantener backwards compatibility: si alguien envía bar_model como texto (sin construcción), que siga funcionando
- El drag-and-drop debe funcionar en mobile (pointer events, no solo mouse)

---

## FASE 3 — Parent Dashboard como Playbook (Unlocks Real Market)

**Objetivo:** Reemplazar el dashboard actual del padre (% completado inútil) con un "Playbook Daily" — una actividad clara por día que el padre puede hacer con el niño, conectada al contenido de la lección actual.

**Multisteps:**
- [ ] 3.1 — Diseñar schema `ParentActivity`: `{id, topic_id, title, description, materials_needed, estimated_time, difficulty_level, connection_to_bar_model}`
- [ ] 3.2 — Crear tabla `parent_activities` en DB via migración
- [ ] 3.3 — Seedear 20 ParentActivities (5 por grade, alineadas a topics actuales)
- [ ] 3.4 — Modificar `/parents/me` endpoint para retornar `daily_activity: ParentActivity | null` basado en la fecha actual
- [ ] 3.5 — Rebuild `parent/page.tsx` para mostrar: actividad del día + "Completé esta actividad" button + streak de participación del padre
- [ ] 3.6 — Añadir `parent_last_engaged_at` a `students` table (fecha última vez que el padre marcó una actividad completa)
- [ ] 3.7 — Test: loguear como padre@test.com, verificar que muestra actividad del día, marcar como completada, verificar streak actualizado

**Guardrails:**
- Mantener `LinkedStudent` y stats existentes — solo AGREGAR nuevos campos, no romper los existentes
- La actividad diaria debe tener fallback ("No hay actividad hoy — explora el progreso de tu hijo") si no hay actividad para ese día/topic

---

## FASE 4 — Teacher "Thinking Process" View (Pedagogical Edge)

**Objetivo:** Dar al teacher una vista de CÓMO el estudiante resolvió el problema (construcción del bar model, intentos, tiempo) no solo si acertó o no.

**Multisteps:**
- [ ] 4.1 — Crear nuevo endpoint `GET /teachers/students/{student_id}/thinking_process?exercise_id=` que retorne el history de constructions para ese ejercicio
- [ ] 4.2 — Diseñar schema `StudentThinkingProcess`: `{exercise_id, student_id, attempts: [{construction_json, correct: bool, time_spent, timestamp}]}`
- [ ] 4.3 — Añadir botón "Ver Proceso" en la vista del teacher de resultados de assignment
- [ ] 4.4 — Build `ThinkingProcessView` component que renderiza las construcciones del estudiante como secuencia de barras animadas (replay del proceso de construcción)
- [ ] 4.5 — Test: como profesor@test.com, crear un assignment con bar_model, como estudiante@test.com resolver interactivamente, verificar que el profesor ve el replay de construcción

**Guardrails:**
- Solo accesible para role=teacher o admin
- No modificar `AssignmentResponse` — crear nuevo endpoint separado

---

## FASE 5 — Sistema de Streaks Invertido (Parent Engagement Input)

**Objetivo:** El streak del estudiante se construye cuando el padre participates, no cuando el estudiante práctica solo. El input (padre) determina el output (streak).

**Multisteps:**
- [ ] 5.1 — Añadir `parent_participation_streak` a `students` table
- [ ] 5.2 — Modificar `_check_achievements` en `students.py` para recalcular streak basado en `parent_last_engaged_at`
- [ ] 5.3 — Cuando el padre marca una actividad completa en Phase 3, actualizar `student.parent_last_engaged_at = now()`
- [ ] 5.4 — Crear badge tipo `FAMILY_PARTICIPATION` con 3 niveles: 3 días, 7 días, 30 días de participación parental
- [ ] 5.5 — En `/parents/me` response, incluir `parent_streak: int` en cada `LinkedStudent`
- [ ] 5.6 — Test: simular 3 días de padre marcando actividades completas, verificar que el linked_student muestra streak=3

**Guardrails:**
- Mantener streak original del estudiante — crear segundo campo `parent_participation_streak`
- No modificar cálculos de XP del estudiante

---

## FASE 6 — "Top Helper" Peer Recognition (Social Dimension)

**Objetivo:** Añadir una dimensión social donde los estudiantes ganan reconocimiento por ayudar a sus compañeros, no solo por acertar ejercicios.

**Multisteps:**
- [ ] 6.1 — Crear badge tipo `TOP_HELPER` en `achievements` seed data
- [ ] 6.2 — Modificar `ExerciseAttempt` para aceptar `helped_peer_id: int | None` (opcional)
- [ ] 6.3 — Añadir endpoint `POST /me/helps/{attempt_id}` donde un estudiante marca que recibió ayuda de otro
- [ ] 6.4 — Cuando un estudiante acumula 3+ `helped_peer_id` referencias en una semana, otorgar badge `TOP_HELPER`
- [ ] 6.5 — Añadir "Ayudaste a X compañeros esta semana" en `/me/achievements` y en el parent dashboard feed
- [ ] 6.6 — Test: crear 2 estudiantes, simular que uno ayuda al otro, verificar que el helper recibe el badge

**Guardrails:**
- Solo students pueden marcar que recibieron ayuda
- Un estudiante no puede marcarse a sí mismo como helped
- `helped_peer_id` es nullable — backward compatible con ejercicios existentes

---

## FASE 7 — Testing Integral de Todas las Nuevas Features

**Multisteps:**
- [ ] 7.1 — Test E2E: estudiante completa bar_model interactivamente → teacher ve el proceso de construcción
- [ ] 7.2 — Test E2E: padre marca actividad completa → streak del padre sube → badge se otorga
- [ ] 7.3 — Test E2E: padre ve actividad diaria → niño practica → streak del niño sube indirectamente
- [ ] 7.4 — Test E2E: estudiante marca que recibió ayuda → helper recibe badge
- [ ] 7.5 — Verificar que todas las API endpoints existentes siguen funcionando sin regression
- [ ] 7.6 — Run `docker compose up -d` completo y smoke test de todos los contenedores

**Guardrails:**
- Usar seed users existentes para tests
- Si algún test falla, no continuar a la siguiente fase hasta resolver

---

## FASE 8 — Documentation & Training Materials

**Multisteps:**
- [ ] 8.1 — Documentar el nuevo flujo del Modelo de Barras Interactivo para teachers
- [ ] 8.2 — Crear guide para padres: "Cómo usar el Playbook Diario"
- [ ] 8.3 — Actualizar `FIXES_APPLIED.md` con todos los cambios de las fases 0-6
- [ ] 8.4 — Documentar schema de `ParentActivity` y `ThinkingProcessView`
- [ ] 8.5 — Crear `UNIQUE_FEATURES.md` describiendo qué hace a esta plataforma única vs Khan Academy

**Guardrails:**
- Documentación en español e inglés
- No modificar archivos de auditoría ya existentes

---

## FASE 9 — Deployment & Verification

**Multisteps:**
- [ ] 9.1 — Rebuild backend (ahora con volume mount, debería ser instantaneo)
- [ ] 9.2 — Rebuild frontend
- [ ] 9.3 — Verificar que `docker compose up -d` levanta todos los servicios sin errores
- [ ] 9.4 — Correr verification script contra Railway si existe deploy url
- [ ] 9.5 — Verificar que backend responde en `localhost:8000` y frontend en `localhost:3000`
- [ ] 9.6 — Ejecutar smoke test completo: login student, teacher, parent + submit attempt

**Guardrails:**
- SIEMPRE ejecutar `Verify-Deploy.ps1` después de deploy a producción
- Si el container no levanta, rollback al image anterior

---

## FASE 10 — Post-Launch Monitoring & Iteration Framework

**Multisteps:**
- [ ] 10.1 — Definir 3 KPIs: (1) % de padres que completan al menos 1 actividad semanal, (2) % de bar_model resueltos interactivamente vs typed answer, (3) badge发放rate de TOP_HELPER
- [ ] 10.2 — Implementar tracking events en frontend para cada KPI
- [ ] 10.3 — Crear dashboard interno con KPIs actualizados semanalmente
- [ ] 10.4 — Schedule bi-weekly review del progreso de KPIs
- [ ] 10.5 — Definir criteria de éxito/failure para cada feature

**Guardrails:**
- KPIs deben ser medibles con queries a la DB existente
- No implementar analytics tools externos — usar lo que ya existe en DB
- Esta fase es un loop continuo

---

## Dependencias

```
FASE 0 (Dedup) ──────────────────────────────────────────────────────────────┐
                                                                        │
FASE 1 (Content cleanup) ──→ FASE 2 (Bar Model Interactive)              │
                                       │                                  │
FASE 3 (Parent Playbook) ←→ FASE 5 (Parent Streak)                       │
         │                         │                                      │
         └─────────────────────────┘                                      │
                    │                                                     │
               FASE 4 (Teacher View) depends on FASE 2                    │
                    │                                                     │
FASE 6 (Top Helper) ←→ FASE 5 (streak incentive)                        │
         │                                                              │
         └──→ FASE 7 (Testing) → FASE 8 (Docs) → FASE 9 (Deploy) → FASE 10
```

**Regla:** No comenzar Phase N si Phase N-1 no pasó su completion audit.

---

## Completion Audit Template

Para cada fase, antes de declarar "done", verificar:
- [ ] Todos los multisteps completados ✅
- [ ] Ninguna regression en features existentes ✅
- [ ] Documentación actualizada ✅
- [ ] Si algo falla → STOP, reportar, no continuar

---

**¿Procedo con Phase 0, o quieres ajustar el scope antes de empezar?**
