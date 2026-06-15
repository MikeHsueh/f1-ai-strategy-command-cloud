import type {
  DashboardSnapshot,
  Driver,
  DriverComparisonRow,
  FeatureItem,
  HealthResponse,
  Prediction,
  Race,
  RaceState,
  Season,
  Selection,
  StrategySimulationInput,
  StrategySimulationResult,
  TireCompound,
  TireState,
  TimelinePoint,
  TrendSeries,
} from '../types'
import { classifyRisk } from '../types'

export const mockSeasons: Season[] = [
  { year: 2024, rounds: Array.from({ length: 24 }, (_, index) => index + 1) },
  { year: 2023, rounds: Array.from({ length: 22 }, (_, index) => index + 1) },
  { year: 2022, rounds: Array.from({ length: 22 }, (_, index) => index + 1) },
]

export const mockRaces: Race[] = [
  { year: 2024, round: 1, label: 'Bahrain GP', short: 'BHR', key: 'Bahrain', total_laps: 57, terrain: 'Permanent', profile: 'traction' },
  { year: 2024, round: 8, label: 'Monaco GP', short: 'MON', key: 'Monaco', total_laps: 78, terrain: 'Street', profile: 'technical' },
  { year: 2024, round: 12, label: 'British GP', short: 'GBR', key: 'GreatBritain', total_laps: 52, terrain: 'Permanent', profile: 'high speed' },
  { year: 2024, round: 18, label: 'Singapore GP', short: 'SGP', key: 'Singapore', total_laps: 62, terrain: 'Street', profile: 'high downforce' },
  { year: 2024, round: 24, label: 'Abu Dhabi GP', short: 'ARE', key: 'AbuDhabi', total_laps: 58, terrain: 'Permanent', profile: 'balanced' },
]

export const mockDrivers: Driver[] = [
  ['VER', 'Max Verstappen', 'Red Bull Racing'],
  ['NOR', 'Lando Norris', 'McLaren'],
  ['LEC', 'Charles Leclerc', 'Ferrari'],
  ['PIA', 'Oscar Piastri', 'McLaren'],
  ['SAI', 'Carlos Sainz', 'Ferrari'],
  ['HAM', 'Lewis Hamilton', 'Mercedes'],
  ['RUS', 'George Russell', 'Mercedes'],
  ['ALO', 'Fernando Alonso', 'Aston Martin'],
  ['PER', 'Sergio Perez', 'Red Bull Racing'],
  ['STR', 'Lance Stroll', 'Aston Martin'],
].map(([code, name, team]) => ({ code, name, team }))

function driverIndex(code: string): number {
  const index = mockDrivers.findIndex((driver) => driver.code === code)
  return index >= 0 ? index : 1
}

function probabilityAt(selection: Selection, offset = 0): number {
  const index = driverIndex(selection.driver)
  const wave = Math.sin((selection.lap + offset + index * 2.3) / 6) * 0.11
  const stintPressure = Math.max(0, ((selection.lap + offset) % 22) - 10) * 0.035
  return Math.max(0.06, Math.min(0.96, 0.18 + wave + stintPressure))
}

export function mockHealth(): HealthResponse {
  return {
    status: 'ok',
    source: 'mock-engine',
    model: {
      name: 'BiLSTM-Attention-40F',
      input_dim: 40,
      sequence_length: 5,
      feature_count: 40,
      weights_loaded: true,
      scaler_mode: 'mock',
      device: 'browser',
    },
    latency_ms: 0,
  }
}

export function mockRaceState(selection: Selection): RaceState {
  const race = mockRaces.find((item) => item.round === selection.roundNumber) ?? mockRaces[2]
  const index = driverIndex(selection.driver)
  const wet = selection.roundNumber === 12 && selection.lap < 18
  const life = Math.max(1, selection.lap % 18)
  return {
    lap: selection.lap,
    total_laps: race.total_laps,
    position: Math.min(20, index + 1),
    gap_ahead: Number((0.7 + index * 0.18).toFixed(2)),
    gap_behind: Number((0.9 + index * 0.16).toFixed(2)),
    safety_car: false,
    safety_car_incident_risk: wet ? 0.24 : 0.08,
    driver: selection.driver,
    team: mockDrivers[index]?.team ?? 'Unknown',
    speed: 284 - index * 2,
    rpm: 11050 - index * 35,
    throttle: 74,
    brake: 16,
    weather: {
      air_temp: wet ? 15.8 : 23.4,
      track_temp: wet ? 27.7 : 36.1,
      humidity: wet ? 67 : 48,
      rain_risk: wet ? 100 : 8,
      model_rain_risk: wet ? 100 : 5,
      historical_rain_risk: wet ? 100 : 10,
      wind_speed: 12.4,
      wind_direction: 248,
      condition: wet ? 'wet' : 'dry',
    },
    tire: {
      compound: wet ? 'INTERMEDIATE' : life > 12 ? 'HARD' : 'MEDIUM',
      life,
      degradation: Number((0.018 + life * 0.0042).toFixed(3)),
      temperature_proxy: wet ? 78 : 94,
      health: Math.max(18, Math.round(100 - life * 4.3)),
    },
  }
}

export function mockPrediction(selection: Selection): Prediction {
  const pit_probability = probabilityAt(selection)
  const status = classifyRisk(pit_probability)
  return {
    pit_probability,
    optimal_pit_lap: Math.min(selection.lap + Math.max(1, Math.round((1 - pit_probability) * 5)), 78),
    recommended_tire: selection.roundNumber === 12 && selection.lap < 18 ? 'INTERMEDIATE' : 'HARD',
    expected_gain: Number((1.1 + pit_probability * 4.2).toFixed(2)),
    undercut_probability: Math.min(0.91, 0.38 + pit_probability * 0.42),
    ...status,
    attention: [0.06, 0.11, 0.17, 0.25, 0.41],
  }
}

export function mockTimeline(selection: Selection): TimelinePoint[] {
  const total = mockRaces.find((race) => race.round === selection.roundNumber)?.total_laps ?? 52
  return Array.from({ length: total }, (_, index) => {
    const lap = index + 1
    const probability = probabilityAt({ ...selection, lap })
    return {
      lap,
      probability,
      actual_pit: lap === 17 || lap === 38,
      compound: lap < 17 ? 'MEDIUM' : lap < 38 ? 'HARD' : 'SOFT',
    }
  })
}

export function mockFeatures(selection: Selection): FeatureItem[] {
  const state = mockRaceState(selection)
  const values: Array<[string, number, number, string]> = [
    ['PitPressureIndex', probabilityAt(selection), 0.19, 'Strategy'],
    ['NormalizedPaceLoss', 0.034, 0.15, 'Tire Physics'],
    ['TyreLife', state.tire.life, 0.13, 'Race State'],
    ['Degradation', state.tire.degradation, 0.11, 'Tire Physics'],
    ['LapTimeTrend', 0.082, 0.09, 'Tire Physics'],
    ['WetConditionIndex', state.weather.rain_risk / 100, 0.08, 'Weather'],
    ['FuelLoad', Math.max(0, 110 * (1 - selection.lap / state.total_laps)), 0.07, 'Race State'],
    ['GapAhead', state.gap_ahead, 0.06, 'Strategy'],
    ['TrackTemp', state.weather.track_temp, 0.05, 'Weather'],
    ['BrakeRatio', 0.19, 0.04, 'Telemetry'],
  ]
  return values.map(([name, value, importance, group]) => ({ name, value, importance, group }))
}

export function mockComparison(selection: Selection): DriverComparisonRow[] {
  return mockDrivers.map((driver, index) => {
    const probability = probabilityAt({ ...selection, driver: driver.code })
    return {
      code: driver.code,
      team: driver.team,
      position: index + 1,
      gap: index === 0 ? 'Leader' : `+${(index * 1.18).toFixed(1)}`,
      compound: index % 5 === 4 ? 'HARD' : 'MEDIUM',
      tyre_age: 4 + ((selection.lap + index) % 16),
      pit_probability: probability,
      predicted_pit_lap: selection.lap + Math.max(1, Math.round((1 - probability) * 6)),
      pace_delta: Number(((index - driverIndex(selection.driver)) * 0.12).toFixed(3)),
    }
  })
}

export function mockPaceTrend(selection: Selection): TrendSeries[] {
  const labels = Array.from({ length: 12 }, (_, index) => `L${Math.max(1, selection.lap - 3) + Math.floor(index / 3)} S${(index % 3) + 1}`)
  return [
    {
      name: 'Gap to car ahead',
      line: 'solid',
      mode: 'historical',
      data: labels.slice(0, 9).map((label, index) => ({ label, value: Number((0.62 - index * 0.035).toFixed(3)) })),
    },
    {
      name: 'Gap to car ahead projected',
      line: 'dashed',
      mode: 'predictive',
      data: labels.slice(9).map((label, index) => ({ label, value: Number((0.3 - index * 0.045).toFixed(3)) })),
    },
    {
      name: 'Gap to car behind',
      line: 'solid',
      mode: 'historical',
      data: labels.slice(0, 9).map((label, index) => ({ label, value: Number((-0.55 - index * 0.025).toFixed(3)) })),
    },
    {
      name: 'Gap to car behind projected',
      line: 'dashed',
      mode: 'predictive',
      data: labels.slice(9).map((label, index) => ({ label, value: Number((-0.78 - index * 0.04).toFixed(3)) })),
    },
  ]
}

export function mockDashboard(selection: Selection): DashboardSnapshot {
  return {
    raceState: mockRaceState(selection),
    prediction: mockPrediction(selection),
    timeline: mockTimeline(selection),
    paceTrend: mockPaceTrend(selection),
    features: mockFeatures(selection),
    comparison: mockComparison(selection),
    strategies: [
      { label: 'Option A', path: 'MEDIUM -> INTERMEDIATE', trigger: 'Box next lap', projected_position: 3, projected_text: 'P3', sample_size: 28, confidence: 0.82, source: 'mock' },
      { label: 'Option B', path: 'MEDIUM -> HARD', trigger: 'Extend 4 laps', projected_position: 5, projected_text: 'P5', sample_size: 41, confidence: 0.71, source: 'mock' },
      { label: 'Option C', path: 'SC -> INTERMEDIATE', trigger: 'Safety car', projected_position: 2, projected_text: 'P2', sample_size: 13, confidence: 0.64, source: 'mock' },
    ],
  }
}

export function mockSimulation(selection: Selection, input: StrategySimulationInput): StrategySimulationResult {
  const base = probabilityAt(selection)
  const liveState = mockRaceState(selection)
  const live = liveState.tire
  const simulatedCompound = input.enableInitialTireOverride ? input.initialCompound : live.compound
  const simulatedLife = input.enableInitialTireOverride ? input.initialTyreLife : live.life
  const expectedLife: Record<TireCompound, number> = {
    SOFT: 18,
    MEDIUM: 26,
    HARD: 36,
    INTERMEDIATE: 20,
    WET: 24,
  }
  const simulatedHealth = Math.max(
    5,
    Math.min(100, 100 - (simulatedLife / expectedLife[simulatedCompound]) * 72 - simulatedLife * 0.055 * 8),
  )
  const simulatedTire: TireState = {
    compound: simulatedCompound,
    life: simulatedLife,
    health: Number(simulatedHealth.toFixed(1)),
    degradation: Number((simulatedLife * 0.055).toFixed(3)),
    temperature_proxy: live.temperature_proxy,
  }
  const scBoost = input.safetyCar ? 0.18 : 0
  const weatherBoost = input.rainRisk > 50 ? 0.12 : 0
  const tirePressure = input.enableInitialTireOverride
    ? Math.max(-0.15, Math.min(0.35, (100 - simulatedHealth) / 180))
    : 0
  const pit_probability = Math.max(0.01, Math.min(0.99, base + scBoost + weatherBoost + tirePressure))
  const decision = classifyRisk(pit_probability)
  const recommendedTire = input.rainRisk > 70
    ? 'WET'
    : input.rainRisk > 35
      ? 'INTERMEDIATE'
      : input.nextCompound
  return {
    pit_probability,
    projected_position: Math.max(1, (input.position ?? driverIndex(selection.driver) + 1) - (pit_probability > 0.65 ? 1 : 0)),
    expected_gain: Number((pit_probability * 5.4).toFixed(2)),
    recommended_tire: recommendedTire,
    selected_next_compound: input.nextCompound,
    optimal_pit_lap: input.targetPitLap,
    undercut_probability: Math.min(0.95, 0.35 + pit_probability * 0.45),
    risk: decision.risk,
    action: decision.action,
    attention: [0.06, 0.11, 0.17, 0.25, 0.41],
    summary: input.safetyCar ? 'Pit window improves under Safety Car delta.' : 'Strategy recalculated from the selected race state.',
    live_current_tire: { ...live },
    simulated_initial_tire: simulatedTire,
    simulated_weather: {
      ...liveState.weather,
      rain_risk: input.rainRisk,
      model_rain_risk: input.rainRisk,
      condition: input.rainRisk >= 45 ? 'wet' : 'dry',
    },
    target_pit_lap: input.targetPitLap,
    override_applied: input.enableInitialTireOverride,
  }
}
