'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api, StudentProgress, AssignmentItem, TopicWithExercises } from '@/lib/api'
import {
  ArrowLeft, Users, FileText, Plus, X,
  Star, Flame, TrendingUp, CheckCircle, Clock, ChevronDown, ChevronUp,
} from 'lucide-react'

type Tab = 'students' | 'assignments'

export default function ClassDetailPage() {
  const params = useParams()
  const classId = parseInt(params.id as string)

  const [activeTab, setActiveTab] = useState<Tab>('students')
  const [classDetail, setClassDetail] = useState<any>(null)
  const [students, setStudents] = useState<StudentProgress[]>([])
  const [assignments, setAssignments] = useState<AssignmentItem[]>([])
  const [loading, setLoading] = useState(true)

  // Create assignment modal state
  const [showCreate, setShowCreate] = useState(false)
  const [pickerTree, setPickerTree] = useState<TopicWithExercises[]>([])
  const [selectedTopic, setSelectedTopic] = useState<number | null>(null)
  const [selectedUnit, setSelectedUnit] = useState<number | null>(null)
  const [selectedExercises, setSelectedExercises] = useState<number[]>([])
  const [assignmentForm, setAssignmentForm] = useState({ title: '', description: '', due_date: '' })
  const [creating, setCreating] = useState(false)
  const [pickerLoading, setPickerLoading] = useState(false)
  const [gcSyncEnabled, setGcSyncEnabled] = useState(false)
  const [gcSyncId, setGcSyncId] = useState<number | null>(null)
  const [gcLinks, setGcLinks] = useState<{id: number, local_class_id: number | null}[]>([])
  const [gcTopics, setGcTopics] = useState<{topic_id: string, name: string}[]>([])
  const [selectedGcTopic, setSelectedGcTopic] = useState<string>('')
  const [syncingAssignment, setSyncingAssignment] = useState(false)

  useEffect(() => {
    if (classId) loadAll()
  }, [classId])

  const loadAll = async () => {
    setLoading(true)
    try {
      const [cls, studs, assigns, links] = await Promise.all([
        api.getClassDetail(classId),
        api.getClassStudents(classId),
        api.getClassAssignments(classId),
        api.getClassroomLinks().catch(() => []),
      ])
      setClassDetail(cls)
      setStudents(studs)
      setAssignments(assigns)
      setGcLinks(links)
      // Auto-select sync link if this class is linked
      const linkForClass = (links as any[]).find((l: any) => l.local_class_id === classId)
      if (linkForClass) {
        setGcSyncId(linkForClass.id)
        setGcSyncEnabled(true)
        // Fetch topics for that course
        api.getClassroomTopics(linkForClass.classroom_course_id)
          .then(setGcTopics)
          .catch(() => {})
      }
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  const openCreateModal = async () => {
    setShowCreate(true)
    setPickerLoading(true)
    try {
      const tree = await api.getTopicPickerTree()
      setPickerTree(tree)
    } catch (e) {
      console.error('Error loading picker tree:', e)
    } finally {
      setPickerLoading(false)
    }
  }

  const toggleExercise = (id: number) => {
    setSelectedExercises(prev =>
      prev.includes(id) ? prev.filter(x => x !== id) : [...prev, id]
    )
  }

  const handleCreateAssignment = async () => {
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
      setSelectedTopic(null)
      setSelectedUnit(null)
      setSelectedGcTopic('')

      // Sync to Google Classroom if enabled
      if (gcSyncEnabled && gcSyncId) {
        setSyncingAssignment(true)
        try {
          await api.syncAssignmentToClassroom(gcSyncId, created.id, selectedGcTopic || undefined)
        } catch (e) {
          console.error('GC sync error:', e)
        } finally {
          setSyncingAssignment(false)
        }
      }
    } catch (e) {
      console.error('Error creating assignment:', e)
    } finally {
      setCreating(false)
    }
  }

  // XP progress within current level: each level needs 100 XP
  const xpInLevel = (points: number) => points % 100
  const xpToNextLevel = (points: number) => 100 - (points % 100)

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600" />
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
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
        {/* Class Info Banner */}
        <div className="card mb-6">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{classDetail?.name}</h1>
              <p className="text-gray-600 mt-1">{classDetail?.subject}</p>
              <div className="flex items-center gap-4 mt-3 text-sm text-gray-500">
                <span className="flex items-center gap-1">
                  <Users className="h-4 w-4" />
                  {students.length} estudiantes
                </span>
                <span className="flex items-center gap-1">
                  <FileText className="h-4 w-4" />
                  {assignments.length} tareas
                </span>
                <span className="flex items-center gap-1 font-mono bg-gray-100 px-2 py-0.5 rounded">
                  Código: {classDetail?.invite_code}
                </span>
              </div>
            </div>
            <button
              onClick={() => setShowCreate(true)}
              className="btn-primary flex items-center gap-2"
            >
              <Plus className="h-5 w-5" />
              Nueva Tarea
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 border-b border-gray-200 mb-6">
          {(['students', 'assignments'] as Tab[]).map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'border-b-2 border-primary-600 text-primary-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              {tab === 'students' ? (
                <span className="flex items-center gap-2">
                  <Users className="h-4 w-4" /> Estudiantes
                </span>
              ) : (
                <span className="flex items-center gap-2">
                  <FileText className="h-4 w-4" /> Tareas
                </span>
              )}
            </button>
          ))}
        </div>

        {/* ── Students Tab ── */}
        {activeTab === 'students' && (
          <div>
            {students.length === 0 ? (
              <div className="card text-center py-12">
                <Users className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No hay estudiantes inscritos</p>
                <p className="text-sm text-gray-500 mt-1">Comparte el código de invitación</p>
                <code className="mt-2 inline-block bg-gray-100 px-3 py-1 rounded font-mono text-sm">
                  {classDetail?.invite_code}
                </code>
              </div>
            ) : (
              <div className="card overflow-hidden">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Estudiante</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Grado</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">XP / Nivel</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Racha</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Dominio</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Última Actividad</th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Ejercicios</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {students.map(student => {
                      const xpCurrent = xpInLevel(student.points)
                      const xpNeeded = xpToNextLevel(student.points)
                      return (
                        <tr key={student.student_id} className="hover:bg-gray-50">
                          <td className="px-6 py-4">
                            <p className="font-medium text-gray-900">{student.name}</p>
                            <p className="text-xs text-gray-500">{student.email}</p>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700">{student.grade}°</td>
                          <td className="px-6 py-4 min-w-48">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="flex items-center gap-1 text-sm">
                                <Star className="h-3.5 w-3.5 text-yellow-500" />
                                <span className="font-medium">{student.points} XP</span>
                              </span>
                              <span className="badge badge-primary text-xs">Nivel {student.level}</span>
                            </div>
                            {/* XP progress bar within current level */}
                            <div className="w-36 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                              <div
                                className="h-full bg-yellow-400 rounded-full transition-all"
                                style={{ width: `${xpCurrent}%` }}
                              />
                            </div>
                            <p className="text-xs text-gray-400 mt-0.5">{xpNeeded} XP para siguiente nivel</p>
                          </td>
                          <td className="px-6 py-4">
                            <span className="flex items-center gap-1.5">
                              <Flame className={`h-4 w-4 ${student.current_streak > 0 ? 'text-orange-500' : 'text-gray-300'}`} />
                              <span className={`text-sm font-medium ${student.current_streak > 0 ? 'text-orange-600' : 'text-gray-400'}`}>
                                {student.current_streak} días
                              </span>
                            </span>
                          </td>
                          <td className="px-6 py-4">
                            <div className="flex items-center gap-2">
                              <div className="w-28 h-2 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className="h-full bg-green-500 rounded-full transition-all"
                                  style={{ width: `${Math.round(student.avg_mastery * 100)}%` }}
                                />
                              </div>
                              <span className="text-sm text-gray-600 w-10">
                                {Math.round(student.avg_mastery * 100)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-6 py-4 text-sm text-gray-700">
                            {student.last_active ? (
                              (() => {
                                const d = new Date(student.last_active)
                                const today = new Date()
                                const diffDays = Math.floor((today.getTime() - d.getTime()) / 86400000)
                                if (diffDays === 0) return 'Hoy'
                                if (diffDays === 1) return 'Ayer'
                                if (diffDays < 7) return `Hace ${diffDays} días`
                                return d.toLocaleDateString('es-BO', { day: 'numeric', month: 'short' })
                              })()
                            ) : (
                              <span className="text-gray-400">—</span>
                            )}
                          </td>
                          <td className="px-6 py-4 text-sm font-semibold text-gray-700">
                            {student.exercises_completed ?? 0}
                          </td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {/* ── Assignments Tab ── */}
        {activeTab === 'assignments' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <p className="text-gray-600">{assignments.length} tarea{assignments.length !== 1 ? 's' : ''} creada{assignments.length !== 1 ? 's' : ''}</p>
              <button onClick={openCreateModal} className="btn-primary flex items-center gap-2">
                <Plus className="h-5 w-5" /> Nueva Tarea
              </button>
            </div>

            {assignments.length === 0 ? (
              <div className="card text-center py-12">
                <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">No hay tareas para esta clase</p>
                <button onClick={openCreateModal} className="btn-primary mt-4">
                  Crear primera tarea
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {assignments.map(a => (
                  <div key={a.id} className="card flex items-center justify-between py-4">
                    <div>
                      <h3 className="font-semibold text-gray-900">{a.title}</h3>
                      {a.description && <p className="text-sm text-gray-500 mt-0.5">{a.description}</p>}
                      <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
                        <span className="flex items-center gap-1">
                          <Clock className="h-3 w-3" />
                          {a.due_date ? `Vence ${new Date(a.due_date).toLocaleDateString('es-BO')}` : 'Sin fecha límite'}
                        </span>
                        <span className="flex items-center gap-1">
                          <FileText className="h-3 w-3" />
                          {a.created_at ? `Creada ${new Date(a.created_at).toLocaleDateString('es-BO')}` : ''}
                        </span>
                      </div>
                    </div>
                    <Link
                      href={`/teacher/classes/${classId}/assignments/${a.id}/results`}
                      className="btn-primary text-sm"
                    >
                      Ver resultados
                    </Link>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>

      {/* ── Create Assignment Modal ── */}
      {showCreate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl w-full max-w-2xl max-h-[90vh] flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b">
              <h2 className="text-xl font-bold">Crear Nueva Tarea</h2>
              <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600">
                <X className="h-5 w-5" />
              </button>
            </div>

            {/* Modal Body */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-5">
              {/* Title + Description */}
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Título de la tarea *</label>
                  <input
                    type="text"
                    value={assignmentForm.title}
                    onChange={e => setAssignmentForm(f => ({ ...f, title: e.target.value }))}
                    className="input w-full"
                    placeholder="Ej: Suma y resta hasta 100"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Descripción</label>
                  <textarea
                    value={assignmentForm.description}
                    onChange={e => setAssignmentForm(f => ({ ...f, description: e.target.value }))}
                    className="input w-full"
                    rows={2}
                    placeholder="Descripción opcional..."
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Fecha límite</label>
                  <input
                    type="date"
                    value={assignmentForm.due_date}
                    onChange={e => setAssignmentForm(f => ({ ...f, due_date: e.target.value }))}
                    className="input w-full"
                  />
                </div>

                {/* Google Classroom Sync */}
                {gcSyncEnabled && gcSyncId && (
                  <div className="border border-blue-200 bg-blue-50 rounded-lg p-4 space-y-3">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="gc-sync-check"
                        checked={gcSyncEnabled}
                        onChange={e => setGcSyncEnabled(e.target.checked)}
                        className="rounded"
                      />
                      <label htmlFor="gc-sync-check" className="text-sm font-medium text-blue-800">
                        📚 Sincronizar con Google Classroom
                      </label>
                    </div>
                    {gcSyncEnabled && gcTopics.length > 0 && (
                      <div>
                        <label className="block text-xs text-blue-700 mb-1">Tema de Google Classroom (opcional)</label>
                        <select
                          className="w-full text-sm border border-blue-300 rounded px-2 py-1"
                          value={selectedGcTopic}
                          onChange={e => setSelectedGcTopic(e.target.value)}
                        >
                          <option value="">Sin tema específico</option>
                          {gcTopics.map(t => (
                            <option key={t.topic_id} value={t.topic_id}>{t.name}</option>
                          ))}
                        </select>
                      </div>
                    )}
                    <p className="text-xs text-blue-600">La tarea se publicará en Google Classroom al crearla.</p>
                  </div>
                )}

                {/* Exercise Picker */}
              <div>
                <p className="text-sm font-medium text-gray-700 mb-2">
                  Selecciona ejercicios * ({selectedExercises.length} seleccionado{selectedExercises.length !== 1 ? 's' : ''})
                </p>

                {pickerLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600" />
                  </div>
                ) : (
                  <div className="space-y-3 max-h-80 overflow-y-auto border rounded-lg p-3">
                    {pickerTree.map(topic => (
                      <div key={topic.id}>
                        <div className="text-xs font-bold text-gray-500 uppercase mb-2 mt-3 first:mt-0">
                          {topic.title}
                        </div>
                        {topic.units.map(unit => (
                          <div key={unit.id} className="ml-2 mb-2">
                            <div className="text-xs font-semibold text-gray-600 mb-1">{unit.title}</div>
                            <div className="grid grid-cols-1 gap-1">
                              {unit.exercises.map(ex => (
                                <label
                                  key={ex.id}
                                  className={`flex items-center gap-2 p-2 rounded cursor-pointer text-sm transition-colors ${
                                    selectedExercises.includes(ex.id)
                                      ? 'bg-primary-50 border border-primary-300 text-primary-700'
                                      : 'hover:bg-gray-50 border border-transparent'
                                  }`}
                                >
                                  <input
                                    type="checkbox"
                                    checked={selectedExercises.includes(ex.id)}
                                    onChange={() => toggleExercise(ex.id)}
                                    className="rounded"
                                  />
                                  <span className="flex-1">{ex.title}</span>
                                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                                    ex.difficulty === 'easy' ? 'bg-green-100 text-green-700' :
                                    ex.difficulty === 'medium' ? 'bg-yellow-100 text-yellow-700' :
                                    'bg-red-100 text-red-700'
                                  }`}>
                                    {ex.difficulty === 'easy' ? 'F' : ex.difficulty === 'medium' ? 'M' : 'D'}
                                  </span>
                                  <span className="text-xs text-gray-400">{ex.points_value} pts</span>
                                </label>
                              ))}
                            </div>
                          </div>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>

            {/* Modal Footer */}
            <div className="flex items-center justify-end gap-3 px-6 py-4 border-t">
              <button onClick={() => setShowCreate(false)} className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50">
                Cancelar
              </button>
              <button
                onClick={handleCreateAssignment}
                disabled={!assignmentForm.title.trim() || selectedExercises.length === 0 || creating}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {creating ? 'Creando...' : `Crear Tarea (${selectedExercises.length} ejercicios)`}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
