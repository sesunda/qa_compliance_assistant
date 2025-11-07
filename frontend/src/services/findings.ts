import api from './api'

export interface Finding {
  id: number
  assessment_id: number
  control_id?: number
  title: string
  description: string
  severity: string
  priority: string
  resolution_status: string
  assigned_to?: number
  assigned_to_username?: string
  assigned_to_name?: string  // Added for FindingDetailPage
  resolved_by?: number
  resolved_by_username?: string
  validated_by?: number
  validated_by_username?: string
  risk_rating?: string
  affected_systems?: string
  remediation_recommendation?: string
  remediation_plan?: string  // Added for FindingDetailPage
  remediation_notes?: string
  resolution_notes?: string  // Added for FindingDetailPage
  false_positive: boolean
  is_false_positive?: boolean  // Alias for compatibility
  due_date?: string
  resolved_at?: string
  validated_at?: string
  updated_at?: string  // Added for FindingDetailPage
  assessment_title: string
  control_name?: string
  comments_count: number
  created_at: string
  metadata_json?: any
}

export interface FindingListItem {
  id: number
  title: string
  severity: string
  priority: string
  resolution_status: string
  assigned_to?: string
  due_date?: string
  assessment_title: string
  created_at: string
  false_positive: boolean
}

export interface CreateFindingData {
  assessment_id: number
  control_id?: number
  title: string
  description: string
  severity: string
  priority?: string
  risk_rating?: string
  affected_systems?: string
  remediation_recommendation?: string
  assigned_to?: number
  due_date?: string
  metadata?: any
}

export interface UpdateFindingData {
  title?: string
  description?: string
  severity?: string
  priority?: string
  affected_systems?: string
  remediation_recommendation?: string
  due_date?: string
  metadata?: any
}

export interface FindingComment {
  id: number
  finding_id: number
  user_id: number
  username: string
  user_name: string  // Added alias for FindingDetailPage
  comment_type: string
  comment_text: string
  comment: string  // Added alias for FindingDetailPage
  created_at: string
}

export const findingsService = {
  // List findings
  list: async (params?: {
    assessment_id?: number
    severity?: string
    resolution_status?: string
    assigned_to_me?: boolean
  }) => {
    const response = await api.get<FindingListItem[]>('/findings', { params })
    return response.data
  },

  // Get finding details
  get: async (id: number) => {
    const response = await api.get<Finding>(`/findings/${id}`)
    return response.data
  },

  // Create finding
  create: async (data: CreateFindingData) => {
    const response = await api.post<Finding>('/findings', data)
    return response.data
  },

  // Update finding
  update: async (id: number, data: UpdateFindingData) => {
    const response = await api.patch<Finding>(`/findings/${id}`, data)
    return response.data
  },

  // Assign finding
  assign: async (id: number, assigned_to: number) => {
    const response = await api.post(`/findings/${id}/assign`, { assigned_to })
    return response.data
  },

  // Resolve finding
  resolve: async (id: number, remediation_notes: string) => {
    const response = await api.post(`/findings/${id}/resolve`, { remediation_notes })
    return response.data
  },

  // Validate finding
  validate: async (id: number, approved: boolean, validation_notes?: string) => {
    const response = await api.post(`/findings/${id}/validate`, {
      approved,
      validation_notes
    })
    return response.data
  },

  // Mark as false positive
  markFalsePositive: async (id: number, justification: string) => {
    const response = await api.post(`/findings/${id}/mark-false-positive`, { justification })
    return response.data
  },

  // Get comments
  getComments: async (id: number) => {
    const response = await api.get<FindingComment[]>(`/findings/${id}/comments`)
    return response.data
  },

  // Add comment
  addComment: async (id: number, comment_type: string, comment_text: string) => {
    const response = await api.post<FindingComment>(`/findings/${id}/comments`, {
      comment_type,
      comment_text
    })
    return response.data
  },

  // Delete finding
  delete: async (id: number) => {
    await api.delete(`/findings/${id}`)
  }
}

export default findingsService
