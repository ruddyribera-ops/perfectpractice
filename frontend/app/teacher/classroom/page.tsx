'use client';
import { useEffect, useState } from 'react';
import { api, ClassroomCourse, ClassroomLink } from '@/lib/api';

export default function TeacherClassroomPage() {
  const [connected, setConnected] = useState(false);
  const [courses, setCourses] = useState<ClassroomCourse[]>([]);
  const [links, setLinks] = useState<ClassroomLink[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [linkingCourse, setLinkingCourse] = useState<string | null>(null);
  const [localClassId, setLocalClassId] = useState<number | null>(null);

  useEffect(() => {
    loadState();
  }, []);

  async function loadState() {
    try {
      const [linksData, myClasses] = await Promise.all([
        api.getClassroomLinks(),
        api.get<{classes: {id: number, name: string}[]}>('/me/classes'),
      ]);
      setLinks(linksData);
      setConnected(linksData.length > 0);
      // Default local class to first available
      if (myClasses.classes?.length && !localClassId) {
        setLocalClassId(myClasses.classes[0].id);
      }
    } catch {
      setConnected(false);
    }
  }

  async function connectGoogle() {
    setLoading(true);
    setError('');
    try {
      const { authorization_url } = await api.getClassroomAuthUrl();
      // Open OAuth in a popup or redirect
      window.location.href = authorization_url;
    } catch (e: any) {
      setError(e.message || 'No se pudo iniciar la conexión');
      setLoading(false);
    }
  }

  async function linkCourse(courseId: string) {
    if (!localClassId) {
      setError('Selecciona una clase primero');
      return;
    }
    setLinkingCourse(courseId);
    try {
      await api.linkClassroomCourse(courseId, localClassId);
      await loadState();
    } catch (e: any) {
      setError(e.message || 'Error al vincular');
    } finally {
      setLinkingCourse(null);
    }
  }

  async function unlink(syncId: number) {
    try {
      await api.unlinkClassroom(syncId);
      await loadState();
    } catch (e: any) {
      setError(e.message || 'Error al desvincular');
    }
  }

  async function fetchCourses() {
    setLoading(true);
    try {
      const courses = await api.getClassroomCourses();
      setCourses(courses);
    } catch (e: any) {
      setError(e.message || 'No se pudieron cargar los cursos');
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Google Classroom</h1>
      <p className="text-gray-500 mb-8">Conecta tu cuenta de Google Classroom para sincronizar tareas y temas.</p>

      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
          {error}
        </div>
      )}

      {/* Connection card */}
      <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
        <div className="flex items-center gap-4">
          <div className="text-4xl">🎓</div>
          <div className="flex-1">
            <h2 className="text-lg font-semibold">
              {connected ? '✅ Conectado a Google Classroom' : 'No conectado'}
            </h2>
            <p className="text-sm text-gray-500">
              {connected
                ? `${links.length} curso(s) vinculado(s)`
                : 'Vincula tu cuenta para sincronizar tareas con tus clases'}
            </p>
          </div>
          {!connected ? (
            <button
              onClick={connectGoogle}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 text-sm font-medium"
            >
              {loading ? 'Conectando...' : 'Conectar Google Classroom'}
            </button>
          ) : (
            <button
              onClick={fetchCourses}
              disabled={loading}
              className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 text-sm"
            >
              {loading ? 'Cargando...' : 'Ver cursos'}
            </button>
          )}
        </div>
      </div>

      {/* Course list */}
      {courses.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Cursos de Google Classroom</h3>
          <div className="space-y-3">
            {courses.map(course => {
              const isLinked = links.some(l => l.classroom_course_id === course.course_id);
              return (
                <div key={course.course_id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div>
                    <div className="font-medium text-gray-900">{course.name}</div>
                    <div className="text-xs text-gray-500">
                      {course.section ? `${course.section} · ` : ''}
                      {course.room ? `Sala: ${course.room}` : 'Sin sala'}
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {isLinked ? (
                      <>
                        <span className="text-sm text-green-600 font-medium">✓ Vinculado</span>
                        <button
                          onClick={() => {
                            const link = links.find(l => l.classroom_course_id === course.course_id);
                            if (link) unlink(link.id);
                          }}
                          className="text-sm text-red-500 hover:underline"
                        >
                          Desvincular
                        </button>
                      </>
                    ) : (
                      <>
                        <select
                          className="text-sm border border-gray-300 rounded px-2 py-1"
                          value={localClassId ?? ''}
                          onChange={e => setLocalClassId(Number(e.target.value))}
                        >
                          <option value="">Seleccionar clase</option>
                          <option value="1">1° Primaria A</option>
                          <option value="2">2° Primaria B</option>
                        </select>
                        <button
                          onClick={() => linkCourse(course.course_id)}
                          disabled={linkingCourse === course.course_id}
                          className="px-3 py-1 bg-primary-600 text-white text-sm rounded hover:bg-primary-700 disabled:opacity-50"
                        >
                          {linkingCourse === course.course_id ? 'Vinculando...' : 'Vincular'}
                        </button>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Current links */}
      {links.length > 0 && (
        <div className="bg-white border border-gray-200 rounded-xl p-6">
          <h3 className="text-lg font-semibold mb-4">Cursos vinculados</h3>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-gray-500 border-b">
                <th className="pb-2">Curso Google</th>
                <th className="pb-2">Clase local</th>
                <th className="pb-2">Fecha</th>
                <th className="pb-2"></th>
              </tr>
            </thead>
            <tbody>
              {links.map(link => (
                <tr key={link.id} className="border-b last:border-0">
                  <td className="py-3 font-medium">{link.classroom_course_name}</td>
                  <td className="py-3 text-gray-500">
                    {link.local_class_id ? `Clase #${link.local_class_id}` : '—'}
                  </td>
                  <td className="py-3 text-gray-400">{new Date(link.created_at).toLocaleDateString('es-BO')}</td>
                  <td className="py-3">
                    <button
                      onClick={() => unlink(link.id)}
                      className="text-red-500 hover:underline text-sm"
                    >
                      Eliminar
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}