import { createApp } from 'vue'
import App from './App.vue'
import router from './router'

const app = createApp(App)

// Isso avisa ao Vue para usar as rotas que criamos
app.use(router)

app.mount('#app')