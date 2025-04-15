<script setup>
import { ref, watch } from 'vue';

const props = defineProps({
  message: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'info'
  },
  duration: {
    type: Number,
    default: 3000
  },
  visible: {
    type: Boolean,
    default: false
  }
});

const emit = defineEmits(['update:visible']);

const isVisible = ref(false);
const toastClass = ref('');

// 监听visible属性变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    show();
  }
});

const show = () => {
  isVisible.value = true;
  toastClass.value = 'toast-enter';
  
  setTimeout(() => {
    hide();
  }, props.duration);
};

const hide = () => {
  toastClass.value = 'toast-leave';
  setTimeout(() => {
    isVisible.value = false;
    emit('update:visible', false);
  }, 300);
};
</script>

<template>
  <Teleport to="body">
    <div v-if="isVisible" :class="['toast', toastClass, type]">
      {{ message }}
    </div>
  </Teleport>
</template>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  z-index: 9999;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  pointer-events: none;
  letter-spacing: 0.4px;
  line-height: 1.4;
  text-rendering: optimizeLegibility;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

.toast.success {
  background: rgba(16, 185, 129, 0.98);
  color: white;
  border: 1px solid rgba(16, 185, 129, 1);
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.1);
}

.toast.error {
  background: rgba(239, 68, 68, 0.98);
  color: white;
  border: 1px solid rgba(239, 68, 68, 1);
  text-shadow: 0 1px 1px rgba(0, 0, 0, 0.1);
}

.toast-enter {
  animation: toast-in 0.3s ease-out forwards;
}

.toast-leave {
  animation: toast-out 0.3s ease-in forwards;
}

@keyframes toast-in {
  from {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
  to {
    opacity: 1;
    transform: translate(-50%, 0);
  }
}

@keyframes toast-out {
  from {
    opacity: 1;
    transform: translate(-50%, 0);
  }
  to {
    opacity: 0;
    transform: translate(-50%, -20px);
  }
}
</style> 