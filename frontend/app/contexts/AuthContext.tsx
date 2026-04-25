'use client'

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { api } from '@/lib/api'

interface User {
  id: number
  email: string
  name: string
  role: 'student' | 'teacher' | 'admin' | 'parent'
}

interface AuthContextType {
  user: User | null
  loading: boolean
  login: (email: string, password: string) => Promise<User>
  register: (data: { name: string; email: string; password: string; role: string; grade?: number }) => Promise<void>
  logout: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  // Synchronous initial auth check — avoids async race on first render
  const initialToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  const initialUser = typeof window !== 'undefined' ? localStorage.getItem('user') : null

  const [user, setUser] = useState<User | null>(initialToken && initialUser ? JSON.parse(initialUser) : null)
  const [loading, setLoading] = useState(!!initialToken && !initialUser) // true only if token exists but no cached user (need to re-hydrate)

  useEffect(() => {
    // Only re-fetch if we have a token but no cached user (e.g. page was refreshed without SSR)
    if (!initialToken || initialUser) return
    checkAuth()
  }, [])

  const checkAuth = async () => {
    try {
      const token = localStorage.getItem('access_token')
      if (token) {
        // In a real app, you'd validate the token with the backend
        const userData = localStorage.getItem('user')
        if (userData) {
          setUser(JSON.parse(userData))
        }
      }
    } catch (error) {
      console.error('Auth check failed:', error)
    } finally {
      setLoading(false)
    }
  }

  const login = async (email: string, password: string): Promise<User> => {
    const response = await api.post<{ user: User; access_token: string; refresh_token: string }>(
      '/auth/login',
      { email, password }
    )

    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    setUser(response.user)
    return response.user
  }

  const register = async (data: { name: string; email: string; password: string; role: string; grade?: number }) => {
    const response = await api.post<{ user: User; access_token: string; refresh_token: string }>(
      '/auth/register',
      data
    )
    
    localStorage.setItem('access_token', response.access_token)
    localStorage.setItem('refresh_token', response.refresh_token)
    localStorage.setItem('user', JSON.stringify(response.user))
    setUser(response.user)
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout')
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      localStorage.removeItem('user')
      setUser(null)
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider')
  }
  return context
}
