'use client'

import { useState, useRef, useCallback } from 'react'

// ─── Base-10 Blocks for Addition/Subtraction ───────────────────────────────
interface Base10BlocksProps {
  a: number
  b: number
  operation?: 'add' | 'subtract'
  showCarry?: boolean
}

export function Base10Blocks({ a, b, operation = 'add', showCarry = false }: Base10BlocksProps) {
  const parsedA = Number(a) || 0
  const parsedB = Number(b) || 0
  const result = operation === 'add' ? parsedA + parsedB : parsedA - parsedB
  const aTens = Math.floor(parsedA / 10)
  const aOnes = parsedA % 10
  const bTens = Math.floor(parsedB / 10)
  const bOnes = parsedB % 10
  const rTens = Math.floor(result / 10)
  const rOnes = result % 10
  const carry = showCarry && operation === 'add' && aOnes + bOnes >= 10

  const Block = ({ filled, label }: { filled: boolean; label?: string }) => (
    <div className={`w-8 h-8 sm:w-10 sm:h-10 rounded flex items-center justify-center font-bold text-xs border-2 transition-all duration-300 ${
      filled
        ? operation === 'subtract' && label === 'ones_result'
          ? 'bg-orange-200 dark:bg-orange-900 border-orange-400 dark:border-orange-600'
          : 'bg-primary-200 dark:bg-primary-900 border-primary-400 dark:border-primary-600'
        : 'bg-gray-100 dark:bg-slate-700 border-gray-300 dark:border-slate-500 dark:border-slate-500'
    }`}>
      {label && <span className="text-xs text-gray-500 dark:text-gray-400">{label}</span>}
    </div>
  )

  const Row = ({ label, tens, ones, resultTens, resultOnes }: { label: string; tens: number; ones: number; resultTens?: number; resultOnes?: number }) => (
    <div className="flex items-center gap-2 sm:gap-3 overflow-x-auto">
      <span className="w-12 sm:w-16 text-xs sm:text-sm font-medium text-gray-600 dark:text-gray-400 dark:text-gray-300 whitespace-nowrap">{label}</span>
      <div className="flex gap-0.5 flex-wrap">
        {Array.from({ length: Math.max(10, tens + (resultTens ?? 0) + 2) }).map((_, i) => (
          <Block key={`b${i}`} filled={i < tens} />
        ))}
      </div>
      <span className="text-gray-400 dark:text-gray-500">+</span>
      <div className="flex gap-0.5 flex-wrap">
        {Array.from({ length: Math.max(10, (bOnes ?? 0) + 2) }).map((_, i) => (
          <Block key={`bo${i}`} filled={i < bOnes} />
        ))}
      </div>
      {resultTens !== undefined && (
        <span className="text-gray-400 dark:text-gray-500 ml-1 sm:ml-2">=</span>
      )}
      {resultTens !== undefined && (
        <div className="flex gap-0.5 flex-wrap">
          {Array.from({ length: Math.max(10, (resultTens ?? 0) + (resultOnes ?? 0) + 2) }).map((_, i) => (
            <Block key={`r${i}`} filled={i < resultTens} />
          ))}
          {resultOnes !== undefined && (
            <div className="flex gap-0.5 flex-wrap">
              {Array.from({ length: Math.max(10, resultOnes + 2) }).map((_, i) => (
                <Block key={`ro${i}`} filled={i < resultOnes} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-3 sm:p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-2 sm:my-4 overflow-x-auto">
      <p className="text-xs sm:text-sm font-semibold text-gray-700 dark:text-gray-200 dark:text-gray-200 mb-2 sm:mb-3">
        {operation === 'add' ? '🎯 Modelo de Base-10' : '🎯 Modelo de Base-10 (Resta)'}
      </p>
      <div className="space-y-1 sm:space-y-2 min-w-0">
        <Row label={`${parsedA} =`} tens={aTens} ones={aOnes} />
        <Row label={`${parsedB} =`} tens={bTens} ones={bOnes} />
        {carry && (
          <div className="text-xs text-green-600 dark:text-green-400 font-medium ml-4 animate-pulse">
            ↑ Llevamos 1 a las decenas ↑
          </div>
        )}
        <div className="border-t border-gray-300 dark:border-slate-500 pt-1 sm:pt-2 mt-1 sm:mt-2">
          <Row label={`= ${result}`} tens={rTens} ones={rOnes} />
        </div>
      </div>
    </div>
  )
}

// ─── Number Line ──────────────────────────────────────────────────────────
interface NumberLineProps {
  a: number
  b: number
  operation?: 'add' | 'subtract'
  max?: number
}

export function NumberLine({ a, b, operation = 'add', max }: NumberLineProps) {
  const parsedA = Number(a) || 0
  const parsedB = Number(b) || 0
  const parsedMax = Number(max) || 0
  const rawResult = operation === 'add' ? parsedA + parsedB : parsedA - parsedB
  const result = Math.max(0, rawResult)
  const effectiveMax = parsedMax || Math.max(parsedA + parsedB + 10, 20)
  const clampedMax = Math.max(effectiveMax, Math.max(parsedA, result) + 5)

  return (
    <div className="bg-white rounded-xl p-3 sm:p-4 border border-gray-200 dark:border-slate-600 my-2 sm:my-4 overflow-hidden">
      <p className="text-xs sm:text-sm font-semibold text-gray-700 dark:text-gray-200 mb-2 sm:mb-3">📏 Recta Numérica</p>
      <div className="relative h-12 sm:h-16 overflow-hidden">
        {/* Line */}
        <div className="absolute top-1/2 left-0 right-0 h-1 bg-gray-300 -translate-y-1/2" />
        {/* Arrow */}
        <div className="absolute right-0 top-1/2 -translate-y-1/2 w-0 h-0 border-t-8 border-b-8 border-l-12 border-l-gray-400 border-t-transparent border-b-transparent" />

        {/* Number marks */}
        {Array.from({ length: Math.min(clampedMax + 1, 30) }).map((_, i) => (
          <div key={i} className="absolute top-1/2 -translate-y-1/2" style={{ left: `${Math.min((i / clampedMax) * 100, 100)}%` }}>
            <div className="w-0.5 h-3 bg-gray-400 -translate-x-1/2" />
            <span className="text-xs text-gray-500 absolute -top-5 left-1/2 -translate-x-1/2 whitespace-nowrap">{i}</span>
          </div>
        ))}

        {/* Start point */}
        <div className="absolute top-1/2 -translate-y-1/2" style={{ left: `${Math.min((parsedA / clampedMax) * 100, 100)}%` }}>
          <div className="w-4 h-4 bg-primary-500 rounded-full border-2 border-white shadow -translate-x-1/2" />
          <span className="text-xs font-bold text-primary-600 absolute -bottom-5 left-1/2 -translate-x-1/2 whitespace-nowrap">{parsedA}</span>
        </div>

        {/* Jump arc */}
        <svg
          className="absolute inset-0 pointer-events-none overflow-visible"
          style={{ zIndex: 2 }}
        >
          <path
            d={`M ${Math.min((parsedA / clampedMax) * 100, 100)}% 50% Q ${Math.min(((parsedA + parsedB / 2) / clampedMax) * 100, 100)}% ${operation === 'add' ? '20%' : '-20%'} ${Math.min((result / clampedMax) * 100, 100)}% 50%`}
            fill="none"
            stroke="var(--primary-400, #818cf8)"
            strokeWidth="3"
            strokeDasharray={operation === 'subtract' ? '6 4' : 'none'}
            className="animate-dash-flow"
          />
          {/* Arrow head */}
          {operation === 'add' ? (
            <polygon
              points={`${Math.min((result / clampedMax) * 100, 100)}%,50% ${Math.min((result / clampedMax) * 100 - 1.5, 100)}%,46% ${Math.min((result / clampedMax) * 100 - 1.5, 100)}%,54%`}
              className="fill-primary-400"
            />
          ) : (
            <polygon
              points={`${Math.min((result / clampedMax) * 100, 100)}%,50% ${Math.min((result / clampedMax) * 100 + 1.5, 100)}%,46% ${Math.min((result / clampedMax) * 100 + 1.5, 100)}%,54%`}
              className="fill-red-400"
            />
          )}
        </svg>

        {/* End point */}
        <div className="absolute top-1/2 -translate-y-1/2" style={{ left: `${Math.min((result / clampedMax) * 100, 100)}%` }}>
          <div className={`w-4 h-4 rounded-full border-2 border-white shadow -translate-x-1/2 ${operation === 'add' ? 'bg-primary-500' : 'bg-red-500'}`} />
          <span className={`text-xs font-bold absolute -bottom-5 left-1/2 -translate-x-1/2 ${operation === 'add' ? 'text-primary-600' : 'text-red-600'}`}>
            {result}
          </span>
        </div>
      </div>

      <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-400 dark:text-gray-400 mt-4 sm:mt-4 text-center">
        {operation === 'add'
          ? `Desde ${parsedA}, avanzamos ${parsedB} → ${result}`
          : `Desde ${parsedA}, retrocedemos ${parsedB} → ${result}`}
      </p>
    </div>
  )
}

// ─── Array Grid (Multiplication) ───────────────────────────────────────────
interface ArrayGridProps {
  rows: number
  cols: number
  highlightCells?: number
}

export function ArrayGrid({ rows, cols, highlightCells }: ArrayGridProps) {
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">🔲 Modelo de Arreglo ({rows} × {cols})</p>
      <div className="flex flex-col gap-1">
        {Array.from({ length: rows }).map((_, row) => (
          <div key={row} className="flex gap-1">
            {Array.from({ length: cols }).map((_, col) => {
              const idx = row * cols + col
              const highlighted = highlightCells !== undefined && idx < highlightCells
              return (
                <div
                  key={col}
                  className={`w-8 h-8 rounded border-2 flex items-center justify-center text-xs font-bold transition-all ${
                    highlighted
                      ? 'bg-orange-200 border-orange-400'
                      : 'bg-purple-100 border-purple-300'
                  }`}
                >
                  {highlighted ? '⬛' : '🔵'}
                </div>
              )
            })}
          </div>
        ))}
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 text-center font-medium">
        {rows} filas × {cols} columnas = <span className="text-primary-600 font-bold text-base">{rows * cols}</span> puntos
      </p>
    </div>
  )
}

// ─── Fraction Visual ──────────────────────────────────────────────────────
interface FractionVisualProps {
  numerator: number
  denominator: number
  showAddition?: { n2: number; d2: number }
}

export function FractionVisual({ numerator, denominator, showAddition }: FractionVisualProps) {
  const total = showAddition ? numerator + numerator * (denominator / showAddition.d2) + showAddition.n2 : numerator
  const maxDenom = showAddition ? Math.max(denominator, showAddition.d2) : denominator

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">🍕 Modelo de Fracciones</p>

      {/* Simple fraction */}
      <div className="flex items-center gap-4 mb-4">
        <div className="flex flex-col items-center gap-0">
          {Array.from({ length: numerator }).map((_, i) => (
            <div key={i} className="w-8 h-4 bg-orange-400 border border-orange-600 rounded-sm" />
          ))}
          {Array.from({ length: denominator - numerator }).map((_, i) => (
            <div key={i} className="w-8 h-4 bg-gray-100 dark:bg-slate-700 border border-gray-300 dark:border-slate-500 dark:border-slate-500 rounded-sm" />
          ))}
          <div className="w-10 border-t-2 border-gray-600 mt-1" />
          <span className="text-xs font-bold text-gray-600 dark:text-gray-400">{denominator}</span>
        </div>
        <span className="text-2xl font-bold text-gray-400">=</span>
        <span className="text-3xl font-bold text-orange-500">{numerator}/{denominator}</span>
      </div>

      {showAddition && (
        <div className="flex items-center gap-4 pt-3 border-t border-gray-200 dark:border-slate-600">
          <div className="flex flex-col items-center gap-0">
            {Array.from({ length: showAddition.n2 }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-orange-400 border border-orange-600 rounded-sm" />
            ))}
            {Array.from({ length: showAddition.d2 - showAddition.n2 }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-gray-100 dark:bg-slate-700 border border-gray-300 dark:border-slate-500 dark:border-slate-500 rounded-sm" />
            ))}
            <div className="w-10 border-t-2 border-gray-600 mt-1" />
            <span className="text-xs font-bold text-gray-600 dark:text-gray-400">{showAddition.d2}</span>
          </div>
          <span className="text-2xl font-bold text-gray-400">+</span>
          <div className="flex flex-col items-center gap-0">
            {Array.from({ length: numerator }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-orange-400 border border-orange-600 rounded-sm" />
            ))}
            {Array.from({ length: denominator - numerator }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-gray-100 dark:bg-slate-700 border border-gray-300 dark:border-slate-500 dark:border-slate-500 rounded-sm" />
            ))}
            <div className="w-10 border-t-2 border-gray-600 mt-1" />
            <span className="text-xs font-bold text-gray-600 dark:text-gray-400">{denominator}</span>
          </div>
          <span className="text-2xl font-bold text-gray-400">=</span>
          <div className="flex flex-col items-center gap-0">
            {Array.from({ length: showAddition.n2 }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-orange-400 border border-orange-600 rounded-sm" />
            ))}
            {Array.from({ length: denominator - numerator }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-orange-400 border border-orange-600 rounded-sm" />
            ))}
            {Array.from({ length: showAddition.d2 - showAddition.n2 }).map((_, i) => (
              <div key={i} className="w-8 h-4 bg-gray-100 dark:bg-slate-700 border border-gray-300 dark:border-slate-500 dark:border-slate-500 rounded-sm" />
            ))}
            <div className="w-10 border-t-2 border-gray-600 mt-1" />
            <span className="text-xs font-bold text-gray-600 dark:text-gray-400">{denominator + showAddition.d2}</span>
          </div>
        </div>
      )}

      <p className="text-sm text-gray-600 dark:text-gray-400 mt-2 text-center">
        {numerator}/{denominator} = {numerator} partes de {denominator}
      </p>
    </div>
  )
}

// ─── Animated Step Counter ─────────────────────────────────────────────────
interface AnimatedStepsProps {
  steps: { label: string; result: string; visual?: React.ReactNode }[]
}

export function AnimatedSteps({ steps }: AnimatedStepsProps) {
  const [visible, setVisible] = useState<number[]>([])

  const reveal = () => {
    const next = visible.length < steps.length ? visible.length : 0
    setVisible([...visible.slice(0, next), next])
  }

  const reset = () => setVisible([])

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">📋 Pasos Animados</p>

      <div className="space-y-2">
        {steps.map((step, i) => (
          <div
            key={i}
            className={`flex items-center gap-3 p-2 rounded-lg border-2 transition-all duration-500 ${
              visible.includes(i)
                ? 'border-primary-300 bg-primary-50 opacity-100'
                : 'border-gray-200 dark:border-slate-600 bg-gray-50 opacity-40'
            }`}
          >
            <div className={`w-7 h-7 rounded-full flex items-center justify-center text-sm font-bold transition-all ${
              visible.includes(i) ? 'bg-primary-500 text-white' : 'bg-gray-300 text-gray-500'
            }`}>
              {visible.includes(i) ? '✓' : i + 1}
            </div>
            <div className="flex-1">
              <span className="text-sm text-gray-700 dark:text-gray-200">{step.label}</span>
              {visible.includes(i) && (
                <span className="ml-2 text-sm font-bold text-primary-600">{step.result}</span>
              )}
            </div>
            {visible.includes(i) && step.visual && (
              <div className="ml-2">{step.visual}</div>
            )}
          </div>
        ))}
      </div>

      <div className="flex gap-2 mt-3">
        <button onClick={reveal} className="btn-secondary text-sm flex-1">
          {visible.length < steps.length ? '▶️ Mostrar siguiente paso' : '🔄 Reiniciar'}
        </button>
        {visible.length > 0 && (
          <button onClick={reset} className="btn-secondary text-sm">🔄</button>
        )}
      </div>
    </div>
  )
}

// ─── Ruler ─────────────────────────────────────────────────────────────────
interface RulerProps {
  start?: number
  end?: number
  unit?: string
  highlightStart?: number
  highlightEnd?: number
}

export function Ruler({ start = 0, end = 10, unit = 'cm', highlightStart, highlightEnd }: RulerProps) {
  const range = end - start
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">📏 Regla Interactiva</p>
      <div className="relative h-16 bg-yellow-50 dark:bg-yellow-900/20 rounded border-2 border-gray-400 flex items-end">
        {Array.from({ length: range + 1 }).map((_, i) => {
          const pos = (i / range) * 100
          const isHighlighted = highlightStart !== undefined && highlightEnd !== undefined && i >= highlightStart && i <= highlightEnd
          return (
            <div key={i} className="absolute bottom-0 flex flex-col items-center" style={{ left: `${pos}%` }}>
              <div className={`w-0.5 ${i % 5 === 0 ? 'h-6 bg-gray-800' : 'h-3 bg-gray-500'}`} />
              {i % 5 === 0 && <span className="text-xs font-bold text-gray-700 dark:text-gray-200 mt-0.5">{start + i}</span>}
            </div>
          )
        })}
        {highlightStart !== undefined && highlightEnd !== undefined && (
          <div
            className="absolute bg-yellow-300 opacity-50 rounded-sm"
            style={{
              left: `${((highlightStart - start) / range) * 100}%`,
              right: `${((end - highlightEnd) / range) * 100}%`,
              bottom: '0.5rem',
              height: '1.5rem',
            }}
          />
        )}
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">Unidad: {unit}</p>
    </div>
  )
}

// ─── Protractor ─────────────────────────────────────────────────────────────
interface ProtractorProps {
  angle?: number
  showLabel?: boolean
}

export function Protractor({ angle = 60, showLabel = true }: ProtractorProps) {
  const clampedAngle = Math.max(0, Math.min(180, angle))
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">📐 Transportador</p>
      <div className="relative w-48 h-24 mx-auto">
        {/* Semicircle background */}
        <div
          className="absolute inset-0 rounded-full border-4 border-gray-300 dark:border-slate-500"
          style={{ borderRadius: '50%', height: '200%', top: '0' }}
        />
        {/* Flat top line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-400 -translate-y-1/2" />
        {/* Degree ticks */}
        {Array.from({ length: 13 }).map((_, i) => {
          const deg = i * 15
          const rad = (deg - 90) * (Math.PI / 180)
          const len = deg % 45 === 0 ? 12 : 6
          const x1 = 96 + Math.cos(rad) * (80 - len)
          const y1 = 96 + Math.sin(rad) * (80 - len)
          const x2 = 96 + Math.cos(rad) * 80
          const y2 = 96 + Math.sin(rad) * 80
          return (
            <svg key={deg} className="absolute inset-0 w-full h-full" viewBox="0 0 192 96">
              <line x1={x1} y1={y1} x2={x2} y2={y2} stroke="gray" strokeWidth={deg % 45 === 0 ? 2 : 1} />
              {deg % 45 === 0 && (
                <text x={96 + Math.cos(rad) * 65} y={96 + Math.sin(rad) * 65} fontSize="8" textAnchor="middle" fill="gray">{deg}</text>
              )}
            </svg>
          )
        })}
        {/* Baseline arm */}
        <div className="absolute top-1/2 left-2 w-20 h-1 bg-blue-500 -translate-y-1/2 origin-left" style={{ transform: 'rotate(0deg)' }} />
        {/* Angle arm */}
        <div
          className="absolute top-1/2 left-2 w-20 h-1 bg-orange-500 -translate-y-1/2 origin-left"
          style={{ transform: `rotate(${clampedAngle}deg)` }}
        />
        {/* Angle arc */}
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 192 96">
          <path
            d={`M 38 96 A 58 58 0 0 1 ${96 + 58 * Math.cos((clampedAngle - 90) * Math.PI / 180)} ${96 + 58 * Math.sin((clampedAngle - 90) * Math.PI / 180)}`}
            fill="none"
            stroke="#f59e0b"
            strokeWidth="3"
          />
        </svg>
        {/* Label */}
        {showLabel && (
          <div
            className="absolute font-bold text-orange-600"
            style={{
              left: '50%',
              top: '25%',
              transform: `rotate(${clampedAngle / 2}deg) translateX(20px)`,
            }}
          >
            {clampedAngle}°
          </div>
        )}
      </div>
    </div>
  )
}

// ─── Division Grouping ───────────────────────────────────────────────────────
interface DivisionGroupingProps {
  total?: number
  groupSize?: number
  color?: string
}

export function DivisionGrouping({ total = 12, groupSize = 3, color = '#6366f1' }: DivisionGroupingProps) {
  const quotient = Math.floor(total / groupSize)
  const remainder = total % groupSize
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">➗ Modelo de División</p>
      <div className="flex flex-wrap gap-1 mb-4 justify-center">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className="w-7 h-7 rounded-full border-2 flex items-center justify-center text-xs font-bold"
            style={{ backgroundColor: color, borderColor: color, color: 'white' }}
          >
            🟢
          </div>
        ))}
      </div>
      {/* Grouping bins */}
      <div className="flex gap-2 justify-center mb-3 flex-wrap">
        {Array.from({ length: quotient }).map((_, g) => (
          <div key={g} className="flex flex-col items-center gap-1">
            <div className="flex gap-0.5 flex-wrap justify-center max-w-24">
              {Array.from({ length: groupSize }).map((_, i) => (
                <div
                  key={i}
                  className="w-5 h-5 rounded-full border-2 flex items-center justify-center text-xs"
                  style={{ backgroundColor: color, borderColor: color, color: 'white' }}
                >
                  ●
                </div>
              ))}
            </div>
            <div className="w-full border-t-2 border-gray-400 mt-1" />
          </div>
        ))}
        {remainder > 0 && (
          <div className="flex flex-col items-center gap-1">
            <div className="flex gap-0.5 flex-wrap justify-center max-w-24">
              {Array.from({ length: remainder }).map((_, i) => (
                <div
                  key={i}
                  className="w-5 h-5 rounded-full border-2 border-dashed flex items-center justify-center text-xs opacity-50"
                  style={{ borderColor: color, color }}
                >
                  ●
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
      <p className="text-center text-sm font-medium text-gray-700 dark:text-gray-200">
        {total} ÷ {groupSize} = <span className="text-primary-600 font-bold text-base">{quotient}</span>
        {remainder > 0 && <span className="text-gray-400 text-xs"> (resto {remainder})</span>}
      </p>
    </div>
  )
}

// ─── Place Value Chart ──────────────────────────────────────────────────────
interface PlaceValueChartProps {
  number?: number
  highlight?: string
}

export function PlaceValueChart({ number: num = 1234, highlight = 'tens' }: PlaceValueChartProps) {
  const thousands = Math.floor(num / 1000) % 10
  const hundreds = Math.floor(num / 100) % 10
  const tens = Math.floor(num / 10) % 10
  const ones = num % 10
  const columns = [
    { label: 'M Miles', emoji: '💎', value: thousands, key: 'thousands' },
    { label: 'C Centenas', emoji: '💰', value: hundreds, key: 'hundreds' },
    { label: 'D Decenas', emoji: '🔟', value: tens, key: 'tens' },
    { label: 'U Unidades', emoji: '1️⃣', value: ones, key: 'ones' },
  ]
  const highlightColor = 'bg-yellow-100 border-yellow-400'

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">🔢 Valor Posicional</p>
      <div className="grid grid-cols-4 gap-2 text-center">
        {columns.map(col => (
          <div
            key={col.key}
            className={`rounded-lg border-2 p-2 transition-all ${col.key === highlight ? highlightColor : 'border-gray-200 dark:border-slate-600 bg-gray-50'}`}
          >
            <div className="text-xs text-gray-500 mb-1">{col.emoji} {col.label}</div>
            <div className={`text-3xl font-bold ${col.key === highlight ? 'text-yellow-600' : 'text-gray-700 dark:text-gray-200'}`}>
              {col.value}
            </div>
          </div>
        ))}
      </div>
      <p className="text-center text-sm text-gray-600 dark:text-gray-400 mt-3 font-medium">
        Número: <span className="text-primary-600 font-bold">{num}</span>
      </p>
    </div>
  )
}

// ─── Comparison Bars ────────────────────────────────────────────────────────
interface ComparisonBarsProps {
  smaller?: number
  bigger?: number
  labelSmaller?: string
  labelBigger?: string
  difference?: number
}

export function ComparisonBars({ smaller = 3, bigger = 7, labelSmaller = 'Pequeño', labelBigger = 'Grande', difference }: ComparisonBarsProps) {
  const diff = difference ?? (bigger - smaller)
  const parsedSmaller = Number(smaller) || 0
  const parsedBigger = Number(bigger) || 0
  const smallerWidth = parsedBigger > 0 ? Math.min((parsedSmaller / parsedBigger) * 100, 100) : 0

  return (
    <div className="bg-white rounded-xl p-3 sm:p-4 border border-gray-200 dark:border-slate-600 my-2 sm:my-4 overflow-hidden">
      <p className="text-xs sm:text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">📊 Barras de Comparación</p>
      <div className="space-y-3 sm:space-y-4">
        {/* Bigger bar */}
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="w-16 sm:w-20 text-xs text-gray-600 dark:text-gray-400 text-right flex-shrink-0">{labelBigger}</span>
          <div className="relative h-7 sm:h-8 min-w-0 bg-blue-400 rounded flex items-center px-2 overflow-hidden" style={{ width: '100%', maxWidth: '200px' }}>
            <span className="text-white text-xs sm:text-sm font-bold whitespace-nowrap">{parsedBigger}</span>
          </div>
        </div>
        {/* Smaller bar */}
        <div className="flex items-center gap-2 sm:gap-3">
          <span className="w-16 sm:w-20 text-xs text-gray-600 dark:text-gray-400 text-right flex-shrink-0">{labelSmaller}</span>
          <div className="relative h-7 sm:h-8 min-w-0 bg-primary-400 rounded flex items-center px-2 overflow-hidden" style={{ width: `${smallerWidth}%`, maxWidth: '200px' }}>
            <span className="text-white text-xs sm:text-sm font-bold whitespace-nowrap">{parsedSmaller}</span>
          </div>
        </div>
        {/* Difference badge */}
        <div className="flex items-center justify-center pt-1">
          <div className="bg-red-100 border-2 border-red-500 rounded px-3 py-1">
            <span className="text-red-600 font-bold text-xs sm:text-sm">+{diff}</span>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Ten Frame ──────────────────────────────────────────────────────────────
interface TenFrameProps {
  filled?: number
  highlight?: number
}

export function TenFrame({ filled = 7, highlight }: TenFrameProps) {
  const cells = Array.from({ length: 10 }, (_, i) => i)
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">🔢 Marco de Diez</p>
      <div className="grid grid-cols-5 gap-1 max-w-48 mx-auto">
        {cells.map(i => {
          const isFilled = i < filled
          const isHighlighted = highlight !== undefined && i === highlight
          return (
            <div
              key={i}
              className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all ${
                isHighlighted
                  ? 'border-yellow-400 bg-yellow-100 ring-2 ring-yellow-400'
                  : isFilled
                    ? 'bg-primary-200 border-primary-400'
                    : 'bg-gray-50 border-gray-300 dark:border-slate-500'
              }`}
            >
              {isFilled ? '🔵' : '⚪'}
            </div>
          )
        })}
      </div>
      <p className="text-center text-sm text-gray-600 dark:text-gray-400 mt-3 font-medium">
        {filled} de 10 <span className="text-primary-600 font-bold">→</span> {10 - filled} vacío{10 - filled !== 1 ? 's' : ''}
      </p>
    </div>
  )
}

// ─── Angle Maker ─────────────────────────────────────────────────────────────
interface AngleMakerProps {
  angle?: number
  armLength?: number
  color?: string
}

export function AngleMaker({ angle, armLength = 100, color = '#f59e0b' }: AngleMakerProps) {
  const parsedAngle = Number(angle)
  const parsedArm = Number(armLength)
  const clampedAngle = Math.max(0, Math.min(180, parsedAngle || 0))
  const rad = (clampedAngle * Math.PI) / 180
  const arcX = parsedArm * Math.cos(rad)
  const arcY = parsedArm * Math.sin(rad)
  const viewBoxSize = parsedArm + 20

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4 overflow-hidden">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">📏 Creador de Ángulos</p>
      <div className="flex justify-center">
        <svg width="200" height="120" viewBox={`-10 -10 ${viewBoxSize + 10} ${viewBoxSize / 2 + 10}`} className="overflow-visible">
          {/* Fixed arm */}
          <line x1="0" y1="0" x2={parsedArm} y2="0" stroke="#3b82f6" strokeWidth="3" strokeLinecap="round" />
          {/* Rotating arm */}
          <line x1="0" y1="0" x2={parsedArm * Math.cos(rad)} y2={-parsedArm * Math.sin(rad)} stroke={color} strokeWidth="3" strokeLinecap="round" />
          {/* Angle arc */}
          {clampedAngle > 0 && (
            <path
              d={`M ${parsedArm - 15} 0 A ${parsedArm - 15} ${parsedArm - 15} 0 0 1 ${(parsedArm - 15) * Math.cos(rad)} ${-(parsedArm - 15) * Math.sin(rad)}`}
              fill="none"
              stroke={color}
              strokeWidth="2"
              strokeDasharray="4 2"
            />
          )}
          {/* Label */}
          <text x={parsedArm / 2 + 10} y={-10} fill={color} fontWeight="bold" fontSize="14">{clampedAngle}°</text>
          {/* Vertex dot */}
          <circle cx="0" cy="0" r="4" fill="#374151" />
        </svg>
      </div>
      <p className="text-xs text-gray-500 mt-2 text-center">Ángulo: {clampedAngle}° | Largo del brazo: {parsedArm}px</p>
    </div>
  )
}

// ─── Animated Array ──────────────────────────────────────────────────────────
interface AnimatedArrayProps {
  rows?: number
  cols?: number
  color?: string
  animate?: boolean
}

export function AnimatedArray({ rows = 3, cols = 4, color = '#8b5cf6', animate = false }: AnimatedArrayProps) {
  const total = rows * cols
  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <p className="text-sm font-semibold text-gray-700 dark:text-gray-200 mb-3">🔢 Arreglo Animado ({rows} × {cols})</p>
      <style>{`
        @keyframes fadeInCell {
          from { opacity: 0; transform: scale(0.5); }
          to { opacity: 1; transform: scale(1); }
        }
        .array-cell-animate {
          animation: fadeInCell 0.3s ease-out forwards;
        }
      `}</style>
      <div className="flex flex-col gap-1">
        {Array.from({ length: rows }).map((_, row) => (
          <div key={row} className="flex gap-1">
            {Array.from({ length: cols }).map((_, col) => {
              const idx = row * cols + col
              const delay = animate ? `${idx * 50}ms` : '0ms'
              return (
                <div
                  key={col}
                  className={`w-8 h-8 rounded border-2 flex items-center justify-center text-xs font-bold array-cell-animate ${animate ? 'array-cell-animate' : ''}`}
                  style={{
                    backgroundColor: color + '20',
                    borderColor: color,
                    color: color,
                    animationDelay: delay,
                    opacity: animate ? 0 : 1,
                  }}
                >
                  🔵
                </div>
              )
            })}
          </div>
        ))}
      </div>
      <p className="text-sm text-gray-600 dark:text-gray-400 mt-3 text-center font-medium">
        {rows} filas × {cols} columnas = <span className="text-primary-600 font-bold text-base">{rows * cols}</span> puntos
      </p>
    </div>
  )
}

// ─── Interactive Bar Model (Singapore Math) — drag-and-drop construction ───────
export interface BarModelSegment {
  id: string
  label: string
  value: number
  order: number
  timestamp: number
}

export interface BarModelConstructionJSON {
  type: 'bar_model_construction'
  segments_built: BarModelSegment[]
  total_built: string
  final_answer: string
  time_spent_ms: number
}

interface InteractiveBarModelProps {
  /** Question text */
  question: string
  /** Expected total (the correct answer — used to know how many parts) */
  expectedTotal: string
  /** Expected units — the parts the student needs to build */
  expectedUnits: { label: string; value: number }[]
  /** Called whenever construction changes — pass to submitAttempt */
  onChange?: (construction: BarModelConstructionJSON, numericAnswer: string) => void
  /** Dark mode */
  dark?: boolean
}

export function InteractiveBarModel({
  question,
  expectedTotal,
  expectedUnits,
  onChange,
  dark = false,
}: InteractiveBarModelProps) {
  const [placed, setPlaced] = useState<BarModelSegment[]>([])
  const [totalInput, setTotalInput] = useState('')
  const [draggingValue, setDraggingValue] = useState<number | null>(null)
  const [draggingId, setDraggingId] = useState<string | null>(null)
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 })
  const [dragPos, setDragPos] = useState({ x: 0, y: 0 })
  const paletteRef = useRef<HTMLDivElement>(null)
  const dropStartTime = useRef<number>(Date.now())

  // Build available values from expectedUnits
  const availableValues = Array.from(new Set(expectedUnits.map(u => u.value))).sort((a, b) => a - b)

  // Colors for placed segments
  const colors = [
    'bg-blue-400', 'bg-green-400', 'bg-yellow-400',
    'bg-red-400', 'bg-purple-400', 'bg-pink-400',
    'bg-orange-400', 'bg-teal-400',
  ]

  const emitChange = useCallback((segs: BarModelSegment[], total: string) => {
    if (!onChange) return
    const construction: BarModelConstructionJSON = {
      type: 'bar_model_construction',
      segments_built: segs,
      total_built: total,
      final_answer: total,
      time_spent_ms: Date.now() - dropStartTime.current,
    }
    onChange(construction, total)
  }, [onChange])

  // Palette item pointer handlers
  const handlePalettePointerDown = (value: number, e: React.PointerEvent) => {
    e.preventDefault()
    setDraggingValue(value)
    setDraggingId(`new_${Date.now()}`)
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setDragOffset({ x: e.clientX - rect.left, y: e.clientY - rect.top })
    setDragPos({ x: e.clientX, y: e.clientY })
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }

  // Placed segment pointer handlers (reposition)
  const handlePlacedPointerDown = (seg: BarModelSegment, e: React.PointerEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDraggingId(seg.id)
    setDraggingValue(seg.value)
    const rect = (e.currentTarget as HTMLElement).getBoundingClientRect()
    setDragOffset({ x: e.clientX - rect.left, y: e.clientY - rect.top })
    setDragPos({ x: e.clientX, y: e.clientY })
    ;(e.currentTarget as HTMLElement).setPointerCapture(e.pointerId)
  }

  // Drop zone pointer handlers
  const handleDropZonePointerUp = (slotIndex: number, e: React.PointerEvent) => {
    e.preventDefault()
    if (draggingId === null || draggingValue === null) return
    const unitLabel = expectedUnits[slotIndex]?.label || `Parte ${slotIndex + 1}`
    if (draggingId.startsWith('new_')) {
      // New segment from palette
      const newSeg: BarModelSegment = {
        id: `seg_${Date.now()}`,
        label: unitLabel,
        value: draggingValue,
        order: slotIndex,
        timestamp: Date.now(),
      }
      const newPlaced = [...placed]
      // Remove from existing position if already placed
      const existingIdx = newPlaced.findIndex(s => s.id === draggingId)
      if (existingIdx !== -1) newPlaced.splice(existingIdx, 1)
      // Insert at slot
      const existingAtSlot = newPlaced.findIndex(s => s.order === slotIndex)
      if (existingAtSlot !== -1) newPlaced.splice(existingAtSlot, 1)
      newPlaced.push({ ...newSeg, order: slotIndex })
      setPlaced(newPlaced)
      emitChange(newPlaced, totalInput)
    }
    setDraggingId(null)
    setDraggingValue(null)
  }

  // Click palette item to add last
  const handlePaletteClick = (value: number) => {
    const nextSlot = placed.length < expectedUnits.length ? placed.length : 0
    const unitLabel = expectedUnits[nextSlot]?.label || `Parte ${nextSlot + 1}`
    const newSeg: BarModelSegment = {
      id: `seg_${Date.now()}`,
      label: unitLabel,
      value,
      order: nextSlot,
      timestamp: Date.now(),
    }
    let newPlaced: BarModelSegment[]
    if (placed.length === 0) {
      newPlaced = [newSeg]
    } else if (placed.length < expectedUnits.length) {
      newPlaced = [...placed, newSeg]
    } else {
      // Replace oldest
      newPlaced = [...placed.slice(1), newSeg]
    }
    setPlaced(newPlaced)
    emitChange(newPlaced, totalInput)
  }

  // Remove a segment
  const removeSegment = (id: string) => {
    const newPlaced = placed.filter(s => s.id !== id)
    setPlaced(newPlaced)
    emitChange(newPlaced, totalInput)
  }

  // Update total
  const handleTotalChange = (val: string) => {
    setTotalInput(val)
    emitChange(placed, val)
  }

  const totalVal = parseFloat(expectedTotal) || 0

  return (
    <div className={`rounded-xl p-4 border-2 ${dark ? 'bg-slate-800 border-slate-600' : 'bg-white border-gray-200'}`}>
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📊</span>
        <p className={`font-bold text-sm ${dark ? 'text-gray-100' : 'text-gray-700'}`}>
          Construye el Modelo de Barras
        </p>
        <span className="text-xs bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-2 py-0.5 rounded-full">
          Interactivo
        </span>
      </div>

      {/* Question */}
      <p className={`text-base font-medium mb-4 ${dark ? 'text-gray-200' : 'text-gray-800'}`}>
        {question}
      </p>

      {/* Instructions */}
      <p className={`text-xs mb-3 ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
        💡 Arrastra los valores al modelo, o haz clic para añadir. Escribe el total abajo.
      </p>

      {/* Segment Palette */}
      <div className="flex flex-wrap gap-2 mb-4" ref={paletteRef}>
        {availableValues.map((val) => (
          <div
            key={val}
            className={`
              px-4 py-2 rounded-lg font-bold text-white cursor-grab active:cursor-grabbing
              select-none transition-transform active:scale-105 shadow-sm
              ${colors[availableValues.indexOf(val) % colors.length]}
            `}
            onPointerDown={(e) => handlePalettePointerDown(val, e)}
            onClick={() => handlePaletteClick(val)}
          >
            {val}
          </div>
        ))}
      </div>

      {/* Drop Zones / Placed Segments */}
      <div className="space-y-2 mb-4">
        {expectedUnits.map((unit, idx) => {
          const placedHere = placed.find(s => s.order === idx)
          const isDragOver = draggingId !== null && draggingValue !== null && !placedHere

          return (
            <div key={idx} className="flex items-center gap-3">
              <span className={`w-20 text-xs text-right flex-shrink-0 truncate ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
                {unit.label}
              </span>
              <div
                className={`
                  flex-1 h-10 rounded-lg border-2 border-dashed flex items-center justify-center
                  transition-all min-w-0 cursor-pointer
                  ${placedHere
                    ? `border-solid ${colors[idx % colors.length]} opacity-90`
                    : isDragOver
                      ? `${dark ? 'border-blue-400 bg-blue-900/30' : 'border-blue-400 bg-blue-50'} border-solid`
                      : `${dark ? 'border-slate-600' : 'border-gray-300'} ${dark ? 'bg-slate-700' : 'bg-gray-50'}`
                  }
                `}
                onPointerUp={(e) => handleDropZonePointerUp(idx, e)}
              >
                {placedHere ? (
                  <div
                    className={`w-full h-full flex items-center px-3 cursor-grab active:cursor-grabbing rounded-lg ${colors[idx % colors.length]}`}
                    onPointerDown={(e) => handlePlacedPointerDown(placedHere, e)}
                    style={{ touchAction: 'none' }}
                  >
                    <span className="text-white text-sm font-bold whitespace-nowrap">{placedHere.value}</span>
                    <button
                      onClick={(e) => { e.stopPropagation(); removeSegment(placedHere.id) }}
                      className="ml-auto text-white/70 hover:text-white text-xs font-bold"
                    >
                      ✕
                    </button>
                  </div>
                ) : (
                  <span className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
                    Arrastra aquí
                  </span>
                )}
              </div>
            </div>
          )
        })}

        {/* Total bar */}
        <div className="flex items-center gap-3 pt-1">
          <span className={`w-20 text-xs text-right flex-shrink-0 ${dark ? 'text-gray-400' : 'text-gray-600'}`}>
            Total
          </span>
          <div className="flex-1 flex gap-2">
            <div className="flex-1 h-8 bg-gradient-to-r from-primary-400 to-purple-400 rounded-lg flex items-center px-3">
              <span className="text-white text-sm font-bold">
                {totalInput || '?'}
              </span>
            </div>
            <input
              type="text"
              value={totalInput}
              onChange={(e) => handleTotalChange(e.target.value)}
              placeholder="?"
              className={`
                w-20 h-8 text-center border rounded-lg text-sm font-bold
                ${dark
                  ? 'bg-slate-700 border-slate-500 text-white placeholder-slate-400'
                  : 'bg-white border-gray-300 text-gray-800 placeholder-gray-400'
                }
              `}
            />
          </div>
        </div>
      </div>

      {/* Visual bar preview */}
      <div className="mt-3">
        <div className={`h-2 rounded-full overflow-hidden flex gap-1 ${dark ? 'bg-slate-700' : 'bg-gray-200'}`}>
          {placed.map((seg, i) => {
            const widthPct = totalVal > 0 ? Math.min((seg.value / totalVal) * 100, 100) : 0
            return (
              <div
                key={seg.id}
                className={`${colors[i % colors.length]} rounded-full transition-all`}
                style={{ width: `${widthPct}%` }}
              />
            )
          })}
        </div>
        <div className="flex justify-between mt-1">
          <span className={`text-xs ${dark ? 'text-gray-500' : 'text-gray-400'}`}>
            {placed.length}/{expectedUnits.length} partes
          </span>
          <span className={`text-xs font-medium ${dark ? 'text-gray-400' : 'text-gray-500'}`}>
            {placed.reduce((s, p) => s + p.value, 0)} / {expectedTotal}
          </span>
        </div>
      </div>
    </div>
  )
}

// ─── Bar Model (Singapore Math) ─────────────────────────────────────────────
interface BarModelProps {
  question: string
  total: string
  units: { label: string; value: number }[]
  type?: string
  grade?: number
}

export function BarModel({ question, total, units, type = 'comparison', grade = 1 }: BarModelProps) {
  // Grade-based color scheme: colorful for G1-G3, more subdued for G4-G6
  const isLowerGrade = grade <= 3
  const colors = isLowerGrade
    ? ['bg-blue-400', 'bg-green-400', 'bg-yellow-400', 'bg-red-400', 'bg-purple-400', 'bg-pink-400']
    : ['bg-blue-500', 'bg-green-500', 'bg-yellow-50 dark:bg-yellow-900/200', 'bg-red-500', 'bg-purple-500', 'bg-pink-500']
  const maxVal = Math.max(...units.map(u => u.value), 1)
  const totalVal = parseFloat(total) || maxVal

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600 dark:border-slate-600 my-4">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📊</span>
        <p className="font-semibold text-gray-700 dark:text-gray-200 dark:text-gray-100 text-sm">Modelo de Barras</p>
        {type && type !== 'comparison' && (
          <span className="text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 px-2 py-0.5 rounded-full capitalize">{type}</span>
        )}
      </div>

      {/* Question */}
      <p className="text-gray-800 dark:text-gray-200 text-base font-medium mb-4">{question}</p>

      {/* Bar diagram */}
      <div className="space-y-3">
        {units.map((unit, idx) => {
          const widthPct = Math.min((unit.value / totalVal) * 100, 100)
          const color = colors[idx % colors.length]
          return (
            <div key={idx} className="flex items-center gap-3">
              <span className="w-20 text-xs text-gray-600 dark:text-gray-400 dark:text-gray-300 text-right flex-shrink-0 truncate">{unit.label}</span>
              <div className="flex-1 relative">
                <div
                  className={`h-8 ${color} rounded-lg flex items-center px-3 min-w-0 transition-all`}
                  style={{ width: `${widthPct}%`, minWidth: '2rem' }}
                >
                  <span className="text-white text-sm font-bold whitespace-nowrap">{unit.value}</span>
                </div>
              </div>
            </div>
          )
        })}

        {/* Total indicator */}
        <div className="flex items-center gap-3 pt-1">
          <span className="w-20 text-xs text-gray-600 dark:text-gray-400 dark:text-gray-300 text-right flex-shrink-0">Total</span>
          <div className="flex-1">
            <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-primary-400 to-purple-400 rounded-full" style={{ width: '100%' }} />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-medium">= {total}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Word Problem Card ──────────────────────────────────────────────────────
interface WordProblemProps {
  scenario: string
  question: string
  answer?: string
  hint?: string
  grade?: number
}

export function WordProblem({ scenario, question, answer, hint, grade = 1 }: WordProblemProps) {
  const [showHint, setShowHint] = useState(false)
  const isLowerGrade = grade <= 3

  return (
    <div className={`rounded-xl p-4 border-2 my-4 transition-all ${
      isLowerGrade
        ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-300 dark:bg-yellow-900/20 dark:border-yellow-700'
        : 'bg-slate-50 border-slate-200 dark:bg-slate-800 dark:border-slate-600'
    }`}>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📖</span>
        <p className={`font-semibold text-sm ${isLowerGrade ? 'text-yellow-800 dark:text-yellow-200' : 'text-slate-700 dark:text-slate-200'}`}>
          Problema Verbal
        </p>
      </div>

      {/* Scenario */}
      <div className={`rounded-lg p-3 mb-3 ${
        isLowerGrade ? 'bg-white/60' : 'bg-white dark:bg-slate-700'
      }`}>
        <p className="text-gray-700 dark:text-gray-200 dark:text-gray-200 text-sm leading-relaxed">
          {scenario}
        </p>
      </div>

      {/* Question */}
      <p className="text-gray-900 dark:text-gray-100 text-base font-semibold mb-3">
        ❓ {question}
      </p>

      {/* Hint toggle */}
      {hint && (
        <div className="mb-3">
          {!showHint ? (
            <button
              onClick={() => setShowHint(true)}
              className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1"
            >
              💡 Ver pista
            </button>
          ) : (
            <div className="flex items-start gap-2 text-xs text-primary-700 dark:text-primary-300 bg-primary-50 dark:bg-primary-900/30 rounded-lg px-3 py-2">
              <span>💡</span>
              <span>{hint}</span>
            </div>
          )}
        </div>
      )}

      {/* Answer reveal (optional, for preview mode) */}
      {answer && (
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2 pt-2 border-t border-gray-200 dark:border-slate-600 dark:border-slate-600">
          Respuesta: <span className="font-semibold text-primary-600 dark:text-primary-400">{answer}</span>
        </div>
      )}
    </div>
  )
}

// ─── Try It Interactive Widget ────────────────────────────────────────────
interface TryItProps {
  question: string
  answer: string
  hint?: string
  explanation?: string
}

export function TryIt({ question, answer, hint, explanation }: TryItProps) {
  const [input, setInput] = useState('')
  const [submitted, setSubmitted] = useState(false)
  const [showHint, setShowHint] = useState(false)

  const isCorrect = input.trim().toLowerCase() === answer.toLowerCase()

  return (
    <div className={`rounded-xl p-3 sm:p-4 my-2 sm:my-4 border-2 transition-all ${
      submitted
        ? isCorrect
          ? 'bg-green-50 dark:bg-green-900/30 border-green-400 dark:border-green-500'
          : 'bg-red-50 dark:bg-red-900/30 border-red-400 dark:border-red-500'
        : 'bg-yellow-50 dark:bg-yellow-900/20 dark:bg-yellow-900/30 border-yellow-300 dark:border-yellow-600'
    }`}>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-xl">✏️</span>
        <p className="font-bold text-gray-800 dark:text-gray-100 text-sm">¡Inténtalo!</p>
      </div>

      <p className="text-gray-700 dark:text-gray-200 dark:text-gray-200 text-sm mb-3">{question}</p>

      <div className="flex gap-2 mb-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && !submitted && setSubmitted(true)}
          disabled={submitted}
          placeholder="Tu respuesta..."
          className="input flex-1 text-sm dark:border-slate-600 dark:bg-slate-800 dark:text-white"
        />
        {!submitted ? (
          <button onClick={() => setSubmitted(true)} className="btn-primary text-sm px-4" disabled={!input.trim()}>
            ✓
          </button>
        ) : (
          <button onClick={() => { setSubmitted(false); setInput(''); setShowHint(false) }} className="btn-secondary text-sm px-3">
            ↺
          </button>
        )}
      </div>

      {submitted && (
        <div className="mt-2 animate-result-pop">
          {isCorrect ? (
            <div className="flex items-center gap-2 text-green-700 dark:text-green-400">
              <span className="text-xl">🎉</span>
              <span className="text-sm font-bold">¡Correcto!</span>
            </div>
          ) : (
            <div className="flex items-center gap-2 text-red-700 dark:text-red-400">
              <span className="text-xl">💪</span>
              <span className="text-sm">La respuesta era <strong>{answer}</strong>. ¡Sigue intentando!</span>
            </div>
          )}
          {explanation && submitted && (
            <p className="text-xs text-gray-600 dark:text-gray-400 dark:text-gray-400 mt-1 italic">💡 {explanation}</p>
          )}
        </div>
      )}

      {hint && !showHint && !submitted && (
        <button onClick={() => setShowHint(true)} className="text-xs text-yellow-700 dark:text-yellow-400 hover:underline mt-1">
          💡 Pista: {hint}
        </button>
      )}
    </div>
  )
}
