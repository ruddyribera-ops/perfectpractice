'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { api } from '@/lib/api';

export default function NotificationBell() {
  const [unread, setUnread] = useState(0);
  
  useEffect(() => {
    api.getNotifications({ limit: 1 }).then(data => {
      setUnread(data.unread_count);
    }).catch(() => {});
  }, []);
  
  return (
    <Link href="/me/notifications" style={{ position: 'relative', display: 'inline-flex', alignItems: 'center', padding: '8px' }}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
        <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
      </svg>
      {unread > 0 && (
        <span style={{
          position: 'absolute',
          top: 2,
          right: 2,
          background: '#ef4444',
          color: 'white',
          borderRadius: '50%',
          fontSize: '11px',
          fontWeight: 'bold',
          width: '18px',
          height: '18px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          {unread > 9 ? '9+' : unread}
        </span>
      )}
    </Link>
  );
}