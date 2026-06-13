import { apiClient, withMock } from './client'
import { mockPaceTrend, mockPrediction, mockTimeline } from '../mocks/mockData'
import type { ApiResult, Prediction, Selection, TimelinePoint, TrendSeries } from '../types'

function payload(selection: Selection) {
  return {
    year: selection.year,
    round_number: selection.roundNumber,
    driver: selection.driver,
    lap: selection.lap,
  }
}

export function predict(selection: Selection): Promise<ApiResult<Prediction>> {
  return withMock(
    async () => (await apiClient.post<Prediction>('/api/predict', payload(selection))).data,
    () => mockPrediction(selection),
  )
}

export function getPitProbabilityTimeline(selection: Selection): Promise<ApiResult<TimelinePoint[]>> {
  return withMock(
    async () => (await apiClient.get<{ timeline: TimelinePoint[] }>('/api/pit-probability-timeline', { params: payload(selection) })).data.timeline,
    () => mockTimeline(selection),
  )
}

export function getPaceTrend(selection: Selection): Promise<ApiResult<TrendSeries[]>> {
  return withMock(
    async () => (await apiClient.get<{ series: TrendSeries[] }>('/api/pace-trend', { params: payload(selection) })).data.series,
    () => mockPaceTrend(selection),
  )
}
