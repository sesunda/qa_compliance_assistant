import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import Cookies from 'js-cookie'
import { api } from '../services/api'
import toast from 'react-hot-toast'

interface User {
  id: number
  username: string
  email: string
  full_name: string
  agency_id: number
  role_id: number
  is_active: boolean
  is_verified: boolean
  role: {
    name: string
    description: string
    permissions: Record<string, string[]> | null
  } | null
  agency?: {
    id: number
    name: string
    code?: string | null
    description?: string | null
    contact_email?: string | null
  } | null
  permissions?: Record<string, string[]> | null
}

interface AuthContextType {
  user: User | null
  token: string | null
  isLoading: boolean
  login: (username: string, password: string) => Promise<boolean>
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

interface AuthProviderProps {
  children: ReactNode
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null)
  const [token, setToken] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const initAuth = async () => {
      // Clean up old localStorage auth data from previous Zustand implementation
      localStorage.removeItem('auth-storage')
      
      const savedToken = Cookies.get('auth_token')
      if (savedToken) {
        setToken(savedToken)
        api.defaults.headers.common['Authorization'] = `Bearer ${savedToken}`
        
        try {
          const response = await api.get('/auth/me')
          setUser(response.data)
        } catch (error) {
          // Token is invalid, remove it
          Cookies.remove('auth_token')
          setToken(null)
          delete api.defaults.headers.common['Authorization']
        }
      }
      setIsLoading(false)
    }

    initAuth()
  }, [])

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await api.post('/auth/login', { username, password })
      const { access_token } = response.data
      
      setToken(access_token)
      
      // Save token to cookie
      Cookies.set('auth_token', access_token, { expires: 1 }) // 1 day
      api.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      
      // Fetch complete user data with permissions from /auth/me
      try {
        const meResponse = await api.get('/auth/me')
        setUser(meResponse.data)
      } catch (meError) {
        console.error('Failed to fetch user details:', meError)
        // Fallback to user from login response if /me fails
        const { user: userData } = response.data
        setUser(userData)
      }
      
      toast.success('Login successful!')
      return true
    } catch (error) {
      toast.error('Login failed. Please check your credentials.')
      return false
    }
  }

  const logout = () => {
    setUser(null)
    setToken(null)
    Cookies.remove('auth_token')
    delete api.defaults.headers.common['Authorization']
    toast.success('Logged out successfully')
  }

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    login,
    logout,
    isAuthenticated: !!user
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}