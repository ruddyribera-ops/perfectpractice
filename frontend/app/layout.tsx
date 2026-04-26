import type { Metadata } from 'next'
import { Inter, Nunito } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/contexts/AuthContext'
import { Providers } from './providers'

const inter = Inter({ subsets: ['latin'] })
const nunito = Nunito({ variable: '--font-nunito', subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Math Platform - Aprende Matemáticas',
  description: 'Plataforma de aprendizaje de matemáticas estilo Khan Academy para escuelas bolivianas',
  icons: {
    icon: '/favicon.svg',
    apple: '/favicon.svg',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="es" suppressHydrationWarning className={nunito.variable}>
      <body className={inter.className}>
        <AuthProvider>
          <Providers>
            {children}
          </Providers>
        </AuthProvider>
      </body>
    </html>
  )
}
