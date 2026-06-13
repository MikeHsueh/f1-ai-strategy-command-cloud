import { apiClient, withMock } from './client'
import {
  mockComparison,
  mockDrivers,
  mockFeatures,
  mockHealth,
  mockRaceState,
  mockRaces,
  mockSeasons,
} from '../mocks/mockData'
import type {
  ApiResult,
  Driver,
  DriverComparisonRow,
  FeatureItem,
  HealthResponse,
  Race,
  RaceState,
  Season,
  Selection,
} from '../types'

let seasonsRequest: Promise<ApiResult<Season[]>> | null = null
const raceRequests = new Map<number, Promise<ApiResult<Race[]>>>()
const driverRequests = new Map<string, Promise<ApiResult<Driver[]>>>()

function cacheRequest<K, T>(
  cache: Map<K, Promise<T>>,
  key: K,
  loader: () => Promise<T>,
): Promise<T> {
  const existing = cache.get(key)
  if (existing) return existing

  const request = loader().catch((error) => {
    cache.delete(key)
    throw error
  })
  cache.set(key, request)
  return request
}

function query(selection: Selection) {
  return {
    year: selection.year,
    round_number: selection.roundNumber,
    driver: selection.driver,
    lap: selection.lap,
  }
}

export function getHealth(): Promise<ApiResult<HealthResponse>> {
  return withMock(
    async () => (await apiClient.get<HealthResponse>('/api/health')).data,
    mockHealth,
  )
}

export function getSeasons(): Promise<ApiResult<Season[]>> {
  if (!seasonsRequest) {
    seasonsRequest = withMock(
      async () => (await apiClient.get<{ seasons: Season[] }>('/api/seasons')).data.seasons,
      () => mockSeasons,
    ).catch((error) => {
      seasonsRequest = null
      throw error
    })
  }
  return seasonsRequest
}

export function getRaces(year: number): Promise<ApiResult<Race[]>> {
  return cacheRequest(raceRequests, year, () =>
    withMock(
      async () => (await apiClient.get<{ races: Race[] }>('/api/races', { params: { year } })).data.races,
      () => mockRaces.map((race) => ({ ...race, year })),
    ),
  )
}

export function getDrivers(year: number, roundNumber: number): Promise<ApiResult<Driver[]>> {
  const key = `${year}:${roundNumber}`
  return cacheRequest(driverRequests, key, () =>
    withMock(
      async () => (await apiClient.get<{ drivers: Driver[] }>('/api/drivers', { params: { year, round_number: roundNumber } })).data.drivers,
      () => mockDrivers,
    ),
  )
}

export function getLaps(selection: Selection): Promise<ApiResult<number[]>> {
  return withMock(
    async () => (await apiClient.get<{ laps: number[] }>('/api/laps', { params: query(selection) })).data.laps,
    () => {
      const total = mockRaces.find((race) => race.round === selection.roundNumber)?.total_laps ?? 52
      return Array.from({ length: total }, (_, index) => index + 1)
    },
  )
}

export function getRaceState(selection: Selection): Promise<ApiResult<RaceState>> {
  return withMock(
    async () => (await apiClient.get<RaceState>('/api/race-state', { params: query(selection) })).data,
    () => mockRaceState(selection),
  )
}

export function getFeatures(selection: Selection): Promise<ApiResult<FeatureItem[]>> {
  return withMock(
    async () => (await apiClient.get<{ features: FeatureItem[] }>('/api/features', { params: query(selection) })).data.features,
    () => mockFeatures(selection),
  )
}

export function getDriverComparison(selection: Selection): Promise<ApiResult<DriverComparisonRow[]>> {
  return withMock(
    async () => (await apiClient.get<{ drivers: DriverComparisonRow[] }>('/api/driver-comparison', { params: query(selection) })).data.drivers,
    () => mockComparison(selection),
  )
}
