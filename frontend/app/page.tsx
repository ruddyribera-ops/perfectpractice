'use client'

import { useState, useEffect, useContext } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { api, AchievementResponse, ProgressItem, MyClassItem } from '@/lib/api'
import NotificationBell from '@/components/notifications/NotificationBell'
import NotificationToast from '@/components/notifications/NotificationToast'
import { useNotificationPolling } from '@/hooks/useNotificationPolling'
import { Trophy, BookOpen, Users, Star, Flame, Snowflake, X, TrendingUp } from 'lucide-react'
import DarkModeToggle from './components/DarkModeToggle'
import MobileNav from './components/MobileNav'
import { LocaleContext, type Locale } from './providers'

export default function Home() {
  const { user, loading } = useAuth()
  const { locale, setLocale } = useContext(LocaleContext)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (user) {
    // Redirect non-students (teacher, parent, admin) to their respective dashboards
    if (user.role !== 'student') {
      if (user.role === 'parent') {
        window.location.href = '/parent'
      } else {
        // teacher or admin -> teacher dashboard at /teacher
        window.location.href = '/teacher'
      }
      return null
    }
    return (
      <div className="min-h-screen bg-gray-50">
        <header className="bg-white shadow-sm">
          <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
            <h1 className="text-2xl font-bold text-primary-600">Math Platform</h1>
            <div className="flex items-center gap-4">
              <NotificationBell />
              <select
                value={locale}
                onChange={e => setLocale(e.target.value as Locale)}
                style={{
                  padding: '6px 10px',
                  borderRadius: '8px',
                  border: '1px solid var(--border-color)',
                  background: 'var(--bg-card)',
                  color: 'var(--text-primary)',
                  fontSize: '13px',
                  cursor: 'pointer',
                }}
              >
                <option value="es-BO">🇧🇴 Español</option>
                <option value="en-US">🇺🇸 English</option>
                <option value="fr">🇫🇷 Français</option>
                <option value="pt-BR">🇧🇷 Português</option>
              </select>
              <DarkModeToggle compact />
              <span className="text-gray-600">¡Hola, {user.name}!</span>
              <button onClick={() => { localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); window.location.href = '/login'; }} className="text-gray-500 hover:text-gray-700">
                Cerrar sesión
              </button>
            </div>
          </nav>
        </header>

        <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <StudentDashboard />
        </main>
      </div>
    )
  }

  return <LandingPage />
}

function LandingPage() {
  return (
    <div className="min-h-screen">
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-primary-600">Math Platform</h1>
          <div className="flex gap-4">
            <Link href="/login" className="btn-primary">
              Iniciar sesión
            </Link>
            <Link href="/register" className="btn-secondary">
              Registrarse
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="py-20 bg-gradient-to-br from-primary-600 to-primary-800 text-white">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
            <h2 className="text-5xl font-bold mb-4">Aprende Matemáticas Jugando</h2>
            <p className="text-xl mb-8 text-primary-100">
              La plataforma educativa que hace las matemáticas divertidas para estudiantes bolivianos
            </p>
            <Link href="/register" className="bg-white text-primary-600 px-8 py-3 rounded-lg font-bold text-lg hover:bg-primary-50 transition">
              ¡Comienza Ahora!
            </Link>
          </div>
        </section>

        <section className="py-16">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <h3 className="text-3xl font-bold text-center mb-12">Características</h3>
            <div className="grid md:grid-cols-3 gap-8">
              <FeatureCard
                icon={<BookOpen className="h-12 w-12 text-primary-600" />}
                title="Contenido Khan Academy"
                description="Currículo completo de matemáticas para grados 1-6 basado en Khan Academy"
              />
              <FeatureCard
                icon={<Trophy className="h-12 w-12 text-secondary-500" />}
                title="Gamificación"
                description="Gana puntos, sube de nivel y desbloquea logros mientras aprendes"
              />
              <FeatureCard
                icon={<Users className="h-12 w-12 text-green-600" />}
                title="Para Docentes"
                description="Crea clases, asigna tareas y sigue el progreso de tus estudiantes"
              />
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}

function FeatureCard({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  return (
    <div className="card text-center">
      <div className="flex justify-center mb-4">{icon}</div>
      <h4 className="text-xl font-semibold mb-2">{title}</h4>
      <p className="text-gray-600">{description}</p>
    </div>
  )
}

function StudentDashboard() {
  const { user } = useAuth()
  const [stats, setStats] = useState<any>(null)
  const [streak, setStreak] = useState<any>(null)
  const [achievements, setAchievements] = useState<AchievementResponse[]>([])
  const [toasts, setToasts] = useState<AchievementResponse[]>([])
  const [usingFreeze, setUsingFreeze] = useState(false)
  const [freezeMsg, setFreezeMsg] = useState<string | null>(null)
  const [progressData, setProgressData] = useState<ProgressItem[]>([])
  const [myClasses, setMyClasses] = useState<MyClassItem[]>([])
  const { unreadCount, dismissToast, newToast } = useNotificationPolling()

  useEffect(() => {
    if (user) fetchStudentData()
  }, [user])

  const fetchStudentData = async () => {
    try {
      const [statsData, streakData, achievData, progress, classes] = await Promise.all([
        api.getStats(),
        api.getStreak(),
        api.getAchievements(),
        api.getProgress(),
        api.getMyClasses(),
      ])
      setStats(statsData)
      setStreak(streakData)
      setAchievements(achievData.slice(0, 3))
      setProgressData(progress ?? [])
      setMyClasses(classes ?? [])
    } catch (error) {
      console.error('Error fetching student data:', error)
    }
  }

  const handleUseFreeze = async () => {
    setUsingFreeze(true)
    setFreezeMsg(null)
    try {
      const result = await api.useStreakFreeze()
      setFreezeMsg(result.message)
      if (result.success) {
        setStreak((s: any) => ({ ...s, streak_freeze_available: result.freezes_remaining }))
        // Show any new achievements from the freeze
        if (result.new_achievements?.length > 0) {
          addToast(result.new_achievements[0])
        }
      }
    } catch (error) {
      setFreezeMsg('Error al usar hielo de racha')
    } finally {
      setUsingFreeze(false)
    }
  }

  const addToast = (achievement: AchievementResponse) => {
    setToasts(prev => [...prev, achievement])
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== achievement.id))
    }, 5000)
  }

  const xpProgress = stats ? ((stats.total_xp % 100) / 100) * 100 : 0

  return (
    <div className="space-y-8">
      {/* Toast notifications */}
      <div className="fixed top-4 right-4 z-50 space-y-2">
        {toasts.map(toast => (
          <div key={toast.id} className="flex items-center gap-3 bg-yellow-50 border border-yellow-300 rounded-xl px-4 py-3 shadow-lg animate-bounce-in min-w-64">
            <span className="text-3xl">{toast.icon}</span>
            <div>
              <p className="font-bold text-yellow-800">¡Nuevo Logro!</p>
              <p className="text-sm font-medium text-yellow-700">{toast.title}</p>
              <p className="text-xs text-yellow-600">{toast.description}</p>
            </div>
            <button onClick={() => setToasts(prev => prev.filter(t => t.id !== toast.id))} className="ml-auto text-yellow-400 hover:text-yellow-600">
              <X className="h-4 w-4" />
            </button>
          </div>
        ))}
      </div>

      {newToast && <NotificationToast notification={newToast} onClose={dismissToast} />}

      {/* Stats row */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatCard icon={<Star className="h-8 w-8 text-yellow-500" />} label="XP Total" value={stats?.total_xp ?? 0} />
        <StatCard icon={<Trophy className="h-8 w-8 text-primary-600" />} label="Nivel" value={stats?.level ?? 1} />
        <StatCard icon={<Flame className={`h-8 w-8 ${(streak?.current_streak ?? 0) > 0 ? 'text-orange-500 animate-streak-pulse' : 'text-gray-300'}`} />} label="Racha" value={`${streak?.current_streak ?? 0} días`} />
        <StatCard icon={<Snowflake className="h-8 w-8 text-cyan-400" />} label="Hielos" value={streak?.streak_freeze_available ?? 0} />
        <StatCard icon={<BookOpen className="h-8 w-8 text-green-500" />} label="Ejercicios" value={stats?.exercises_completed ?? 0} />
      </div>

      {/* Streak freeze alert */}
      {streak?.streak_at_risk && (
        <div className="card bg-cyan-50 border-cyan-200 flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <Snowflake className="h-6 w-6 text-cyan-500" />
            <div>
              <p className="font-semibold text-cyan-800">¡Tu racha está en riesgo!</p>
              <p className="text-sm text-cyan-600">Completa un ejercicio hoy para no perder tu racha de {streak?.current_streak} días</p>
            </div>
          </div>
          {(streak?.streak_freeze_available ?? 0) > 0 ? (
            <button
              onClick={handleUseFreeze}
              disabled={usingFreeze}
              className="btn-primary flex items-center gap-2 bg-cyan-600 hover:bg-cyan-700 disabled:opacity-50"
            >
              <Snowflake className="h-4 w-4" />
              {usingFreeze ? 'Usando...' : 'Usar hielo'}
            </button>
          ) : (
            <span className="text-sm text-cyan-500">Sin hielos disponibles</span>
          )}
        </div>
      )}

      {/* Freeze message */}
      {freezeMsg && (
        <div className={`card ${freezeMsg.includes('protegida') ? 'bg-green-50 border-green-200' : 'bg-red-50 border-red-200'}`}>
          <p className={freezeMsg.includes('protegida') ? 'text-green-700' : 'text-red-700'}>{freezeMsg}</p>
        </div>
      )}

      {/* XP Progress bar */}
      {stats && (
        <div className="card">
          <div className="flex items-center justify-between mb-2">
            <span className="font-semibold text-gray-700">Nivel {stats.level}</span>
            <span className="text-sm text-gray-500">{stats.xp_to_next_level} XP para siguiente nivel</span>
          </div>
          <div className="h-3 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-gradient-to-r from-yellow-400 to-orange-500 rounded-full transition-all duration-700 flex items-center justify-end pr-2" style={{ width: `${xpProgress}%` }}>
              <span className="text-xs font-bold text-white">{stats.total_xp % 100} XP</span>
            </div>
          </div>
        </div>
      )}

      <div className="card">
        <h2 className="text-2xl font-bold mb-4">Continúa Aprendiendo</h2>
        <div className="flex gap-3 flex-wrap">
          <Link href="/topics" className="btn-primary inline-block">
            Ver Temas
          </Link>
          <Link href="/me/history" className="btn-secondary inline-flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Mi Progreso
          </Link>
        </div>
      </div>

      {achievements.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">Logros Recientes</h2>
          <div className="flex gap-4 flex-wrap">
            {achievements.map((a) => (
              <div key={a.badge_key} className="flex items-center gap-2 p-3 bg-yellow-50 rounded-lg animate-bounce-in">
                <span className="text-2xl">{a.icon}</span>
                <div>
                  <p className="font-semibold">{a.title}</p>
                  <p className="text-sm text-gray-600">{a.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {progressData.length > 0 && (
        <div className="card">
          <h2 className="text-xl font-bold mb-4">📊 Mi Dominio por Tema</h2>
          <div className="flex flex-col gap-3">
            {progressData.slice(0, 6).map((topic) => (
              <div key={topic.topic_id}>
                <div className="flex justify-between mb-1">
                  <span className="text-sm font-medium text-gray-700">{topic.topic_title}</span>
                  <span className={`text-sm font-semibold ${
                    topic.mastery_score >= 80 ? 'text-green-600' :
                    topic.mastery_score >= 50 ? 'text-yellow-600' : 'text-gray-500'
                  }`}>
                    {Math.round(topic.mastery_score)}%
                  </span>
                </div>
                <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full transition-all ${
                      topic.mastery_score >= 80 ? 'bg-green-500' :
                      topic.mastery_score >= 50 ? 'bg-yellow-400' : 'bg-primary-500'
                    }`}
                    style={{ width: `${topic.mastery_score}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {myClasses.length > 0 && (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-bold">🏫 Mis Clases</h2>
            <Link href="/me/classes" className="text-sm text-primary-600 no-underline hover:underline">
              Ver todas →
            </Link>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {myClasses.slice(0, 4).map(cls => (
              <div key={cls.id} className="border border-gray-200 rounded-lg p-4">
                <div className="font-semibold text-sm text-gray-900 mb-1">{cls.name}</div>
                {cls.subject && <div className="text-xs text-gray-500">{cls.subject}</div>}
                <div className="text-xs text-gray-400 mt-2">
                  {cls.enrolled_at ? new Date(cls.enrolled_at).toLocaleDateString('es-BO') : ''}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      <MobileNav />
      <div style={{ height: '80px' }} />
    </div>
  )
}

function TeacherDashboard() {
  return (
    <div className="space-y-8">
      <div className="card">
        <h2 className="text-2xl font-bold mb-4">Panel de Docente</h2>
        <div className="grid md:grid-cols-2 gap-4">
          <Link href="/teacher/classes" className="p-4 border rounded-lg hover:bg-gray-50">
            <h3 className="font-semibold text-lg">Mis Clases</h3>
            <p className="text-gray-600">Gestiona tus clases y estudiantes</p>
          </Link>
          <Link href="/leaderboard" className="p-4 border rounded-lg hover:bg-gray-50">
            <h3 className="font-semibold text-lg">Tabla de Posiciones</h3>
            <p className="text-gray-600">Ver rankings globales y de clase</p>
          </Link>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return (
    <div className="card flex items-center gap-4">
      {icon}
      <div>
        <p className="text-sm text-gray-600">{label}</p>
        <p className="text-2xl font-bold">{value}</p>
      </div>
    </div>
  )
}
