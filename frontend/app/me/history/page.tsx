'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api, AttemptHistoryItem, ProgressItem } from '@/lib/api'
import { CheckCircle, XCircle, RotateCcw, ChevronLeft, ChevronRight, BookOpen } from 'lucide-react'

type FilterCorrect = 'all' | 'correct' | 'incorrect'

export default function HistoryPage() {
  const [items, setItems] = useState<AttemptHistoryItem[]>([])
  const [topics, setTopics] = useState<ProgressItem[]>([])
  const [loading, setLoading] = useState(true)
  const [total, setTotal] = useState(0)
  const [pages, setPages] = useState(0)
  const [page, setPage] = useState(1)

  const [topicFilter, setTopicFilter] = useState<number | undefined>(undefined)
  const [correctFilter, setCorrectFilter] = useState<FilterCorrect>('all')
  const limit = 20

  useEffect(() => {
    loadProgress()
  }, [])

  useEffect(() => {
    const handler = () => { api.getProgress().then(setTopics).catch(() => {}); };
    window.addEventListener('mastery-updated', handler);
    return () => window.removeEventListener('mastery-updated', handler);
  }, []);

  useEffect(() => {
    loadHistory()
  }, [page, topicFilter, correctFilter])

  const loadProgress = async () => {
    try {
      const data = await api.getProgress()
      setTopics(data)
    } catch (e) {
      console.error(e)
    }
  }

  const loadHistory = async () => {
    setLoading(true)
    try {
      const params: Parameters<typeof api.getAttemptHistory>[0] = {
        page,
        limit,
        ...(topicFilter != null && { topic_id: topicFilter }),
        ...(correctFilter !== 'all' && { correct: correctFilter === 'correct' }),
      }
      const data = await api.getAttemptHistory(params)
      setItems(data.items)
      setTotal(data.total)
      setPages(data.pages)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const correctCount = items.filter(i => i.correct).length
  const incorrectCount = items.filter(i => !i.correct).length

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="max-w-4xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-400">/</span>
          <span className="font-medium">Mi Progreso</span>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h1 className="text-2xl font-bold">Historial de Ejercicios</h1>
          <Link href="/" className="text-primary-600 hover:underline text-sm flex items-center gap-1">
            <ChevronLeft className="h-4 w-4" /> Volver al inicio
          </Link>
        </div>

        {/* Topic mastery summary cards */}
        {topics.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
            {topics.map(t => (
              <div key={t.topic_id} className="card">
                <div className="flex items-center gap-2 mb-2">
                  <BookOpen className="h-4 w-4 text-primary-500" />
                  <span className="font-semibold text-gray-800 text-sm">{t.topic_title}</span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden mb-1">
                  <div
                    className="h-full bg-green-500 rounded-full transition-all"
                    style={{ width: `${Math.round(t.mastery_score)}%` }}
                  />
                </div>
                <p className="text-xs text-gray-500">
                  {t.exercises_completed}/{t.total_exercises} ejercicios • {Math.round(t.mastery_score)}% dominio
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          <select
            value={topicFilter ?? ''}
            onChange={e => { setTopicFilter(e.target.value ? Number(e.target.value) : undefined); setPage(1) }}
            className="input text-sm py-2"
          >
            <option value="">Todos los temas</option>
            {topics.map(t => (
              <option key={t.topic_id} value={t.topic_id}>{t.topic_title}</option>
            ))}
          </select>

          <div className="flex gap-1 bg-gray-200 rounded-lg p-1">
            {(['all', 'correct', 'incorrect'] as FilterCorrect[]).map(f => (
              <button
                key={f}
                onClick={() => { setCorrectFilter(f); setPage(1) }}
                className={`px-3 py-1.5 rounded-md text-sm font-medium transition ${
                  correctFilter === f ? 'bg-white shadow text-primary-600' : 'text-gray-600 hover:text-gray-800'
                }`}
              >
                {f === 'all' ? 'Todos' : f === 'correct' ? `Correctos (${correctCount})` : `Incorrectos (${incorrectCount})`}
              </button>
            ))}
          </div>
        </div>

        {/* Results count */}
        <p className="text-sm text-gray-500 mb-4">
          {total === 0 ? 'Sin resultados' : `${total} ejercicio${total !== 1 ? 's' : ''} encontrado${total !== 1 ? 's' : ''}`}
        </p>

        {/* Attempt list */}
        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
          </div>
        ) : items.length === 0 ? (
          <div className="card text-center py-12">
            <p className="text-gray-600">Aún no has hecho ningún ejercicio</p>
            <Link href="/topics" className="btn-primary mt-4 inline-block">Empezar a practicar</Link>
          </div>
        ) : (
          <div className="space-y-3">
            {items.map(item => (
              <div key={item.id} className={`card flex items-center gap-4 py-3 ${
                item.correct ? 'border-l-4 border-l-green-500' : 'border-l-4 border-l-red-400'
              }`}>
                <div className="flex-shrink-0">
                  {item.correct
                    ? <CheckCircle className="h-8 w-8 text-green-500" />
                    : <XCircle className="h-8 w-8 text-red-400" />
                  }
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-semibold text-gray-900">{item.exercise_title}</p>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-500">{item.topic_title}</span>
                    <span className="text-xs text-gray-400">•</span>
                    <span className="text-xs text-gray-500">{item.unit_title}</span>
                  </div>
                  <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                    <span>{item.attempted_at ? new Date(item.attempted_at).toLocaleString('es-BO') : ''}</span>
                    {item.xp_earned > 0 && (
                      <span className="text-yellow-600 font-medium">+{item.xp_earned} XP</span>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2 flex-shrink-0">
                  {!item.correct && (
                    <Link
                      href={`/exercises/${item.exercise_id}`}
                      className="flex items-center gap-1.5 px-3 py-1.5 bg-red-50 text-red-600 rounded-lg text-sm font-medium hover:bg-red-100 transition"
                    >
                      <RotateCcw className="h-4 w-4" />
                      Reintentar
                    </Link>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Pagination */}
        {pages > 1 && (
          <div className="flex items-center justify-center gap-2 mt-6">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-2 border rounded-lg disabled:opacity-40 hover:bg-gray-50"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <span className="text-sm text-gray-600">
              Página {page} de {pages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(pages, p + 1))}
              disabled={page === pages}
              className="px-3 py-2 border rounded-lg disabled:opacity-40 hover:bg-gray-50"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        )}
      </main>
    </div>
  )
}
