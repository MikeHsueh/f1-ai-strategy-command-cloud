<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { FlaskConical, LoaderCircle, RotateCcw } from '@lucide/vue'
import type {
  RaceState,
  StrategySimulationInput,
  StrategySimulationResult,
  TireCompound,
  TireState,
} from '../types'

const props = withDefaults(defineProps<{
  raceState: RaceState
  result: StrategySimulationResult | null
  allowInitialOverride?: boolean
  requestError?: string
}>(), {
  allowInitialOverride: false,
})

const emit = defineEmits<{
  simulate: [input: StrategySimulationInput]
  reset: []
}>()

const compounds: TireCompound[] = ['SOFT', 'MEDIUM', 'HARD', 'INTERMEDIATE', 'WET']
const expectedLife: Record<TireCompound, number> = {
  SOFT: 18,
  MEDIUM: 26,
  HARD: 36,
  INTERMEDIATE: 20,
  WET: 24,
}

function normalizeCompound(value: string): TireCompound {
  return compounds.includes(value as TireCompound) ? value as TireCompound : 'MEDIUM'
}

function calculateTireHealth(compound: TireCompound, life: number): number {
  const safeLife = Math.max(0, life)
  const degradation = safeLife * 0.055
  return Math.max(5, Math.min(100, 100 - (safeLife / expectedLife[compound]) * 72 - degradation * 8))
}

const form = reactive<StrategySimulationInput>({
  enableInitialTireOverride: false,
  initialCompound: normalizeCompound(props.raceState.tire.compound),
  initialTyreLife: props.raceState.tire.life,
  initialTireHealth: props.raceState.tire.health,
  nextCompound: 'HARD',
  targetPitLap: Math.min(props.raceState.total_laps, props.raceState.lap + 1),
  safetyCar: false,
  rainRisk: props.raceState.weather.model_rain_risk,
  position: props.raceState.position,
})

const running = ref(false)

function syncInitialHealth() {
  form.initialTireHealth = Number(calculateTireHealth(
    form.initialCompound,
    form.initialTyreLife,
  ).toFixed(1))
}

function resetToLiveState() {
  form.enableInitialTireOverride = false
  form.initialCompound = normalizeCompound(props.raceState.tire.compound)
  form.initialTyreLife = props.raceState.tire.life
  form.initialTireHealth = props.raceState.tire.health
  form.nextCompound = 'HARD'
  form.targetPitLap = Math.min(props.raceState.total_laps, props.raceState.lap + 1)
  form.safetyCar = props.raceState.safety_car
  form.rainRisk = props.raceState.weather.model_rain_risk
  form.position = props.raceState.position
  emit('reset')
}

watch(
  () => [form.initialCompound, form.initialTyreLife, form.enableInitialTireOverride],
  () => {
    if (form.enableInitialTireOverride) syncInitialHealth()
  },
)

watch(
  () => [
    props.raceState.driver,
    props.raceState.lap,
    props.raceState.tire.compound,
    props.raceState.tire.life,
  ],
  resetToLiveState,
)

const simulatedPreview = computed<TireState>(() => {
  if (props.result) return props.result.simulated_initial_tire
  if (!form.enableInitialTireOverride) return props.raceState.tire
  return {
    compound: form.initialCompound,
    life: form.initialTyreLife,
    health: form.initialTireHealth,
    degradation: Number((form.initialTyreLife * 0.055).toFixed(3)),
    temperature_proxy: props.raceState.tire.temperature_proxy,
  }
})

const recommendedNextTire = computed(() =>
  props.result?.recommended_tire ?? form.nextCompound,
)

async function run() {
  running.value = true
  emit('simulate', { ...form })
  window.setTimeout(() => {
    running.value = false
  }, 450)
}
</script>

<template>
  <section class="command-card what-if-panel" data-tour="simulation-controls">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Decision sandbox</span>
        <h2>What-if Simulator</h2>
      </div>
      <FlaskConical :size="18" />
    </header>

    <div class="tire-state-summary">
      <article>
        <span>Live Current Tire</span>
        <strong>{{ raceState.tire.compound }}</strong>
        <small>{{ raceState.tire.life }} laps · {{ Math.round(raceState.tire.health) }}% health</small>
      </article>
      <article :class="{ overridden: form.enableInitialTireOverride }">
        <span>Simulated Initial Tire</span>
        <strong>{{ simulatedPreview.compound }}</strong>
        <small>{{ simulatedPreview.life }} laps · {{ Math.round(simulatedPreview.health) }}% health</small>
      </article>
      <article class="recommended-tire">
        <span>Recommended Next Tire</span>
        <strong>{{ recommendedNextTire }}</strong>
        <small>Target pit L{{ result?.target_pit_lap ?? form.targetPitLap }}</small>
      </article>
    </div>

    <label v-if="allowInitialOverride" class="override-control" data-tour="initial-tire-override">
      <span>
        <strong>Initial Tire Override</strong>
        <small>Use a simulated starting tire without changing live RaceState.</small>
      </span>
      <input v-model="form.enableInitialTireOverride" type="checkbox">
      <i></i>
    </label>

    <div v-if="allowInitialOverride" class="simulator-fields initial-tire-fields">
      <label>
        <span>Initial compound</span>
        <select v-model="form.initialCompound" :disabled="!form.enableInitialTireOverride">
          <option v-for="compound in compounds" :key="compound">{{ compound }}</option>
        </select>
      </label>
      <label>
        <span>Initial tyre life</span>
        <input
          v-model.number="form.initialTyreLife"
          type="number"
          min="0"
          :max="raceState.total_laps"
          :disabled="!form.enableInitialTireOverride"
        >
      </label>
      <label>
        <span>Initial tire health (auto)</span>
        <input :value="form.initialTireHealth.toFixed(1)" type="number" readonly disabled>
      </label>
    </div>

    <div class="simulator-fields">
      <label>
        <span>Next compound</span>
        <select v-model="form.nextCompound">
          <option v-for="compound in compounds" :key="compound">{{ compound }}</option>
        </select>
      </label>
      <label>
        <span>Target pit lap</span>
        <input v-model.number="form.targetPitLap" type="number" :min="raceState.lap" :max="raceState.total_laps">
      </label>
      <label>
        <span>Rain risk</span>
        <input v-model.number="form.rainRisk" type="number" min="0" max="100">
      </label>
      <label class="toggle-field">
        <span>Safety Car</span>
        <input v-model="form.safetyCar" type="checkbox">
        <i></i>
      </label>
    </div>

    <div class="simulator-actions">
      <button class="command-button" type="button" :disabled="running" @click="run">
        <LoaderCircle v-if="running" class="spin" :size="16" />
        <FlaskConical v-else :size="16" />
        Run Simulation
      </button>
      <button class="secondary-command-button" type="button" :disabled="running" @click="resetToLiveState">
        <RotateCcw :size="15" />
        Reset to Live State
      </button>
    </div>

    <div v-if="result" class="simulation-output">
      <article><span>Pit probability</span><strong>{{ Math.round(result.pit_probability * 100) }}%</strong></article>
      <article><span>Projected finish</span><strong>P{{ result.projected_position }}</strong></article>
      <article><span>Expected gain</span><strong>{{ result.expected_gain.toFixed(2) }}s</strong></article>
      <p>{{ result.summary }}</p>
    </div>
    <div v-else-if="requestError" class="inline-panel-error">
      Data loading failed. Please try again shortly.
    </div>
  </section>
</template>
