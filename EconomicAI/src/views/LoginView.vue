<!-- eslint-disable @typescript-eslint/no-unused-vars -->
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const loginEmail = ref<string>('')
const loginPassword = ref<string>('')
const isLoggingIn = ref<boolean>(false)

const handleLogin = async () => {
  if (!loginEmail.value || !loginPassword.value) return
  
  isLoggingIn.value = true
  
  try {
    const response = await fetch('http://localhost:3000/api/auth/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        email: loginEmail.value,
        senha: loginPassword.value
      })
    })

    if (response.ok) {
      const data = await response.json()
      localStorage.setItem('auth_token', data.token)
      router.push('/')
    } else {
      alert('E-mail ou senha incorretos.')
    }
  } catch (error) {
    alert('Erro ao conectar com o servidor. Verifique se a API está rodando na porta 3000.')
  } finally {
    isLoggingIn.value = false
  }
}
</script>

<template>
  <div class="login-layout">
    <div class="login-card">
      <div class="login-header">
        <div class="brand-logo-large">
          <svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
        </div>
        <h2>EconomicAI</h2>
        <p>Orquestração Multiagente para B3</p>
      </div>
      
      <form @submit.prevent="handleLogin" class="login-form">
        <div class="input-group">
          <label>E-mail Institucional</label>
          <input type="email" v-model="loginEmail" placeholder="usuario@esalq.usp.br" required />
        </div>
        <div class="input-group">
          <label>Senha de Acesso</label>
          <input type="password" v-model="loginPassword" placeholder="••••••••" required />
        </div>
        
        <button type="submit" class="btn-login" :disabled="isLoggingIn">
          <span v-if="!isLoggingIn">Acessar Plataforma</span>
          <span v-else class="loader"></span>
        </button>
      </form>
      
      <div class="login-footer">
        Protótipo para TCC - MBA USP/Esalq
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-layout { height: 100vh; width: 100vw; display: flex; align-items: center; justify-content: center; background: linear-gradient(135deg, #f0e6ff 0%, #ffe6f2 100%); }
.login-card { background: white; padding: 40px; border-radius: 16px; box-shadow: 0 10px 40px rgba(0,0,0,0.08); width: 100%; max-width: 420px; }
.login-header { text-align: center; margin-bottom: 32px; }
.brand-logo-large { color: var(--primary-purple); margin-bottom: 16px; display: flex; justify-content: center; }
.login-header h2 { font-size: 1.5rem; color: #0f172a; margin-bottom: 8px; font-weight: 700; }
.login-header p { color: var(--text-muted); font-size: 0.9rem; }
.login-form { display: flex; flex-direction: column; gap: 20px; }
.input-group { display: flex; flex-direction: column; gap: 8px; }
.input-group label { font-size: 0.85rem; font-weight: 600; color: #334155; }
.input-group input { padding: 12px 16px; border: 1px solid var(--border-light); border-radius: 8px; font-size: 1rem; transition: all 0.2s; }
.input-group input:focus { border-color: var(--primary-purple); outline: none; box-shadow: 0 0 0 3px rgba(139, 92, 246, 0.1); }
.btn-login { background: var(--primary-purple); color: white; border: none; padding: 14px; border-radius: 8px; font-size: 1rem; font-weight: 600; cursor: pointer; transition: background 0.2s; display: flex; justify-content: center; align-items: center; height: 48px; }
.btn-login:hover:not(:disabled) { background: var(--primary-purple-hover); }
.btn-login:disabled { opacity: 0.8; cursor: not-allowed; }
.login-footer { text-align: center; margin-top: 24px; font-size: 0.75rem; color: var(--text-muted); border-top: 1px solid var(--border-light); padding-top: 16px; }

.loader { width: 20px; height: 20px; border: 3px solid rgba(255,255,255,0.3); border-radius: 50%; border-top-color: white; animation: spin 1s ease-in-out infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
</style>