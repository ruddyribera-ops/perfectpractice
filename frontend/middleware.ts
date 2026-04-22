import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Public routes — no auth needed
  const publicRoutes = ['/login', '/register', '/landing']
  if (publicRoutes.some(route => pathname.startsWith(route))) {
    return NextResponse.next()
  }

  // API routes hit the backend directly — backend handles auth
  if (pathname.startsWith('/api/')) {
    return NextResponse.next()
  }

  // Check for auth token
  const token = request.cookies.get('access_token')?.value
    || request.cookies.get('access_token')?.value
    || request.headers.get('authorization')?.replace('Bearer ', '')

  const localToken = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
  const hasToken = token || localToken

  // Root redirect based on role
  if (pathname === '/') {
    // Client-side redirect handled by page.tsx useAuth — skip server redirect
    return NextResponse.next()
  }

  // /teacher/* → teacher or admin only
  if (pathname.startsWith('/teacher')) {
    // Role check done client-side for now — middleware can't read localStorage
    return NextResponse.next()
  }

  // /parent/* → parent only
  if (pathname.startsWith('/parent')) {
    return NextResponse.next()
  }

  return NextResponse.next()
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (public/*)
     */
    '/((?!_next/static|_next/image|favicon.ico|public/).*)',
  ],
}
