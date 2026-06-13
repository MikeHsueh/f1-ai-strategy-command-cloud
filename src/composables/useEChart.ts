import { BarChart, GaugeChart, LineChart, RadarChart, ScatterChart } from 'echarts/charts'
import {
  GridComponent,
  MarkAreaComponent,
  MarkLineComponent,
  RadarComponent,
  TooltipComponent,
} from 'echarts/components'
import type { EChartsOption } from 'echarts'
import { init, use, type ECharts } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { nextTick, onBeforeUnmount, onMounted, ref, watch, type Ref } from 'vue'

use([
  BarChart,
  GaugeChart,
  LineChart,
  RadarChart,
  ScatterChart,
  GridComponent,
  MarkAreaComponent,
  MarkLineComponent,
  RadarComponent,
  TooltipComponent,
  CanvasRenderer,
])

export function useEChart(options: Ref<EChartsOption>) {
  const chartElement = ref<HTMLElement | null>(null)
  let chart: ECharts | null = null

  const render = async () => {
    await nextTick()
    if (!chartElement.value) return
    if (!chart) chart = init(chartElement.value)
    chart.setOption(options.value, true)
    chart.resize()
  }

  const resize = () => chart?.resize()

  watch(options, render, { deep: true })
  onMounted(() => {
    render()
    window.addEventListener('resize', resize)
  })
  onBeforeUnmount(() => {
    window.removeEventListener('resize', resize)
    chart?.dispose()
  })

  return { chartElement, render }
}
