'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import Link from 'next/link'
import { api } from '@/lib/api'
import { ChevronRight, BookOpen } from 'lucide-react'

interface Unit {
  id: number
  slug: string
  title: string
  description: string | null
  order_index: number
}

interface TopicDetail {
  id: number
  slug: string
  title: string
  description: string | null
  icon_name: string | null
  units: Unit[]
}

export default function TopicDetailPage() {
  const params = useParams()
  const slug = params.slug as string
  const [topic, setTopic] = useState<TopicDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (slug) fetchTopic()
  }, [slug])

  const fetchTopic = async () => {
    try {
      const data = await api.get<TopicDetail>(`/topics/${slug}`)
      setTopic(data)
    } catch (error) {
      console.error('Error fetching topic:', error)
    } finally {
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    )
  }

  if (!topic) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-gray-600">Tema no encontrado</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center gap-4">
          <Link href="/" className="text-2xl font-bold text-primary-600">Math Platform</Link>
          <span className="text-gray-500">/</span>
          <Link href="/topics" className="text-gray-500 hover:text-gray-700">Temas</Link>
          <span className="text-gray-500">/</span>
          <span className="font-medium">{topic.title}</span>
        </nav>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">{topic.title}</h1>
          {topic.description && (
            <p className="text-gray-600">{topic.description}</p>
          )}
        </div>

        <h2 className="text-xl font-semibold mb-4">Unidades</h2>
        <div className="space-y-4">
          {topic.units.map((unit) => (
            <Link key={unit.id} href={`/units/${unit.slug}`}>
              <div className="card hover:shadow-md transition-shadow cursor-pointer">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-secondary-100 rounded-lg">
                    <BookOpen className="h-6 w-6 text-secondary-600" />
                  </div>
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold">{unit.title}</h3>
                    {unit.description && (
                      <p className="text-gray-600 text-sm">{unit.description}</p>
                    )}
                  </div>
                  <ChevronRight className="h-5 w-5 text-gray-400" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      </main>
    </div>
  )
}
