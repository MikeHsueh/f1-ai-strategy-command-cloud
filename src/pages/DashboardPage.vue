<script setup lang="ts">
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'

import DriverComparisonTable from '../components/DriverComparisonTable.vue'
import FeatureImportancePanel from '../components/FeatureImportancePanel.vue'
import ModelHealthPanel from '../components/ModelHealthPanel.vue'
import PaceTrendChart from '../components/PaceTrendChart.vue'
import PitProbabilityGauge from '../components/PitProbabilityGauge.vue'
import PitProbabilityTimeline from '../components/PitProbabilityTimeline.vue'
import RaceSelectorBar from '../components/RaceSelectorBar.vue'
import RaceStatePanel from '../components/RaceStatePanel.vue'
import StrategyRecommendation from '../components/StrategyRecommendation.vue'
import TireHealthPanel from '../components/TireHealthPanel.vue'
import WeatherPanel from '../components/WeatherPanel.vue'
import WhatIfSimulator from '../components/WhatIfSimulator.vue'
import { useRaceStore } from '../stores/raceStore'

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
} = storeToRefs(store)

onMounted(store.initialize)
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
      <RaceStatePanel class="area-race-state" :state="raceState" />
      <PitProbabilityGauge
        class="area-gauge"
        :probability="prediction.pit_probability"
        :risk="prediction.risk"
        :action="prediction.action"
      />
      <PitProbabilityTimeline class="area-timeline" :points="timeline" :current-lap="selection.lap" />
      <TireHealthPanel class="area-tire" :tire="raceState.tire" />
      <WeatherPanel class="area-weather" :weather="raceState.weather" />
      <PaceTrendChart class="area-pace" :series="paceTrend" />
      <StrategyRecommendation class="area-strategy" :prediction="prediction" :options="strategyOptions" />
      <WhatIfSimulator
        class="area-simulator"
        :race-state="raceState"
        :result="simulationResult"
        @simulate="store.runSimulation"
        @reset="store.resetSimulation"
      />
      <FeatureImportancePanel class="area-features" :features="features" :limit="8" />
      <ModelHealthPanel
        class="area-health"
        :health="health"
        :source="dataSource"
        :last-updated="lastUpdated"
        :loading="loading"
      />
      <DriverComparisonTable
        class="area-comparison"
        :rows="comparison"
        :selected-driver="selection.driver"
        compact
        @select="store.setDriver"
      />
    </div>
  </div>
</template>
