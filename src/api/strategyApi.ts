import { apiClient, withMock } from './client'
import { mockSimulation } from '../mocks/mockData'
import type {
  ApiResult,
  Selection,
  StrategySimulationInput,
  StrategySimulationResult,
} from '../types'

export function simulateStrategy(
  selection: Selection,
  input: StrategySimulationInput,
): Promise<ApiResult<StrategySimulationResult>> {
  return withMock(
    async () => (await apiClient.post<StrategySimulationResult>('/api/simulate-strategy', {
      year: selection.year,
      round_number: selection.roundNumber,
      driver: selection.driver,
      lap: selection.lap,
      enableInitialTireOverride: input.enableInitialTireOverride,
      initialCompound: input.initialCompound,
      initialTyreLife: input.initialTyreLife,
      initialTireHealth: input.initialTireHealth,
      nextCompound: input.nextCompound,
      targetPitLap: input.targetPitLap,
      safetyCar: input.safetyCar,
      rainRisk: input.rainRisk,
      position: input.position,
    })).data,
    () => mockSimulation(selection, input),
  )
}
