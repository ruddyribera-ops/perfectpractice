'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, Exercise, AttemptResult, AchievementResponse, BarModelConstructionJSON } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { CheckCircle, XCircle, Lightbulb, ChevronLeft, Flame, Star, ArrowUp, ArrowDown, X } from 'lucide-react'
import { BarModel, WordProblem, InteractiveBarModel } from '@/components/LessonVisuals'

// ─── Bar Model Display (standalone) ─────────────────────────────────────────
function BarModelDisplay({ data }: { data: import('@/lib/api').BarModelData }) {
  const { question, total, units, type } = data
  const colors = ['bg-blue-400', 'bg-green-400', 'bg-yellow-400', 'bg-red-400', 'bg-purple-400']
  const maxVal = Math.max(...units.map(u => u.value), 1)
  const totalVal = parseFloat(total) || maxVal

  return (
    <div className="bg-white dark:bg-slate-800 rounded-xl p-4 border border-gray-200 dark:border-slate-600">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📊</span>
        <p className="font-semibold text-gray-700 dark:text-gray-100 text-sm">Modelo de Barras</p>
        {type && type !== 'comparison' && (
          <span className="text-xs bg-primary-100 dark:bg-primary-900 text-primary-700 dark:text-primary-300 px-2 py-0.5 rounded-full capitalize">{type}</span>
        )}
      </div>
      <p className="text-gray-800 dark:text-gray-200 text-base font-medium mb-4">{question}</p>
      <div className="space-y-3">
        {units.map((unit, idx) => {
          const widthPct = Math.min((unit.value / totalVal) * 100, 100)
          return (
            <div key={idx} className="flex items-center gap-3">
              <span className="w-20 text-xs text-gray-600 dark:text-gray-300 text-right flex-shrink-0 truncate">{unit.label}</span>
              <div className="flex-1 relative">
                <div
                  className={`h-8 ${colors[idx % colors.length]} rounded-lg flex items-center px-3 min-w-0`}
                  style={{ width: `${widthPct}%`, minWidth: '2rem' }}
                >
                  <span className="text-white text-sm font-bold whitespace-nowrap">{unit.value}</span>
                </div>
              </div>
            </div>
          )
        })}
        <div className="flex items-center gap-3 pt-1">
          <span className="w-20 text-xs text-gray-600 dark:text-gray-300 text-right flex-shrink-0">Total</span>
          <div className="flex-1">
            <div className="h-2 bg-gray-200 dark:bg-slate-600 rounded-full overflow-hidden">
              <div className="h-full bg-gradient-to-r from-primary-400 to-purple-400 rounded-full" />
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-1 font-medium">= {total}</p>
          </div>
        </div>
      </div>
    </div>
  )
}

// ─── Word Problem Display (standalone) ─────────────────────────────────────
function WordProblemDisplay({ data }: { data: import('@/lib/api').WordProblemData }) {
  const [showHint, setShowHint] = useState(false)
  const { scenario, question, answer, hint } = data

  return (
    <div className="bg-yellow-50 dark:bg-yellow-900/20 rounded-xl p-4 border border-yellow-300 dark:border-yellow-700">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">📖</span>
        <p className="font-semibold text-yellow-800 dark:text-yellow-200 text-sm">Problema Verbal</p>
      </div>
      <div className="bg-white/60 dark:bg-slate-800 rounded-lg p-3 mb-3">
        <p className="text-gray-700 dark:text-gray-200 text-sm leading-relaxed">{scenario}</p>
      </div>
      <p className="text-gray-900 dark:text-gray-100 text-base font-semibold mb-3">❓ {question}</p>
      {hint && (
        <div className="mb-3">
          {!showHint ? (
            <button onClick={() => setShowHint(true)} className="text-xs text-primary-600 dark:text-primary-400 hover:underline flex items-center gap-1">
              💡 Ver pista
            </button>
          ) : (
            <div className="flex items-start gap-2 text-xs text-primary-700 dark:text-primary-300 bg-primary-50 dark:bg-primary-900/30 rounded-lg px-3 py-2">
              <span>💡</span><span>{hint}</span>
            </div>
          )}
        </div>
      )}
      {answer && (
        <div className="text-xs text-gray-500 dark:text-gray-400 mt-2 pt-2 border-t border-gray-200 dark:border-slate-600">
          Respuesta: <span className="font-semibold text-primary-600 dark:text-primary-400">{answer}</span>
        </div>
      )}
    </div>
  )
}

export default function ExercisePage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()

  const exerciseId = params.id as string
  const id = exerciseId ? parseInt(exerciseId, 10) : NaN

  const [exercise, setExercise] = useState<Exercise | null>(null)
  const [loading, setLoading] = useState(true)
  const [answer, setAnswer] = useState<string>('')
  const [barModelConstruction, setBarModelConstruction] = useState<BarModelConstructionJSON | null>(null)
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [orderedItems, setOrderedItems] = useState<string[]>([])
  const [showHint, setShowHint] = useState(false)
  const [hintIndex, setHintIndex] = useState(0)
  const [result, setResult] = useState<AttemptResult | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [currentStreak, setCurrentStreak] = useState(0)
  const [toasts, setToasts] = useState<AchievementResponse[]>([])
  const startTime = useRef(Date.now())

  useEffect(() => {
    if (user === undefined) return
    if (user === null) { router.push('/login'); return }
    if (id && !isNaN(id) && id > 0) fetchExercise()
  }, [user, id, router])

  const fetchExercise = async () => {
    try {
      const data = await api.getExercise(id)
      setExercise(data)
      // Reset all answer state for new exercise
      setAnswer('')
      setBarModelConstruction(null)
      setResult(null)
      // Set ordered items if ordering type
      if (data.exercise_type === 'ordering' && data.data.options) {
        setOrderedItems([...data.data.options].sort(() => Math.random() - 0.5))
      }
      // Fetch current streak
      try {
        const streak = await api.getStreak()
        setCurrentStreak(streak.current_streak)
      } catch {}
    } catch (error: any) {
      const msg = error.message || ''
      if (msg.includes('401') || msg.includes('403')) {
        localStorage.removeItem('access_token')
        router.push('/login')
      } else {
        setExercise(null)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async () => {
    if (!exercise || submitting) return
    let finalAnswer: string

    if (exercise.exercise_type === 'multiple_choice') {
      if (selectedOption === null || !exercise.data.options) return
      finalAnswer = exercise.data.options[selectedOption]
    } else if (exercise.exercise_type === 'true_false') {
      finalAnswer = selectedOption === 0 ? 'true' : 'false'
    } else     if (exercise.exercise_type === 'ordering') {
      finalAnswer = JSON.stringify(orderedItems)
    } else if (exercise.exercise_type === 'bar_model') {
      if (!answer.trim()) return
      // Send both numeric answer AND construction process
      finalAnswer = JSON.stringify({ numeric: answer.trim(), construction: barModelConstruction })
    } else {
      if (!answer.trim()) return
      finalAnswer = answer.trim()
    }

    setSubmitting(true)
    const timeSpent = Math.round((Date.now() - startTime.current) / 1000)
    const assignmentIdFromUrl = typeof window !== 'undefined'
      ? new URLSearchParams(window.location.search).get('assignment_id')
      : null
    try {
      const r = await api.submitAttempt(id, finalAnswer, timeSpent, assignmentIdFromUrl ? Number(assignmentIdFromUrl) : undefined)
      setResult(r)
      setCurrentStreak(r.current_streak)
      // Show achievement toasts for newly earned badges
      if (r.new_achievements?.length > 0) {
        r.new_achievements.forEach(a => addToast(a))
      }
      // Refresh mastery state
      if (r.correct) {
        api.getProgress().catch(() => {})
        window.dispatchEvent(new CustomEvent('mastery-updated'))
      }
    } catch (e: any) {
      console.error('Error:', e.message)
      // Show error toast to user
      addToast({
        id: -Date.now(),
        icon: '⚠️',
        title: 'Error',
        description: e.message?.includes('401') || e.message?.includes('403')
          ? 'Tu sesión expiró. Recarga la página.'
          : 'No se pudo verificar la respuesta. Intenta de nuevo.',
        unlocked_at: new Date().toISOString(),
      })
    } finally {
      setSubmitting(false)
    }
  }

  const addToast = (achievement: AchievementResponse) => {
    setToasts(prev => [...prev, achievement])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== achievement.id))
    }, 5000)
  }

  const moveOrderItem = (from: number, dir: 'up' | 'down') => {
    if (result) return
    const newItems = [...orderedItems]
    const to = dir === 'up' ? from - 1 : from + 1
    if (to < 0 || to >= newItems.length) return
    ;[newItems[from], newItems[to]] = [newItems[to], newItems[from]]
    setOrderedItems(newItems)
  }

  const hints = exercise?.hints ?? []

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Cargando ejercicio...</p>
      </div>
    </div>
  )

  if (!exercise) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <p className="text-gray-600 mb-4">Ejercicio no encontrado</p>
        <Link href="/topics" className="text-primary-600 hover:underline">Volver a temas</Link>
      </div>
    </div>
  )

  const typeLabel = {
    multiple_choice: 'Opción múltiple',
    true_false: 'Verdadero / Falso',
    numeric: 'Numérico',
    ordering: 'Ordenar',
    bar_model: 'Modelo de Barras',
    word_problem: 'Problema Verbal',
  }[exercise.exercise_type] ?? exercise.exercise_type

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <nav className="max-w-2xl mx-auto px-4 py-3 flex items-center gap-4">
          <Link href="/topics" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-400">/</span>
          <span className="font-medium text-gray-700">{exercise.title}</span>
          <div className="ml-auto flex items-center gap-3">
            <div className="flex items-center gap-1 bg-orange-50 px-3 py-1.5 rounded-full">
              <Flame className="h-4 w-4 text-orange-500 animate-streak-pulse" />
              <span className="text-sm font-bold text-orange-600">{currentStreak}</span>
            </div>
          </div>
        </nav>
      </header>

      {/* Achievement toasts */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div key={toast.id} className="flex items-center gap-3 bg-yellow-50 border border-yellow-300 rounded-xl px-4 py-3 shadow-xl animate-bounce-in min-w-64">
            <span className="text-3xl">{toast.icon}</span>
            <div>
              <p className="font-bold text-yellow-800 text-sm">¡Nuevo Logro!</p>
              <p className="font-semibold text-yellow-700">{toast.title}</p>
              <p className="text-xs text-yellow-600">{toast.description}</p>
            </div>
            <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} className="ml-auto text-yellow-400 hover:text-yellow-600">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Card */}
        <div className="card mb-4">
          <div className="flex items-center justify-between mb-3">
            <span className={`badge ${
              exercise.exercise_type === 'multiple_choice' ? 'badge-primary' :
              exercise.exercise_type === 'true_false' ? 'badge-secondary' :
              exercise.exercise_type === 'ordering' ? 'bg-purple-100 text-purple-800' : 'badge-success'
            }`}>{typeLabel}</span>
            <span className="text-sm text-yellow-600 flex items-center gap-1">
              <Star className="h-4 w-4 fill-yellow-500" /> +{exercise.points_value} XP
            </span>
          </div>
          <p className="text-xl text-gray-900 text-center py-4">{exercise.data.question}</p>
        </div>

        {/* Hint system */}
        {hints.length > 0 && !result && (
          <div className="mb-4">
            {!showHint ? (
              <button onClick={() => { setShowHint(true); setHintIndex(0) }} className="text-primary-600 hover:underline text-sm flex items-center gap-1">
                <Lightbulb className="h-4 w-4" /> ¿Necesitas ayuda?
              </button>
            ) : (
              <div className="card bg-yellow-50 border-yellow-200">
                <p className="text-sm font-semibold text-yellow-800 mb-1">
                  💡 Pista {hintIndex + 1} de {hints.length}
                </p>
                <p className="text-gray-700">{hints[Math.min(hintIndex, hints.length - 1)]}</p>
                {hintIndex < hints.length - 1 && (
                  <button onClick={() => setHintIndex(prev => prev + 1)} className="text-xs text-yellow-700 hover:underline mt-1">
                    Ver siguiente pista →
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Multiple Choice */}
        {exercise.exercise_type === 'multiple_choice' && exercise.data.options && (
          <div className="space-y-3 mb-4">
            {exercise.data.options.map((opt, i) => {
              let cls = 'w-full p-4 text-left rounded-xl border-2 transition-all font-medium flex items-center gap-3'
              if (result) {
                cls += selectedOption === i
                  ? (result.correct ? ' border-green-500 bg-green-50' : ' border-red-500 bg-red-50')
                  : ' border-gray-200 opacity-50'
              } else {
                cls += selectedOption === i ? ' border-primary-500 bg-primary-50' : ' border-gray-200 hover:border-primary-300'
              }
              return (
                <button key={i} onClick={() => !result && setSelectedOption(i)} disabled={!!result} className={cls}>
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-700 font-bold text-sm flex-shrink-0">
                    {String.fromCharCode(65 + i)}
                  </span>
                  {opt}
                </button>
              )
            })}
          </div>
        )}

        {/* True/False */}
        {exercise.exercise_type === 'true_false' && (
          <div className="grid grid-cols-2 gap-4 mb-4">
            {[
              { label: 'Verdadero', value: 0 },
              { label: 'Falso', value: 1 },
            ].map(({ label, value }) => {
              let cls = 'p-6 rounded-xl border-2 text-center text-lg font-bold transition-all'
              if (result) {
                cls += selectedOption === value
                  ? (result.correct ? ' border-green-500 bg-green-50 text-green-700' : ' border-red-500 bg-red-50 text-red-700')
                  : ' border-gray-200 opacity-50'
              } else {
                cls += selectedOption === value ? ' border-primary-500 bg-primary-50 text-primary-700' : ' border-gray-200 hover:border-primary-300'
              }
              return (
                <button key={value} onClick={() => !result && setSelectedOption(value)} disabled={!!result} className={cls}>
                  {label}
                </button>
              )
            })}
          </div>
        )}

        {/* Numeric */}
        {exercise.exercise_type === 'numeric' && (
          <div className="mb-4">
            <input
              type="text"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              disabled={!!result}
              className="input text-2xl text-center py-4"
              placeholder="Escribe tu respuesta..."
              onKeyDown={e => e.key === 'Enter' && !result && !submitting && handleSubmit()}
            />
          </div>
        )}

        {/* Ordering */}
        {exercise.exercise_type === 'ordering' && (
          <div className="card mb-4">
            <p className="text-sm text-gray-600 mb-3">Ordena de menor a mayor (arrastra o usa las flechas):</p>
            <div className="space-y-2">
              {orderedItems.map((item, i) => (
                <div key={i} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <span className="w-8 h-8 rounded-full bg-primary-100 text-primary-600 font-bold text-sm flex items-center justify-center flex-shrink-0">
                    {i + 1}
                  </span>
                  <span className="flex-1 font-medium text-gray-800">{item}</span>
                  {!result && (
                    <div className="flex gap-1">
                      <button onClick={() => moveOrderItem(i, 'up')} disabled={i === 0} className="p-1.5 hover:bg-gray-200 rounded transition disabled:opacity-30">
                        <ArrowUp className="h-4 w-4 text-gray-600" />
                      </button>
                      <button onClick={() => moveOrderItem(i, 'down')} disabled={i === orderedItems.length - 1} className="p-1.5 hover:bg-gray-200 rounded transition disabled:opacity-30">
                        <ArrowDown className="h-4 w-4 text-gray-600" />
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Bar Model */}
        {exercise.exercise_type === 'bar_model' && (
          <div className="mb-4">
            <InteractiveBarModel
              question={(exercise.data as any).question || ''}
              expectedTotal={(exercise.data as any).total || '?'}
              expectedUnits={(exercise.data as any).units || []}
              onChange={(construction, numericAnswer) => {
                setBarModelConstruction(construction)
                setAnswer(numericAnswer)
              }}
            />
            <input
              type="hidden"
              value={answer}
            />
          </div>
        )}

        {/* Word Problem */}
        {exercise.exercise_type === 'word_problem' && (
          <div className="mb-4">
            <WordProblemDisplay data={exercise.data as import('@/lib/api').WordProblemData} />
            <input
              type="text"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              disabled={!!result}
              className="input text-2xl text-center py-4 mt-4"
              placeholder="Escribe tu respuesta..."
              onKeyDown={e => e.key === 'Enter' && !result && !submitting && handleSubmit()}
            />
          </div>
        )}

        {/* Result */}
        {result && (
          <div className={`card mb-4 animate-result-pop ${result.correct ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
            <div className="flex items-center gap-3 mb-3">
              {result.correct ? (
                <>
                  <CheckCircle className="h-10 w-10 text-green-600" />
                  <div>
                    <h2 className="text-xl font-bold text-green-800">¡Correcto!</h2>
                    <p className="text-green-700 flex items-center gap-2">
                      <Star className="h-4 w-4 fill-yellow-500 text-yellow-500" /> +{result.xp_earned} XP
                      {result.streak_updated && (
                        <span className="flex items-center gap-1 ml-2 text-orange-500 animate-streak-pulse">
                          <Flame className="h-4 w-4" /> ¡Racha {result.current_streak}!
                        </span>
                      )}
                    </p>
                  </div>
                </>
              ) : (
                <>
                  <XCircle className="h-10 w-10 text-red-600" />
                  <div>
                    <h2 className="text-xl font-bold text-red-800">Incorrecto</h2>
                    <p className="text-red-700">La respuesta correcta era diferente</p>
                  </div>
                </>
              )}
            </div>
            {result.explanation && (
              <div className="p-3 bg-white rounded-lg">
                <p className="text-sm font-semibold text-gray-700 mb-1 flex items-center gap-1">
                  <Lightbulb className="h-4 w-4 text-yellow-500" /> Explicación
                </p>
                <p className="text-gray-700">{result.explanation}</p>
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3">
          {!result ? (
            <button
              onClick={handleSubmit}
              disabled={submitting || (
                exercise.exercise_type === 'multiple_choice' ? selectedOption === null :
                exercise.exercise_type === 'true_false' ? selectedOption === null :
                exercise.exercise_type === 'ordering' ? false :
                !answer.trim()
              )}
              className="btn-primary flex-1 text-lg py-3"
            >
              {submitting ? 'Verificando...' : 'Verificar Respuesta'}
            </button>
          ) : (
            <button onClick={handleNext} className="btn-primary flex-1 text-lg py-3">
              Siguiente <ChevronLeft className="h-5 w-5 ml-2 rotate-180" />
            </button>
          )}
        </div>
      </main>
    </div>
  )
}

function handleNext() {
  // Navigate back - will be enhanced to go to next exercise
  window.history.back()
}