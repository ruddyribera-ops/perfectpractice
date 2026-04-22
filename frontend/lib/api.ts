const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

// ─── Shared types ─────────────────────────────────────────────────────────────

export interface StreakData {
  current_streak: number
  longest_streak: number
  last_activity_date: string | null
  streak_freeze_available: number
  streak_at_risk: boolean
}

export interface StatsData {
  total_xp: number
  level: number
  points: number
  current_streak: number
  longest_streak: number
  exercises_completed: number
  lessons_completed: number
  xp_to_next_level: number
}

export interface Lesson {
  id: number
  unit_id: number
  title: string
  content: string
  order_index: number
}

export interface Exercise {
  id: number
  unit_id: number
  lesson_id: number | null
  slug: string
  title: string
  exercise_type: string
  difficulty: string
  points_value: number
  data: ExerciseData
  hints: string[] | null
  is_anked: boolean
  is_summative: boolean
}

type ExerciseData =
  | { question: string; options?: string[]; explanation?: string }
  | BarModelData
  | WordProblemData

export interface BarModelData {
  question: string
  total: string
  units: { label: string; value: number }[]
  type: string
}

export interface WordProblemData {
  scenario: string
  question: string
  answer: string
  hint?: string
}

export interface AttemptResult {
  correct: boolean
  points_earned: number
  xp_earned: number
  explanation: string | null
  new_mastery: number
  streak_updated: boolean
  current_streak: number
  new_achievements: AchievementResponse[]
}

// ─── API Client ───────────────────────────────────────────────────────────────

class ApiClient {
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
    }
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Request failed' }))
      const err = new Error(error.detail || 'Request failed')
      ;(err as any).status = response.status
      throw err
    }
    return response.json()
  }

  async get<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'GET',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async post<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })
    return this.handleResponse<T>(response)
  }

  async put<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'PUT',
      headers: this.getHeaders(),
      body: JSON.stringify(data),
    })
    return this.handleResponse<T>(response)
  }

  async delete<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'DELETE',
      headers: this.getHeaders(),
    })
    return this.handleResponse<T>(response)
  }

  async patch<T>(endpoint: string, data?: any): Promise<T> {
    const response = await fetch(`${API_URL}/api${endpoint}`, {
      method: 'PATCH',
      headers: this.getHeaders(),
      body: data ? JSON.stringify(data) : undefined,
    })
    return this.handleResponse<T>(response)
  }

  /** Expose auth headers for raw fetch calls outside the class */
  _auth(): { headers: HeadersInit } {
    return { headers: this.getHeaders() }
  }

  // ─── Gamification ─────────────────────────────────────────────────────────
  getStreak() { return this.get<StreakData>('/me/streaks/me') }
  getStats() { return this.get<StatsData>('/me/stats/me') }
  getAchievements() { return this.get<AchievementResponse[]>('/me/achievements') }
  useStreakFreeze() { return this.post<StreakFreezeResponse>('/me/streaks/freeze') }
  getMyRank() { return this.get<LeaderboardMeResponse>('/leaderboard/me') }

  // ─── Lessons ───────────────────────────────────────────────────────────────
  getLessonsForUnit(unitId: number) { return this.get<Lesson[]>(`/lessons/unit/${unitId}`) }
  getLesson(id: number) { return this.get<Lesson & { exercises: Exercise[] }>(`/lessons/${id}`) }

  // ─── Exercises ─────────────────────────────────────────────────────────────
  getExercise(id: number) { return this.get<Exercise>(`/exercises/${id}`) }
  submitAttempt(id: number, answer: any, timeSpentSeconds: number, assignmentId?: number) {
    const body: Record<string, any> = {
      answer,
      time_spent_seconds: timeSpentSeconds,
    }
    if (assignmentId !== undefined) body.assignment_id = assignmentId
    return this.post<AttemptResult>(`/me/exercises/${id}/attempt`, body)
  }

  // ─── Student Progress ─────────────────────────────────────────────────
  getProgress() { return this.get<ProgressItem[]>('/me/progress') }
  getNotifications(params?: {
    page?: number
    limit?: number
    read_filter?: 'all' | 'read' | 'unread'
  }) {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set('page', String(params.page))
    if (params?.limit) searchParams.set('limit', String(params.limit))
    if (params?.read_filter) searchParams.set('read_filter', params.read_filter)
    const qs = searchParams.toString()
    return this.get<NotificationListResponse>(`/me/notifications${qs ? `?${qs}` : ''}`)
  }
  markNotificationRead(id: number) {
    return this.patch<NotificationResponse>(`/me/notifications/${id}/read`)
  }
  markAllNotificationsRead() {
    return this.post<{ success: boolean; updated: number }>(`/me/notifications/mark-all-read`)
  }
  getAttemptHistory(params: {
    topic_id?: number
    unit_id?: number
    correct?: boolean
    page?: number
    limit?: number
  }) {
    const qs = new URLSearchParams()
    if (params.topic_id != null) qs.set('topic_id', String(params.topic_id))
    if (params.unit_id != null) qs.set('unit_id', String(params.unit_id))
    if (params.correct != null) qs.set('correct', String(params.correct))
    if (params.page != null) qs.set('page', String(params.page))
    if (params.limit != null) qs.set('limit', String(params.limit))
    const query = qs.toString() ? `?${qs.toString()}` : ''
    return this.get<AttemptHistoryResponse>(`/me/history${query}`)
  }

  // ─── Teacher Dashboard ────────────────────────────────────────────────────
  getClassDetail(id: number) {
    return this.get<ClassDetail>(`/classes/${id}`)
  }
  getClassStudents(id: number) {
    return this.get<StudentProgress[]>(`/classes/${id}/students`)
  }
  getClassAssignments(id: number) {
    return this.get<AssignmentItem[]>(`/classes/${id}/assignments`)
  }
  createAssignment(classId: number, data: {
    title: string
    description?: string
    exercise_ids: number[]
    due_date?: string
  }) {
    return this.post<AssignmentItem>(`/classes/${classId}/assignments`, data)
  }
  getTopicPickerTree() {
    return this.get<TopicWithExercises[]>(`/topics/picker/full`)
  }
  getAssignmentResults(assignmentId: number) {
    return this.get<AssignmentResultResponse>(`/assignments/${assignmentId}/results`)
  }

  // ─── Student Assignments ────────────────────────────────────────────────
  getMyAssignments() {
    return this.get<MyAssignmentsResponse>('/me/assignments')
  }
  getMyAssignmentDetail(id: number) {
    return this.get<StudentAssignmentDetail>(`/me/assignments/${id}`)
  }

  // ─── My Classes ───────────────────────────────────────────────────────────
  getMyClasses() {
    return this.get<MyClassItem[]>('/me/classes')
  }

  // ─── Parent Portal ────────────────────────────────────────────────────────
  getParentDashboard() {
    return this.get<ParentDashboardResponse>('/parents/me')
  }
  generateParentLinkCode() {
    return this.post<{ link_code: string }>('/parents/generate-code')
  }
  linkStudent(linkCode: string) {
    return this.post<{ success: boolean; parent_name: string }>('/me/link-parent', { link_code: linkCode })
  }

  // ─── Google Classroom ────────────────────────────────────────────────────
  getClassroomAuthUrl() {
    return this.get<{ authorization_url: string }>('/classroom/authorize')
  }
  getClassroomCourses() {
    return this.get<ClassroomCourse[]>('/classroom/courses')
  }
  linkClassroomCourse(classroomCourseId: string, localClassId: number) {
    return this.post<ClassroomLinkResponse>('/classroom/link', {
      classroom_course_id: classroomCourseId,
      local_class_id: localClassId,
    })
  }
  getClassroomLinks() {
    return this.get<ClassroomLink[]>('/classroom/links')
  }
  unlinkClassroom(syncId: number) {
    return this.delete<{ message: string }>(`/classroom/link/${syncId}`)
  }
  syncAssignmentToClassroom(syncId: number, assignmentId: number, topicId?: string) {
    const body: Record<string, any> = { assignment_id: assignmentId }
    if (topicId) body.topic_id = topicId
    return this.post<ClassroomSyncResult>('/classroom/sync-assignment', body)
  }
  getClassroomTopics(courseId: string) {
    return this.get<ClassroomTopic[]>(`/classroom/courses/${courseId}/topics`)
  }
}

export interface ClassDetail {
  id: number
  name: string
  subject: string
  invite_code: string
  created_at: string
  student_count: number
  assignment_count: number
}

export interface MyClassItem {
  id: number
  name: string
  subject: string | null
  invite_code: string
  enrolled_at: string | null
}

export interface StudentProgress {
  student_id: number
  name: string
  email: string
  grade: number
  points: number
  level: number
  current_streak: number
  avg_mastery: number
  enrolled_at: string
  last_active: string | null
  exercises_completed: number
}

export interface AssignmentItem {
  id: number
  class_id: number
  title: string
  description: string | null
  due_date: string | null
  created_at: string
}

export interface ExerciseInAssignment {
  id: number
  title: string
  exercise_type: string
  difficulty: string
  order_index: number
  status: 'not_started' | 'in_progress' | 'correct' | 'incorrect'
}

export interface MyAssignmentItem {
  id: number
  title: string
  description: string | null
  due_date: string | null
  class_id: number
  class_name: string
  score: number | null
  completion_rate: number
  completed_at: string | null
}

export interface MyAssignmentsResponse {
  items: MyAssignmentItem[]
  total: number
}

export interface StudentAssignmentDetail {
  id: number
  title: string
  description: string | null
  due_date: string | null
  class_id: number
  class_name: string
  score: number | null
  completion_rate: number
  exercises: ExerciseInAssignment[]
}

export interface TopicWithExercises {
  id: number
  slug: string
  title: string
  units: UnitWithExercises[]
}

export interface UnitWithExercises {
  id: number
  title: string
  slug: string
  exercises: ExercisePickerItem[]
}

export interface ExercisePickerItem {
  id: number
  title: string
  exercise_type: string
  difficulty: string
  points_value: number
  lesson_title: string | null
  unit_title: string
}

export interface AchievementResponse {
  id: number
  badge_key: string
  title: string
  description: string | null
  icon: string | null
  earned_at: string
}

export interface StreakFreezeResponse {
  success: boolean
  message: string
  freezes_remaining: number
  new_achievements: AchievementResponse[]
}

export interface LeaderboardMeResponse {
  student_id: number
  name: string
  weekly_rank: number | null
  weekly_points: number
  monthly_rank: number | null
  monthly_points: number
  all_time_rank: number | null
  all_time_points: number
}

export interface ProgressItem {
  topic_id: number
  topic_title: string
  exercises_completed: number
  total_exercises: number
  mastery_score: number
  new_mastery?: number
}

export interface NotificationResponse {
  id: number
  type: string
  title: string
  body: string | null
  link: string | null
  read: boolean
  created_at: string
}

export interface NotificationListResponse {
  items: NotificationResponse[]
  total: number
  unread_count: number
  page: number
  pages: number
}

export interface AttemptHistoryItem {
  id: number
  exercise_id: number
  exercise_title: string
  topic_id: number
  topic_title: string
  unit_id: number
  unit_title: string
  correct: boolean
  answer: any
  correct_answer: any
  xp_earned: number
  points_earned: number
  attempted_at: string
}

export interface AttemptHistoryResponse {
  items: AttemptHistoryItem[]
  total: number
  page: number
  pages: number
  limit: number
}

export interface ExerciseResultItem {
  exercise_id: number
  exercise_title: string
  correct: boolean
  points_earned: number
  xp_earned: number
}

export interface StudentAssignmentResult {
  student_id: number
  student_name: string
  score: number | null
  completion_rate: number
  completed_at: string | null
  started_at: string | null
  exercises: ExerciseResultItem[]
  rank?: number
}

export interface AssignmentResultResponse {
  assignment_id: number
  title: string
  total_students: number
  completed_count: number
  avg_score: number | null
  completion_rate: number
  results: StudentAssignmentResult[]
}

export interface LinkedStudent {
  id: number
  name: string
  grade: number
  xp_total: number
  current_streak: number
  avg_mastery: number
  exercises_completed: number
  total_exercises: number
  completion_rate: number
}

export interface ParentDashboardResponse {
  parent_name: string
  linked_students: LinkedStudent[]
}

export interface ClassroomCourse {
  course_id: string
  name: string
  section: string
  description: string
  room: string
  owner: string
}

export interface ClassroomLink {
  id: number
  classroom_course_id: string
  classroom_course_name: string
  local_class_id: number | null
  created_at: string
}

export interface ClassroomLinkResponse {
  message: string
  sync_id: number
}

export interface ClassroomTopic {
  topic_id: string
  name: string
}

export interface ClassroomSyncResult {
  id: number
  classroom_course_id: string
  classroom_assignment_id?: string
  assignment_title?: string
}

export const api = new ApiClient()
