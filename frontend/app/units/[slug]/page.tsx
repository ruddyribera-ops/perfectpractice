'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { ChevronRight, Target, Zap, BookOpen, Flame } from 'lucide-react'

interface Lesson {
  id: number
  unit_id: number
  title: string
  order_index: number
}

interface Exercise {
  id: number
  slug: string
  title: string
  exercise_type: string
  difficulty: string
  points_value: number
  lesson_id: number | null
  is_anked: boolean
  is_summative: boolean
}

interface UnitDetail {
  id: number
  topic_id: number
  slug: string
  title: string
  description: string | null
  order_index: number
  exercises: Exercise[]
  lessons: Lesson[]
}

const difficultyColors = {
  easy: 'badge-success',
  medium: 'badge-secondary',
  hard: 'bg-red-100 text-red-800',
}

export default function UnitDetailPage() {
  const params = useParams()
  const slug = params.slug as string
  const [unit, setUnit] = useState<UnitDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (slug) fetchUnit()
  }, [slug])

  const fetchUnit = async () => {
    try {
      const data = await api.get<UnitDetail>(`/units/${slug}`)
      setUnit(data)
    } catch (error) {
      console.error('Error fetching unit:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!unit) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Unidad no encontrada</p>
      </div>
    )
  }

  const totalXP = unit.exercises.reduce((sum, e) => sum + e.points_value, 0)

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4 text-sm">
          <Link href="/" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-500">/</span>
          <Link href="/topics" className="text-gray-500 hover:text-gray-700">Temas</Link>
          <span className="text-gray-500">/</span>
          <span className="font-medium">{unit.title}</span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-6">
          <h1 className="text-3xl font-bold mb-2">{unit.title}</h1>
          {unit.description && <p className="text-gray-600">{unit.description}</p>}
        </div>

        <div className="flex flex-wrap items-center gap-4 mb-8">
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <BookOpen className="h-4 w-4" />
            {unit.lessons.length} lecciones
          </div>
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <Target className="h-4 w-4" />
            {unit.exercises.length} ejercicios
          </div>
          <div className="flex items-center gap-1 text-sm text-gray-600">
            <Zap className="h-4 w-4 text-yellow-500" />
            {totalXP} XP totales
          </div>
          <Link href={`/learn/${unit.slug}`} className="btn-primary ml-auto">
            🚀 Camino de Aprendizaje
          </Link>
        </div>

        {/* Lessons */}
        {unit.lessons.length > 0 && (
          <div className="mb-8">
            <h2 className="text-xl font-bold text-gray-900 mb-4">Lecciones</h2>
            <div className="grid md:grid-cols-2 gap-4">
              {unit.lessons.sort((a, b) => a.order_index - b.order_index).map((lesson) => {
                const lessonExercises = unit.exercises.filter(e => e.lesson_id === lesson.id)
                return (
                  <Link key={lesson.id} href={`/lessons/${lesson.id}`}>
                    <div className="card hover:shadow-md transition-shadow cursor-pointer border-l-4 border-l-primary-500">
                      <div className="flex items-start gap-3">
                        <div className="w-10 h-10 rounded-full bg-primary-100 text-primary-600 flex items-center justify-center flex-shrink-0">
                          <BookOpen className="h-5 w-5" />
                        </div>
                        <div className="flex-1">
                          <h3 className="font-semibold text-gray-900">{lesson.title}</h3>
                          <p className="text-sm text-gray-500 mt-1">
                            {lessonExercises.length} ejercicios
                          </p>
                        </div>
                        <ChevronRight className="h-5 w-5 text-gray-400 mt-2" />
                      </div>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        )}

        {/* Ungrouped Exercises */}
        {unit.exercises.filter(e => !e.lesson_id).length > 0 && (
          <div>
            <h2 className="text-xl font-bold text-gray-900 mb-4">Ejercicios de Práctica</h2>
            <div className="space-y-4">
              {unit.exercises.filter(e => !e.lesson_id).map((exercise, index) => (
                <Link key={exercise.id} href={`/exercises/${exercise.id}`}>
                  <div className="card hover:shadow-md transition-shadow cursor-pointer">
                    <div className="flex items-center gap-4">
                      <div className="flex items-center justify-center w-10 h-10 rounded-full bg-purple-100 text-purple-600 font-bold">
                        {index + 1}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h3 className="text-lg font-semibold">{exercise.title}</h3>
                          {exercise.is_anked && <span className="badge badge-primary">Panderado</span>}
                          {exercise.is_summative && <span className="badge badge-secondary">Sumativo</span>}
                        </div>
                        <div className="flex items-center gap-3 text-sm">
                          <span className={`badge ${difficultyColors[exercise.difficulty as keyof typeof difficultyColors]}`}>
                            {exercise.difficulty}
                          </span>
                          <span className="flex items-center gap-1">
                            <Zap className="h-4 w-4 text-yellow-500" />{exercise.points_value} pts
                          </span>
                          <span className="text-gray-500 capitalize">{exercise.exercise_type.replace('_', ' ')}</span>
                        </div>
                      </div>
                      <ChevronRight className="h-5 w-5 text-gray-400" />
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
