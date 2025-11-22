import axios from 'axios'
import Cookies from 'js-cookie'

// Determine API base URL based on environment
const getApiBaseUrl = () => {
  // In production (Azure), use the API container app URL with HTTPS
  if (window.location.hostname.includes('azurecontainerapps.io')) {
    return 'https://ca-api-qca-dev.victoriousmushroom-f7d2d81f.westus2.azurecontainerapps.io'
  }
  // In development, use proxy
  return '/api'
}

// Create axios instance with base configuration
export const api = axios.create({
  baseURL: getApiBaseUrl(),
  timeout: 30000, // Increased to 30s for cold start wake-up
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true // Ensure cookies are sent with requests
})

// Request interceptor
api.interceptors.request.use(
  (config) => {
    // Add auth token from cookie if available
    const token = Cookies.get('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor with retry logic for cold start
api.interceptors.response.use(
  (response) => {
    return response
  },
  async (error) => {
    const originalRequest = error.config
    
    // Handle cold start: Retry on timeout or 502/503/504 errors
    if (!originalRequest._retry && (
      error.code === 'ECONNABORTED' || 
      error.response?.status === 502 || 
      error.response?.status === 503 || 
      error.response?.status === 504
    )) {
      // Mark request as retried
      originalRequest._retry = true
      originalRequest._retryCount = (originalRequest._retryCount || 0) + 1
      
      // Retry up to 3 times with exponential backoff
      if (originalRequest._retryCount <= 3) {
        const delay = Math.min(1000 * Math.pow(2, originalRequest._retryCount - 1), 5000) // Max 5s delay
        
        console.log(`🔄 Container app waking up... Retry ${originalRequest._retryCount}/3 in ${delay}ms`)
        
        await new Promise(resolve => setTimeout(resolve, delay))
        
        // Increase timeout for retries
        originalRequest.timeout = 30000
        
        return api(originalRequest)
      }
    }
    
    if (error.response?.status === 401) {
      // Only redirect to login if we're NOT already on the login page
      // and NOT attempting to login (don't redirect on failed login attempts)
      const isLoginAttempt = error.config?.url?.includes('/auth/login')
      const isAlreadyOnLoginPage = window.location.pathname === '/login'
      
      if (!isLoginAttempt && !isAlreadyOnLoginPage) {
        // Handle unauthorized access (expired token, etc)
        Cookies.remove('auth_token')
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default api