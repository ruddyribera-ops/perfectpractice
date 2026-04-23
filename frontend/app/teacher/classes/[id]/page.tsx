'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api, StudentProgress, AssignmentItem, TopicWithExercises } from '@/lib/api'
import { ArrowLeft, Users, FileText, Plus, X, Star, Flame, Clock } from 'lucide-react'

type Tab = 'students' | 'assignments'

export default function ClassDetailPage() {
  const params = useParams()
  const classId = parseInt(params.id as string)
  const [activeTab, setActiveTab] = useState<Tab>('students')
  const [classDetail, setClassDetail] = useState<any>(null)
  const [students, setStudents] = useState<StudentProgress[]>([])
  const [assignments, setAssignments] = useState<AssignmentItem[]>([])
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [pickerTree, setPickerTree] = useState<TopicWithExercises[]>([])
  const [selectedExercises, setSelectedExercises] = useState<number[]>([])
  const [assignmentForm, setAssignmentForm] = useState({ title: '', description: '', due_date: '' })
  const [creating, setCreating] = useState(false)
  const [pickerLoading, setPickerLoading] = useState(false)

  useEffect(() => {
    if (classId) {
      loadAll()
    }
  }, [classId])

  async function loadAll() {
    setLoading(true)
    try {
      const [cls, studs, assigns] = await Promise.all([
        api.getClassDetail(classId),
        api.getClassStudents(classId),
        api.getClassAssignments(classId),
      ])
      setClassDetail(cls)
      setStudents(studs)
      setAssignments(assigns)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  function openCreateModal() {
    setShowCreate(true)
    setPickerLoading(true)
    api.getTopicPickerTree()
      .then(setPickerTree)
      .catch((e: any) => console.error('Error:', e))
      .finally(() => setPickerLoading(false))
  }

  function toggleExercise(id: number) {
    setSelectedExercises(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  async function handleCreateAssignment() {
    if (!assignmentForm.title.trim() || selectedExercises.length === 0) return
    setCreating(true)
    try {
      const created = await api.createAssignment(classId, {
        title: assignmentForm.title,
        description: assignmentForm.description || undefined,
        exercise_ids: selectedExercises,
        due_date: assignmentForm.due_date || undefined,
      })
      setAssignments(prev => [created, ...prev])
      setShowCreate(false)
      setAssignmentForm({ title: '', description: '', due_date: '' })
      setSelectedExercises([])
    } catch (e) {
      console.error('Error creating assignment:', e)
    } finally {
      setCreating(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Link href="/teacher/classes" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-400">/</span>
          <Link href="/teacher/classes" className="text-gray-500 hover:text-gray-700">Mis Clases</Link>
          <span className="text-gray-400">/</span>
          <span className="font-medium text-gray-900">{classDetail?.name}</span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="card mb-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{classDetail?.name}</h1>
              <p className="text-gray-600 mt-1">{classDetail?.subject}</p>
              <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                <span className="flex items-center gap-1"><Users className="h-4 w-4" />{students.length} estudiantes</span>
                <span className="flex items-center gap-1"><FileText className="h-4 w-4" />{assignments.length} tareas</span>
                <span className="font-mono bg-gray-100 px-2 py-0.5 rounded">Codigo: {classDetail?.invite_code}</span>
              </div>
            </div>
            <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
              <Plus className="h-5 w-5" />Nueva Tarea
            </button>
          </div>
        </div>

        <div className="flex gap-1 border-b border-gray-200 mb-6">
          <button onClick={() => setActiveTab('students')} className={`px-4 py-3 text-sm font-medium ${activeTab === 'students' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500'}`}>
            <Users className="h-4 w-4 inline mr-1" />Estudiantes
          </button>
          <button onClick={() => setActiveTab('assignments')} className={`px-4 py-3 text-sm font-medium ${activeTab === 'assignments' ? 'border-b-2 border-primary-600 text-primary-600' : 'text-gray-500'}`}>
            <FileText className="h-4 w-4 inline mr-1" />Tareas
          </button>
        </div>

        {activeTab === 'students' && (
          <div>
            {students.length === 0 ? (
              <div className="card text-center py-12">
                <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No hay estudiantes inscritos</p>
              </div>
            ) : (
              <div className="card overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estudiante</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grado</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">XP</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Racha</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dominio</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {students.map(s => (
                      <tr key={s.student_id} className="hover:bg-gray-50">
                        <td className="px-6 py-4">
                          <p className="font-medium text-gray-900">{s.name}</p>
                          <p className="text-xs text-gray-500">{s.email}</p>
                        </td>
                        <td className="px-6 py-4 text-sm text-gray-700">{s.grade}</td>
                        <td className="px-6 py-4 text-sm">
                          <span className="flex items-center gap-1"><Star className="h-3.5 w-3.5 text-yellow-500" />{s.points} XP</span>
                        </td>
                        <td className="px-6 py-4">
                          <span className="flex items-center gap-1"><Flame className={`h-4 w-4 ${s.current_streak > 0 ? 'text-orange-500' : 'text-gray-300'}`} />{s.current_streak} dias</span>
                        </td>
                        <td className="px-6 py-4 text-sm">{Math.round((s.avg_mastery || 0) * 100)}%</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {activeTab === 'assignments' && (
          <div>
            {assignments.length === 0 ? (
              <div className="card text-center py-12">
                <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No hay tareas</p>
                <button onClick={openCreateModal} className="btn-primary mt-4">Crear primera tarea</button>
              </div>
            ) : (
              <div className="space-y-3">
                {assignments.map(a => (
                  <div key={a.id} className="card flex items-center justify-between py-4">
                    <div>
                      <h3 className="font-semibold text-gray-900">{a.title}</h3>
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                        <span className="flex items-center gap-1"><Clock className="h-3 w-3" />{a.due_date ? new Date(a.due_date).toLocaleDateString('es-BO') : 'Sin fecha'}</span>
                      </div>
                    </div>
                    <Link href={`/teacher/classes/${classId}/assignments/${a.id}/results`} className="btn-primary text-sm">Ver resultados</Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-xl font-bold">Crear Nueva Tarea</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600"><X className="h-5 w-5" /></button>
            </div>
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Titulo *</label>
                <input type="text" value={assignmentForm.title} onChange={e => setAssignmentForm(f => ({ ...f, title: e.target.value }))} className="input w-full" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Descripcion</label>
                <textarea value={assignmentForm.description} onChange={e => setAssignmentForm(f => ({ ...f, description: e.target.value }))} className="input w-full" rows={2} />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Fecha limite</label>
                <input type="date" value={assignmentForm.due_date} onChange={e => setAssignmentForm(f => ({ ...f, due_date: e.target.value }))} className="input w-full" />
              </div>
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">Ejercicios ({selectedExercises.length})</p>
                {pickerLoading ? (
                  <div className="flex justify-center py-8"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" /></div>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto border rounded-lg p-3">
                    {pickerTree.map(topic => (
                      <div key={topic.id}>
                        <p className="text-xs font-bold text-gray-500 uppercase">{topic.title}</p>
                        {topic.units.map(unit => (
                          <div key={unit.id} className="ml-2">
                            <p className="text-xs font-semibold text-gray-600">{unit.title}</p>
                            {unit.exercises.map((ex: any) => (
                              <label key={ex.id} className="flex items-center gap-2 p-1 cursor-pointer text-sm">
                                <input type="checkbox" checked={selectedExercises.includes(ex.id)} onChange={() => toggleExercise(ex.id)} className="rounded" />
                                <span>{ex.title}</span>
                              </label>
                            ))}
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">Cancelar</button>
              <button onClick={handleCreateAssignment} disabled={!assignmentForm.title.trim() || selectedExercises.length === 0 || creating} className="btn-primary disabled:opacity-50">
                {creating ? 'Creando...' : `Crear (${selectedExercises.length})`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
