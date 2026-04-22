'use client';
import { useEffect, useState } from 'react';
import { api, MyClassItem } from '@/lib/api';

export default function MyClassesPage() {
  const [classes, setClasses] = useState<MyClassItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [joinCode, setJoinCode] = useState('');
  const [joinError, setJoinError] = useState('');
  const [joining, setJoining] = useState(false);

  useEffect(() => {
    api.getMyClasses().then(data => { setClasses(data); setLoading(false); }).catch(() => setLoading(false));
  }, []);

  const handleJoin = async () => {
    if (!joinCode.trim()) return;
    setJoining(true);
    setJoinError('');
    try {
      const res = await fetch(`/api/classes/join/${joinCode.trim()}`, {
        method: 'POST',
        ...api._auth(),
      });
      if (!res.ok) {
        const err = await res.json();
        setJoinError(err.detail || 'Código inválido');
      } else {
        // Refresh class list
        const updated = await api.getMyClasses();
        setClasses(updated);
        setJoinCode('');
      }
    } catch {
      setJoinError('Error al unirse a la clase');
    }
    setJoining(false);
  };

  if (loading) return <div style={{ textAlign: 'center', padding: '64px', color: '#666' }}>Cargando...</div>;

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', padding: '24px 16px' }}>
      <h1 style={{ fontSize: '24px', fontWeight: 700, marginBottom: '24px' }}>Mis Clases</h1>

      {/* Join with invite code */}
      <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px', padding: '20px', marginBottom: '24px' }}>
        <h2 style={{ fontSize: '15px', fontWeight: 600, marginBottom: '12px' }}>Unirse a una clase</h2>
        <div style={{ display: 'flex', gap: '8px' }}>
          <input
            type="text"
            value={joinCode}
            onChange={e => setJoinCode(e.target.value.toUpperCase())}
            placeholder="Código de invitación"
            style={{ flex: 1, padding: '8px 12px', border: '1px solid #e5e7eb', borderRadius: '8px', fontSize: '14px' }}
          />
          <button
            onClick={handleJoin}
            disabled={joining || !joinCode.trim()}
            style={{
              background: '#3b82f6', color: 'white', border: 'none', borderRadius: '8px',
              padding: '8px 16px', fontSize: '14px', cursor: joining ? 'not-allowed' : 'pointer',
              opacity: joining ? 0.7 : 1,
            }}
          >
            {joining ? 'Uniéndose...' : 'Unirse'}
          </button>
        </div>
        {joinError && <div style={{ color: '#ef4444', fontSize: '13px', marginTop: '8px' }}>{joinError}</div>}
      </div>

      {/* Class list */}
      {classes.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '48px 0', color: '#999' }}>
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>🏫</div>
          <div>No estás inscrito en ninguna clase.</div>
          <div style={{ fontSize: '14px', marginTop: '4px', color: '#aaa' }}>Usa un código de invitación para unirte.</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {classes.map(cls => (
            <div key={cls.id} style={{
              background: 'white', border: '1px solid #e5e7eb', borderRadius: '12px',
              padding: '16px 20px',
            }}>
              <div style={{ fontWeight: 600, fontSize: '15px', color: '#111' }}>{cls.name}</div>
              {cls.subject && <div style={{ fontSize: '13px', color: '#666', marginTop: '2px' }}>{cls.subject}</div>}
              <div style={{ fontSize: '12px', color: '#aaa', marginTop: '6px' }}>
                Inscrito: {cls.enrolled_at ? new Date(cls.enrolled_at).toLocaleDateString('es-BO') : 'Fecha desconocida'}
              </div>
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '24px', textAlign: 'center' }}>
        <a href="/me/assignments" style={{ color: '#3b82f6', fontSize: '14px', textDecoration: 'none' }}>
          → Ver mis tareas
        </a>
      </div>
    </div>
  );
}
