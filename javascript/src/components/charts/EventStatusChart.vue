<template>
  <div class="event-status-chart-wrapper">
    <Bar
      :options="chartOptions"
      :data="chartData"
      class="event-status-chart"
    />
  </div>
</template>

<script>
import { Bar } from 'vue-chartjs'
import {
  Chart as ChartJS,
  Title,
  Tooltip,
  Legend,
  BarElement,
  CategoryScale,
  LinearScale,
} from 'chart.js'

ChartJS.register(Title, Tooltip, Legend, BarElement, CategoryScale, LinearScale)

export default {
  name: 'EventStatusChart',
  components: { Bar },
  props: {
    numEvents: { type: Number, required: true },
    numEventsScored: { type: Number, required: true },
  },
  computed: {
    chartData() {
      return {
        labels: ['Events'],
        datasets: [
          { label: 'Scored', data: [this.numEventsScored], backgroundColor: '#63BE7B' },
          { 
            label: 'Projected', 
            data: [Math.max(this.numEvents - this.numEventsScored, 0)], 
            backgroundColor: '#e5f7ff' 
          },
        ],
      }
    },
    chartOptions() {
      const max = this.numEvents

      return {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        animations: {
          y: {
            easing: 'easeInOutElastic',
            from: (ctx) => {
              if (ctx.type === 'data') {
                if (ctx.mode === 'default' && !ctx.dropped) {
                  ctx.dropped = true;
                  return 0;
                }
              }
            }
          }
        },
        plugins: {
          legend: {
            position: 'bottom',
            onClick: null,
          },
          tooltip: { enabled: true },
        },
        scales: {
          x: {
            stacked: true,
            beginAtZero: true,
            max,
            ticks: {
              callback: function(value) {
                // Only show start, end
                if (value === 0 || value === max) return value
                return ''
              },
            },
            grid: {
              // Only draw grid lines for start, middle, end
              drawTicks: true,
              drawOnChartArea: true,
              color: function(context) {
                const val = context.tick.value
                if (val === 0 || val === max) return '#ccc'
                return 'transparent'
              },
            },
          },
          y: { stacked: true, grid: { display: false } },
        },
      }
    },
  },
}
</script>

<style scoped>
.event-status-chart-wrapper {
  height: 100px;
  width: 100%;
}
</style>
