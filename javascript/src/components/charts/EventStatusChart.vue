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

function toDimmedColor(color, alpha) {
  // Already rgba → just replace alpha
  if (typeof color === 'string' && color.startsWith('rgba')) {
    return color.replace(/rgba\(([^,]+),([^,]+),([^,]+),([^)]+)\)/, `rgba($1,$2,$3,${alpha})`)
  }

  // Not a hex string → bail safely
  if (typeof color !== 'string' || !color.startsWith('#')) {
    return color
  }

  const r = parseInt(color.slice(1, 3), 16)
  const g = parseInt(color.slice(3, 5), 16)
  const b = parseInt(color.slice(5, 7), 16)

  return `rgba(${r}, ${g}, ${b}, ${alpha})`
}


export default {
  name: 'EventStatusChart',
  components: { Bar },
  props: {
    stats: { type: Object, required: true },
  },
  data() {
    return {
      hoveredLegendLabel: null,
      originalColors: []
    }
  },
  computed: {
    chartData() {
      const s = this.stats || {}
      return {
        labels: [''],
        datasets: [
          {
            label: 'Scored',
            data: [s.scored || 0],
            backgroundColor: '#63BE7B',
            borderColor: '#1D6F42',
            borderWidth: 1
          },
          {
            label: 'Scored (Under Review | Protest)',
            data: [s['scored-pending'] || 0],
            backgroundColor: '#B30000'
          },
          {
            label: 'In-progress',
            data: [s['in-progress'] || 0],
            backgroundColor: '#FFFF99',
            borderColor: '#BDBD00',
            borderWidth: 1
          },
          {
            label: 'Projected',
            data: [s.projected || 0],
            backgroundColor: '#E5F7FF',
            borderColor: '#007ac6',
            borderWidth: 1
          },
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
            onClick: null,

            labels: {
              filter: (legendItem, chartData) => {
                const dataset = chartData.datasets[legendItem.datasetIndex]
                return dataset.data[0] > 0
              }
            },

            onHover: (e, legendItem, legend) => {
              const chart = legend.chart

              // store original colors once
              if (!this.originalColors.length) {
                this.originalColors = chart.data.datasets.map(
                  d => d.backgroundColor
                )
              }

              chart.data.datasets.forEach((dataset, index) => {
                dataset.backgroundColor =
                  index === legendItem.datasetIndex
                    ? this.originalColors[index]
                    : toDimmedColor(this.originalColors[index], 0.25)
              })

              chart.tooltip.setActiveElements(
                [{ datasetIndex: legendItem.datasetIndex, index: 0 }],
                { x: e.x, y: e.y }
              )

              chart.update()
            },

            onLeave: (e, legendItem, legend) => {
              const chart = legend.chart

              chart.data.datasets.forEach((dataset, index) => {
                dataset.backgroundColor = this.originalColors[index]
              })

              chart.tooltip.setActiveElements([], {})
              chart.update()
            }
          },

          tooltip: {
            callbacks: {
              label(context) {
                return `${context.dataset.label} events: ${context.parsed.x}`
              }
            }
          }
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
  height: 150px;
  width: 33%;
  padding-left: 15px;
}

@media (max-width: 768px) {
  .event-status-chart-wrapper {
    height: 200px;
    width: 100%;
    padding-left: 0;
  }
}
</style>
