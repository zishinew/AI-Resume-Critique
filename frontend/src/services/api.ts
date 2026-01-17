import { API_BASE_URL } from '../config'
import { supabase } from '../lib/supabase'

class ApiService {
  private async getAuthHeaders(): Promise<HeadersInit> {
    const { data: { session } } = await supabase.auth.getSession()
    return session ? { Authorization: `Bearer ${session.access_token}` } : {}
  }

  async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    const authHeaders = await this.getAuthHeaders()
    const headers = {
      ...authHeaders,
      ...options.headers,
    }

    const response = await fetch(`${API_BASE_URL}${url}`, {
      ...options,
      headers,
    })

    // Handle 401 - try to refresh session
    if (response.status === 401) {
      const { data: { session }, error } = await supabase.auth.refreshSession()

      if (session && !error) {
        // Retry with new token
        return fetch(`${API_BASE_URL}${url}`, {
          ...options,
          headers: {
            Authorization: `Bearer ${session.access_token}`,
            ...options.headers,
          },
        })
      }
    }

    return response
  }

  // Convenience methods
  async get(url: string) {
    return this.fetch(url)
  }

  async post(url: string, body?: unknown) {
    return this.fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async put(url: string, body?: unknown) {
    return this.fetch(url, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: body ? JSON.stringify(body) : undefined,
    })
  }

  async delete(url: string) {
    return this.fetch(url, { method: 'DELETE' })
  }
}

export const api = new ApiService()
