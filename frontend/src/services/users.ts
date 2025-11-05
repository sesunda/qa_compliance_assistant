import { api } from './api'

export interface Agency {
  id: number
  name: string
  code?: string | null
  description?: string | null
  contact_email?: string | null
}

export interface Role {
  id: number
  name: string
  description?: string | null
  permissions: Record<string, string[]>
  created_at: string
}

export interface UserSummary {
  id: number
  username: string
  email: string
  full_name?: string | null
  agency_id: number
  role_id: number
  is_active: boolean
  is_verified: boolean
  last_login?: string | null
  created_at: string
  updated_at: string
  role?: Role | null
  agency?: Agency | null
}

export interface CreateUserPayload {
  username: string
  email: string
  full_name?: string
  password: string
  agency_id: number
  role_id: number
}

export interface UpdateUserPayload {
  username?: string
  email?: string
  full_name?: string | null
  role_id?: number
  is_active?: boolean
}

export const fetchUsers = async (): Promise<UserSummary[]> => {
  const response = await api.get<UserSummary[]>('/auth/users')
  return response.data
}

export const fetchRoles = async (): Promise<Role[]> => {
  const response = await api.get<Role[]>('/auth/roles')
  return response.data
}

export const fetchAgencies = async (): Promise<Agency[]> => {
  const response = await api.get<Agency[]>('/auth/agencies')
  return response.data
}

export const createUser = async (payload: CreateUserPayload): Promise<UserSummary> => {
  const response = await api.post<UserSummary>('/auth/users', payload)
  return response.data
}

export const updateUser = async (
  userId: number,
  payload: UpdateUserPayload
): Promise<UserSummary> => {
  const response = await api.put<UserSummary>(`/auth/users/${userId}`, payload)
  return response.data
}
