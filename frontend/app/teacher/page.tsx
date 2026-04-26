'use client';
import { useEffect, useState } from 'react';
import Link from 'next/link';

export default function TeacherDashboardPage() {
  const [stats, setStats] = useState({ totalClasses: 0, totalStudents: 0, avgMastery: 0 });

  useEffect(() => {
    // Fetch from the teacher's classes endpoint to compute stats
    fetch('/api/classes', {
      headers: { Authorization: `Bearer ${localStorage.getItem('access_token') || ''}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        const classes = Array.isArray(data) ? data : (data.classes || []);
        const students = classes.reduce((acc: number, c: any) => acc + (c.student_count || 0), 0);
        const avgMastery = classes.length > 0
          ? Math.round(classes.reduce((acc: number, c: any) => acc + (c.avg_mastery || 0), 0) / classes.length)
          : 0;
        setStats({ totalClasses: classes.length, totalStudents: students, avgMastery });
      })
      .catch(() => {});
  }, []);

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Panel del Profesor</h1>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold text-primary-600">{stats.totalClasses}</div>
          <div className="text-sm text-gray-500 mt-1">Clases activas</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold text-green-600">{stats.totalStudents}</div>
          <div className="text-sm text-gray-500 mt-1">Estudiantes inscritos</div>
        </div>
        <div className="bg-white border border-gray-200 rounded-xl p-5 text-center">
          <div className="text-3xl font-bold text-yellow-500">{stats.avgMastery}%</div>
          <div className="text-sm text-gray-500 mt-1">Dominio promedio</div>
        </div>
      </div>

      {/* Quick actions */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Acciones rápidas</h2>
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Link href="/teacher/classes" className="no-underline">
          <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-primary-400 hover:shadow-sm transition cursor-pointer">
            <div className="text-3xl mb-2">🏫</div>
            <div className="font-semibold text-sm text-gray-900">Mis Clases</div>
            <div className="text-xs text-gray-500 mt-1">Ver y gestionar clases</div>
          </div>
        </Link>
        <Link href="/teacher/classes" className="no-underline">
          <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-primary-400 hover:shadow-sm transition cursor-pointer">
            <div className="text-3xl mb-2">📝</div>
            <div className="font-semibold text-sm text-gray-900">Crear Tarea</div>
            <div className="text-xs text-gray-500 mt-1">Asignar ejercicios</div>
          </div>
        </Link>
        <Link href="/teacher/classroom" className="no-underline">
          <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-primary-400 hover:shadow-sm transition cursor-pointer">
            <div className="text-3xl mb-2">🎓</div>
            <div className="font-semibold text-sm text-gray-900">Google Classroom</div>
            <div className="text-xs text-gray-500 mt-1">Sincronizar tareas</div>
          </div>
        </Link>
        <Link href="/leaderboard" className="no-underline">
          <div className="bg-white border border-gray-200 rounded-xl p-5 hover:border-primary-400 hover:shadow-sm transition cursor-pointer">
            <div className="text-3xl mb-2">🏆</div>
            <div className="font-semibold text-sm text-gray-900">Tabla de Posiciones</div>
            <div className="text-xs text-gray-500 mt-1">Ver ranking semanal</div>
          </div>
        </Link>
      </div>

      {/* Quick link to class list */}
      <div className="bg-gray-50 border border-gray-200 rounded-xl px-5 py-4">
        <Link href="/teacher/classes" className="text-primary-600 text-sm font-semibold no-underline hover:underline">
          → Ver todas mis clases →
        </Link>
      </div>
    </div>
  );
}
