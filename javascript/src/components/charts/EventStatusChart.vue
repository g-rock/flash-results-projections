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
    stats: { type: Object, required: true },
  },
  computed: {
  chartData() {
    const s = this.stats || {}
    const total = s.total || 0

    return {
      labels: [''],
      datasets: [
        {
          label: 'Scored',
          data: [s.scored || 0],
          backgroundColor: '#63BE7B'
        },
        {
          label: 'Scored (Protest)',
          data: [s['scored-protest'] || 0],
          backgroundColor: '#B30000'
        },
        {
          label: 'Scored (Under Review)',
          data: [s['scored-under-review'] || 0],
          backgroundColor: '#FFBF00'
        },
        {
          label: 'Complete',
          data: [s.complete || 0],
          backgroundColor: '#005b96'
        },
        {
          label: 'Official',
          data: [s.official || 0],
          backgroundColor: '#005b96'
        },
        {
          label: 'Scheduled',
          data: [s.scheduled || 0],
          backgroundColor: '#E5F7FF'
        },
        {
          label: 'In-progress',
          data: [s['in-progress'] || 0],
          backgroundColor: '#FFFF99'
        }
      ]
    }
  },
  chartOptions() {
    const max = this.stats?.total || 0

    return {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'bottom',
          onClick: null
        },
        tooltip: { enabled: true }
      },
      scales: {
        x: {
          stacked: true,
          beginAtZero: true,
          max,
          ticks: {
            callback(value) {
              if (value === 0 || value === max) return value
              return ''
            }
          },
          title: {
            display: true,
            text: 'Number of Events',
            font: { size: 12, weight: '600' }
          }
        },
        y: {
          stacked: true,
          grid: { display: false }
        }
      }
    }
  }
}

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
