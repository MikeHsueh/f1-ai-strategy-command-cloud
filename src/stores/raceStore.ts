import { defineStore } from 'pinia'
import { computed, reactive, ref } from 'vue'

import {
  getDriverComparison,
  getDrivers,
  getFeatures,
  getHealth,
  getLaps,
  getRaceState,
  getRaces,
  getSeasons,
} from '../api/raceApi'
import { getPaceTrend, getPitProbabilityTimeline, predict } from '../api/predictionApi'
import { simulateStrategy } from '../api/strategyApi'
import { forceMock } from '../api/client'
import type {
  DataSource,
  Driver,
  DriverComparisonRow,
  FeatureItem,
  HealthResponse,
  Prediction,
  Race,
  RaceState,
  Season,
  Selection,
  StrategyOption,
  StrategySimulationInput,
  StrategySimulationResult,
  TimelinePoint,
  TrendSeries,
} from '../types'

const emptyHealth: HealthResponse = {
  status: 'degraded',
  source: 'standby',
  model: {
    name: 'BiLSTM-Attention-40F',
    input_dim: 40,
    sequence_length: 5,
    feature_count: 40,
    weights_loaded: false,
    scaler_mode: 'standby',
    device: 'unknown',
  },
}

const emptyRaceState: RaceState = {
  lap: 1,
  total_laps: 52,
  position: 1,
  gap_ahead: 0,
  gap_behind: 0,
  safety_car: false,
  safety_car_incident_risk: 0,
  driver: 'NOR',
  team: 'McLaren',
  speed: 0,
  rpm: 0,
  throttle: 0,
  brake: 0,
  weather: {
    air_temp: 0,
    track_temp: 0,
    humidity: 0,
    rain_risk: 0,
    model_rain_risk: 0,
    historical_rain_risk: 0,
    wind_speed: 0,
    wind_direction: 0,
    condition: 'dry',
  },
  tire: {
    compound: 'MEDIUM',
    life: 0,
    degradation: 0,
    temperature_proxy: 0,
    health: 100,
  },
}

const emptyPrediction: Prediction = {
  pit_probability: 0,
  optimal_pit_lap: 0,
  recommended_tire: 'HOLD',
  expected_gain: 0,
  undercut_probability: 0,
  risk: 'LOW',
  action: 'STAY_OUT',
  attention: [],
}

export const useRaceStore = defineStore('race', () => {
  const selection = reactive<Selection>({
    year: 2024,
    roundNumber: 12,
    driver: 'NOR',
    lap: 1,
  })

  const seasons = ref<Season[]>([])
  const races = ref<Race[]>([])
  const drivers = ref<Driver[]>([])
  const laps = ref<number[]>([])
  const health = ref<HealthResponse>(emptyHealth)
  const raceState = ref<RaceState>(emptyRaceState)
  const prediction = ref<Prediction>(emptyPrediction)
  const timeline = ref<TimelinePoint[]>([])
  const paceTrend = ref<TrendSeries[]>([])
  const features = ref<FeatureItem[]>([])
  const comparison = ref<DriverComparisonRow[]>([])
  const simulationResult = ref<StrategySimulationResult | null>(null)
  const loading = ref(false)
  const initializing = ref(false)
  const lastUpdated = ref<Date | null>(null)
  const dataSource = ref<DataSource>(forceMock ? 'mock' : 'api')
  const error = ref('')
  let requestId = 0

  const selectedRace = computed(() =>
    races.value.find((race) => race.round === selection.roundNumber) ?? races.value[0],
  )

  const selectedDriver = computed(() =>
    drivers.value.find((driver) => driver.code === selection.driver),
  )

  const strategyOptions = computed<StrategyOption[]>(() => {
    const currentPosition = raceState.value.position
    const confidence = prediction.value.pit_probability
    return [
      {
        label: 'Primary',
        path: `${raceState.value.tire.compound} -> ${prediction.value.recommended_tire}`,
        trigger: `Box L${prediction.value.optimal_pit_lap}`,
        projected_position: Math.max(1, currentPosition - (confidence >= 0.65 ? 1 : 0)),
        projected_text: `P${Math.max(1, currentPosition - (confidence >= 0.65 ? 1 : 0))}`,
        sample_size: Math.max(1, Math.round(24 + confidence * 38)),
        confidence,
        source: dataSource.value,
      },
      {
        label: 'Extend',
        path: `${raceState.value.tire.compound} long-run`,
        trigger: `Extend ${Math.max(2, Math.round((1 - confidence) * 6))} laps`,
        projected_position: Math.min(20, currentPosition + (confidence >= 0.65 ? 2 : 0)),
        projected_text: `P${Math.min(20, currentPosition + (confidence >= 0.65 ? 2 : 0))}`,
        sample_size: Math.max(1, Math.round(18 + (1 - confidence) * 44)),
        confidence: Math.max(0.08, 1 - confidence),
        source: dataSource.value,
      },
      {
        label: 'Safety Car',
        path: `SC -> ${raceState.value.weather.rain_risk > 45 ? 'INTERMEDIATE' : prediction.value.recommended_tire}`,
        trigger: 'Neutralized pit delta',
        projected_position: Math.max(1, currentPosition - 1),
        projected_text: `P${Math.max(1, currentPosition - 1)}`,
        sample_size: Math.max(1, Math.round(raceState.value.safety_car_incident_risk * 100)),
        confidence: Math.min(0.92, raceState.value.safety_car_incident_risk + 0.35),
        source: dataSource.value,
      },
    ]
  })

  function useSources(...sources: DataSource[]) {
    dataSource.value = forceMock || sources.includes('mock') ? 'mock' : 'api'
  }

  async function refreshDashboard() {
    const currentRequest = ++requestId
    loading.value = true
    error.value = ''
    if (!forceMock) dataSource.value = 'api'

    try {
      const [stateResult, predictionResult, timelineResult, trendResult, featureResult, comparisonResult] =
        await Promise.all([
          getRaceState(selection),
          predict(selection),
          getPitProbabilityTimeline(selection),
          getPaceTrend(selection),
          getFeatures(selection),
          getDriverComparison(selection),
        ])

      if (currentRequest !== requestId) return

      raceState.value = stateResult.data
      prediction.value = predictionResult.data
      timeline.value = timelineResult.data
      paceTrend.value = trendResult.data
      features.value = featureResult.data
      comparison.value = comparisonResult.data
      useSources(
        stateResult.source,
        predictionResult.source,
        timelineResult.source,
        trendResult.source,
        featureResult.source,
        comparisonResult.source,
      )
      lastUpdated.value = new Date()
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Dashboard refresh failed.'
    } finally {
      if (currentRequest === requestId) loading.value = false
    }
  }

  async function loadLaps() {
    const result = await getLaps(selection)
    laps.value = result.data
    useSources(result.source)
    if (!laps.value.includes(selection.lap)) selection.lap = laps.value[0] ?? 1
  }

  async function loadDrivers() {
    const result = await getDrivers(selection.year, selection.roundNumber)
    drivers.value = result.data
    useSources(result.source)
    if (!drivers.value.some((driver) => driver.code === selection.driver)) {
      selection.driver = drivers.value[0]?.code ?? 'NOR'
    }
  }

  async function setYear(year: number) {
    selection.year = year
    const result = await getRaces(year)
    races.value = result.data
    useSources(result.source)
    selection.roundNumber = races.value[0]?.round ?? 1
    await setRace(selection.roundNumber)
  }

  async function setRace(roundNumber: number) {
    selection.roundNumber = roundNumber
    selection.lap = 1
    await Promise.all([loadDrivers(), loadLaps()])
    await refreshDashboard()
  }

  async function setDriver(driver: string) {
    selection.driver = driver
    simulationResult.value = null
    await refreshDashboard()
  }

  async function setLap(lap: number) {
    selection.lap = lap
    simulationResult.value = null
    await refreshDashboard()
  }

  async function runSimulation(input: StrategySimulationInput) {
    const result = await simulateStrategy(selection, input)
    simulationResult.value = result.data
    useSources(result.source)
    return result.data
  }

  function resetSimulation() {
    simulationResult.value = null
  }

  async function initialize() {
    if (initializing.value || seasons.value.length) return
    initializing.value = true
    error.value = ''
    try {
      // Wake cloud instances with the lightweight health request before
      // loading datasets and running model-backed dashboard queries.
      const healthResult = await getHealth()
      health.value = healthResult.data
      useSources(healthResult.source)

      const seasonResult = await getSeasons()
      seasons.value = seasonResult.data
      useSources(healthResult.source, seasonResult.source)

      if (!seasons.value.some((season) => season.year === selection.year)) {
        selection.year = seasons.value[0]?.year ?? 2024
      }

      const raceResult = await getRaces(selection.year)
      races.value = raceResult.data
      useSources(raceResult.source)
      if (!races.value.some((race) => race.round === selection.roundNumber)) {
        selection.roundNumber = races.value[0]?.round ?? 1
      }

      await Promise.all([loadDrivers(), loadLaps()])
      await refreshDashboard()
    } catch (cause) {
      error.value = cause instanceof Error ? cause.message : 'Initialization failed.'
    } finally {
      initializing.value = false
    }
  }

  return {
    selection,
    seasons,
    races,
    drivers,
    laps,
    health,
    raceState,
    prediction,
    timeline,
    paceTrend,
    features,
    comparison,
    strategyOptions,
    simulationResult,
    selectedRace,
    selectedDriver,
    loading,
    initializing,
    lastUpdated,
    dataSource,
    error,
    initialize,
    refreshDashboard,
    setYear,
    setRace,
    setDriver,
    setLap,
    runSimulation,
    resetSimulation,
  }
})
