import axios from 'axios'
import type { ApiResult } from '../types'

export const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/',
  timeout: 75000,
})

export const forceMock = String(import.meta.env.VITE_USE_MOCK || '').toLowerCase() === 'true'
const allowMockFallback = forceMock
  || String(import.meta.env.VITE_ALLOW_MOCK_FALLBACK || '').toLowerCase() === 'true'
  || import.meta.env.DEV

function isTransientApiError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false
  const status = error.response?.status
  return error.code === 'ECONNABORTED'
    || error.code === 'ERR_NETWORK'
    || status === 408
    || status === 429
    || (status !== undefined && status >= 500)
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, milliseconds))
}

export async function withMock<T>(
  request: () => Promise<T>,
  fallback: () => T | Promise<T>,
): Promise<ApiResult<T>> {
  if (forceMock) {
    return { data: await fallback(), source: 'mock' }
  }

  let lastError: unknown

  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      return { data: await request(), source: 'api' }
    } catch (error) {
      lastError = error
      if (attempt === 0 && isTransientApiError(error)) {
        await wait(1200)
        continue
      }
      break
    }
  }

  if (allowMockFallback) {
    console.warn('API unavailable, using mock data.', lastError)
    return { data: await fallback(), source: 'mock' }
  }

  console.error('Production API request failed. Mock fallback is disabled.', lastError)
  throw lastError
}
