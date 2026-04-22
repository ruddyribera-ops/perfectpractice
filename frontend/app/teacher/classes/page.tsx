'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { api } from '@/lib/api'
import { Plus, Users, Copy, CheckCircle } from 'lucide-react'

interface Class {
  id: number
  name: string
  subject: string
  invite_code: string
  created_at: string
  student_count?: number
  assignment_count?: number
}

export default function TeacherClassesPage() {
  const [classes, setClasses] = useState<Class[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [newClass, setNewClass] = useState({ name: '', subject: '' })
  const [creating, setCreating] = useState(false)
  const [copied, setCopied] = useState<string | null>(null)

  useEffect(() => {
    fetchClasses()
  }, [])

  const fetchClasses = async () => {
    try {
      const data = await api.get<Class[]>('/classes')
      // Enrich each class with student + assignment counts
      const enriched = await Promise.all(
        data.map(async (cls) => {
          try {
            const detail = await api.get<Class>(`/classes/${cls.id}`)
            return { ...cls, student_count: (detail as any).student_count ?? 0, assignment_count: (detail as any).assignment_count ?? 0 }
          } catch {
            return { ...cls, student_count: 0, assignment_count: 0 }
          }
        })
      )
      setClasses(enriched)
    } catch (error) {
      console.error('Error fetching classes:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    setCreating(true)
    try {
      const newClassData = await api.post<Class>('/classes', newClass)
      setClasses([...classes, newClassData])
      setShowCreate(false)
      setNewClass({ name: '', subject: '' })
    } catch (error) {
      console.error('Error creating class:', error)
    } finally {
      setCreating(false)
    }
  }

  const copyInviteCode = async (code: string) => {
    await navigator.clipboard.writeText(code)
    setCopied(code)
    setTimeout(() => setCopied(null), 2000)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Link href="/" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-500">/</span>
          <span className="font-medium">Mis Clases</span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Mis Clases</h1>
          <button
            onClick={() => setShowCreate(!showCreate)}
            className="btn-primary flex items-center gap-2"
          >
            <Plus className="h-5 w-5" />
            Nueva Clase
          </button>
        </div>

        {showCreate && (
          <div className="card mb-8">
            <h2 className="text-xl font-semibold mb-4">Crear Nueva Clase</h2>
            <form onSubmit={handleCreate} className="space-y-4">
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Nombre de la clase
                  </label>
                  <input
                    type="text"
                    value={newClass.name}
                    onChange={(e) => setNewClass({ ...newClass, name: e.target.value })}
                    className="input"
                    placeholder="Matemáticas 3° Básico A"
                    required
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Materia
                  </label>
                  <input
                    type="text"
                    value={newClass.subject}
                    onChange={(e) => setNewClass({ ...newClass, subject: e.target.value })}
                    className="input"
                    placeholder="Matemáticas"
                    required
                  />
                </div>
              </div>
              <div className="flex gap-4">
                <button type="submit" disabled={creating} className="btn-primary">
                  {creating ? 'Creando...' : 'Crear Clase'}
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreate(false)}
                  className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                >
                  Cancelar
                </button>
              </div>
            </form>
          </div>
        )}

        {classes.length === 0 ? (
          <div className="card text-center py-12">
            <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
            <h2 className="text-xl font-semibold mb-2">No tienes clases aún</h2>
            <p className="text-gray-600 mb-4">Crea tu primera clase para comenzar</p>
            <button
              onClick={() => setShowCreate(true)}
              className="btn-primary"
            >
              Crear Clase
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {classes.map((class_) => (
              <div key={class_.id} className="card">
                <h3 className="text-xl font-semibold mb-1">{class_.name}</h3>
                <p className="text-gray-600 text-sm mb-4">{class_.subject}</p>
                
                <div className="flex items-center gap-2 mb-4 p-3 bg-gray-50 rounded-lg">
                  <input
                    type="text"
                    value={class_.invite_code}
                    readOnly
                    className="flex-1 bg-transparent text-sm font-mono"
                  />
                  <button
                    onClick={() => copyInviteCode(class_.invite_code)}
                    className="text-primary-600 hover:text-primary-700"
                  >
                    {copied === class_.invite_code ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <Copy className="h-5 w-5" />
                    )}
                  </button>
                </div>

                <div className="flex gap-2">
                  <Link
                    href={`/teacher/classes/${class_.id}`}
                    className="flex-1 text-center px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                  >
                    Ver Clase
                  </Link>
                </div>

                <div className="mt-3 flex items-center justify-between text-xs text-gray-500 border-t pt-3">
                  <span className="flex items-center gap-1">
                    <Users className="h-3 w-3" />
                    {class_.student_count ?? 0} estudiantes
                  </span>
                  <span>
                    {class_.assignment_count ?? 0} tareas
                  </span>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
