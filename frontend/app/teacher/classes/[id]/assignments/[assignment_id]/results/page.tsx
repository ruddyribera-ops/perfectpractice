'use client'

import React, { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import {
  api, AssignmentResultResponse, StudentAssignmentResult, ExerciseResultItem,
} from '@/lib/api'
import {
  ChevronLeft, CheckCircle, XCircle, User, TrendingUp, Clock, ChevronDown, ChevronUp,
} from 'lucide-react'

export default function AssignmentResultsPage() {
  const params = useParams()
  const router = useRouter()
  const classId = parseInt(params.id as string)
  const assignmentId = parseInt(params.assignment_id as string)

  const [data, setData] = useState<AssignmentResultResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [expandedStudents, setExpandedStudents] = useState<Set<number>>(new Set())
  const [sortBy, setSortBy] = useState<'name' | 'score' | 'completion'>('name')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')

  useEffect(() => {
    if (assignmentId) loadResults()
  }, [assignmentId])

  const loadResults = async () => {
    setLoading(true)
    try {
      const result = await api.getAssignmentResults(assignmentId)
      setData(result)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const toggleStudent = (studentId: number) => {
    setExpandedStudents(prev => {
      const next = new Set(prev)
      if (next.has(studentId)) next.delete(studentId)
      else next.add(studentId)
      return next
    })
  }

  const sortedStudents = React.useMemo(() => {
    if (!data?.results) return []
    const list = [...data.results]
    list.sort((a, b) => {
      let cmp = 0
      if (sortBy === 'name') cmp = a.student_name.localeCompare(b.student_name)
      else if (sortBy === 'score') cmp = (a.score ?? 0) - (b.score ?? 0)
      else if (sortBy === 'completion') cmp = (a.completion_rate ?? 0) - (b.completion_rate ?? 0)
      return sortDir === 'asc' ? cmp : -cmp
    })
    const sorted = [...list].sort((a, b) => (b.score ?? 0) - (a.score ?? 0))
    const rankMap: Record<number, number> = {}
    sorted.forEach((s, i) => { rankMap[s.student_id] = i + 1 })
    return list.map(s => ({ ...s, rank: rankMap[s.student_id] }))
  }, [data, sortBy, sortDir])

  const toggleSort = (col: typeof sortBy) => {
    if (sortBy === col) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortBy(col); setSortDir('desc') }
  }

  const exportCSV = () => {
    if (!data) return
    const headers = ['#', 'Nombre', 'Puntaje', 'Completado %', 'Ejercicios', 'Tiempo', 'Rango']
    const rows = sortedStudents.map((s, i) => [
      i + 1,
      s.student_name,
      s.score ?? 0,
      s.completion_rate ?? 0,
      `${s.exercises.filter((e: ExerciseResultItem) => e.correct).length}/${s.exercises.length}`,
      (() => {
        if (!s.started_at || !s.completed_at) return 'N/A'
        const diff = Math.floor((new Date(s.completed_at).getTime() - new Date(s.started_at).getTime()) / 1000)
        const h = Math.floor(diff / 3600)
        const m = Math.floor((diff % 3600) / 60)
        const s2 = diff % 60
        return `${h > 0 ? `${h}h ` : ''}${m > 0 ? `${m}m ` : ''}${s2}s`
      })(),
      s.rank ?? '-',
    ])
    const csv = [headers, ...rows].map(r => r.join(',')).join('\n')
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `resultados_tarea_${assignmentId}.csv`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  if (!data) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">No se encontraron resultados</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <nav className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-4">
          <button onClick={() => router.back()} className="flex items-center gap-1 text-gray-500 hover:text-gray-700">
            <ChevronLeft className="h-5 w-5" />
          </button>
          <Link href="/teacher/classes" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-400">/</span>
          <Link href="/teacher/classes" className="text-gray-500 hover:text-gray-700">Mis Clases</Link>
          <span className="text-gray-400">/</span>
          <span className="font-medium">Resultados</span>
        </nav>
      </header>

      <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Assignment title + summary */}
        <div className="card mb-6">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <h1 className="text-2xl font-bold text-gray-900 mb-3">{data.title}</h1>
            <button onClick={exportCSV} style={{
              background: '#22c55e', color: 'white', border: 'none',
              borderRadius: '8px', padding: '8px 16px', fontSize: '13px',
              cursor: 'pointer', fontWeight: 600,
            }}>
              📥 Exportar CSV
            </button>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="flex items-center gap-2">
              <User className="h-5 w-5 text-gray-400" />
              <div>
                <p className="text-xs text-gray-500">Total estudiantes</p>
                <p className="text-xl font-bold">{data.total_students}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-xs text-gray-500">Completaron</p>
                <p className="text-xl font-bold">{data.completed_count}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-primary-500" />
              <div>
                <p className="text-xs text-gray-500">Promedio clase</p>
                <p className="text-xl font-bold">{data.avg_score != null ? `${data.avg_score}%` : '—'}</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5 text-orange-500" />
              <div>
                <p className="text-xs text-gray-500">Tasa finalización</p>
                <p className="text-xl font-bold">{Math.round(data.completion_rate)}%</p>
              </div>
            </div>
          </div>
        </div>

        {/* Class progress bar */}
        <div className="card mb-6">
          <p className="text-sm font-medium text-gray-700 mb-2">Promedio de la clase</p>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-primary-400 to-primary-600 rounded-full transition-all"
              style={{ width: `${data.avg_score ?? 0}%` }}
            />
          </div>
        </div>

        {/* Per-student results */}
        <div className="space-y-3">
          {data.results.length === 0 ? (
            <div className="card text-center py-12">
              <p className="text-gray-600">Ningún estudiante ha comenzado esta tarea</p>
            </div>
          ) : (
            <>
              {/* Sort controls */}
              <div style={{ display: 'flex', gap: '12px', alignItems: 'center', marginBottom: '8px' }}>
                <span style={{ fontSize: '13px', color: '#666' }}>Ordenar por:</span>
                {(['name', 'score', 'completion'] as const).map(col => (
                  <button key={col} onClick={() => toggleSort(col)} style={{
                    padding: '6px 12px',
                    borderRadius: '6px',
                    border: '1px solid',
                    borderColor: sortBy === col ? '#3b82f6' : '#e5e7eb',
                    background: sortBy === col ? '#3b82f6' : 'white',
                    color: sortBy === col ? 'white' : '#666',
                    fontSize: '13px',
                    cursor: 'pointer',
                  }}>
                    {col === 'name' ? 'Nombre' : col === 'score' ? 'Puntaje' : 'Completado'} {sortBy === col ? (sortDir === 'asc' ? '↑' : '↓') : ''}
                  </button>
                ))}
              </div>

              {sortedStudents.map((student) => {
                const isExpanded = expandedStudents.has(student.student_id)
                const exercisesCorrect = student.exercises.filter((e: ExerciseResultItem) => e.correct).length
                const exercisesTotal = student.exercises.length
                const timeDisplay = (() => {
                  if (!student.started_at || !student.completed_at) return null
                  const diff = Math.floor((new Date(student.completed_at).getTime() - new Date(student.started_at).getTime()) / 1000)
                  const h = Math.floor(diff / 3600)
                  const m = Math.floor((diff % 3600) / 60)
                  const s = diff % 60
                  return { h, m, s }
                })()
                return (
                  <div key={student.student_id} className="card overflow-hidden">
                    {/* Student row — always visible */}
                    <button
                      onClick={() => toggleStudent(student.student_id)}
                      className="w-full flex items-center gap-4 py-4 px-4 hover:bg-gray-50 transition text-left"
                    >
                      <div className="w-10 h-10 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold text-lg flex-shrink-0">
                        {student.student_name.charAt(0).toUpperCase()}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <p className="font-semibold text-gray-900">{student.student_name}</p>
                          {student.rank != null && (
                            <span style={{ fontSize: '12px', color: '#666' }}>
                              {student.rank <= 3 ? ['🥇','🥈','🥉'][student.rank - 1] : ''} #{student.rank}
                            </span>
                          )}
                        </div>
                        <div className="flex items-center gap-3 mt-0.5 text-xs text-gray-500">
                          {student.completed_at
                            ? <span className="flex items-center gap-1 text-green-600"><CheckCircle className="h-3 w-3" /> Completado</span>
                            : <span className="flex items-center gap-1 text-orange-500"><Clock className="h-3 w-3" /> En proceso</span>
                          }
                          <span>{student.completion_rate}% completado</span>
                          {timeDisplay && (
                            <span style={{ color: '#888' }}>
                              {timeDisplay.h > 0 ? `${timeDisplay.h}h ` : ''}{timeDisplay.m > 0 ? `${timeDisplay.m}m ` : ''}{timeDisplay.s}s
                            </span>
                          )}
                        </div>
                      </div>
                      <div className="text-right flex-shrink-0">
                        <p style={{
                          fontSize: '20px',
                          fontWeight: 700,
                          color: student.score != null
                            ? (student.score >= 80 ? '#22c55e' : student.score >= 50 ? '#eab308' : '#ef4444')
                            : '#9ca3af'
                        }}>
                          {student.score != null ? `${student.score}%` : '—'}
                        </p>
                        <p style={{ fontSize: '11px', color: '#888', marginTop: '2px' }}>
                          {exercisesCorrect}/{exercisesTotal} ejercicios
                        </p>
                      </div>
                      <div className="text-gray-400 flex-shrink-0">
                        {isExpanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
                      </div>
                    </button>

                    {/* Expanded: per-exercise breakdown */}
                    {isExpanded && (
                      <div className="border-t border-gray-100 px-4 py-3 space-y-2">
                        <p className="text-xs font-bold text-gray-500 uppercase mb-2">Desglose por ejercicio</p>
                        {student.exercises.map((ex, idx) => (
                          <div key={ex.exercise_id} className={`flex items-center gap-3 py-2 px-3 rounded-lg ${
                            ex.correct ? 'bg-green-50' : 'bg-red-50'
                          }`}>
                            <div className="flex-shrink-0">
                              {ex.correct
                                ? <CheckCircle className="h-5 w-5 text-green-500" />
                                : <XCircle className="h-5 w-5 text-red-400" />
                              }
                            </div>
                            <span className="flex-1 text-sm font-medium text-gray-800">{ex.exercise_title}</span>
                            <span className={`text-xs font-medium ${ex.correct ? 'text-green-600' : 'text-red-500'}`}>
                              {ex.correct ? `+${ex.points_earned} pts` : 'Incorrecto'}
                            </span>
                            {ex.xp_earned > 0 && (
                              <span className="text-xs text-yellow-600">+{ex.xp_earned} XP</span>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })}
            </>
          )}
        </div>
      </main>
    </div>
  )
}
