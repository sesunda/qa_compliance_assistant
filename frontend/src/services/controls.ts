import { api } from './api'

export interface ControlSummary {
  id: number
  project_id: number
  agency_id: number
  name: string
  description?: string | null
  control_type?: string | null
  status: string
  created_at: string
  updated_at: string
}

export const fetchControls = async (): Promise<ControlSummary[]> => {
  const response = await api.get<ControlSummary[]>('/controls/')
  return response.data
}
