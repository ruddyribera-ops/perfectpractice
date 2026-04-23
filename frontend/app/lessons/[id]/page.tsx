'use client'

import { useEffect, useState, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, Exercise, StatsData } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { ChevronLeft, ChevronRight, Flame, Star, Lightbulb, CheckCircle, XCircle, BookOpen } from 'lucide-react'
import { EnhancedLessonContent } from '@/components/EnhancedLessonContent'
import { BarModel, WordProblem } from '@/components/LessonVisuals'

interface LessonData {
  id: number
  unit_id: number
  unit_slug: string
  title: string
  content: string
  order_index: number
  exercises: Exercise[]
  content_type?: 'text' | 'video'
}

export default function LessonPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const id = parseInt(params.id as string, 10)

  const [lesson, setLesson] = useState<LessonData | null>(null)
  const [stats, setStats] = useState<StatsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Practice round state
  const [practiceActive, setPracticeActive] = useState(false)
  const [currentIndex, setCurrentIndex] = useState(0)
  const [answer, setAnswer] = useState('')
  const [selectedOption, setSelectedOption] = useState<number | null>(null)
  const [showHint, setShowHint] = useState(false)
  const [hintIndex, setHintIndex] = useState(0)
  const [result, setResult] = useState<{ correct: boolean; xp_earned: number; explanation: string | null; streak_updated: boolean; current_streak: number } | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [roundResults, setRoundResults] = useState<boolean[]>([])
  const startTime = useRef(Date.now())

  useEffect(() => {
    if (!user || isNaN(id)) return
    Promise.all([
      api.getLesson(id),
      api.getStats(),
    ]).then(([lessonData, statsData]) => {
      setLesson(lessonData as any)
      setStats(statsData)
    }).catch((error: any) => {
      console.error(error)
      if (error.status === 401 || error.status === 403) {
        localStorage.removeItem('access_token')
        router.push('/login')
      }
      // else: lesson stays null → shows "Lección no encontrada"
    }).finally(() => setLoading(false))
  }, [user, id])

  const startPractice = () => {
    if (!lesson?.exercises.length) return
    setPracticeActive(true)
    setCurrentIndex(0)
    setAnswer('')
    setSelectedOption(null)
    setShowHint(false)
    setHintIndex(0)
    setResult(null)
    setRoundResults([])
    startTime.current = Date.now()
  }

  const currentExercise = lesson?.exercises[currentIndex]

  const handleSubmit = async () => {
    if (!currentExercise || submitting) return
    let finalAnswer: string
    if (currentExercise.exercise_type === 'multiple_choice' && (currentExercise.data as any).options) {
      if (selectedOption === null) return
      finalAnswer = (currentExercise.data as any).options[selectedOption]
    } else if (currentExercise.exercise_type === 'true_false') {
      finalAnswer = selectedOption === 0 ? 'true' : 'false'
    } else {
      if (!answer.trim()) return
      finalAnswer = answer.trim()
    }

    setSubmitting(true)
    const timeSpent = Math.round((Date.now() - startTime.current) / 1000)

    try {
      const res = await api.submitAttempt(currentExercise.id, finalAnswer, timeSpent)
      setResult(res)
      setRoundResults(prev => [...prev, res.correct])
    } catch (e: any) {
      console.error(e)
      setError('No se pudo verificar la respuesta. Intenta de nuevo.')
    } finally {
      setSubmitting(false)
    }
  }

  const handleNext = () => {
    if (currentIndex < (lesson?.exercises.length ?? 0) - 1) {
      setCurrentIndex(prev => prev + 1)
      setAnswer('')
      setSelectedOption(null)
      setShowHint(false)
      setHintIndex(0)
      setResult(null)
      startTime.current = Date.now()
    } else {
      // Round complete
      setPracticeActive(false)
    }
  }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Cargando lección...</p>
      </div>
    </div>
  )

  if (!lesson) return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <p className="text-gray-600">Lección no encontrada</p>
    </div>
  )

  // ── Round Complete Screen ───────────────────────────────────────────────
  if (!practiceActive && roundResults.length > 0) {
    const correct = roundResults.filter(Boolean).length
    const total = roundResults.length
    const allCorrect = correct === total
    const xpTotal = roundResults.reduce((sum, r, i) => {
      // Estimate XP per result (actual is in DB)
      return sum + (r ? 15 : 0)
    }, 0)

    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-purple-50 flex items-center justify-center p-4">
        <div className="card text-center max-w-md w-full animate-level-up">
          <div className={`text-6xl mb-4 ${allCorrect ? 'animate-bounce' : ''}`}>
            {allCorrect ? '🏆' : '💪'}
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {allCorrect ? '¡Lección Completada!' : '¡Sigue Practicando!'}
          </h2>
          <p className="text-gray-600 mb-6">
            {allCorrect
              ? '¡Perfecto! Dominaste esta lección.'
              : `Vas bien, sigue practicando para mejorar.`}
          </p>
          <div className="flex justify-center gap-8 mb-6">
            <div className="text-center">
              <p className="text-3xl font-bold text-green-600">{correct}/{total}</p>
              <p className="text-sm text-gray-500">Correctas</p>
            </div>
            <div className="text-center">
              <p className="text-3xl font-bold text-yellow-500">+{correct * 10}</p>
              <p className="text-sm text-gray-500">XP ganados</p>
            </div>
          </div>
          <div className="flex gap-3">
            <button onClick={startPractice} className="btn-secondary flex-1">
              Repetir
            </button>
            <Link href={`/learn/${lesson.unit_slug}`} className="btn-primary flex-1">
              Continuar
            </Link>
          </div>
        </div>
      </div>
    )
  }

  // ── Practice Round ───────────────────────────────────────────────────────
  if (practiceActive && currentExercise) {
    return (
      <PracticeView
        exercise={currentExercise}
        result={result}
        answer={answer}
        setAnswer={setAnswer}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        showHint={showHint}
        hintIndex={hintIndex}
        submitting={submitting}
        currentIndex={currentIndex}
        total={lesson.exercises.length}
        onShowHint={() => { setShowHint(true); setHintIndex(0) }}
        onNextHint={() => setHintIndex(prev => Math.min(prev + 1, (currentExercise.hints?.length ?? 1) - 1))}
        onSubmit={handleSubmit}
        onNext={handleNext}
        xpProgress={stats ? ((stats.total_xp % 100) / 100) * 100 : 0}
        currentStreak={stats?.current_streak ?? 0}
      />
    )
  }

  // ── Lesson Content View ─────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <nav className="max-w-3xl mx-auto px-4 py-3 flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-lg transition">
            <ChevronLeft className="h-5 w-5 text-gray-600" />
          </button>
          <BookOpen className="h-5 w-5 text-primary-600" />
          <span className="font-medium text-gray-700">{lesson.title}</span>
          <div className="ml-auto flex items-center gap-2">
            <Flame className="h-4 w-4 text-orange-500" />
            <span className="text-sm font-bold text-orange-600">{stats?.current_streak}</span>
          </div>
        </nav>
      </header>

      <main className="max-w-3xl mx-auto px-4 py-8">
        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-xl text-red-700 text-sm">
            ⚠️ {error}
          </div>
        )}
        {/* Lesson card */}
        <div className="card mb-6">
          <span className="text-xs font-bold text-primary-600 uppercase tracking-wider">Lección</span>
          <h1 className="text-2xl font-bold text-gray-900 mt-1 mb-4">{lesson.title}</h1>
          <div className="prose prose-gray max-w-none">
            {(lesson.content_type === 'video') ? (
              <div className="relative w-full" style={{ paddingTop: '56.25%' }}>
                <iframe
                  className="absolute top-0 left-0 w-full h-full rounded-xl"
                  src={lesson.content.includes('youtube')
                    ? lesson.content.replace('watch?v=', 'embed/').split('&')[0]
                    : lesson.content}
                  title="Video lección"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
                  allowFullScreen
                />
              </div>
            ) : (
              <EnhancedLessonContent content={lesson.content} />
            )}
          </div>
        </div>

        {/* Practice CTA */}
        {lesson.exercises.length > 0 && (
          <div className="card bg-gradient-to-br from-primary-50 to-purple-50 border-primary-100 text-center">
            <div className="text-4xl mb-3">🎯</div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">¡Pon a prueba tus conocimientos!</h2>
            <p className="text-gray-600 mb-5">
              {lesson.exercises.length} ejercicios para practicar lo que aprendiste
            </p>
            <button onClick={startPractice} className="btn-primary text-lg px-8 py-3 animate-glow-pulse">
              Comenzar Práctica
            </button>
          </div>
        )}

        {lesson.exercises.length === 0 && (
          <div className="card text-center">
            <p className="text-gray-600">No hay ejercicios para esta lección todavía.</p>
            <Link href={`/topics`} className="text-primary-600 hover:underline mt-2 inline-block">
              Volver a temas
            </Link>
          </div>
        )}
      </main>
    </div>
  )
}

// ─── Practice View Component ──────────────────────────────────────────────────

function PracticeView({
  exercise, result, answer, setAnswer, selectedOption, setSelectedOption,
  showHint, hintIndex, submitting, currentIndex, total,
  onShowHint, onNextHint, onSubmit, onNext,
  xpProgress, currentStreak
}: {
  exercise: Exercise
  result: { correct: boolean; xp_earned: number; explanation: string | null; streak_updated: boolean; current_streak: number } | null
  answer: string
  setAnswer: (v: string) => void
  selectedOption: number | null
  setSelectedOption: (v: number | null) => void
  showHint: boolean
  hintIndex: number
  submitting: boolean
  currentIndex: number
  total: number
  onShowHint: () => void
  onNextHint: () => void
  onSubmit: () => void
  onNext: () => void
  xpProgress: number
  currentStreak: number
}) {
  const hints = exercise.hints ?? []
  const canSubmit = submitting || (
    exercise.exercise_type === 'multiple_choice' ? selectedOption === null :
    exercise.exercise_type === 'true_false' ? selectedOption === null :
    !answer.trim()
  )

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-2xl mx-auto px-4 py-3">
          <div className="flex items-center gap-4 mb-2">
            <span className="text-sm font-medium text-gray-600">
              Ejercicio {currentIndex + 1} de {total}
            </span>
            <div className="ml-auto flex items-center gap-2">
              <Flame className="h-4 w-4 text-orange-500" />
              <span className="text-sm font-bold text-orange-600">{currentStreak}</span>
            </div>
          </div>
          {/* Progress bar */}
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-primary-500 to-purple-500 rounded-full transition-all duration-500"
              style={{ width: `${((currentIndex) / total) * 100}%` }} />
          </div>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        {/* Question */}
        <div className="card mb-4">
          <div className="flex items-center justify-between mb-3">
            <span className={`badge ${
              exercise.exercise_type === 'multiple_choice' ? 'badge-primary' :
              exercise.exercise_type === 'true_false' ? 'badge-secondary' : 'badge-success'
            }`}>
              {exercise.exercise_type === 'multiple_choice' ? 'Opción múltiple' :
               exercise.exercise_type === 'true_false' ? 'Verdadero / Falso' :
               exercise.exercise_type === 'bar_model' ? 'Modelo de Barras' :
               exercise.exercise_type === 'word_problem' ? 'Problema Verbal' : 'Numérico'}
            </span>
            <span className="text-sm text-yellow-600 flex items-center gap-1">
              <Star className="h-4 w-4 fill-yellow-500" /> +{exercise.points_value} XP
            </span>
          </div>
          <p className="text-xl text-gray-900 text-center py-4">{exercise.data.question}</p>
        </div>

        {/* Hint button */}
        {hints.length > 0 && !result && (
          <div className="mb-4">
            {!showHint ? (
              <button onClick={onShowHint} className="text-primary-600 hover:underline text-sm flex items-center gap-1">
                <Lightbulb className="h-4 w-4" /> ¿Necesitas ayuda?
              </button>
            ) : (
              <div className="card bg-yellow-50 border-yellow-200">
                <p className="text-sm font-semibold text-yellow-800 mb-1">
                  Pista {hintIndex + 1} de {hints.length}
                </p>
                <p className="text-gray-700 text-sm">{hints[Math.min(hintIndex, hints.length - 1)]}</p>
                {hintIndex < hints.length - 1 && (
                  <button onClick={onNextHint} className="text-xs text-yellow-700 hover:underline mt-1">
                    Ver siguiente pista
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* Multiple Choice */}
        {exercise.exercise_type === 'multiple_choice' && (exercise.data as any).options && (
          <div className="space-y-3 mb-4">
            {(exercise.data as any).options.map((opt: any, i: number) => {
              let cls = 'w-full p-4 text-left rounded-xl border-2 transition-all font-medium'
              if (result) {
                if (i === selectedOption) cls += result.correct ? ' border-green-500 bg-green-50' : ' border-red-500 bg-red-50'
                else cls += ' border-gray-200 opacity-50'
              } else {
                cls += selectedOption === i ? ' border-primary-500 bg-primary-50' : ' border-gray-200 hover:border-primary-300'
              }
              return (
                <button key={i} onClick={() => !result && setSelectedOption(i)} disabled={!!result} className={cls}>
                  <span className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-gray-100 text-gray-700 font-bold mr-3 text-sm">
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
            {['Verdadero', 'Falso'].map((label, i) => {
              let cls = 'p-6 rounded-xl border-2 text-center text-lg font-bold transition-all'
              if (result) {
                cls += selectedOption === i
                  ? (i === 0 && exercise.data.question.includes('falso') || i === 1 ? ' border-green-500 bg-green-50 text-green-700' : ' border-red-500 bg-red-50 text-red-700')
                  : ' border-gray-200 opacity-50'
              } else {
                cls += selectedOption === i ? ' border-primary-500 bg-primary-50 text-primary-700' : ' border-gray-200 hover:border-primary-300'
              }
              return (
                <button key={i} onClick={() => !result && setSelectedOption(i)} disabled={!!result} className={cls}>
                  {label}
                </button>
              )
            })}
          </div>
        )}

        {/* Numeric Input */}
        {(exercise.exercise_type === 'numeric') && (
          <div className="mb-4">
            <input
              type="text"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              disabled={!!result}
              className="input text-2xl text-center py-4"
              placeholder="Tu respuesta..."
              onKeyDown={e => e.key === 'Enter' && !result && !canSubmit && onSubmit()}
            />
          </div>
        )}

        {/* Bar Model */}
        {exercise.exercise_type === 'bar_model' && (
          <div className="mb-4">
            <BarModel
              question={(exercise.data as any).question}
              total={(exercise.data as any).total}
              units={(exercise.data as any).units || []}
              type={(exercise.data as any).type}
              grade={1}
            />
            <input
              type="text"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              disabled={!!result}
              className="input text-2xl text-center py-4 mt-4"
              placeholder="Tu respuesta..."
              onKeyDown={e => e.key === 'Enter' && !result && !canSubmit && onSubmit()}
            />
          </div>
        )}

        {/* Word Problem */}
        {exercise.exercise_type === 'word_problem' && (
          <div className="mb-4">
            <WordProblem
              scenario={(exercise.data as any).scenario}
              question={(exercise.data as any).question}
              answer={(exercise.data as any).answer}
              hint={(exercise.data as any).hint}
              grade={1}
            />
            <input
              type="text"
              value={answer}
              onChange={e => setAnswer(e.target.value)}
              disabled={!!result}
              className="input text-2xl text-center py-4 mt-4"
              placeholder="Tu respuesta..."
              onKeyDown={e => e.key === 'Enter' && !result && !canSubmit && onSubmit()}
            />
          </div>
        )}

        {/* Result Feedback */}
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
                        <span className="flex items-center gap-1 ml-2 text-orange-500">
                          <Flame className="h-4 w-4" /> ¡Racha actualizada!</span>
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

        {/* Action Buttons */}
        <div className="flex gap-3">
          {!result ? (
            <button
              onClick={onSubmit}
              disabled={canSubmit}
              className="btn-primary flex-1 text-lg py-3"
            >
              {submitting ? 'Verificando...' : 'Verificar'}
            </button>
          ) : (
            <button onClick={onNext} className="btn-primary flex-1 text-lg py-3 flex items-center justify-center gap-2">
              {currentIndex < total - 1 ? (
                <>Siguiente <ChevronRight className="h-5 w-5" /></>
              ) : (
                <>Finalizar <span className="text-lg">🎉</span></>
              )}
            </button>
          )}
        </div>
      </main>
    </div>
  )
}
