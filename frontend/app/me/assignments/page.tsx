'use client';
import { useEffect, useState } from 'react';
import { api, MyAssignmentItem } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function MyAssignmentsPage() {
  const [assignments, setAssignments] = useState<MyAssignmentItem[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    api.getMyAssignments()
      .then(data => { setAssignments(data.items); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  const getStatusColor = (item: MyAssignmentItem) => {
    if (item.completed_at) return '#22c55e';
    if (item.due_date && new Date(item.due_date) < new Date()) return '#ef4444';
    if (item.completion_rate > 0) return '#eab308';
    return '#6b7280';
  };

  const getStatusLabel = (item: MyAssignmentItem) => {
    if (item.completed_at) return 'Completada';
    if (item.due_date && new Date(item.due_date) < new Date()) return 'Vencida';
    if (item.completion_rate >= 1) return 'Completada';
    if (item.completion_rate > 0) return 'En progreso';
    return 'No iniciada';
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '64px 0', color: '#666' }}>
        Cargando tareas...
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '720px', margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '24px' }}>Mis Tareas</h1>

      {assignments.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#999' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>📋</div>
          <div>No tienes tareas asignadas todavía.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {assignments.map(item => (
            <Link key={item.id} href={`/me/assignments/${item.id}`} style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'white',
                border: '1px solid #e5e7eb',
                borderRadius: '12px',
                padding: '16px 20px',
                transition: 'all 0.2s',
                cursor: 'pointer',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '8px' }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: '15px', color: '#111' }}>{item.title}</div>
                    <div style={{ fontSize: '13px', color: '#666', marginTop: '2px' }}>{item.class_name}</div>
                  </div>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    padding: '3px 10px',
                    borderRadius: '12px',
                    background: getStatusColor(item) + '20',
                    color: getStatusColor(item),
                  }}>
                    {getStatusLabel(item)}
                  </span>
                </div>

                {item.description && (
                  <div style={{ fontSize: '13px', color: '#666', marginBottom: '8px' }}>
                    {item.description}
                  </div>
                )}

                <div style={{ display: 'flex', gap: '16px', alignItems: 'center' }}>
                  {/* Completion bar */}
                  <div style={{ flex: 1, height: '6px', background: '#f3f4f6', borderRadius: '3px', overflow: 'hidden' }}>
                    <div style={{
                      width: `${(item.completion_rate || 0) * 100}%`,
                      height: '100%',
                      background: item.completion_rate >= 1 ? '#22c55e' : '#3b82f6',
                      borderRadius: '3px',
                      transition: 'width 0.3s',
                    }} />
                  </div>
                  <span style={{ fontSize: '12px', color: '#666', minWidth: '40px', textAlign: 'right' }}>
                    {Math.round((item.completion_rate || 0) * 100)}%
                  </span>
                  {item.due_date && (
                    <span style={{ fontSize: '12px', color: new Date(item.due_date) < new Date() && !item.completed_at ? '#ef4444' : '#888' }}>
                      📅 {new Date(item.due_date).toLocaleDateString('es-BO')}
                    </span>
                  )}
                  {item.score !== null && (
                    <span style={{ fontSize: '12px', color: '#666' }}>
                      ⭐ {item.score}
                    </span>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}

      <div style={{ marginTop: '24px', textAlign: 'center' }}>
        <Link href="/me/history" style={{ color: '#3b82f6', fontSize: '14px', textDecoration: 'none' }}>
          → Ver mi historial de ejercicios
        </Link>
      </div>
    </div>
  );
}