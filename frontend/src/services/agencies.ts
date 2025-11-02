import { api } from './api'

export interface Agency {
  id: number
  name: string
  code: string | null
  description: string | null
  contact_email: string | null
  active: boolean
  created_at: string
}

export interface AgencyCreate {
  name: string
  code?: string
  description?: string
  contact_email?: string
  active?: boolean
}

export interface AgencyUpdate {
  name?: string
  code?: string
  description?: string
  contact_email?: string
  active?: boolean
}

export interface AgencyStats {
  agency_id: number
  agency_name: string
  total_users: number
  active_users: number
  total_projects: number
}

export const agenciesService = {
  getAll: async (params?: { active_only?: boolean; search?: string }) => {
    const response = await api.get<Agency[]>('/agencies/', { params })
    return response.data
  },

  getById: async (id: number) => {
    const response = await api.get<Agency>(`/agencies/${id}`)
    return response.data
  },

  create: async (data: AgencyCreate) => {
    const response = await api.post<Agency>('/agencies/', data)
    return response.data
  },

  update: async (id: number, data: AgencyUpdate) => {
    const response = await api.put<Agency>(`/agencies/${id}`, data)
    return response.data
  },

  delete: async (id: number) => {
    await api.delete(`/agencies/${id}`)
  },

  getStats: async (id: number) => {
    const response = await api.get<AgencyStats>(`/agencies/${id}/stats`)
    return response.data
  }
}
