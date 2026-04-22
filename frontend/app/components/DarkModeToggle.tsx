'use client'
import { useContext } from 'react'
import { ThemeContext } from '../providers'

export default function DarkModeToggle({ compact = false }: { compact?: boolean }) {
  const { theme, setTheme } = useContext(ThemeContext)

  return (
    <button
      onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '6px',
        padding: compact ? '6px 10px' : '8px 16px',
        borderRadius: '8px',
        border: '1px solid var(--border-color)',
        background: 'var(--bg-card)',
        color: 'var(--text-primary)',
        fontSize: '13px',
        cursor: 'pointer',
        transition: 'all 0.15s',
      }}
    >
      {theme === 'dark' ? '☀️ Claro' : '🌙 Oscuro'}
    </button>
  )
}
