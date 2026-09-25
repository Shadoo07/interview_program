import { createApp } from 'vue'
import { createPinia } from 'pinia'
import router from './router'
import { ElDialog } from 'element-plus/es/components/dialog/index.mjs'
import { ElIcon } from 'element-plus/es/components/icon/index.mjs'
import 'element-plus/dist/index.css'
import './styles/global.css'
import './styles/components.css'
import App from './App.vue'

const app = createApp(App)

app.use(createPinia())
app.use(router)
app.component(ElIcon.name!, ElIcon)
app.component(ElDialog.name!, ElDialog)

app.mount('#app')
