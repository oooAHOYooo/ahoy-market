<template>
  <Teleport to="body">
    <!-- Modal backdrop -->
    <div v-if="isOpen" class="cast-modal-backdrop" @click="closeModal"></div>

    <!-- Modal -->
    <div v-if="isOpen" class="cast-modal">
      <div class="cast-modal-content">
        <!-- Header -->
        <div class="cast-modal-header">
          <h2><i class="fas fa-archive"></i> Legacy Cast</h2>
          <button type="button" class="cast-modal-close" @click="closeModal" title="Close">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="cast-info-section">
          <div class="info-icon">
            <i class="fas fa-info-circle"></i>
          </div>
          <h3>Outdated feature</h3>
          <p>This is a legacy surface and is not part of the v1.0.8 shipment. The live app does not expose cast controls.</p>
        </div>

        <!-- Footer -->
        <div class="cast-modal-footer">
          <span class="cast-learn-more">
            <i class="fas fa-archive"></i> Archived for future review
          </span>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  modelValue: Boolean,
})

const emit = defineEmits(['update:modelValue'])

const isOpen = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

function closeModal() {
  isOpen.value = false
}
</script>

<style scoped>
.cast-modal-backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  z-index: 999;
}

.cast-modal {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 480px;
  max-height: 90vh;
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1.5rem;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  box-shadow: 0 25px 50px rgba(0, 0, 0, 0.3);
}

.cast-modal-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.cast-modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.cast-modal-header h2 {
  font-size: 1.25rem;
  font-weight: 700;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: white;
}

.cast-modal-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1.25rem;
  transition: color 0.2s;
  padding: 0;
}

.cast-modal-close:hover {
  color: white;
}

/* Info section (Safari, Chrome) */
.cast-info-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  text-align: center;
}

.info-icon {
  font-size: 2.5rem;
  color: #6ddcff;
  margin-bottom: 1rem;
}

.cast-info-section h3 {
  font-size: 1.2rem;
  font-weight: 700;
  margin: 0 0 0.75rem;
  color: white;
}

.cast-info-section p {
  color: rgba(255, 255, 255, 0.8);
  margin: 0;
  line-height: 1.6;
  font-size: 0.95rem;
}

.cast-info-section strong {
  color: #6ddcff;
  font-weight: 600;
}

/* Connecting section */
.cast-connecting-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  text-align: center;
}

.cast-connecting-section p {
  color: rgba(255, 255, 255, 0.8);
  margin-top: 1rem;
}

/* Casting in progress */
.cast-casting-section {
  flex: 1;
  padding: 2rem 1.5rem;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.casting-spinner {
  font-size: 2.5rem;
  color: #6ddcff;
  margin-bottom: 0.5rem;
}

.cast-casting-section h3 {
  font-size: 1.1rem;
  font-weight: 700;
  margin: 0;
  color: white;
}

.now-casting-track {
  color: rgba(255, 255, 255, 0.8);
  margin: 0.5rem 0 1rem;
  font-size: 0.95rem;
  max-height: 60px;
  overflow: hidden;
}

.cast-btn-stop {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  border-radius: 0.5rem;
  cursor: pointer;
  font-weight: 600;
  transition: all 0.2s;
}

.cast-btn-stop:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #fff;
}

/* Footer */
.cast-modal-footer {
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  justify-content: center;
  flex-shrink: 0;
}

.cast-learn-more {
  color: rgba(255, 255, 255, 0.6);
  text-decoration: none;
  font-size: 0.9rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  transition: color 0.2s;
}

.cast-learn-more:hover {
  color: white;
}

@media (max-width: 480px) {
  .cast-modal {
    width: 95%;
    border-radius: 1.25rem;
  }

  .cast-modal-header {
    padding: 1rem;
  }

  .cast-modal-header h2 {
    font-size: 1.1rem;
  }

  .cast-strategies {
    padding: 0.75rem;
    gap: 0.5rem;
  }

  .cast-strategy-btn {
    padding: 0.75rem;
  }
}
</style>
