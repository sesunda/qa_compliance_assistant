import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  role: {
    name: string
    description: string
    permissions: Record<string, string[]> | null
  } | null
  agency_id: number
  is_active: boolean
  agency?: {
    id: number
    name: string
    code?: string | null
    description?: string | null
    contact_email?: string | null
  } | null
}

interface AuthState {
  token: string | null
  user: User | null
  isAuthenticated: boolean
  login: (token: string, user: User) => void
  logout: () => void
  updateUser: (user: User) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,
      isAuthenticated: false,
      login: (token: string, user: User) =>
        set({ token, user, isAuthenticated: true }),
      logout: () =>
        set({ token: null, user: null, isAuthenticated: false }),
      updateUser: (user: User) =>
        set((state) => ({ ...state, user })),
    }),
    {
      name: 'auth-storage',
    }
  )
)