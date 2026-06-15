<script setup lang="ts">
import { computed, defineAsyncComponent, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import AsyncPanelPlaceholder from '../components/AsyncPanelPlaceholder.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import StrategyRecommendation from '../components/StrategyRecommendation.vue'
import TireHealthPanel from '../components/TireHealthPanel.vue'
import WeatherPanel from '../components/WeatherPanel.vue'
import WhatIfSimulator from '../components/WhatIfSimulator.vue'
import { useRaceStore } from '../stores/raceStore'
import { classifyRisk } from '../types'
import type { Prediction, StrategyOption } from '../types'

const PitProbabilityGauge = defineAsyncComponent({
  loader: () => import('../components/PitProbabilityGauge.vue'),
  loadingComponent: AsyncPanelPlaceholder,
  delay: 0,
})

const store = useRaceStore()
const {
  selection, seasons, races, drivers, laps, raceState, prediction,
  strategyOptions, simulationResult, loading, panels, dataSource,
} = storeToRefs(store)

onMounted(() => store.activatePage('simulator'))

const simulatedDecision = computed(() =>
  classifyRisk(simulationResult.value?.pit_probability ?? prediction.value.pit_probability),
)

const simulatedPrediction = computed<Prediction>(() => {
  const result = simulationResult.value
  if (!result) return prediction.value

  return {
    pit_probability: result.pit_probability,
    optimal_pit_lap: result.optimal_pit_lap,
    recommended_tire: result.recommended_tire,
    expected_gain: result.expected_gain,
    undercut_probability: result.undercut_probability,
    risk: result.risk,
    action: result.action,
    attention: result.attention,
  }
})

const simulatedOptions = computed<StrategyOption[]>(() => {
  const result = simulationResult.value
  if (!result) return strategyOptions.value

  const initialCompound = result.simulated_initial_tire.compound
  return [
    {
      label: 'Simulated plan',
      path: `${initialCompound} -> ${result.recommended_tire}`,
      trigger: `Box L${result.target_pit_lap}`,
      projected_position: result.projected_position,
      projected_text: `P${result.projected_position}`,
      sample_size: 0,
      confidence: result.pit_probability,
      source: dataSource.value,
    },
    {
      label: 'Stay out',
      path: `${initialCompound} long-run`,
      trigger: `Hold beyond L${result.target_pit_lap}`,
      projected_position: raceState.value.position,
      projected_text: `P${raceState.value.position}`,
      sample_size: 0,
      confidence: 1 - result.pit_probability,
      source: dataSource.value,
    },
  ]
})

const displayedTire = computed(() =>
  simulationResult.value?.simulated_initial_tire ?? raceState.value.tire,
)

const displayedWeather = computed(() =>
  simulationResult.value?.simulated_weather ?? raceState.value.weather,
)
</script>

<template>
  <div class="page simulator-page">
    <RaceSelectorBar
      :seasons="seasons" :races="races" :drivers="drivers" :laps="laps"
      :year="selection.year" :round-number="selection.roundNumber" :driver="selection.driver"
      :lap="selection.lap" :loading="loading"
      @year="store.setYear" @race="store.setRace" @driver="store.setDriver"
      @lap="store.setLap" @refresh="store.refreshDashboard"
    />

    <div class="simulator-page-grid">
      <WhatIfSimulator
        class="simulator-workbench"
        :race-state="raceState"
        :result="simulationResult"
        :request-error="panels.simulation.error"
        :loading="panels.simulation.loading"
        :disabled="panels.raceState.loading || panels.prediction.loading"
        allow-initial-override
        @simulate="store.runSimulation"
        @reset="store.resetSimulation"
      />
      <PitProbabilityGauge
        class="simulator-gauge"
        :probability="simulationResult?.pit_probability ?? prediction.pit_probability"
        :risk="simulatedDecision.risk"
        :action="simulatedDecision.action"
        :loading="panels.simulation.loading || (!simulationResult && panels.prediction.loading)"
        :error="panels.simulation.error || panels.prediction.error"
        @retry="simulationResult || panels.simulation.error ? store.retrySimulation() : store.loadPrediction()"
      />
      <StrategyRecommendation
        class="simulator-strategy"
        :prediction="simulatedPrediction"
        :options="simulatedOptions"
        :current-compound="simulationResult?.simulated_initial_tire.compound"
        :loading="panels.simulation.loading || (!simulationResult && panels.prediction.loading)"
        :error="panels.simulation.error || panels.prediction.error"
        @retry="simulationResult || panels.simulation.error ? store.retrySimulation() : store.loadPrediction()"
      />
      <TireHealthPanel
        class="simulator-tire"
        :tire="displayedTire"
        :loading="panels.simulation.loading || (!simulationResult && panels.raceState.loading)"
        :error="panels.simulation.error || panels.raceState.error"
        @retry="simulationResult || panels.simulation.error ? store.retrySimulation() : store.loadRaceState()"
      />
      <WeatherPanel
        class="simulator-weather"
        :weather="displayedWeather"
        :loading="panels.simulation.loading || (!simulationResult && panels.raceState.loading)"
        :error="panels.simulation.error || panels.raceState.error"
        @retry="simulationResult || panels.simulation.error ? store.retrySimulation() : store.loadRaceState()"
      />
    </div>
  </div>
</template>
