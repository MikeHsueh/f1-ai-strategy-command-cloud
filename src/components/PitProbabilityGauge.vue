<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useEChart } from '../composables/useEChart'
import type { RiskLevel, StrategyAction } from '../types'

const props = defineProps<{
  probability: number
  risk: RiskLevel
  action: StrategyAction
}>()

const color = computed(() => {
  if (props.probability >= 0.85) return '#ff2438'
  if (props.probability >= 0.65) return '#ff7a1a'
  if (props.probability >= 0.35) return '#f4c430'
  return '#28d17c'
})

const options = computed<EChartsOption>(() => ({
  animationDuration: 450,
  series: [{
    type: 'gauge',
    startAngle: 210,
    endAngle: -30,
    min: 0,
    max: 100,
    radius: '98%',
    center: ['50%', '54%'],
    progress: { show: true, width: 15, itemStyle: { color: color.value } },
    axisLine: { lineStyle: { width: 15, color: [[1, '#202b35']] } },
    axisTick: { show: false },
    splitLine: { show: false },
    axisLabel: { color: '#8b9aaa', fontSize: 10, distance: -34 },
    pointer: { width: 4, length: '58%', itemStyle: { color: '#edf2f7' } },
    anchor: { show: true, size: 9, itemStyle: { color: '#edf2f7' } },
    title: { show: false },
    detail: {
      valueAnimation: true,
      formatter: '{value}%',
      color: '#f8fafc',
      fontFamily: 'Rajdhani',
      fontSize: 38,
      fontWeight: 700,
      offsetCenter: [0, '58%'],
    },
    data: [{ value: Math.round(props.probability * 100) }],
  }],
}))

const { chartElement } = useEChart(options)
</script>

<template>
  <section class="command-card gauge-panel" data-tour="ai-strategy" :style="{ '--risk-color': color }">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Next-lap prediction</span>
        <h2>Pit Probability</h2>
      </div>
      <span class="risk-badge" :data-risk="risk">{{ risk }}</span>
    </header>
    <div ref="chartElement" class="chart gauge-chart"></div>
    <div class="gauge-decision">
      <span>AI instruction</span>
      <strong>{{ action.replaceAll('_', ' ') }}</strong>
    </div>
    <div class="threshold-scale">
      <span>0–35 Stay out</span>
      <span>35–65 Monitor</span>
      <span>65–85 Prepare</span>
      <span>85+ Pit now</span>
    </div>
  </section>
</template>
