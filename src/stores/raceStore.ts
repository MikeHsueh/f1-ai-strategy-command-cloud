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

type PageName = 'dashboard' | 'replay' | 'simulator' | 'model-analysis'
type PanelKey =
  | 'health'
  | 'raceState'
  | 'prediction'
  | 'timeline'
  | 'pace'
  | 'features'
  | 'comparison'
  | 'simulation'

interface PanelLoadState {
  loading: boolean
  error: string
}

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

function panelState(): PanelLoadState {
  return { loading: false, error: '' }
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
  const initializing = ref(false)
  const lastUpdated = ref<Date | null>(null)
  const dataSource = ref<DataSource>(forceMock ? 'mock' : 'api')
  const error = ref('')
  const activePage = ref<PageName>('dashboard')
  const panels = reactive<Record<PanelKey, PanelLoadState>>({
    health: panelState(),
    raceState: panelState(),
    prediction: panelState(),
    timeline: panelState(),
    pace: panelState(),
    features: panelState(),
    comparison: panelState(),
    simulation: panelState(),
  })

  const requestTokens: Record<PanelKey, number> = {
    health: 0,
    raceState: 0,
    prediction: 0,
    timeline: 0,
    pace: 0,
    features: 0,
    comparison: 0,
    simulation: 0,
  }
  let deferredContextKey = ''
  let deferredRun = 0

  const loading = computed(() =>
    initializing.value || panels.raceState.loading || panels.prediction.loading,
  )

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

  function selectionSnapshot(): Selection {
    return { ...selection }
  }

  function useSources(...sources: DataSource[]) {
    dataSource.value = forceMock || sources.includes('mock') ? 'mock' : 'api'
  }

  function friendlyPanelError(): string {
    return 'Data unavailable. Please try again shortly.'
  }

  async function runPanelRequest<T>(
    key: PanelKey,
    request: () => Promise<{ data: T; source: DataSource }>,
    apply: (value: T) => void,
  ): Promise<void> {
    const token = ++requestTokens[key]
    panels[key].loading = true
    panels[key].error = ''

    try {
      const result = await request()
      if (token !== requestTokens[key]) return
      apply(result.data)
      useSources(result.source)
    } catch (cause) {
      if (token !== requestTokens[key]) return
      console.error(`Failed to load ${key}.`, cause)
      panels[key].error = friendlyPanelError()
    } finally {
      if (token === requestTokens[key]) panels[key].loading = false
    }
  }

  function loadHealth(): Promise<void> {
    return runPanelRequest('health', getHealth, (value) => {
      health.value = value
    })
  }

  function loadRaceState(): Promise<void> {
    const current = selectionSnapshot()
    return runPanelRequest('raceState', () => getRaceState(current), (value) => {
      raceState.value = value
    })
  }

  function loadPrediction(): Promise<void> {
    const current = selectionSnapshot()
    return runPanelRequest('prediction', () => predict(current), (value) => {
      prediction.value = value
    })
  }

  function loadTimeline(): Promise<void> {
    const current = selectionSnapshot()
    return runPanelRequest('timeline', () => getPitProbabilityTimeline(current), (value) => {
      timeline.value = value
    })
  }

  function loadPaceTrend(): Promise<void> {
    const current = selectionSnapshot()
    return runPanelRequest('pace', () => getPaceTrend(current), (value) => {
      paceTrend.value = value
    })
  }

  function loadFeatures(): Promise<void> {
    const current = selectionSnapshot()
    return runPanelRequest('features', () => getFeatures(current), (value) => {
      features.value = value
    })
  }

  function loadComparison(): Promise<void> {
    const current = selectionSnapshot()
    return runPanelRequest('comparison', () => getDriverComparison(current), (value) => {
      comparison.value = value
    })
  }

  async function refreshCore(): Promise<void> {
    await Promise.allSettled([loadRaceState(), loadPrediction()])
    lastUpdated.value = new Date()
  }

  function clearDeferredTimers() {
    deferredRun += 1
  }

  function waitForDeferredStart(delay: number): Promise<void> {
    return new Promise((resolve) => window.setTimeout(resolve, delay))
  }

  function prepareDeferredPanel(key: PanelKey) {
    panels[key].loading = true
    panels[key].error = ''
  }

  function loadDeferredForActivePage(force = false) {
    clearDeferredTimers()
    if (!seasons.value.length) return

    const contextKey = [
      activePage.value,
      selection.year,
      selection.roundNumber,
      selection.driver,
      selection.lap,
    ].join(':')
    if (!force && deferredContextKey === contextKey) return
    deferredContextKey = contextKey
    const run = deferredRun

    const tasks: Array<[PanelKey, () => Promise<void>]> = activePage.value === 'dashboard'
      ? [
          ['features', loadFeatures],
          ['pace', loadPaceTrend],
          ['comparison', loadComparison],
          ['timeline', loadTimeline],
        ]
      : activePage.value === 'replay'
        ? [
            ['pace', loadPaceTrend],
            ['comparison', loadComparison],
            ['timeline', loadTimeline],
          ]
        : activePage.value === 'model-analysis'
          ? [['features', loadFeatures]]
          : []

    tasks.forEach(([key]) => prepareDeferredPanel(key))

    void (async () => {
      await waitForDeferredStart(150)
      for (const [, task] of tasks) {
        if (run !== deferredRun || deferredContextKey !== contextKey) return
        await task()
        await waitForDeferredStart(120)
      }
    })()
  }

  function activatePage(page: PageName) {
    activePage.value = page
    if (initializing.value) return
    loadDeferredForActivePage()
  }

  async function loadLaps() {
    const result = await getLaps(selectionSnapshot())
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

  async function refreshCurrentPage() {
    await refreshCore()
    loadDeferredForActivePage(true)
  }

  async function setYear(year: number) {
    selection.year = year
    try {
      const result = await getRaces(year)
      races.value = result.data
      useSources(result.source)
      selection.roundNumber = races.value[0]?.round ?? 1
      await setRace(selection.roundNumber)
    } catch (cause) {
      console.error('Failed to load races.', cause)
      error.value = 'Race selector data is temporarily unavailable.'
    }
  }

  async function setRace(roundNumber: number) {
    selection.roundNumber = roundNumber
    selection.lap = 1
    error.value = ''
    try {
      await Promise.all([loadDrivers(), loadLaps()])
    } catch (cause) {
      console.error('Failed to load race metadata.', cause)
      error.value = 'Race selector data is temporarily unavailable.'
    }
    await refreshCurrentPage()
  }

  async function setDriver(driver: string) {
    selection.driver = driver
    simulationResult.value = null
    await refreshCurrentPage()
  }

  async function setLap(lap: number) {
    selection.lap = lap
    simulationResult.value = null
    await refreshCurrentPage()
  }

  async function runSimulation(input: StrategySimulationInput) {
    let result: StrategySimulationResult | null = null
    await runPanelRequest(
      'simulation',
      () => simulateStrategy(selectionSnapshot(), input),
      (value) => {
        simulationResult.value = value
        result = value
      },
    )
    return result
  }

  function resetSimulation() {
    simulationResult.value = null
    panels.simulation.error = ''
  }

  async function initialize() {
    if (initializing.value || seasons.value.length) return
    initializing.value = true
    error.value = ''
    panels.raceState.loading = true
    panels.prediction.loading = true

    try {
      await loadHealth()

      const seasonResult = await getSeasons()
      seasons.value = seasonResult.data
      useSources(seasonResult.source)
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
    } catch (cause) {
      console.error('Failed to initialize race selectors.', cause)
      error.value = 'Race selector data is temporarily unavailable.'
    } finally {
      initializing.value = false
    }

    await refreshCore()
    loadDeferredForActivePage()
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
    panels,
    selectedRace,
    selectedDriver,
    loading,
    initializing,
    lastUpdated,
    dataSource,
    error,
    initialize,
    activatePage,
    refreshDashboard: refreshCurrentPage,
    loadTimeline,
    loadPaceTrend,
    loadFeatures,
    loadComparison,
    loadRaceState,
    loadPrediction,
    loadHealth,
    setYear,
    setRace,
    setDriver,
    setLap,
    runSimulation,
    resetSimulation,
  }
})
