import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import 'driver.js/dist/driver.css'
import './style.css'

createApp(App)
  .use(createPinia())
  .use(router)
  .mount('#app')
