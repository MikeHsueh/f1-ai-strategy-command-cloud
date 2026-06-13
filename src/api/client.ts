import axios from 'axios'
import type { ApiResult } from '../types'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/',
  timeout: 15000,
})

export const forceMock = String(import.meta.env.VITE_USE_MOCK || '').toLowerCase() === 'true'

export async function withMock<T>(
  request: () => Promise<T>,
  fallback: () => T | Promise<T>,
): Promise<ApiResult<T>> {
  if (forceMock) {
    return { data: await fallback(), source: 'mock' }
  }

  try {
    return { data: await request(), source: 'api' }
  } catch (error) {
    console.warn('API unavailable, using mock data.', error)
    return { data: await fallback(), source: 'mock' }
  }
}
