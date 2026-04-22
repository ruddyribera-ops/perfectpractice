'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function MobileNav() {
  const pathname = usePathname();

  const links = [
    { href: '/', label: '🏠', active: pathname === '/' },
    { href: '/me/assignments', label: '📋', active: pathname.startsWith('/me/assignments') },
    { href: '/me/history', label: '📊', active: pathname.startsWith('/me/history') },
    { href: '/leaderboard', label: '🏆', active: pathname.startsWith('/leaderboard') },
    { href: '/me/notifications', label: '🔔', active: pathname.startsWith('/me/notifications') },
  ];

  return (
    <nav style={{
      position: 'fixed',
      bottom: 0,
      left: 0,
      right: 0,
      background: 'var(--bg-card)',
      borderTop: '1px solid var(--border-color)',
      display: 'flex',
      justifyContent: 'space-around',
      padding: '8px 0 max(8px, env(safe-area-inset-bottom))',
      zIndex: 50,
    }}>
      {links.map(link => (
        <Link
          key={link.href}
          href={link.href}
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: '2px',
            fontSize: '20px',
            textDecoration: 'none',
            opacity: link.active ? 1 : 0.5,
            color: 'var(--text-primary)',
          }}
        >
          <span>{link.label}</span>
        </Link>
      ))}
    </nav>
  );
}