<template>

<div class="panel">

<h2>🎮 Strategy Simulator</h2>

<label>Lap</label>
<input type="range"
v-model="simulationInput.lap"
min="1"
max="57"
/>

<label>Tire Age</label>
<input type="range"
v-model="simulationInput.tire_age"
min="1"
max="40"
/>

<label>Track Temp</label>
<input type="range"
v-model="simulationInput.track_temp"
min="20"
max="60"
/>

<label>Rain Risk</label>
<input type="range"
v-model="simulationInput.rain_risk"
min="0"
max="100"
/>

<select
v-model="simulationInput.compound"
>
<option>SOFT</option>
<option>MEDIUM</option>
<option>HARD</option>
<option>INTER</option>
</select>

<button @click="$emit('simulate')">
RUN SIMULATION
</button>

</div>

</template>

<script setup>

defineProps([
  'simulationInput'
])

</script>