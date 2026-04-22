'use client';
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { NotificationResponse } from '@/lib/api';

interface Props {
  notification: NotificationResponse;
  onClose: () => void;
}

export default function NotificationToast({ notification, onClose }: Props) {
  const router = useRouter();
  
  useEffect(() => {
    const timer = setTimeout(onClose, 6000);
    return () => clearTimeout(timer);
  }, [onClose]);
  
  const handleClick = () => {
    if (notification.link) {
      router.push(notification.link);
    }
    onClose();
  };
  
  return (
    <div onClick={handleClick} style={{
      position: 'fixed',
      top: '80px',
      right: '20px',
      zIndex: 9999,
      background: 'white',
      border: '1px solid #e5e7eb',
      borderRadius: '12px',
      boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
      padding: '16px 20px',
      maxWidth: '360px',
      cursor: notification.link ? 'pointer' : 'default',
      animation: 'slideIn 0.3s ease-out',
    }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ fontWeight: 600, fontSize: '14px', color: '#111' }}>
            {notification.title}
          </div>
          {notification.body && (
            <div style={{ fontSize: '13px', color: '#666', marginTop: '4px' }}>
              {notification.body}
            </div>
          )}
        </div>
        <button onClick={(e) => { e.stopPropagation(); onClose(); }} style={{
          background: 'none',
          border: 'none',
          fontSize: '18px',
          cursor: 'pointer',
          padding: '0 0 0 8px',
          color: '#999',
        }}>
          ×
        </button>
      </div>
    </div>
  );
}