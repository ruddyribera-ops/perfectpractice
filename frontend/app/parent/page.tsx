'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
import { api } from '@/lib/api';

export default function ParentDashboardPage() {
  const { user } = useAuth();
  const router = useRouter();
  const [students, setStudents] = useState<any[]>([]);
  const [parentName, setParentName] = useState('');
  const [loading, setLoading] = useState(true);
  const [linkCode, setLinkCode] = useState('');
  const [codeLoading, setCodeLoading] = useState(false);
  const [studentCode, setStudentCode] = useState('');
  const [linkMsg, setLinkMsg] = useState('');

  useEffect(() => {
    if (user?.role !== 'parent') { router.replace('/'); return; }
    api.getParentDashboard()
      .then(data => { setStudents(data.linked_students || []); setParentName(data.parent_name); setLoading(false); })
      .catch(() => setLoading(false));
  }, [user, router]);

  const handleGenerateCode = async () => {
    setCodeLoading(true);
    try {
      const data = await api.generateParentLinkCode();
      setLinkCode(data.link_code);
    } catch { setLinkMsg('Error al generar código'); }
    setCodeLoading(false);
  };

  const handleLinkStudent = async () => {
    if (!studentCode.trim()) return;
    try {
      const data = await api.linkStudent(studentCode.trim());
      setLinkMsg('¡Vinculación exitosa! — vinculado a ' + data.parent_name);
      setStudentCode('');
      const dash = await api.getParentDashboard();
      setStudents(dash.linked_students || []);
    } catch {
      setLinkMsg('Error al vincular');
    }
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '64px', color: 'var(--text-secondary)' }}>Cargando...</div>;

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ fontSize: '26px', fontWeight: 700, marginBottom: '24px' }}>Portal de Padres 👨‍👩‍👧</h1>

      {/* Generate link code */}
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

      {/* Manual link by code */}
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Código de vinculación</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            placeholder="Ingresa el código de tu hijo"
            value={studentCode}
            onChange={e => setStudentCode(e.target.value)}
            style={{
              flex: 1,
              padding: '8px 12px',
              border: '1px solid var(--border-color)',
              borderRadius: '8px',
              fontSize: '14px',
              background: 'var(--bg-primary)',
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

      {/* Linked students */}
      <h2 style={{ fontSize: '18px', fontWeight: 700, marginBottom: '16px' }}>Estudiantes Vinculados ({students.length})</h2>

      {students.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-muted)', background: 'var(--bg-card)', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
          No hay estudiantes vinculados todavía.
        </div>
      ) : (
        <div className="full-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', gap: '16px' }}>
          {students.map(s => (
            <div key={s.id} style={{ background: 'var(--bg-card)', border: '1px solid var(--border-color)', borderRadius: '12px', padding: '20px' }}>
              <div style={{ fontWeight: 700, fontSize: '16px', marginBottom: '4px' }}>{s.name}</div>
              <div style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
                Nivel {s.grade || 1}
              </div>

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
                  <span>Completado</span>
                  <span>{s.completion_rate}%</span>
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