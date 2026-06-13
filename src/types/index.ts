export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'
export type StrategyAction = 'STAY_OUT' | 'MONITOR' | 'PREPARE_PIT' | 'PIT_NOW'
export type DataSource = 'api' | 'mock'
export type TireCompound = 'SOFT' | 'MEDIUM' | 'HARD' | 'INTERMEDIATE' | 'WET'

export interface Selection {
  year: number
  roundNumber: number
  driver: string
  lap: number
}

export interface Season {
  year: number
  rounds: number[]
}

export interface Race {
  round: number
  year: number
  label: string
  short: string
  key: string
  total_laps: number
  terrain?: string
  profile?: string
  length?: string
}

export interface Driver {
  code: string
  name: string
  team: string
}

export interface ModelInfo {
  name: string
  input_dim: number
  sequence_length: number
  feature_count: number
  weights_loaded: boolean
  scaler_mode: string
  device: string
  load_error?: string | null
}

export interface HealthResponse {
  status: 'ok' | 'degraded'
  source: string
  model: ModelInfo
  latency_ms?: number
}

export interface WeatherState {
  air_temp: number
  track_temp: number
  humidity: number
  rain_risk: number
  model_rain_risk: number
  historical_rain_risk: number
  wind_speed: number
  wind_direction: number
  condition: string
}

export interface TireState {
  compound: TireCompound
  life: number
  degradation: number
  temperature_proxy: number
  health: number
}

export interface RaceState {
  lap: number
  total_laps: number
  position: number
  gap_ahead: number
  gap_behind: number
  safety_car: boolean
  safety_car_incident_risk: number
  driver: string
  team: string
  speed: number
  rpm: number
  throttle: number
  brake: number
  weather: WeatherState
  tire: TireState
}

export interface Prediction {
  pit_probability: number
  optimal_pit_lap: number
  recommended_tire: string
  expected_gain: number
  undercut_probability: number
  risk: RiskLevel
  action: StrategyAction
  attention: number[]
}

export interface TimelinePoint {
  lap: number
  probability: number
  actual_pit: boolean
  compound: string
}

export interface TrendPoint {
  label: string
  value: number
}

export interface TrendSeries {
  name: string
  line: 'solid' | 'dashed'
  mode: 'historical' | 'predictive'
  data: TrendPoint[]
}

export interface StrategyOption {
  label: string
  path: string
  trigger: string
  projected_position: number
  projected_text: string
  sample_size: number
  confidence: number
  source: string
}

export interface FeatureItem {
  name: string
  value: number
  importance: number
  group: string
}

export interface DriverComparisonRow {
  code: string
  team: string
  position: number
  gap: string
  compound: string
  tyre_age: number
  pit_probability: number
  predicted_pit_lap: number | null
  pace_delta: number
}

export interface StrategySimulationInput {
  enableInitialTireOverride: boolean
  initialCompound: TireCompound
  initialTyreLife: number
  initialTireHealth: number
  nextCompound: TireCompound
  targetPitLap: number
  safetyCar: boolean
  rainRisk: number
  position?: number
}

export interface StrategySimulationResult {
  pit_probability: number
  projected_position: number
  expected_gain: number
  recommended_tire: string
  summary: string
  live_current_tire: TireState
  simulated_initial_tire: TireState
  target_pit_lap: number
  override_applied: boolean
}

export interface DashboardSnapshot {
  raceState: RaceState
  prediction: Prediction
  timeline: TimelinePoint[]
  paceTrend: TrendSeries[]
  features: FeatureItem[]
  comparison: DriverComparisonRow[]
  strategies: StrategyOption[]
}

export interface ApiResult<T> {
  data: T
  source: DataSource
}

export function classifyRisk(probability: number): { risk: RiskLevel; action: StrategyAction } {
  if (probability >= 0.85) return { risk: 'CRITICAL', action: 'PIT_NOW' }
  if (probability >= 0.65) return { risk: 'HIGH', action: 'PREPARE_PIT' }
  if (probability >= 0.35) return { risk: 'MEDIUM', action: 'MONITOR' }
  return { risk: 'LOW', action: 'STAY_OUT' }
}

export function normalizeProbability(value: unknown): number {
  const number = Number(value)
  if (!Number.isFinite(number)) return 0
  return Math.max(0, Math.min(1, number > 1 ? number / 100 : number))
}
