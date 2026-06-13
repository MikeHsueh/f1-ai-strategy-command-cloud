<script setup lang="ts">
import { computed } from 'vue'
import type { EChartsOption } from 'echarts'
import { useEChart } from '../composables/useEChart'
import type { TrendSeries } from '../types'

const props = defineProps<{ series: TrendSeries[] }>()

const options = computed<EChartsOption>(() => {
  const labels = [...new Set(props.series.flatMap((series) => series.data.map((point) => point.label)))]
  const colors = ['#25c8d9', '#25c8d9', '#f5c542', '#f5c542']
  return {
    animationDuration: 350,
    grid: { top: 24, left: 48, right: 14, bottom: 32 },
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#090e13',
      borderColor: '#34414e',
      textStyle: { color: '#f1f5f9', fontSize: 12 },
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: labels,
      axisLine: { lineStyle: { color: '#2b3742' } },
      axisLabel: { color: '#8998a8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      name: 'Delta (s)',
      nameTextStyle: { color: '#8998a8', fontSize: 10 },
      axisLabel: { color: '#8998a8', fontSize: 10 },
      splitLine: { lineStyle: { color: '#1d2730' } },
    },
    series: props.series.map((series, index) => ({
      name: series.name,
      type: 'line',
      smooth: 0.25,
      showSymbol: false,
      connectNulls: false,
      data: labels.map((label) => series.data.find((point) => point.label === label)?.value ?? null),
      lineStyle: {
        color: colors[index % colors.length],
        width: series.line === 'dashed' ? 2 : 3,
        type: series.line,
      },
    })),
  }
})

const { chartElement } = useEChart(options)
</script>

<template>
  <section class="command-card pace-panel" data-tour="pace-trend">
    <header class="card-heading">
      <div>
        <span class="eyebrow">Immediate rivals</span>
        <h2>Pace Trend</h2>
      </div>
      <div class="chart-legend">
        <span><i></i> Historical</span>
        <span><i class="dashed"></i> Predictive</span>
      </div>
    </header>
    <div ref="chartElement" class="chart pace-chart"></div>
  </section>
</template>
