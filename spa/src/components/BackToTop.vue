<template>
  <Transition name="fade-slide">
    <button 
      v-if="isVisible" 
      class="back-to-top" 
      @click="scrollToTop"
      aria-label="Back to top"
    >
      <i class="fas fa-chevron-up"></i>
    </button>
  </Transition>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const isVisible = ref(false)

function checkScroll() {
  isVisible.value = window.pageYOffset > 400
}

function scrollToTop() {
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

onMounted(() => {
  window.addEventListener('scroll', checkScroll)
})

onUnmounted(() => {
  window.removeEventListener('scroll', checkScroll)
})
</script>

<style scoped>
.back-to-top {
  position: fixed;
  bottom: 100px;
  right: 24px;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: rgba(30, 30, 40, 0.8);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  z-index: 100;
  transition: all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.back-to-top:hover {
  background: #00ffff;
  color: #000;
  transform: translateY(-4px);
  box-shadow: 0 8px 25px rgba(0, 255, 255, 0.4);
}

.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.8);
}
</style>
