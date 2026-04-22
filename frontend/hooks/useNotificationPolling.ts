'use client';
import { useEffect, useRef, useState, useCallback } from 'react';
import { api, NotificationResponse } from '@/lib/api';

export function useNotificationPolling(onNewNotification?: (n: NotificationResponse) => void) {
  const [unreadCount, setUnreadCount] = useState(0);
  const lastIdsRef = useRef<Set<number>>(new Set());
  const [newToast, setNewToast] = useState<NotificationResponse | null>(null);
  
  const fetchNotifications = useCallback(async () => {
    try {
      const data = await api.getNotifications({ limit: 10 });
      setUnreadCount(data.unread_count);
      
      // Detect new notifications
      const currentIds = new Set(data.items.map(n => n.id));
      const newOnes = data.items.filter(n => !lastIdsRef.current.has(n.id));
      
      if (newOnes.length > 0 && lastIdsRef.current.size > 0) {
        // Only show toast for the most recent new one
        setNewToast(newOnes[0]);
        onNewNotification?.(newOnes[0]);
      }
      
      lastIdsRef.current = currentIds;
    } catch {
      // Silently ignore polling errors
    }
  }, [onNewNotification]);
  
  useEffect(() => {
    fetchNotifications(); // Initial fetch
    const interval = setInterval(fetchNotifications, 30000); // Poll every 30s
    return () => clearInterval(interval);
  }, [fetchNotifications]);
  
  return { unreadCount, dismissToast: () => setNewToast(null), newToast };
}