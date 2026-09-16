<!-- eslint-disable @typescript-eslint/no-unused-vars -->
<script setup lang="ts">
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// --- INTERFACES E ESTADOS DO DASHBOARD ---
interface ChatMessage {
  id: number
  role: 'system' | 'user'
  text: string
  hasWidget?: boolean
}

const inputMessage = ref<string>('')
const messagesContainer = ref<HTMLElement | null>(null)
const activeAction = ref<string>('Analisar Carteira')
const activeSidebarItem = ref<string>('Chat')

const sidebarMenu = [
  { label: 'Chat', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path></svg>' },
  { label: 'Gráficos gerados', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="20" x2="18" y2="10"></line><line x1="12" y1="20" x2="12" y2="4"></line><line x1="6" y1="20" x2="6" y2="14"></line></svg>' },
  { label: 'Relatórios', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" x2="8" y1="13" y2="13"></line><line x1="16" x2="8" y1="17" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>' },
  { label: 'Logs', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="4 17 10 11 4 5"></polyline><line x1="12" y1="19" x2="20" y2="19"></line></svg>' }
]

const quickActions = [
  { label: 'Analisar Carteira', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect width="20" height="14" x="2" y="7" rx="2" ry="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/></svg>' },
  { label: 'Tendências Hoje', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/><polyline points="16 7 22 7 22 13"/></svg>' },
  { label: 'Simular Cenários', icon: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>' }
]

const messages = ref<ChatMessage[]>([
  { id: 1, role: 'user', text: 'Quais as projeções para o mercado e insights de hoje?' },
  { id: 2, role: 'system', text: 'Aqui está a análise de mercado de hoje baseada nos dados recentes:', hasWidget: true }
])

const scrollToBottom = async (): Promise<void> => {
  await nextTick()
  if (messagesContainer.value) {
    messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight
  }
}

const handleSidebarClick = (label: string): void => {
  activeSidebarItem.value = label
}

const handleActionClick = (label: string): void => {
  activeAction.value = label
  sendMessage(label)
}

const sendMessage = async (text: string = inputMessage.value): Promise<void> => {
  if (!text.trim()) return

  // 1. Adiciona a mensagem do usuário na tela
  messages.value.push({ id: Date.now(), role: 'user', text: text })
  inputMessage.value = ''
  scrollToBottom()

  // 2. Cria uma mensagem de "digitando..." temporária (opcional, mas melhora a UX)
  const loadingId = Date.now() + 1
  messages.value.push({
    id: loadingId,
    role: 'system',
    text: `[Log MCP]: Processando matriz de risco...`
  })
  scrollToBottom()

  try {
    // 3. Faz a requisição para o nosso backend
    const response = await fetch('http://localhost:3000/api/ai/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mensagem: text })
    })

    if (response.ok) {
      const data = await response.json()
      
      // Remove a mensagem de carregamento e insere a resposta real
      const loadingIndex = messages.value.findIndex(m => m.id === loadingId)
      if (loadingIndex !== -1) {
        messages.value[loadingIndex]!.text = data.resposta
      }
    } else {
      throw new Error('Falha na resposta do servidor')
    }
  } catch (error) {
    const loadingIndex = messages.value.findIndex(m => m.id === loadingId)
    if (loadingIndex !== -1) {
      messages.value[loadingIndex]!.text = 'Erro ao processar a solicitação no servidor de IA.'
    }
  } finally {
    scrollToBottom()
  }
}

const logout = () => {
  localStorage.removeItem('auth_token')
  router.push('/login')
}

onMounted(() => {
  scrollToBottom()
})
</script>

<template>
  <div class="dashboard-layout">
    
    <!-- Menu Lateral -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <div class="brand-logo">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        </div>
        <h2>EconomicAI</h2>
      </div>

      <nav class="sidebar-nav">
        <span class="nav-section-title">MENU PRINCIPAL</span>
        <button 
          v-for="item in sidebarMenu" 
          :key="item.label"
          @click="handleSidebarClick(item.label)"
          :class="['nav-item', activeSidebarItem === item.label ? 'active' : '']"
        >
          <span class="nav-icon" v-html="item.icon"></span>
          {{ item.label }}
        </button>
      </nav>

      <div class="sidebar-footer">
        <!-- Adicionado evento de click para o logout -->
        <div class="user-profile" @click="logout" title="Clique para sair">
          <div class="user-avatar">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          </div>
          <div class="user-info">
            <span class="user-name">Administrador</span>
            <span class="user-role">Sair da plataforma</span>
          </div>
        </div>
      </div>
    </aside>

    <!-- Área Principal do Chat -->
    <main class="main-content">
      <header class="content-header">
        <h1>{{ activeSidebarItem }}</h1>
        <div class="header-divider"></div>
        <span class="header-subtitle">Orquestração Multiagente</span>
      </header>

      <div v-show="activeSidebarItem === 'Chat'" class="chat-wrapper">
        <div class="messages-area" ref="messagesContainer">
          <div v-for="msg in messages" :key="msg.id" :class="['message-row', msg.role]">
            
            <!-- Avatar do Bot Substituído pelo Cifrão -->
            <div v-if="msg.role === 'system'" class="bot-avatar">
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
            </div>
            
            <div class="message-content">
              <div class="bubble">{{ msg.text }}</div>
              
              <div v-if="msg.hasWidget" class="widget-card">
                <div class="widget-chart-placeholder">
                  <svg viewBox="0 0 100 40" class="mock-chart">
                    <path d="M 0 35 Q 10 25, 20 28 T 40 15 T 60 20 T 80 5 T 100 10" fill="none" stroke="url(#grad)" stroke-width="3" />
                    <defs>
                      <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stop-color="#10b981" />
                        <stop offset="100%" stop-color="#8b5cf6" />
                      </linearGradient>
                    </defs>
                  </svg>
                </div>
                <div class="widget-data">
                  <div class="data-point">
                    <span class="label">PIB</span>
                    <span class="value positive">+3.2%</span>
                    <span class="subtitle">Meta de Alta</span>
                  </div>
                  <div class="data-point">
                    <span class="label">Inflação</span>
                    <span class="value negative">-0.5%</span>
                    <span class="subtitle text-link">Setor Tech ↗</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="interaction-zone">
          <div class="quick-actions">
            <span class="actions-title">Ações Rápidas</span>
            <div class="actions-list">
              <button 
                v-for="action in quickActions" 
                :key="action.label" 
                @click="handleActionClick(action.label)"
                :class="['action-pill', action.label === activeAction ? 'active' : '']"
              >
                <span class="svg-icon" v-html="action.icon"></span>
                {{ action.label }}
              </button>
            </div>
          </div>

          <div class="input-area">
            <div class="input-box">
              <input 
                v-model="inputMessage" 
                @keyup.enter="sendMessage()"
                type="text" 
                placeholder="Pergunte ao EconomicAI..."
              />
              <div class="input-tools">
                <button class="icon-btn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.44 11.05-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg></button>
                <button class="icon-btn"><svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3Z"/><path d="M19 10v2a7 7 0 0 1-14 0v-2"/><line x1="12" x2="12" y1="19" y2="22"/></svg></button>
                <button class="send-btn" @click="sendMessage()" :disabled="!inputMessage.trim()">
                  <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="margin-left: -2px;"><line x1="22" x2="11" y1="2" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div v-show="activeSidebarItem !== 'Chat'" class="placeholder-area">
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>
        <p>A seção <strong>{{ activeSidebarItem }}</strong> está em desenvolvimento.</p>
      </div>
    </main>
  </div>
</template>

<style scoped>
.system .bubble::selection,
.user .bubble::selection {
  background-color: #0f172a;
  color: #ffffff;
}

.dashboard-layout { display: flex; height: 100vh; width: 100vw; background-color: var(--bg-color); overflow: hidden; }

.sidebar { width: 260px; background-color: var(--sidebar-bg); display: flex; flex-direction: column; border-right: 1px solid var(--sidebar-border); flex-shrink: 0; }
.sidebar-brand { height: 70px; padding: 0 20px; display: flex; align-items: center; gap: 12px; border-bottom: 1px solid var(--sidebar-border); }
.brand-logo { color: var(--primary-purple); display: flex; align-items: center; }
.sidebar-brand h2 { color: var(--sidebar-title); font-size: 1.25rem; font-weight: 700; }

.sidebar-nav { flex: 1; padding: 24px 12px; display: flex; flex-direction: column; gap: 8px; overflow-y: auto; }
.nav-section-title { font-size: 0.7rem; color: #94a3b8; font-weight: 700; padding: 0 8px; margin-bottom: 8px; letter-spacing: 1px; }

.nav-item { display: flex; align-items: center; gap: 12px; padding: 12px; background: transparent; border: none; border-radius: 8px; color: var(--sidebar-text); font-size: 0.95rem; cursor: pointer; text-align: left; transition: all 0.2s; font-weight: 600; }
.nav-item:hover { background-color: var(--sidebar-hover); color: var(--sidebar-title); }
.nav-item.active { background-color: var(--sidebar-active-bg); color: var(--sidebar-active-text); } 
.nav-icon { display: flex; align-items: center; }

.sidebar-footer { padding: 16px; border-top: 1px solid var(--sidebar-border); }
.user-profile { display: flex; align-items: center; gap: 12px; padding: 8px; border-radius: 8px; transition: background 0.2s; cursor: pointer; }
.user-profile:hover { background-color: var(--sidebar-hover); }
.user-avatar { width: 36px; height: 36px; background: #f1f5f9; border-radius: 50%; display: flex; align-items: center; justify-content: center; color: var(--sidebar-text); }
.user-info { display: flex; flex-direction: column; }
.user-name { color: var(--sidebar-title); font-size: 0.85rem; font-weight: 700; }
.user-role { color: var(--sidebar-text); font-size: 0.75rem; }

.main-content { flex: 1; display: flex; flex-direction: column; background-color: var(--bg-color); position: relative; }
.content-header { height: 70px; padding: 0 32px; background-color: white; border-bottom: 1px solid var(--border-light); display: flex; align-items: center; gap: 16px; flex-shrink: 0; }
.content-header h1 { font-size: 1.2rem; color: #0f172a; font-weight: 600; }
.header-divider { width: 1px; height: 20px; background-color: var(--border-light); }
.header-subtitle { color: var(--text-muted); font-size: 0.9rem; }

.chat-wrapper { flex: 1; display: flex; flex-direction: column; overflow: hidden; position: relative; }
.messages-area { flex: 1; padding: 32px; overflow-y: auto; display: flex; flex-direction: column; gap: 24px; scroll-behavior: smooth; }
.message-row { display: flex; gap: 16px; align-items: flex-start; max-width: 800px; margin: 0 auto; width: 100%; }
.message-row.user { justify-content: flex-end; }
.bot-avatar { width: 36px; height: 36px; background: #ede9fe; color: var(--primary-purple); border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }

.message-content { display: flex; flex-direction: column; gap: 8px; max-width: 85%; }
.bubble { padding: 14px 18px; border-radius: 12px; font-size: 0.95rem; line-height: 1.6; }
.system .bubble { background-color: white; border: 1px solid var(--border-light); color: var(--text-main); border-top-left-radius: 2px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.user .bubble { background-color: var(--primary-purple); color: white; border-top-right-radius: 2px; box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2); }

.widget-card { background: white; border: 1px solid var(--border-light); border-radius: 12px; padding: 16px; width: 350px; box-shadow: 0 4px 6px rgba(0,0,0,0.02); margin-top: 8px; }
.widget-chart-placeholder { height: 80px; width: 100%; margin-bottom: 16px; display: flex; align-items: center; justify-content: center; }
.mock-chart { width: 100%; height: 100%; }
.widget-data { display: flex; justify-content: space-between; border-top: 1px solid var(--border-light); padding-top: 12px; }
.data-point { display: flex; flex-direction: column; gap: 4px; }
.data-point .label { font-size: 0.8rem; color: var(--text-muted); font-weight: 500; }
.data-point .value { font-size: 1.1rem; font-weight: 700; }
.value.positive { color: #10b981; }
.value.negative { color: #ef4444; }
.data-point .subtitle { font-size: 0.75rem; color: var(--text-muted); display: flex; align-items: center; }
.text-link { color: var(--primary-purple); font-weight: 600; cursor: pointer; }

.interaction-zone { background: linear-gradient(180deg, rgba(248,250,252,0) 0%, #f8fafc 20%); padding: 0 32px 32px; flex-shrink: 0; }
.quick-actions { max-width: 800px; margin: 0 auto 16px; }
.actions-title { display: none; }
.actions-list { display: flex; gap: 10px; overflow-x: auto; padding-bottom: 4px; }
.actions-list::-webkit-scrollbar { display: none; }
.action-pill { background: white; border: 1px solid var(--border-light); padding: 8px 16px; border-radius: 20px; font-size: 0.85rem; color: var(--text-main); cursor: pointer; white-space: nowrap; transition: all 0.2s; font-weight: 500; display: flex; align-items: center; gap: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
.action-pill:hover { border-color: var(--primary-purple); color: var(--primary-purple); }

.action-pill.active { background-color: #000000; border-color: #000000; color: #ffffff; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25); }
.action-pill.active .svg-icon { color: #ffffff; }

.input-area { max-width: 800px; margin: 0 auto; }
.input-box { display: flex; align-items: center; background: white; border: 1px solid var(--border-light); padding: 10px 16px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); transition: border 0.2s; }
.input-box:focus-within { border-color: var(--primary-purple); box-shadow: 0 4px 20px rgba(139, 92, 246, 0.1); }
.input-box input { flex: 1; border: none; outline: none; font-size: 1rem; color: var(--text-main); padding: 8px 0; background: transparent; }
.input-box input::placeholder { color: #94a3b8; }
.input-tools { display: flex; align-items: center; gap: 8px; }
.icon-btn { background: none; border: none; display: flex; align-items: center; justify-content: center; cursor: pointer; color: var(--text-muted); transition: color 0.2s; padding: 4px; border-radius: 6px; }
.icon-btn:hover { color: var(--primary-purple); background: #f1f5f9; }
.send-btn { background: var(--primary-purple); color: white; border: none; width: 36px; height: 36px; border-radius: 8px; display: flex; align-items: center; justify-content: center; cursor: pointer; transition: background 0.2s; margin-left: 4px; }
.send-btn:disabled { background: #cbd5e1; cursor: not-allowed; }
.send-btn:hover:not(:disabled) { background: var(--primary-purple-hover); }

.placeholder-area { flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 16px; color: var(--text-muted); }
.placeholder-area p { font-size: 1.1rem; }

::selection { background-color: #8b5cf6 !important; color: #ffffff !important; }
.bubble::selection, .bubble *::selection { background-color: #0f172a !important; color: #ffffff !important; }
.action-pill.active, .action-pill.active:hover { background-color: #000000 !important; border-color: #000000 !important; color: #ffffff !important; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25) !important; }
.action-pill.active .svg-icon { color: #ffffff !important; }
</style>