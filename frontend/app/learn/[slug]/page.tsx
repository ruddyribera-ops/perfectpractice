'use client'

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import { api, Lesson, StatsData } from '@/lib/api'
import { useAuth } from '@/contexts/AuthContext'
import { Flame, Star, ChevronLeft, BookOpen, Target, Lock, CheckCircle } from 'lucide-react'

interface UnitDetail {
  id: number
  slug: string
  title: string
  description: string | null
  exercises: {
    id: number
    title: string
    exercise_type: string
    points_value: number
    lesson_id: number | null
  }[]
  lessons: Lesson[]
}

interface CompletedExercises {
  [exerciseId: number]: boolean
}

export default function LearnPage() {
  const params = useParams()
  const router = useRouter()
  const { user } = useAuth()
  const slug = params.slug as string

  const [unit, setUnit] = useState<UnitDetail | null>(null)
  const [stats, setStats] = useState<StatsData | null>(null)
  const [completed, setCompleted] = useState<CompletedExercises>({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!user || !slug) return
    Promise.all([
      api.get<UnitDetail>(`/units/${slug}`),
      api.get<StatsData>('/me/stats/me'),
    ]).then(([unitData, statsData]) => {
      setUnit(unitData)
      setStats(statsData)
      // Build completed map from progress
      const completedMap: CompletedExercises = {}
      unitData.exercises.forEach(e => { completedMap[e.id] = false })
      setCompleted(completedMap)
    }).catch(console.error).finally(() => setLoading(false))
  }, [user, slug])

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
        <p className="text-gray-600">Cargando camino de aprendizaje...</p>
      </div>
    </div>
  )

  if (!unit) return (
    <div className="min-h-screen flex items-center justify-center">
      <p className="text-gray-600">Unidad no encontrada</p>
    </div>
  )

  // Group exercises by lesson
  const lessonIds = [...new Set(unit.exercises.map(e => e.lesson_id).filter(Boolean))] as number[]
  const ungroupedExercises = unit.exercises.filter(e => !e.lesson_id)
  const lessons = unit.lessons.sort((a, b) => a.order_index - b.order_index)

  // XP bar progress
  const xpProgress = stats ? ((stats.total_xp % 100) / 100) * 100 : 0

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ── Navbar ─────────────────────────────────────────────────────────── */}
      <header className="bg-white shadow-sm sticky top-0 z-50">
        <nav className="max-w-5xl mx-auto px-4 py-3 flex items-center gap-4">
          <button onClick={() => router.back()} className="p-2 hover:bg-gray-100 rounded-lg transition">
            <ChevronLeft className="h-5 w-5 text-gray-600" />
          </button>
          <Link href="/topics" className="text-xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-400">/</span>
          <span className="font-medium text-gray-700">{unit.title}</span>
          <div className="ml-auto flex items-center gap-3">
            {/* XP bar */}
            <div className="flex items-center gap-2">
              <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />
              <div className="w-24 h-2 bg-gray-200 rounded-full overflow-hidden">
                <div className="h-full bg-yellow-400 rounded-full transition-all duration-500" style={{ width: `${xpProgress}%` }} />
              </div>
              <span className="text-xs font-medium text-gray-600">Nivel {stats?.level}</span>
            </div>
            {/* Streak */}
            <div className="flex items-center gap-1 bg-orange-50 px-3 py-1.5 rounded-full">
              <Flame className="h-4 w-4 text-orange-500 animate-streak-pulse" />
              <span className="text-sm font-bold text-orange-600">{stats?.current_streak}</span>
            </div>
          </div>
        </nav>
      </header>

      <main className="max-w-5xl mx-auto px-4 py-8">

        {/* ── Unit Header ─────────────────────────────────────────────────── */}
        <div className="text-center mb-10">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">{unit.title}</h1>
          {unit.description && <p className="text-gray-600 text-lg">{unit.description}</p>}
          {stats && (
            <div className="flex items-center justify-center gap-6 mt-4">
              <div className="flex items-center gap-1">
                <Star className="h-5 w-5 text-yellow-500 fill-yellow-500" />
                <span className="font-bold text-gray-800">{stats.total_xp} XP</span>
              </div>
              <div className="flex items-center gap-1">
                <Flame className="h-5 w-5 text-orange-500" />
                <span className="font-bold text-gray-800">{stats.current_streak} días</span>
              </div>
              <div className="flex items-center gap-1">
                <Target className="h-5 w-5 text-green-500" />
                <span className="font-bold text-gray-800">{stats.exercises_completed} ejercicios</span>
              </div>
            </div>
          )}
        </div>

        {/* ── Learning Path ───────────────────────────────────────────────── */}
        <div className="relative">
          {/* The path line */}
          <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-green-400 via-primary-400 to-purple-400 rounded-full opacity-30" />

          <div className="space-y-6">

            {/* Lessons */}
            {lessons.map((lesson, li) => {
              const lessonExercises = unit.exercises.filter(e => e.lesson_id === lesson.id)
              const completedCount = 0 // Will be wired to real completion data
              const totalCount = lessonExercises.length
              const allDone = completedCount === totalCount && totalCount > 0

              return (
                <div key={lesson.id} className="relative flex items-start gap-6">
                  {/* Node on path */}
                  <div className={`relative z-10 flex-shrink-0 w-16 h-16 rounded-full flex items-center justify-center shadow-lg ${
                    allDone
                      ? 'bg-gradient-to-br from-green-400 to-green-600 text-white'
                      : 'bg-gradient-to-br from-primary-500 to-primary-700 text-white'
                  }`}>
                    {allDone ? (
                      <CheckCircle className="h-8 w-8" />
                    ) : (
                      <BookOpen className="h-8 w-8" />
                    )}
                  </div>

                  {/* Content card */}
                  <div className="flex-1 card hover:shadow-md transition-shadow">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-xs font-bold text-primary-600 uppercase tracking-wider">
                        Lección {li + 1}
                      </span>
                      {allDone && (
                        <span className="badge badge-success">Completada</span>
                      )}
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">{lesson.title}</h3>
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">{lesson.content.replace(/[#*`]/g, '').substring(0, 120)}...</p>
                    <div className="flex items-center gap-3">
                      <Link href={`/lessons/${lesson.id}`} className="btn-primary text-sm">
                        {allDone ? 'Repasar' : 'Comenzar'}
                      </Link>
                      <span className="text-xs text-gray-500">{totalCount} ejercicios</span>
                    </div>
                  </div>
                </div>
              )
            })}

            {/* Ungrouped / Final exercises */}
            {ungroupedExercises.length > 0 && (
              <div className="relative flex items-start gap-6">
                <div className="relative z-10 flex-shrink-0 w-16 h-16 rounded-full bg-gradient-to-br from-purple-500 to-purple-700 text-white flex items-center justify-center shadow-lg">
                  <Target className="h-8 w-8" />
                </div>
                <div className="flex-1 card">
                  <span className="text-xs font-bold text-purple-600 uppercase tracking-wider">Práctica Final</span>
                  <h3 className="text-xl font-bold text-gray-900 mb-3">Ejercicios de Repaso</h3>
                  <div className="space-y-2">
                    {ungroupedExercises.map((ex, i) => (
                      <Link key={ex.id} href={`/lessons/practice/${ex.id}`}>
                        <div className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-50 transition cursor-pointer">
                          <div className="w-8 h-8 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center text-sm font-bold">
                            {i + 1}
                          </div>
                          <div className="flex-1">
                            <p className="font-medium text-gray-800">{ex.title}</p>
                            <p className="text-xs text-gray-500">{ex.points_value} XP</p>
                          </div>
                          <span className={`badge ${
                            ex.exercise_type === 'multiple_choice' ? 'badge-primary' :
                            ex.exercise_type === 'true_false' ? 'badge-secondary' : 'badge-success'
                          }`}>
                            {ex.exercise_type === 'multiple_choice' ? 'Opción múltiple' :
                             ex.exercise_type === 'true_false' ? 'Verdadero/Falso' : 'Numérico'}
                          </span>
                        </div>
                      </Link>
                    ))}
                  </div>
                </div>
              </div>
            )}

          </div>
        </div>
      </main>
    </div>
  )
}
