// API Configuration
// Update this URL after deploying your backend to production
export const API_BASE_URL = import.meta.env.PROD 
  ? 'https://ai-resume-critique-production.up.railway.app'
  : 'http://localhost:8000'

export const WS_BASE_URL = import.meta.env.PROD
  ? 'wss://ai-resume-critique-production.up.railway.app'
  : 'ws://localhost:8000'
