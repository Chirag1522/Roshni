import axios from 'axios'

// Get base URL from environment or use default
let baseURL = import.meta.env.VITE_BACKEND_URL || 'http://localhost:8000'

// Ensure baseURL always ends with /api
if (!baseURL.endsWith('/api')) {
  baseURL = baseURL.endsWith('/') ? baseURL + 'api' : baseURL + '/api'
}

const api = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
    'Cache-Control': 'no-cache',
  },
})

// Add request interceptor for logging
api.interceptors.request.use(
  config => {
    console.log(`[API] ${config.method.toUpperCase()} ${config.url}`)
    return config
  },
  error => Promise.reject(error)
)

// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  error => {
    console.error('[API Error]', error.response?.data || error.message)
    return Promise.reject(error)
  }
)

export default api