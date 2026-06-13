<script setup lang="ts">
import { defineAsyncComponent, onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import AsyncPanelPlaceholder from '../components/AsyncPanelPlaceholder.vue'
import DriverComparisonTable from '../components/DriverComparisonTable.vue'
import ModelHealthPanel from '../components/ModelHealthPanel.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import RaceStatePanel from '../components/RaceStatePanel.vue'
import StrategyRecommendation from '../components/StrategyRecommendation.vue'
import TireHealthPanel from '../components/TireHealthPanel.vue'
import WeatherPanel from '../components/WeatherPanel.vue'
import WhatIfSimulator from '../components/WhatIfSimulator.vue'
import { useRaceStore } from '../stores/raceStore'

const lazyPanel = (loader: () => Promise<unknown>) => defineAsyncComponent({
  loader: loader as () => Promise<{ default: never }>,
  loadingComponent: AsyncPanelPlaceholder,
  delay: 0,
})
const FeatureImportancePanel = lazyPanel(() => import('../components/FeatureImportancePanel.vue'))
const PaceTrendChart = lazyPanel(() => import('../components/PaceTrendChart.vue'))
const PitProbabilityGauge = lazyPanel(() => import('../components/PitProbabilityGauge.vue'))
const PitProbabilityTimeline = lazyPanel(() => import('../components/PitProbabilityTimeline.vue'))

const store = useRaceStore()
const {
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
  loading,
  lastUpdated,
  dataSource,
  panels,
} = storeToRefs(store)

onMounted(() => store.activatePage('dashboard'))
</script>

<template>
  <div class="page dashboard-page">
    <RaceSelectorBar
      :seasons="seasons"
      :races="races"
      :drivers="drivers"
      :laps="laps"
      :year="selection.year"
      :round-number="selection.roundNumber"
      :driver="selection.driver"
      :lap="selection.lap"
      :loading="loading"
      @year="store.setYear"
      @race="store.setRace"
      @driver="store.setDriver"
      @lap="store.setLap"
      @refresh="store.refreshDashboard"
    />

    <div class="dashboard-grid">
      <RaceStatePanel
        class="area-race-state"
        :state="raceState"
        :loading="panels.raceState.loading"
        :error="panels.raceState.error"
        @retry="store.loadRaceState"
      />
      <PitProbabilityGauge
        class="area-gauge"
        :probability="prediction.pit_probability"
        :risk="prediction.risk"
        :action="prediction.action"
        :loading="panels.prediction.loading"
        :error="panels.prediction.error"
        @retry="store.loadPrediction"
      />
      <PitProbabilityTimeline
        class="area-timeline"
        :points="timeline"
        :current-lap="selection.lap"
        :loading="panels.timeline.loading"
        :error="panels.timeline.error"
        @retry="store.loadTimeline"
      />
      <TireHealthPanel
        class="area-tire"
        :tire="raceState.tire"
        :loading="panels.raceState.loading"
        :error="panels.raceState.error"
        @retry="store.loadRaceState"
      />
      <WeatherPanel
        class="area-weather"
        :weather="raceState.weather"
        :loading="panels.raceState.loading"
        :error="panels.raceState.error"
        @retry="store.loadRaceState"
      />
      <PaceTrendChart
        class="area-pace"
        :series="paceTrend"
        :loading="panels.pace.loading"
        :error="panels.pace.error"
        @retry="store.loadPaceTrend"
      />
      <StrategyRecommendation
        class="area-strategy"
        :prediction="prediction"
        :options="strategyOptions"
        :loading="panels.prediction.loading"
        :error="panels.prediction.error"
        @retry="store.loadPrediction"
      />
      <WhatIfSimulator
        class="area-simulator"
        :race-state="raceState"
        :result="simulationResult"
        :request-error="panels.simulation.error"
        @simulate="store.runSimulation"
        @reset="store.resetSimulation"
      />
      <FeatureImportancePanel
        class="area-features"
        :features="features"
        :limit="8"
        :loading="panels.features.loading"
        :error="panels.features.error"
        @retry="store.loadFeatures"
      />
      <ModelHealthPanel
        class="area-health"
        :health="health"
        :source="dataSource"
        :last-updated="lastUpdated"
        :loading="panels.health.loading"
        :error="panels.health.error"
        @retry="store.loadHealth"
      />
      <DriverComparisonTable
        class="area-comparison"
        :rows="comparison"
        :selected-driver="selection.driver"
        :loading="panels.comparison.loading"
        :error="panels.comparison.error"
        compact
        @select="store.setDriver"
        @retry="store.loadComparison"
      />
    </div>
  </div>
</template>
