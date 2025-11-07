import api from './api'

export interface Assessment {
  id: number
  agency_id: number
  title: string
  assessment_type: string
  framework?: string
  scope?: string
  status: string
  progress_percentage: number
  assigned_to?: number
  assigned_to_username?: string
  target_completion_date?: string
  assessment_period_start?: string
  assessment_period_end?: string
  completed_at?: string
  findings_count: number
  findings_resolved?: number
  findings_by_severity?: {
    critical: number
    high: number
    medium: number
    low: number
    info: number
  }
  controls_tested_count: number
  created_at: string
  metadata_json?: any
}

export interface AssessmentListItem {
  id: number
  title: string
  assessment_type: string
  framework?: string
  status: string
  progress_percentage: number
  assigned_to?: string
  findings_count: number
  controls_tested_count: number
  target_completion_date?: string
  created_at: string
}

export interface CreateAssessmentData {
  title: string
  assessment_type: string
  framework?: string
  scope?: string
  target_completion_date?: string
  period_start?: string
  period_end?: string
  assigned_to?: number
  metadata?: any
}

export interface UpdateAssessmentData {
  title?: string
  scope?: string
  status?: string
  target_completion_date?: string
  metadata?: any
}

export const assessmentsService = {
  // List assessments
  list: async (params?: {
    status_filter?: string
    assessment_type?: string
    assigned_to_me?: boolean
  }) => {
    const response = await api.get<AssessmentListItem[]>('/assessments', { params })
    return response.data
  },

  // Get assessment details
  get: async (id: number) => {
    const response = await api.get<Assessment>(`/assessments/${id}`)
    return response.data
  },

  // Create assessment
  create: async (data: CreateAssessmentData) => {
    const response = await api.post<Assessment>('/assessments', data)
    return response.data
  },

  // Update assessment
  update: async (id: number, data: UpdateAssessmentData) => {
    const response = await api.patch<Assessment>(`/assessments/${id}`, data)
    return response.data
  },

  // Assign assessment
  assign: async (id: number, assigned_to: number) => {
    const response = await api.post(`/assessments/${id}/assign`, { assigned_to })
    return response.data
  },

  // Update progress
  updateProgress: async (id: number, progress_percentage: number) => {
    const response = await api.patch(`/assessments/${id}/progress`, { progress_percentage })
    return response.data
  },

  // Complete assessment
  complete: async (id: number) => {
    const response = await api.post(`/assessments/${id}/complete`)
    return response.data
  },

  // Get assessment controls
  getControls: async (id: number) => {
    const response = await api.get(`/assessments/${id}/controls`)
    return response.data
  },

  // Add controls to assessment
  addControls: async (id: number, control_ids: number[]) => {
    const response = await api.post(`/assessments/${id}/controls`, control_ids)
    return response.data
  },

  // Get assessment findings
  getFindings: async (id: number) => {
    const response = await api.get(`/assessments/${id}/findings`)
    return response.data
  },

  // Delete assessment
  delete: async (id: number) => {
    await api.delete(`/assessments/${id}`)
  }
}

export default assessmentsService
