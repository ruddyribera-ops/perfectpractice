'use client';
import { useEffect, useState } from 'react';
import { api, StudentAssignmentDetail, ExerciseInAssignment } from '@/lib/api';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';

export default function AssignmentDetailPage() {
  const params = useParams();
  const router = useRouter();
  const id = Number(params.id);

  const [assignment, setAssignment] = useState<StudentAssignmentDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (isNaN(id)) return;
    api.getMyAssignmentDetail(id)
      .then(data => { setAssignment(data); setLoading(false); })
      .catch(() => setLoading(false));
  }, [id]);

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0', color: '#666' }}>
        Cargando...
      </div>
    );
  }

  if (!assignment) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0', color: '#666' }}>
        Tarea no encontrada.
      </div>
    );
  }

  const completedCount = assignment.exercises.filter(e => e.status === 'correct').length;
  const totalCount = assignment.exercises.length;
  const allDone = completedCount === totalCount && totalCount > 0;

  const getStatusIcon = (status: ExerciseInAssignment['status']) => {
    switch (status) {
      case 'correct': return '✅';
      case 'incorrect': return '❌';
      case 'in_progress': return '🔄';
      default: return '⭕';
    }
  };

  const getStatusColor = (status: ExerciseInAssignment['status']) => {
    switch (status) {
      case 'correct': return '#22c55e';
      case 'incorrect': return '#ef4444';
      case 'in_progress': return '#eab308';
      default: return '#e5e7eb';
    }
  };

  const difficultyColor = (d: string) => {
    switch (d) {
      case 'easy': return '#22c55e';
      case 'medium': return '#eab308';
      case 'hard': return '#ef4444';
      default: return '#6b7280';
    }
  };

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', padding: '24px 16px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <Link href="/me/assignments" style={{ color: '#3b82f6', fontSize: '14px', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}>
          ← Volver a Mis Tareas
        </Link>
      </div>

      <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '16px', padding: '24px', marginBottom: '24px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
          <div>
            <h1 style={{ fontSize: '22px', fontWeight: 700, margin: 0 }}>{assignment.title}</h1>
            <div style={{ fontSize: '14px', color: '#666', marginTop: '4px' }}>{assignment.class_name}</div>
          </div>
          {allDone && (
            <span style={{ background: '#22c55e20', color: '#22c55e', padding: '4px 12px', borderRadius: '20px', fontSize: '13px', fontWeight: 600 }}>
              🎉 Completada
            </span>
          )}
        </div>

        {assignment.description && (
          <p style={{ fontSize: '14px', color: '#666', margin: '0 0 16px' }}>{assignment.description}</p>
        )}

        {assignment.due_date && (
          <div style={{ fontSize: '13px', color: new Date(assignment.due_date) < new Date() && !allDone ? '#ef4444' : '#888', marginBottom: '16px' }}>
            📅 Fecha límite: {new Date(assignment.due_date).toLocaleDateString('es-BO', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        )}

        {/* Progress bar */}
        <div style={{ marginBottom: '8px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', color: '#666', marginBottom: '6px' }}>
            <span>Progreso</span>
            <span>{completedCount}/{totalCount} ejercicios</span>
          </div>
          <div style={{ height: '10px', background: '#f3f4f6', borderRadius: '5px', overflow: 'hidden' }}>
            <div style={{
              width: `${(assignment.completion_rate || 0) * 100}%`,
              height: '100%',
              background: allDone ? '#22c55e' : '#3b82f6',
              borderRadius: '5px',
              transition: 'width 0.4s',
            }} />
          </div>
        </div>

        {assignment.score !== null && (
          <div style={{ fontSize: '14px', color: '#666', marginTop: '8px' }}>
            ⭐ Puntaje: <strong>{assignment.score}</strong>
          </div>
        )}
      </div>

      {/* Exercise list */}
      <h2 style={{ fontSize: '16px', fontWeight: 700, marginBottom: '16px' }}>Ejercicios</h2>

      {assignment.exercises.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '32px', color: '#999', background: 'white', borderRadius: '12px', border: '1px solid #e5e7eb' }}>
          No hay ejercicios asignados en esta tarea.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
          {assignment.exercises.map((exercise, index) => (
            <Link
              key={exercise.id}
              href={`/exercises/${exercise.id}${assignment.id ? `?assignment_id=${assignment.id}` : ''}`}
              style={{ textDecoration: 'none' }}
            >
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                padding: '14px 16px',
                background: 'white',
                border: '1px solid',
                borderColor: exercise.status === 'correct' ? '#bbf7d0' : '#e5e7eb',
                borderRadius: '10px',
                cursor: 'pointer',
                transition: 'all 0.15s',
              }}>
                {/* Status icon */}
                <span style={{ fontSize: '22px' }}>{getStatusIcon(exercise.status)}</span>

                {/* Order + title */}
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '14px', fontWeight: 500, color: '#111' }}>
                    {index + 1}. {exercise.title}
                  </div>
                  <div style={{ display: 'flex', gap: '8px', marginTop: '4px' }}>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: getStatusColor(exercise.status) + '20',
                      color: getStatusColor(exercise.status),
                    }}>
                      {exercise.status === 'not_started' ? 'No iniciado' :
                       exercise.status === 'in_progress' ? 'En progreso' :
                       exercise.status === 'correct' ? 'Correcto' : 'Incorrecto'}
                    </span>
                    <span style={{
                      fontSize: '11px',
                      padding: '2px 8px',
                      borderRadius: '10px',
                      background: difficultyColor(exercise.difficulty) + '20',
                      color: difficultyColor(exercise.difficulty),
                    }}>
                      {exercise.difficulty === 'easy' ? 'Fácil' : exercise.difficulty === 'medium' ? 'Medio' : 'Difícil'}
                    </span>
                  </div>
                </div>

                {/* Arrow */}
                <span style={{ color: '#9ca3af', fontSize: '18px' }}>→</span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {allDone && (
        <div style={{ marginTop: '24px', textAlign: 'center', padding: '24px', background: '#f0fdf4', border: '1px solid #bbf7d0', borderRadius: '12px' }}>
          <div style={{ fontSize: '32px', marginBottom: '8px' }}>🎉</div>
          <div style={{ fontWeight: 700, color: '#166534', fontSize: '16px' }}>¡Tarea completada!</div>
          <div style={{ color: '#166534', fontSize: '14px', marginTop: '4px' }}>Has resuelto correctamente todos los ejercicios.</div>
          <div style={{ marginTop: '16px' }}>
            <Link href="/me/assignments" style={{ color: '#3b82f6', fontSize: '14px', textDecoration: 'none' }}>
              ← Ver otras tareas
            </Link>
          </div>
        </div>
      )}
    </div>
  );
}