<script setup>
import { ref, onMounted } from 'vue';
import { invoke } from '@tauri-apps/api/tauri';
import Toast from './components/Toast.vue';

const loading = ref(false);
const toastVisible = ref(false);
const toastMessage = ref('');
const toastType = ref('info');
const showSettings = ref(false);
const apiUrl = ref('http://127.0.0.1:5007');

// 从本地存储加载设置
onMounted(() => {
  const savedApiUrl = localStorage.getItem('apiUrl');
  if (savedApiUrl) {
    apiUrl.value = savedApiUrl;
  }
});

// 显示消息
const showMessage = (msg, isSuccess) => {
  toastMessage.value = msg;
  toastType.value = isSuccess ? 'success' : 'error';
  toastVisible.value = true;
};

// 保存设置
const saveSettings = async (newApiUrl) => {
  try {
    apiUrl.value = newApiUrl;
    localStorage.setItem('apiUrl', newApiUrl);
    showSettings.value = false;
    showMessage('设置已保存', true);
  } catch (error) {
    showMessage(`保存设置失败: ${error}`, false);
  }
};

// 切换账号
const changeAccount = async () => {
  try {
    loading.value = true;
    const response = await invoke('change_account_command', {
      apiUrl: apiUrl.value
    });
    // 如果 response.message 包含 error: Connection refused 则显示错误
    if (response.message.includes('error: Connection refused') || response.message.includes('error sending request')) {
      showMessage('连接失败，请检查网络连接', false);
    } else {
      showMessage(response.message, response.success);
    }
  } catch (error) {
    showMessage(`操作失败: ${error}`, false);
  } finally {
    loading.value = false;
  }
};

// 重置机器ID
const resetMachineId = async () => {
  try {
    loading.value = true;
    const response = await invoke('reset_cursor_machine_id_command', { restart: true });
    showMessage(response.message, response.success);
  } catch (error) {
    showMessage(`操作失败: ${error}`, false);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div class="container">
    <div class="glass-card">
      <div class="header">
        <h1>Cursor 助手</h1>
        <button @click="showSettings = true" class="settings-button">
          <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="3"></circle>
            <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path>
          </svg>
        </button>
      </div>
      
      <div class="button-group">
        <button @click="changeAccount" :disabled="loading" class="glass-button">
          <span v-if="!loading">切换账号</span>
          <span v-else class="loading"></span>
        </button>
        
        <button @click="resetMachineId" :disabled="loading" class="glass-button">
          <span v-if="!loading">重置机器ID</span>
          <span v-else class="loading"></span>
        </button>
      </div>
      
      <div class="footer">
        <p>Cursor Helper v1.0.0</p>
      </div>
    </div>
  </div>

  <!-- 设置弹窗 -->
  <div v-if="showSettings" class="dialog-overlay" @click="showSettings = false">
    <div class="dialog-content" @click.stop>
      <h2>设置</h2>
      <div class="form-group">
        <label for="apiUrl">API 地址</label>
        <input
          id="apiUrl"
          v-model="apiUrl"
          type="text"
          placeholder="请输入 API 地址"
          class="glass-input"
        />
      </div>
      <div class="dialog-actions">
        <button class="glass-button cancel" @click="showSettings = false">取消</button>
        <button class="glass-button" @click="saveSettings(apiUrl)">保存</button>
      </div>
    </div>
  </div>

  <Toast
    v-model:visible="toastVisible"
    :message="toastMessage"
    :type="toastType"
    :duration="3000"
  />
</template>

<style>
:root {
  --primary-color: #6366f1;
  --success-color: #10b981;
  --error-color: #ef4444;
  --text-color: #1f2937;
  --background-color: #f3f4f6;
  --card-background: rgba(255, 255, 255, 0.7);
  --button-hover: rgba(255, 255, 255, 0.9);
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

body {
  background: linear-gradient(135deg, #a5b4fc, #818cf8);
  color: var(--text-color);
  height: 100vh;
  overflow: hidden;
}

.container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  padding: 1rem;
}

.glass-card {
  background: var(--card-background);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 2rem;
  width: 100%;
  max-width: 400px;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

h1 {
  text-align: center;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: 0.5rem;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.glass-button {
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 0.8rem 1.5rem;
  font-size: 1rem;
  font-weight: 500;
  color: var(--primary-color);
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  height: 48px;
}

.glass-button:hover:not(:disabled) {
  background: var(--button-hover);
  transform: translateY(-2px);
}

.glass-button:active:not(:disabled) {
  transform: translateY(0);
}

.glass-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.message {
  padding: 1rem;
  border-radius: 8px;
  text-align: center;
  font-size: 0.9rem;
  line-height: 1.4;
}

.message.success {
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: var(--success-color);
}

.message.error {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: var(--error-color);
}

.footer {
  text-align: center;
  font-size: 0.8rem;
  opacity: 0.7;
  margin-top: auto;
}

.loading {
  display: inline-block;
  width: 20px;
  height: 20px;
  border: 2px solid rgba(99, 102, 241, 0.3);
  border-radius: 50%;
  border-top-color: var(--primary-color);
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.settings-button {
  background: transparent;
  border: none;
  color: var(--primary-color);
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 50%;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.settings-button:hover {
  background: rgba(255, 255, 255, 0.2);
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.dialog-content {
  background: var(--card-background);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  padding: 2rem;
  width: 90%;
  max-width: 400px;
}

.form-group {
  margin-bottom: 1.5rem;
}

label {
  display: block;
  margin-bottom: 0.5rem;
  color: var(--text-color);
  font-size: 0.9rem;
}

.glass-input {
  width: 100%;
  padding: 0.8rem;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  color: var(--text-color);
  font-size: 1rem;
  transition: all 0.3s ease;
}

.glass-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  margin-top: 2rem;
}

.glass-button.cancel {
  background: rgba(239, 68, 68, 0.1);
  color: var(--error-color);
}

.glass-button.cancel:hover {
  background: rgba(239, 68, 68, 0.2);
}

h2 {
  margin-bottom: 1.5rem;
  color: var(--primary-color);
  font-size: 1.5rem;
}
</style>
