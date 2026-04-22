'use client'
import { useEffect, useState, createContext, useContext } from 'react'
import { t as translate, localeNames, supportedLocales } from '@/lib/translations'

export type Locale = 'es-BO' | 'fr' | 'pt-BR' | 'en-US'

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState('light')

  useEffect(() => {
    const stored = localStorage.getItem('theme') || 'light'
    setThemeState(stored)
    document.documentElement.setAttribute('data-theme', stored)
  }, [])

  const setTheme = (t: string) => {
    setThemeState(t)
    localStorage.setItem('theme', t)
    document.documentElement.setAttribute('data-theme', t)
  }

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>
}

// ─── Theme Context (exported for consumers) ───────────────────────────────────
export const ThemeContext = createContext<{ theme: string; setTheme: (t: string) => void }>({
  theme: 'light',
  setTheme: () => {},
})

// ─── Locale Context ─────────────────────────────────────────────────────────
export type Locale = 'es-BO' | 'fr' | 'pt-BR' | 'en-US'

export const LocaleContext = createContext<{ locale: Locale; setLocale: (l: Locale) => void }>({
  locale: 'es-BO',
  setLocale: () => {},
})

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>('es-BO')

  useEffect(() => {
    const stored = localStorage.getItem('locale') as Locale
    if (stored) setLocaleState(stored)
  }, [])

  const setLocale = (l: Locale) => {
    setLocaleState(l)
    localStorage.setItem('locale', l)
  }

  return <LocaleContext.Provider value={{ locale, setLocale }}>{children}</LocaleContext.Provider>
}

// ─── Combined Providers ──────────────────────────────────────────────────────
export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <ThemeProvider>
      <LocaleProvider>
        {children}
      </LocaleProvider>
    </ThemeProvider>
  )
}

// ─── Translation hook ────────────────────────────────────────────────────────
export function useTranslation() {
  const { locale } = useContext(LocaleContext)
  return {
    t: (key: string) => translate(key, locale),
    locale,
    localeNames,
    supportedLocales,
  }
}
