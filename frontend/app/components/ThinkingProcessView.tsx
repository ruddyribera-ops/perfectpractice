'use client'
import { useEffect, useState } from 'react'
import { X, ChevronRight, CheckCircle, XCircle, Clock } from 'lucide-react'
import { api } from '@/lib/api'
import type { ThinkingProcessResponse, ThinkingProcessAttempt, BarModelSegment } from '@/lib/api'

interface Segment {
  id: string
  label: string
  value: number
  order: number
  timestamp: number
}

const PALETTE = ['#3b82f6', '#f59e0b', '#22c55e', '#8b5cf6', '#ef4444', '#06b6d4']

function BarModelReplay({ segments, total }: { segments: Segment[]; total: string }) {
  const [visible, setVisible] = useState<Set<number>>(new Set())

  useEffect(() => {
    setVisible(new Set())
    segments.forEach((seg, i) => {
      const delay = i * 600
      const t = setTimeout(() => {
        setVisible(prev => new Set([...prev, i]))
      }, delay)
      return () => clearTimeout(t)
    })
  }, [segments])

  const totalNum = parseFloat(total) || 100
  const barMaxWidth = 320

  return (
    <div style={{ padding: '16px', background: '#f8fafc', borderRadius: '12px', border: '1px solid #e2e8f0' }}>
      {/* Bar container */}
      <div style={{ position: 'relative', height: '80px', marginBottom: '12px' }}>
        {/* Total line */}
        <div style={{
          position: 'absolute', top: 0, right: 0, height: '100%',
          display: 'flex', alignItems: 'center', paddingLeft: '8px',
        }}>
          <div style={{
            height: '60px', minWidth: '4px',
            borderLeft: '3px solid #94a3b8', paddingLeft: '8px',
            display: 'flex', alignItems: 'center',
          }}>
            <span style={{ fontSize: '13px', fontWeight: 700, color: '#475569', whiteSpace: 'nowrap' }}>={total}</span>
          </div>
        </div>

        {/* Segments */}
        <div style={{ display: 'flex', height: '60px', gap: '4px', overflowX: 'auto', alignItems: 'flex-end', paddingBottom: '4px' }}>
          {segments.map((seg, i) => {
            const widthPct = seg.value / totalNum
            const w = Math.max(widthPct * barMaxWidth, 40)
            const color = PALETTE[i % PALETTE.length]
            const isVisible = visible.has(i)
            return (
              <div
                key={seg.id}
                style={{
                  height: isVisible ? `${Math.round(widthPct * 56 + 4)}px` : '4px',
                  width: `${w}px`,
                  background: color,
                  borderRadius: '6px 6px 3px 3px',
                  transition: `height 0.4s ease ${i * 0.08}s, opacity 0.3s ease ${i * 0.08}s`,
                  opacity: isVisible ? 1 : 0,
                  display: 'flex',
                  alignItems: 'flex-end',
                  justifyContent: 'center',
                  boxShadow: '0 2px 6px rgba(0,0,0,0.15)',
                  flexShrink: 0,
                }}
              >
                <span style={{ fontSize: '11px', fontWeight: 700, color: 'white', padding: '0 4px 3px', textShadow: '0 1px 2px rgba(0,0,0,0.3)' }}>
                  {seg.value}
                </span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Legend */}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', justifyContent: 'center' }}>
        {segments.map((seg, i) => {
          const color = PALETTE[i % PALETTE.length]
          return (
            <div key={seg.id} style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '3px', background: color }} />
              <span style={{ fontSize: '11px', color: '#64748b' }}>{seg.label}: {seg.value}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

function AttemptCard({ attempt, index }: { attempt: ThinkingProcessAttempt; index: number }) {
  const construction = attempt.answer_json?.type === 'bar_model_construction' ? attempt.answer_json : null
  const segments: Segment[] = construction?.segments_built ?? []
  const total = construction?.total_built ?? ''

  return (
    <div style={{
      border: `1px solid ${attempt.correct ? '#bbf7d0' : '#fecaca'}`,
      borderRadius: '12px',
      padding: '16px',
      background: attempt.correct ? '#f0fdf4' : '#fef2f2',
      marginBottom: '12px',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <span style={{
            width: '24px', height: '24px', borderRadius: '50%',
            background: attempt.correct ? '#22c55e' : '#ef4444',
            color: 'white', display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: '12px', fontWeight: 700,
          }}>
            {index + 1}
          </span>
          {attempt.correct
            ? <CheckCircle size={16} color="#22c55e" />
            : <XCircle size={16} color="#ef4444" />
          }
          <span style={{ fontSize: '13px', fontWeight: 600, color: attempt.correct ? '#166534' : '#991b1b' }}>
            {attempt.correct ? 'Correcto' : 'Incorrecto'}
          </span>
        </div>
        <div style={{ display: 'flex', gap: '12px', fontSize: '12px', color: '#64748b' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '3px' }}>
            <Clock size={12} />
            {attempt.time_spent_seconds}s
          </span>
          {attempt.xp_earned > 0 && (
            <span style={{ color: '#ca8a04' }}>+{attempt.xp_earned} XP</span>
          )}
        </div>
      </div>

      {/* Bar model replay — only for bar_model constructions */}
      {segments.length > 0 ? (
        <BarModelReplay segments={segments} total={total} />
      ) : (
        <div style={{ fontSize: '13px', color: '#64748b', textAlign: 'center', padding: '12px', background: '#f1f5f9', borderRadius: '8px' }}>
          📝 Respuesta enviada: <code style={{ background: '#e2e8f0', padding: '2px 6px', borderRadius: '4px' }}>
            {attempt.answer_json?.answer ?? JSON.stringify(attempt.answer_json)}
          </code>
        </div>
      )}
    </div>
  )
}

interface ThinkingProcessViewProps {
  studentId: number
  exerciseId: number
  onClose: () => void
}

export default function ThinkingProcessView({ studentId, exerciseId, onClose }: ThinkingProcessViewProps) {
  const [data, setData] = useState<ThinkingProcessResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getStudentThinkingProcess(studentId, exerciseId)
      .then(setData)
      .catch(e => setError((e as Error).message))
      .finally(() => setLoading(false))
  }, [studentId, exerciseId])

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.5)',
      display: 'flex', alignItems: 'center', justifyContent: 'center',
      zIndex: 9999, padding: '16px',
    }}>
      <div style={{
        background: 'white', borderRadius: '16px', width: '100%', maxWidth: '640px',
        maxHeight: '90vh', overflowY: 'auto', boxShadow: '0 24px 48px rgba(0,0,0,0.2)',
      }}>
        {/* Modal header */}
        <div style={{
          padding: '20px 24px', borderBottom: '1px solid #e2e8f0',
          display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start',
          position: 'sticky', top: 0, background: 'white', borderRadius: '16px 16px 0 0',
        }}>
          <div>
            <p style={{ fontSize: '11px', color: '#64748b', margin: '0 0 4px', textTransform: 'uppercase', letterSpacing: '1px' }}>
              🧠 Proceso de pensamiento
            </p>
            {data ? (
              <>
                <h2 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 4px' }}>{data.exercise_title}</h2>
                <p style={{ fontSize: '13px', color: '#64748b', margin: 0 }}>Estudiante: {data.student_name}</p>
              </>
            ) : <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>Cargando...</h2>}
          </div>
          <button
            onClick={onClose}
            style={{
              background: '#f1f5f9', border: 'none', borderRadius: '8px',
              padding: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center',
            }}
          >
            <X size={18} color="#64748b" />
          </button>
        </div>

        {/* Modal body */}
        <div style={{ padding: '24px' }}>
          {loading && <p style={{ textAlign: 'center', color: '#64748b' }}>Cargando proceso...</p>}
          {error && <p style={{ color: '#ef4444', textAlign: 'center' }}>Error: {error}</p>}
          {!loading && data && (
            data.attempts.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '32px', color: '#94a3b8' }}>
                No hay intentos registrados para este ejercicio.
              </div>
            ) : (
              <>
                <div style={{
                  display: 'flex', gap: '12px', marginBottom: '20px',
                  fontSize: '13px', color: '#64748b',
                }}>
                  <span>{data.attempts.length} intento{data.attempts.length !== 1 ? 's' : ''}</span>
                  <span>•</span>
                  <span style={{
                    padding: '2px 8px', borderRadius: '999px', fontSize: '11px', fontWeight: 600,
                    background: data.exercise_type === 'bar_model' ? '#dbeafe' : '#f1f5f9',
                    color: data.exercise_type === 'bar_model' ? '#1d4ed8' : '#475569',
                  }}>
                    {data.exercise_type}
                  </span>
                </div>

                {data.attempts.map((att, i) => (
                  <AttemptCard key={att.id} attempt={att} index={i} />
                ))}
              </>
            )
          )}
        </div>
      </div>
    </div>
  )
}
