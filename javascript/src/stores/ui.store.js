import { defineStore } from 'pinia'

export const useUIStore = defineStore('ui', {
  state: () => ({
    showHover: true,
    showTeamAbbr: true,
    showFullColumnName: false
  }),

  actions: {
    toggleHover(val) {
      this.showHover = val
    },
    toggleTeamAbbr(val) {
      this.showTeamAbbr = val
    },
    toggleFullColumnName(val) {
      this.showFullColumnName = val
    }
  }
})
