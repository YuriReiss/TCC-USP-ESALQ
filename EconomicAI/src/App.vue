<script setup lang="ts">
import { RouterView } from 'vue-router'
</script>

<template>
  <RouterView />
</template>

<style>
/* ESTILOS GLOBAIS (Variáveis e Resets) */
:root {
  --sidebar-bg: #ffffff;
  --sidebar-border: #e2e8f0;
  --sidebar-hover: #f8fafc;
  --sidebar-active-bg: #f3e8ff; 
  --sidebar-active-text: #7c3aed; 
  --sidebar-text: #64748b;
  --sidebar-title: #0f172a;
  
  --bg-color: #f8fafc;
  --chat-bg: #ffffff;
  --text-main: #334155;
  --text-muted: #64748b;
  --primary-purple: #8b5cf6;
  --primary-purple-hover: #7c3aed;
  --system-bubble: #ffffff;
  --border-light: #e2e8f0;
}

* { 
  box-sizing: border-box; 
  margin: 0; 
  padding: 0; 
  font-family: 'Segoe UI', Roboto, Helvetica, sans-serif; 
}

::selection {
  background-color: var(--primary-purple);
  color: #ffffff;
}
</style>