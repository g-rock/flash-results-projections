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
    numEventsInProgress: { type: Number, required: true }
  },
  computed: {
    chartData() {
      const total = this.numEvents
      const scored = this.numEventsScored
      const inProgress = this.numEventsInProgress
      const projected = Math.max(total - scored - inProgress, 0)

      return {
        labels: ['Events'],
        datasets: [
          {
            label: 'Scored',
            data: [scored],
            backgroundColor: '#63BE7B'
          },
          {
            label: 'In-progress',
            data: [inProgress],
            backgroundColor: '#FFFF99'
          },
          {
            label: 'Projected',
            data: [projected],
            backgroundColor: '#e5f7ff'
          }
        ]
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
            maxWidth: 150
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
  width: 33%;
  padding-left: 15px;
}

@media (max-width: 768px) {
  .event-status-chart-wrapper {
    height: 100px;
    width: 100%;
    padding-left: 0;
  }
}
</style>
