import { apiClient, withMock } from './client'
import { mockRaceState } from '../mocks/mockData'
import type { ApiResult, Selection, WeatherState } from '../types'

export function getWeather(selection: Selection): Promise<ApiResult<WeatherState>> {
  const params = {
    year: selection.year,
    round_number: selection.roundNumber,
    driver: selection.driver,
    lap: selection.lap,
  }
  return withMock(
    async () => (await apiClient.get<WeatherState>('/api/weather', { params })).data,
    () => mockRaceState(selection).weather,
  )
}
