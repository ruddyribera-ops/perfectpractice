'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api, LeaderboardMeResponse } from '@/lib/api'
import { Trophy, Medal, Star, TrendingUp } from 'lucide-react'

interface LeaderboardEntry {
  rank: number
  student_id: number
  student_name: string
  points: number
  avatar_url: string | null
  level: number
}

export default function LeaderboardPage() {
  const [entries, setEntries] = useState<LeaderboardEntry[]>([])
  const [myRank, setMyRank] = useState<LeaderboardMeResponse | null>(null)
  const [period, setPeriod] = useState<'weekly' | 'monthly' | 'all_time'>('weekly')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchLeaderboard()
  }, [period])

  const fetchLeaderboard = async () => {
    setLoading(true)
    try {
      const [data, rankData] = await Promise.all([
        api.get<LeaderboardEntry[]>(`/leaderboard/global?period=${period}`),
        api.getMyRank().catch(() => null),
      ])
      setEntries(data)
      setMyRank(rankData)
    } catch (error) {
      console.error('Error fetching leaderboard:', error)
    } finally {
      setLoading(false)
    }
  }

  const getRankIcon = (rank: number) => {
    if (rank === 1) return <Trophy className="h-8 w-8 text-yellow-500" />
    if (rank === 2) return <Medal className="h-8 w-8 text-gray-400" />
    if (rank === 3) return <Medal className="h-8 w-8 text-amber-600" />
    return <span className="text-xl font-bold text-gray-500">#{rank}</span>
  }

  const currentPeriodRank = period === 'weekly' ? myRank?.weekly_rank
    : period === 'monthly' ? myRank?.monthly_rank
    : myRank?.all_time_rank
  const currentPeriodPoints = period === 'weekly' ? myRank?.weekly_points
    : period === 'monthly' ? myRank?.monthly_points
    : myRank?.all_time_points

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Link href="/" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-500">/</span>
          <span className="font-medium">Tabla de Posiciones</span>
        </nav>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Tabla de Posiciones Global</h1>
          
          <div className="flex gap-2">
            {(['weekly', 'monthly', 'all_time'] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  period === p
                    ? 'bg-primary-600 text-white'
                    : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                }`}
              >
                {p === 'weekly' ? 'Semanal' : p === 'monthly' ? 'Mensual' : 'Todos los tiempos'}
              </button>
            ))}
          </div>
        </div>

        {/* User's own rank card */}
        {myRank && currentPeriodRank != null && (
          <div className="card bg-gradient-to-r from-primary-50 to-primary-100 border-primary-200 mb-6">
            <div className="flex items-center justify-between flex-wrap gap-4">
              <div className="flex items-center gap-3">
                <div className="w-12 h-12 rounded-full bg-primary-600 flex items-center justify-center text-white font-bold text-lg">
                  {myRank.name.charAt(0).toUpperCase()}
                </div>
                <div>
                  <p className="text-sm text-primary-600 font-medium">Tu posición</p>
                  <p className="text-2xl font-bold text-primary-800">#{currentPeriodRank} — {myRank.name}</p>
                </div>
              </div>
              <div className="text-right">
                <p className="flex items-center gap-1 text-2xl font-bold text-primary-700">
                  <Star className="h-6 w-6 text-yellow-500 fill-yellow-500" />
                  {currentPeriodPoints} pts
                </p>
                <p className="text-sm text-primary-500">Nivel {myRank.weekly_rank ?? 1}</p>
              </div>
            </div>
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
          </div>
        ) : entries.length === 0 ? (
          <div className="card text-center py-12">
            <Trophy className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">No hay datos aún</h2>
            <p className="text-gray-600">¡Sé el primero en la tabla de posiciones!</p>
          </div>
        ) : (
          <div className="space-y-4">
            {entries.map((entry) => (
              <div
                key={entry.student_id}
                className={`card flex items-center gap-4 ${
                  entry.rank <= 3 ? 'bg-gradient-to-r from-yellow-50 to-transparent' : ''
                }`}
              >
                <div className="w-12 flex justify-center">
                  {getRankIcon(entry.rank)}
                </div>
                
                <div className="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-bold text-lg">
                  {entry.student_name.charAt(0).toUpperCase()}
                </div>
                
                <div className="flex-1">
                  <p className="font-semibold text-lg">{entry.student_name}</p>
                  <p className="text-sm text-gray-500">Nivel {entry.level}</p>
                </div>
                
                <div className="text-right">
                  <p className="flex items-center gap-1 text-xl font-bold text-primary-600">
                    <Star className="h-5 w-5 text-yellow-500" />
                    {entry.points}
                  </p>
                  <p className="text-sm text-gray-500">puntos</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
