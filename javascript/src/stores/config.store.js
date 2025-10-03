import { defineStore } from 'pinia';
import axios from 'axios';

export const useConfigStore = defineStore('config', {
  state: () => ({
    viewMode: 'projected',
    meets: [],
    loadingMeets: false,
    meetsError: null,
  }),
  getters: {
    isProjected: (state) => state.viewMode === 'projected',
  },
  actions: {
    toggleViewMode() {
      this.viewMode = this.viewMode === 'projected' ? 'actual' : 'projected';
    },

    async fetchMeets() {
      this.loadingMeets = true;
      this.meetsError = null;
      try {
        const response = await axios.get('http://127.0.0.1:8000/list_meets');
        console.log(response);
        this.meets = response.data.meets;
      } catch (error) {
        console.error("Failed to fetch meets:", error);
        this.meetsError = error;
      } finally {
        this.loadingMeets = false;
      }
    },
  },
});
