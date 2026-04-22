'use client';
import { useEffect, useState } from 'react';
import { api, NotificationResponse } from '@/lib/api';
import Link from 'next/link';
import { useRouter } from 'next/navigation';

export default function NotificationsPage() {
  const [notifications, setNotifications] = useState<NotificationResponse[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [filter, setFilter] = useState<'all' | 'unread' | 'read'>('all');
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const router = useRouter();

  const fetchNotifications = async (f: typeof filter, p: number) => {
    try {
      const data = await api.getNotifications({ read_filter: f, page: p, limit: 20 });
      setNotifications(data.items);
      setUnreadCount(data.unread_count);
      setPages(data.pages);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => { fetchNotifications(filter, page); }, [filter, page]);

  const handleMarkAllRead = async () => {
    await api.markAllNotificationsRead();
    fetchNotifications(filter, page);
  };

  const handleMarkRead = async (id: number) => {
    await api.markNotificationRead(id);
    fetchNotifications(filter, page);
  };

  return (
    <div style={{ maxWidth: '640px', margin: '0 auto', padding: '24px 16px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <h1 style={{ fontSize: '24px', fontWeight: 700 }}>Notificaciones</h1>
        {unreadCount > 0 && (
          <button onClick={handleMarkAllRead} style={{
            background: '#3b82f6', color: 'white', border: 'none',
            borderRadius: '8px', padding: '8px 16px', fontSize: '14px', cursor: 'pointer',
          }}>
            Marcar todas como leídas
          </button>
        )}
      </div>

      {/* Filter tabs */}
      <div style={{ display: 'flex', gap: '8px', marginBottom: '20px' }}>
        {(['all', 'unread', 'read'] as const).map(f => (
          <button key={f} onClick={() => { setFilter(f); setPage(1); }} style={{
            padding: '6px 16px',
            borderRadius: '20px',
            border: '1px solid',
            borderColor: filter === f ? '#3b82f6' : '#e5e7eb',
            background: filter === f ? '#3b82f6' : 'white',
            color: filter === f ? 'white' : '#666',
            fontSize: '13px',
            cursor: 'pointer',
          }}>
            {f === 'all' ? 'Todas' : f === 'unread' ? 'No leídas' : 'Leídas'}
          </button>
        ))}
      </div>

      {notifications.length === 0 ? (
        <div style={{ textAlign: 'center', color: '#999', padding: '48px 0' }}>
          No tienes notificaciones
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          {notifications.map(n => (
            <div key={n.id} onClick={() => !n.read && handleMarkRead(n.id)} style={{
              background: n.read ? '#f9fafb' : 'white',
              border: '1px solid',
              borderColor: n.read ? '#f3f4f6' : '#dbeafe',
              borderRadius: '12px',
              padding: '16px',
              cursor: n.read ? 'default' : 'pointer',
              transition: 'all 0.2s',
            }}>
              <div style={{ fontWeight: 600, fontSize: '14px', color: n.read ? '#999' : '#111' }}>
                {n.title}
              </div>
              {n.body && (
                <div style={{ fontSize: '13px', color: '#666', marginTop: '4px' }}>{n.body}</div>
              )}
              <div style={{ fontSize: '12px', color: '#aaa', marginTop: '8px' }}>
                {new Date(n.created_at).toLocaleString('es-BO')}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Pagination */}
      {pages > 1 && (
        <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginTop: '24px' }}>
          <button disabled={page <= 1} onClick={() => setPage(p => p - 1)} style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #e5e7eb', background: 'white', cursor: page <= 1 ? 'not-allowed' : 'pointer' }}>Anterior</button>
          <span style={{ padding: '8px 16px', fontSize: '14px', color: '#666' }}>Página {page} de {pages}</span>
          <button disabled={page >= pages} onClick={() => setPage(p => p + 1)} style={{ padding: '8px 16px', borderRadius: '8px', border: '1px solid #e5e7eb', background: 'white', cursor: page >= pages ? 'not-allowed' : 'pointer' }}>Siguiente</button>
        </div>
      )}
    </div>
  );
}