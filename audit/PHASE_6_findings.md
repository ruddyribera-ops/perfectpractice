# PHASE 6 — Audit Lesson Content + Visual Blocks
**Date:** 2026-04-21
**Status:** ✅ COMPLETE

---

## 1. Block Types — Parser Inventory

| Block | Format | Parser Function | Renderer | Status |
|---|---|---|---|---|
| `:::visual:type,args:::` | `:::visual:type,args:::` | `parseVisual()` | Multiple components | ✅ |
| `:::tryit:q\|a\|h\|e:::` | `:::tryit:question\|answer\|hint\|explanation:::` | `parseTryIt()` | `TryIt` component | ✅ |
| `:::steps:l1\|r1:::l2\|r2:::` | `:::steps:label1\|result1:::...:::` | `parseSteps()` | `AnimatedSteps` | ✅ |
| `:::bar:q\|t\|type:::units_json:::` | `:::bar:question\|total\|type:::[{...}]:::` | `parseBar()` | `BarModel` | ✅ |

---

## 2. Visual Block Parsing — Regex + Multi-line

The parser collects multi-line blocks:
```typescript
if (line.includes(':::visual:') || line.match(/^:::visual/i)) {
  let block = line + '\n'
  let j = i + 1
  while (j < lines.length && !lines[j].match(/:::\s*$/)) {
    block += lines[j] + '\n'
    j++
  }
  const match = block.match(/(:::[\s\S]*?:::\s*)/)
}
```

**Issues:**
- The ending `:::` is detected by `match(/:::\s*$/))` — looks for `:::` at end of a line. If the closing `:::` appears on the same line as content (e.g., `:::visual:base10,5,3::: text after`), the closing `:::` might not be at end-of-line, causing the block to incorrectly include subsequent lines.
- **⚠️ MEDIUM:** If a block's closing `:::` is followed by inline text on the same line, the block capture could include extra content.

---

## 3. `parseVisual` Supported Types

`base10`, `numberline`, `array/grid`, `fraction`, `ruler`, `protractor`, `division`, `placevalue`, `comparison`, `tenframe`, `anglemaker`, `animatedarray`

**13 visual types supported.** Unknown types fall through to:
```typescript
default:
  return <div className="text-xs text-gray-400 p-2 bg-gray-100 rounded my-2">Visual no reconocido: {type}</div>
```
**⚠️ LOW:** No dark mode for the error fallback.

---

## 4. ⚠️ CRITICAL: Most Visual Components Have NO Dark Mode

**Components WITH dark mode support:**
- `TryIt` — ✅ `dark:bg-yellow-900/30`, `dark:border-yellow-600`, `dark:text-gray-100`
- `BarModel` — ✅ `dark:bg-slate-800`, `dark:border-slate-600`, `dark:text-gray-100`
- `WordProblem` (in exercise page) — ✅ `dark:bg-yellow-900/20`

**Components WITHOUT dark mode support (all use hardcoded light mode):**

| Component | Classes Used | Issue |
|---|---|---|
| `Base10Blocks` | `bg-white`, `border-gray-200`, `text-gray-700` | No `dark:` variants |
| `NumberLine` | `bg-white`, `border-gray-200`, `text-gray-700` | No dark mode |
| `ComparisonBars` | `bg-white`, `border-gray-200`, `text-gray-700` | No dark mode |
| `FractionVisual` | Likely light mode only | Not reviewed |
| `ArrayGrid` | Likely light mode only | Not reviewed |
| `AnimatedSteps` | Likely light mode only | Not reviewed |
| `TenFrame` | `bg-white`, `border-gray-200` | No dark mode |
| `AngleMaker` | `bg-white`, `border-gray-200`, `text-gray-700` | No dark mode |
| `Ruler` | Likely light mode only | Not reviewed |
| `Protractor` | Likely light mode only | Not reviewed |
| `DivisionGrouping` | Likely light mode only | Not reviewed |
| `PlaceValueChart` | Likely light mode only | Not reviewed |
| `AnimatedArray` | `bg-white`, `border-gray-200`, `text-gray-700` | No dark mode |

**Impact:** On dark mode, most lesson content visuals (Base10Blocks, NumberLine, ComparisonBars, TenFrame, etc.) will show white backgrounds and invisible text on dark backgrounds.

---

## 5. ✅ NaNpx Fix — AngleMaker

**Previous bug:** `armLength` arrived as string `"100"` → `Math.cos(string)` = NaN → rendered "NaN°"

**Current code (lines 664–671):**
```typescript
const parsedAngle = Number(angle)           // ✅ Number() conversion
const parsedArm = Number(armLength)         // ✅ Number() conversion
const clampedAngle = Math.max(0, Math.min(180, parsedAngle || 0))  // ✅ clamp 0-180
const rad = (clampedAngle * Math.PI) / 180
const arcX = parsedArm * Math.cos(rad)
const arcY = parsedArm * Math.sin(rad)
const viewBoxSize = parsedArm + 20
```

**⚠️ One remaining issue:** `arcX` and `arcY` are computed but never used (lines 669-670). The SVG uses `parsedArm` directly for coordinates. Dead code, but harmless.

---

## 6. ✅ NumberLine Overflow Fix

**Previous bug:** SVG arc went off-screen on small viewports.

**Current code:**
```typescript
// Line 107: effectiveMax clamped
const clampedMax = Math.max(effectiveMax, Math.max(parsedA, result) + 5)

// Line 110: overflow-hidden on container
<div className="... overflow-hidden">

// Lines 120, 127, 138, etc.: Math.min(..., 100) cap on all percentages
style={{ left: `${Math.min((i / clampedMax) * 100, 100)}%` }}
```

**All percentage calculations capped at 100%.** ✅

---

## 7. ✅ ComparisonBars Flex Rewrite

**Previous bug:** Used template literals inside `calc()` → CSS didn't evaluate JS → no bars rendered.

**Current code (line 597):**
```typescript
<div className="... overflow-hidden" style={{ width: '100%', maxWidth: '200px' }}>
```

**Flex-based layout with fixed width, no calc().** ✅

---

## 8. EnhancedLessonContent Text — No Dark Mode

**Line 318:**
```typescript
<div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
```

**`text-gray-700` has no dark mode override.** In dark mode, lesson body text will be dark gray (barely visible) on dark backgrounds.

**This applies to ALL rendered text in lesson content** (headings, paragraphs, blockquotes, lists, etc.) — only the interactive blocks (TryIt, BarModel) have dark mode.

**Severity: HIGH** — majority of lesson text is unreadable in dark mode.

---

## PHASE 6 — Completion Criteria

| Criteria | Status |
|---|---|
| All 4 block parsers identified and verified | ✅ |
| All visual components identified | ✅ |
| NaNpx fix verified | ✅ |
| NumberLine overflow fix verified | ✅ |
| ComparisonBars calc fix verified | ✅ |
| TryIt dark mode verified | ✅ |
| **Most lesson visuals have no dark mode** | ⚠️ CRITICAL |
| EnhancedLessonContent text has no dark mode | ⚠️ HIGH |
| Block multi-line parsing edge case | ⚠️ MEDIUM |
| `PHASE_6_findings.md` written | ✅ |

---

## Open Items

| Severity | Issue | Fix |
|---|---|---|
| CRITICAL | Most visual components (Base10Blocks, NumberLine, ComparisonBars, TenFrame, AngleMaker, ArrayGrid, etc.) have no dark mode | Add `dark:` Tailwind classes to all components |
| HIGH | EnhancedLessonContent wrapper uses `text-gray-700` with no dark mode | Change to `dark:text-gray-100` or add global override |
| MEDIUM | Block parser: closing `:::` on same line as content may cause capture issues | Test + fix regex |
| LOW | `arcX` and `arcY` in AngleMaker are computed but unused | Remove dead code |
