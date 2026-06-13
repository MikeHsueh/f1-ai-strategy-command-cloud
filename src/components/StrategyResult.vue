<template>
  <div class="panel">

    <h2>🧠 AI Strategy</h2>

    <div class="big-number">
      {{ data.pit_probability }}%
    </div>

    <div class="item">
      <span>Recommended Tire</span>
      <strong>{{ data.recommended_tire }}</strong>
    </div>

    <div class="item">
      <span>Optimal Pit Lap</span>
      <strong>{{ data.optimal_pit_lap }}</strong>
    </div>

    <div class="item">
      <span>Expected Gain</span>
      <strong>{{ data.expected_gain }} s</strong>
    </div>

    <div class="item">
      <span>Undercut Risk</span>
      <strong>{{ data.undercut_risk }}</strong>
    </div>

  </div>
</template>

<script setup>
defineProps({
  data: Object
})
</script>

<style scoped>
.panel {
  background: #111827;
  padding: 20px;
  border-radius: 12px;
  color: white;
}

.big-number {
  font-size: 48px;
  font-weight: bold;
  color: #ef4444;
  text-align: center;
  margin: 20px 0;
}

.item {
  display: flex;
  justify-content: space-between;
  margin: 12px 0;
}
</style>