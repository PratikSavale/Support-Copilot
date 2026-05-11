const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const WS_BASE_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000/api/v1/chat/ws'

export { API_BASE_URL, WS_BASE_URL }
