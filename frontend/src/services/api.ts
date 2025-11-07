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
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
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

// Response interceptor
api.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api