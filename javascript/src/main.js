import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

import './plugins/ag-grid'

createApp(App).use(router).mount('#app')
