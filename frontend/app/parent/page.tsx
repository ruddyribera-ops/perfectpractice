'use client';
import { useEffect, useState, useRef } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';
import type { ParentDashboardResponse, ParentActivity, LinkedStudent } from '@/lib/api';

const DIFFICULTY_LABEL: Record<string, { label: string; color: string }> = {
  easy: { label: 'Fácil', color: '#22c55e' },
  medium: { label: 'Intermedio', color: '#f59e0b' },
  hard: { label: 'Difícil', color: '#ef4444' },
};

function ActivityCard({ activity, studentId, onComplete }: {
  activity: ParentActivity
  studentId: number
  onComplete: (activityId: number, studentId: number) => Promise<void>
}) {
  const [loading, setLoading] = useState(false);
  const [justCompleted, setJustCompleted] = useState(false);
  const diff = DIFFICULTY_LABEL[activity.difficulty] ?? DIFFICULTY_LABEL.medium;

  const handleComplete = async () => {
    setLoading(true);
    try {
      await onComplete(activity.id, studentId);
      setJustCompleted(true);
    } finally {
      setLoading(false);
    }
  };

  if (justCompleted || activity.already_completed) {
    return (
      <div style={{
        background: 'linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%)',
        border: '2px solid #22c55e',
        borderRadius: '16px',
        padding: '24px',
        marginBottom: '24px',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
          <span style={{ fontSize: '28px' }}>✅</span>
          <h2 style={{ fontSize: '18px', fontWeight: 700, color: '#166534', margin: 0 }}>
            ¡Actividad completada!
          </h2>
        </div>
        <p style={{ color: '#15803d', fontSize: '14px', margin: 0 }}>
          {activity.title} — Tu hijo pudo practicar con una actividad del modelo de barras.
        </p>
      </div>
    );
  }

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border-color)',
      borderRadius: '16px',
      padding: '24px',
      marginBottom: '24px',
      boxShadow: '0 2px 12px rgba(0,0,0,0.06)',
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ fontSize: '24px' }}>🎯</span>
          <div>
            <p style={{ fontSize: '11px', textTransform: 'uppercase', letterSpacing: '1px', color: 'var(--text-muted)', margin: 0 }}>Actividad de Hoy</p>
            <h2 style={{ fontSize: '18px', fontWeight: 700, margin: 0 }}>{activity.title}</h2>
          </div>
        </div>
        <span style={{
          fontSize: '12px', fontWeight: 600, padding: '3px 10px', borderRadius: '999px',
          background: diff.color + '22', color: diff.color, border: `1px solid ${diff.color}44`,
        }}>
          {diff.label}
        </span>
      </div>

      {/* Description */}
      <p style={{ fontSize: '14px', color: 'var(--text-secondary)', lineHeight: 1.6, marginBottom: '16px' }}>
        {activity.description}
      </p>

      {/* Meta row */}
      <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', marginBottom: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
          <span>⏱️</span>
          <span>~{activity.estimated_minutes} min</span>
        </div>
        {activity.materials && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <span>📦</span>
            <span>{activity.materials}</span>
          </div>
        )}
        {activity.bar_model_topic && (
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', color: 'var(--text-muted)' }}>
            <span>📊</span>
            <span>Modelo de barras: {activity.bar_model_topic}</span>
          </div>
        )}
      </div>

      {/* CTA */}
      <button
        onClick={handleComplete}
        disabled={loading}
        style={{
          width: '100%',
          padding: '12px 20px',
          background: 'var(--accent-green)',
          color: 'white',
          border: 'none',
          borderRadius: '10px',
          fontSize: '15px',
          fontWeight: 600,
          cursor: loading ? 'not-allowed' : 'pointer',
          opacity: loading ? 0.7 : 1,
          transition: 'opacity 0.15s',
        }}
      >
        {loading ? 'Guardando...' : 'Completé esta actividad ✅'}
      </button>
    </div>
  );
}

function StreakBadge({ streak }: { streak: number }) {
  if (streak <= 0) return null;
  return (
    <div style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: '6px',
      background: 'linear-gradient(135deg, #fff7ed 0%, #fed7aa 100%)',
      border: '1px solid #fb923c55',
      borderRadius: '999px',
      padding: '4px 12px',
      fontSize: '13px',
      fontWeight: 600,
      color: '#c2410c',
    }}>
      🔥 {streak} {streak === 1 ? 'día' : 'días'} de participación
    </div>
  );
}

export default function ParentDashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<ParentDashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [linkCode, setLinkCode] = useState('');
  const [codeLoading, setCodeLoading] = useState(false);
  const [studentCode, setStudentCode] = useState('');
  const fetchedRef = useRef(false);
  const [linkMsg, setLinkMsg] = useState('');

  useEffect(() => {
    if (user?.role !== 'parent') { router.replace('/'); return; }
    if (fetchedRef.current) return;
    fetchedRef.current = true;
    api.getParentDashboard()
      .then(d => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, [user, router]);

  const refresh = () => api.getParentDashboard().then(setData);

  const handleComplete = async (activityId: number, studentId: number) => {
    await api.completeParentActivity(activityId, studentId);
    await refresh();
  };

  const handleGenerateCode = async () => {
    setCodeLoading(true);
    try {
      const d = await api.generateParentLinkCode();
      setLinkCode(d.link_code);
    } catch { setLinkMsg('Error al generar código'); }
    setCodeLoading(false);
  };

  const handleLinkStudent = async () => {
    if (!studentCode.trim()) return;
    try {
      const d = await api.linkStudent(studentCode.trim());
      setLinkMsg('¡Vinculación exitosa! — vinculado a ' + d.parent_name);
      setStudentCode('');
      await refresh();
    } catch { setLinkMsg('Error al vincular'); }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-secondary)' }}>Cargando...</div>;

  const students: LinkedStudent[] = data?.linked_students ?? [];
  const parentStreak = students[0]?.parent_streak ?? 0;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '24px 16px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '12px' }}>
        <div>
          <h1 style={{ fontSize: '26px', fontWeight: 700, marginBottom: '4px' }}>Portal de Padres 👨‍👩‍👧</h1>
          <p style={{ fontSize: '14px', color: 'var(--text-secondary)', margin: 0 }}>
            Hola, {data?.parent_name}. Aquí está el progreso de tus hijos.
          </p>
        </div>
        <StreakBadge streak={parentStreak} />
      </div>

      {/* Daily Activity — shown if there's a linked student */}
      {data?.daily_activity && data?.student_id ? (
        <ActivityCard
          activity={data.daily_activity}
          studentId={data.student_id}
          onComplete={handleComplete}
        />
      ) : (
        <div style={{
          background: 'var(--bg-card)',
          border: '1px solid var(--border-color)',
          borderRadius: '16px',
          padding: '24px',
          marginBottom: '24px',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '14px',
        }}>
          Vincule un estudiante para ver la actividad del día.
        </div>
      )}

      {/* Link code section */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Vincular Estudiante</h2>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '12px' }}>
          Genera un código y compártelo con tu hijo para vincular su cuenta.
        </p>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', alignItems: 'center' }}>
          <button onClick={handleGenerateCode} disabled={codeLoading} style={{
            background: 'var(--accent-blue)', color: 'white', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px', cursor: 'pointer',
          }}>
            {codeLoading ? '...' : 'Generar código'}
          </button>
          {linkCode && (
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <code style={{ fontSize: '20px', fontWeight: 700, letterSpacing: '4px', background: 'var(--bg-secondary)', padding: '6px 14px', borderRadius: '8px' }}>{linkCode}</code>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Compártelo con tu hijo</span>
            </div>
          )}
        </div>
        {linkMsg && <p style={{ marginTop: '12px', fontSize: '13px', color: 'var(--accent-green)' }}>{linkMsg}</p>}
      </div>

      {/* Manual link */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Código de vinculación</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="Ingresa el código de tu hijo"
            value={studentCode}
            onChange={e => setStudentCode(e.target.value)}
            style={{
              flex: 1, padding: '8px 12px', border: '1px solid var(--border-color)',
              borderRadius: '8px', fontSize: '14px', background: 'var(--bg-primary)',
              color: 'var(--text-primary)',
            }}
          />
          <button onClick={handleLinkStudent} style={{
            background: 'var(--accent-green)', color: 'white', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px', cursor: 'pointer',
          }}>
            Vincular
          </button>
        </div>
      </div>

      {/* Students */}
      <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>
        Estudiantes Vinculados ({students.length})
      </h2>

      {students.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          No hay estudiantes vinculados todavía.
        </div>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {students.map(s => (
            <div key={s.id} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px' }}>
              <div style={{ fontWeight: 700, fontSize: '16px', marginBottom: '4px' }}>{s.name}</div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>Nivel {s.grade || 1}</div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>XP Total</div>
                  <div style={{ fontWeight: 600, color: 'var(--accent-blue)' }}>{s.xp_total?.toLocaleString()}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Racha</div>
                  <div style={{ fontWeight: 600 }}>🔥 {s.current_streak}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Ejercicios</div>
                  <div style={{ fontWeight: 600 }}>{s.exercises_completed}</div>
                </div>
                <div>
                  <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Dominio</div>
                  <div style={{ fontWeight: 600, color: s.avg_mastery >= 80 ? 'var(--accent-green)' : s.avg_mastery >= 50 ? 'var(--accent-yellow)' : 'var(--text-secondary)' }}>
                    {s.avg_mastery}%
                  </div>
                </div>
              </div>

              <div style={{ marginTop: '12px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '12px', color: 'var(--text-muted)', marginBottom: '4px' }}>
                  <span>Completado</span><span>{s.completion_rate}%</span>
                </div>
                <div style={{ height: '6px', background: 'var(--border-color)', borderRadius: '3px', overflow: 'hidden' }}>
                  <div style={{ width: `${s.completion_rate}%`, height: '100%', background: 'var(--accent-blue)', borderRadius: '3px' }} />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '24px' }}>
        <Link href="/" style={{ color: 'var(--accent-blue)', fontSize: '14px', textDecoration: 'none' }}>← Inicio</Link>
      </div>
    </div>
  );
}
