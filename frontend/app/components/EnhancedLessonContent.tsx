'use client'

import { useState } from 'react'
import {
  Base10Blocks,
  NumberLine,
  ArrayGrid,
  FractionVisual,
  AnimatedSteps,
  TryIt,
  Ruler,
  Protractor,
  DivisionGrouping,
  PlaceValueChart,
  ComparisonBars,
  TenFrame,
  AngleMaker,
  AnimatedArray,
  BarModel,
} from './LessonVisuals'

// ─── Block parsers ────────────────────────────────────────────────────────

// Parse visual blocks: :::visual:type,args::: or :::visual:type|args:::
function parseVisual(raw: string): React.ReactNode {
  const inner = raw.replace(/^:::visual:\s*/i, '').replace(/:::\s*$/i, '').trim()
  const commaIdx = inner.indexOf(',')
  const colonIdx = inner.indexOf(':')

  // Split on first comma only
  const firstSplit = commaIdx >= 0 ? [inner.slice(0, commaIdx), inner.slice(commaIdx + 1)] : [inner, '']
  const type = firstSplit[0].trim().toLowerCase()
  const args = firstSplit[1]

  // Split args by comma (for array:type,a,b)
  const parts = args.split(',').map(s => s.trim())

  switch (type) {
    case 'base10':
    case 'base-10': {
      return <Base10Blocks a={parseInt(parts[0])} b={parseInt(parts[1])} operation="add" showCarry />
    }
    case 'numberline':
    case 'number-line': {
      const op = parts[2] === 'subtract' || parts[2] === 'resta' ? 'subtract' : 'add'
      return <NumberLine a={parseInt(parts[0])} b={parseInt(parts[1])} operation={op} />
    }
    case 'array':
    case 'grid': {
      return <ArrayGrid rows={parseInt(parts[0])} cols={parseInt(parts[1])} />
    }
    case 'fraction': {
      return <FractionVisual numerator={parseInt(parts[0])} denominator={parseInt(parts[1])} />
    }
    case 'ruler': {
      return <Ruler start={parseFloat(parts[0])} end={parseFloat(parts[1])} unit={parts[2]} highlightStart={parseFloat(parts[3])} highlightEnd={parseFloat(parts[4])} />
    }
    case 'protractor': {
      return <Protractor angle={parseInt(parts[0])} showLabel={parts[1] !== 'false'} />
    }
    case 'division': {
      return <DivisionGrouping total={parseInt(parts[0])} groupSize={parseInt(parts[1])} color={parts[2]} />
    }
    case 'placevalue': {
      return <PlaceValueChart number={parseInt(parts[0])} highlight={parts[1]} />
    }
    case 'comparison': {
      const diff = parts[4] !== undefined ? parseInt(parts[4]) : undefined
      return <ComparisonBars smaller={parseInt(parts[0])} bigger={parseInt(parts[1])} labelSmaller={parts[2]} labelBigger={parts[3]} difference={diff} />
    }
    case 'tenframe': {
      return <TenFrame filled={parseInt(parts[0])} highlight={parts[1] !== undefined ? parseInt(parts[1]) : undefined} />
    }
    case 'anglemaker': {
      return <AngleMaker angle={parseInt(parts[0])} armLength={parseInt(parts[1])} color={parts[2]} />
    }
    case 'animatedarray': {
      return <AnimatedArray rows={parseInt(parts[0])} cols={parseInt(parts[1])} color={parts[2]} animate={parts[3] === 'true'} />
    }
    default:
      return <div className="text-xs text-gray-400 p-2 bg-gray-100 rounded my-2">Visual no reconocido: {type}</div>
  }
}

// Parse Try It blocks: :::tryit:question|answer|explanation:::
function parseTryIt(raw: string): React.ReactNode {
  const inner = raw.replace(/^:::tryit:\s*/i, '').replace(/:::\s*$/i, '')
  const parts = inner.split('|').map(s => s.trim())
  const question = parts[0] || ''
  const answer = parts[1] || ''
  const hint = parts[2] || ''
  const explanation = parts[3] || ''
  return <TryIt question={question} answer={answer} hint={hint} explanation={explanation} />
}

// Parse Steps blocks: :::steps:label1|result1:::label2|result2:::...
function parseSteps(raw: string): React.ReactNode {
  const inner = raw.replace(/^:::steps:\s*/i, '').replace(/:::\s*$/i, '')
  const stepParts = inner.split(':::').filter(Boolean)
  const steps = stepParts.map(part => {
    const [label, result] = part.split('|').map(s => s.trim())
    return { label: label || '', result: result || '' }
  })
  return <AnimatedSteps steps={steps} />
}

// Parse Bar Model blocks: :::bar:question|total|units:::[{"label":"...","value":N}...]
// Units encoded as pipe-separated: label1,value1|label2,value2|...
function parseBar(raw: string, grade = 1): React.ReactNode {
  const inner = raw.replace(/^:::bar:\s*/i, '').replace(/:::\s*$/i, '')
  const parts = inner.split(':::')
  // First part is question|total|type
  const mainPart = parts[0]
  const mainSections = mainPart.split('|').map((s: string) => s.trim())
  const question = mainSections[0] || ''
  const total = mainSections[1] || ''
  const barType = mainSections[2] || 'comparison'

  // Second part (if exists) is units JSON array string
  let units: { label: string; value: number }[] = []
  if (parts.length > 1) {
    try {
      units = JSON.parse(parts[1].trim())
    } catch {
      // Try pipe-separated fallback: label1,value1|label2,value2|...
      const unitParts = parts[1].split('|')
      units = unitParts.map((up: string) => {
        const [label, val] = up.split(',').map((s: string) => s.trim())
        return { label: label || '', value: parseInt(val) || 0 }
      })
    }
  }

  return <BarModel question={question} total={total} units={units} type={barType} grade={grade} />
}

// ─── Process inline markdown ─────────────────────────────────────────────

function renderInline(text: string): React.ReactNode[] {
  const parts: React.ReactNode[] = []
  const regex = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g
  let last = 0
  let match: RegExpExecArray | null
  while ((match = regex.exec(text)) !== null) {
    if (match.index > last) parts.push(text.slice(last, match.index))
    const m = match[0]
    if (m.startsWith('**')) parts.push(<strong key={match.index} className="font-bold">{m.slice(2, -2)}</strong>)
    else if (m.startsWith('*')) parts.push(<em key={match.index} className="italic">{m.slice(1, -1)}</em>)
    else if (m.startsWith('`')) parts.push(<code key={match.index} className="bg-gray-100 rounded px-1 text-sm">{m.slice(1, -1)}</code>)
    last = regex.lastIndex
  }
  if (last < text.length) parts.push(text.slice(last))
  return parts
}

// ─── Emoji map for illustration shortcuts ──────────────────────────────────

const emojiMap: Record<string, string> = {
  '➕': 'SUMA', '➖': 'RESTA', '✖️': 'MULT', '➗': 'DIV',
  '🔢': 'NÚMERO', '📐': 'GEOMETRÍA', '📊': 'DATOS', '🧮': 'CÁLCULO',
  '🍎': 'MANZANA', '🍊': 'NARANJA', '⭐': 'ESTRELLA', '🎯': 'OBJETIVO',
}

// ─── Enhanced line renderer ───────────────────────────────────────────────

function renderLine(line: string, key: number): React.ReactNode {
  if (line.startsWith('# ')) return <h1 key={key} className="text-2xl font-bold text-gray-900 mt-6 mb-3">{renderInline(line.slice(2))}</h1>
  if (line.startsWith('## ')) return <h2 key={key} className="text-xl font-bold text-gray-900 mt-5 mb-2">{renderInline(line.slice(3))}</h2>
  if (line.startsWith('### ')) return <h3 key={key} className="text-lg font-semibold text-gray-800 mt-4 mb-1">{renderInline(line.slice(4))}</h3>
  if (line.startsWith('> ')) return <blockquote key={key} className="border-l-4 border-primary-300 pl-4 italic text-gray-600 my-3">{renderInline(line.slice(2))}</blockquote>
  if (line.startsWith('- ')) return <li key={key} className="ml-4 text-gray-700">{renderInline(line.slice(2))}</li>
  if (line.match(/^\d+\. /)) return <li key={key} className="ml-4 text-gray-700 list-decimal">{renderInline(line.replace(/^\d+\. /, ''))}</li>
  if (line.match(/^[A-Z][a-z]+.*:/)) return <p key={key} className="font-semibold text-gray-800 mt-3">{renderInline(line)}</p>
  if (line.trim() === '') return <div key={key} className="h-2" />
  return <p key={key} className="text-gray-700 my-1">{renderInline(line)}</p>
}

// ─── Main Enhanced Lesson Renderer ───────────────────────────────────────

interface EnhancedLessonContentProps {
  content: string
}

export function EnhancedLessonContent({ content }: EnhancedLessonContentProps) {
  const lines = content.split('\n')
  const elements: React.ReactNode[] = []
  let i = 0
  let key = 0

  while (i < lines.length) {
    const line = lines[i]

    // Skip empty lines at start
    if (line.trim() === '' && elements.length === 0) { i++; continue }

    // Check for visual blocks (:::...:::)
    if (line.includes(':::visual:') || line.match(/^:::visual/i)) {
      // Collect the full block (may span multiple lines)
      let block = line + '\n'
      let j = i + 1
      while (j < lines.length && !lines[j].match(/:::\s*$/)) {
        block += lines[j] + '\n'
        j++
      }
      // Extract the complete block
      const match = block.match(/(:::[\s\S]*?:::\s*)/)
      if (match) {
        elements.push(
          <div key={key++} className="my-3">
            {parseVisual(match[1])}
          </div>
        )
        i = j
        continue
      }
    }

    // Check for Try It blocks
    if (line.match(/^:::tryit/i)) {
      let block = line + '\n'
      let j = i + 1
      while (j < lines.length && !lines[j].match(/:::\s*$/)) {
        block += lines[j] + '\n'
        j++
      }
      const match = block.match(/(:::[\s\S]*?:::\s*)/)
      if (match) {
        elements.push(<div key={key++}>{parseTryIt(match[1])}</div>)
        i = j
        continue
      }
    }

    // Check for Steps blocks
    if (line.match(/^:::steps/i)) {
      let block = line + '\n'
      let j = i + 1
      while (j < lines.length && !lines[j].match(/:::\s*$/)) {
        block += lines[j] + '\n'
        j++
      }
      const match = block.match(/(:::[\s\S]*?:::\s*)/)
      if (match) {
        elements.push(<div key={key++}>{parseSteps(match[1])}</div>)
        i = j
        continue
      }
    }

    // Check for Bar Model blocks
    if (line.match(/^:::bar/i)) {
      let block = line + '\n'
      let j = i + 1
      while (j < lines.length && !lines[j].match(/:::\s*$/)) {
        block += lines[j] + '\n'
        j++
      }
      const match = block.match(/(:::[\s\S]*?:::\s*)/)
      if (match) {
        elements.push(<div key={key++}>{parseBar(match[1])}</div>)
        i = j
        continue
      }
    }

    // Handle headings that contain inline TryIts or embedded content
    if (line.startsWith('# ') || line.startsWith('## ') || line.startsWith('### ')) {
      // Check if heading contains inline visual reference
      if (line.includes(':::visual') || line.includes(':::tryit') || line.includes(':::steps')) {
        // Extract inline blocks within heading and render separately
        const headingLevel = line.match(/^(#+)/)?.[1].length || 2
        const headingContent = line.replace(/^#+\s*/, '')
        const headingClass = headingLevel === 1
          ? 'text-2xl font-bold text-gray-900 dark:text-gray-100 mt-6 mb-3'
          : headingLevel === 2
            ? 'text-xl font-bold text-gray-900 dark:text-gray-100 mt-5 mb-2'
            : 'text-lg font-semibold text-gray-800 dark:text-gray-200 mt-4 mb-1'

        elements.push(
          <div key={key++} className={headingClass}>
            {renderInline(headingContent)}
          </div>
        )
        i++
        continue
      }
      elements.push(renderLine(line, key++))
      i++
      continue
    }

    // Regular content — group consecutive non-empty lines into paragraphs
    if (line.trim() !== '' && !line.startsWith('#') && !line.startsWith('-') && !line.match(/^\d+\. /)) {
      const paragraphLines: string[] = []
      let j = i
      while (j < lines.length && lines[j].trim() !== '' && !lines[j].startsWith('#') && !lines[j].startsWith('-') && !lines[j].match(/^\d+\. /)) {
        paragraphLines.push(lines[j])
        j++
      }
      // If it's just one line that's not a special case, render as paragraph with inline
      if (paragraphLines.length === 1) {
        elements.push(renderLine(paragraphLines[0], key++))
      } else {
        // Multiple lines — render each with spacing
        paragraphLines.forEach((l, idx) => {
          elements.push(renderLine(l, key++))
        })
      }
      i = j
      continue
    }

    elements.push(renderLine(line, key++))
    i++
  }

  return (
    <div className="text-gray-700 dark:text-gray-200 leading-relaxed whitespace-pre-wrap">
      {elements}
    </div>
  )
}
