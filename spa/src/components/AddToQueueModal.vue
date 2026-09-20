<template>
  <div v-if="addToQueue.showModal.value" class="modal-overlay" @click.self="addToQueue.close()">
    <div class="modal add-to-queue-modal" role="dialog" aria-modal="true" aria-label="Add to queue">
      <div class="modal-header">
        <h3>Add to Queue</h3>
        <button type="button" class="modal-close" aria-label="Close" @click="addToQueue.close()">
          <i class="fas fa-times"></i>
        </button>
      </div>
      <div v-if="track" class="modal-track">
        <div class="modal-track-art">
          <img
            :src="track.cover_art || track.artwork || track.thumbnail || '/static/img/default-cover.jpg'"
            :alt="track.title"
          />
        </div>
        <div class="modal-track-info">
          <div class="modal-track-title">{{ track.title }}</div>
          <div class="modal-track-artist">{{ track.artist || track.host || 'Unknown' }}</div>
        </div>
      </div>
      <div class="modal-content">
        <p>Add this track to the end of your queue?</p>
        <div class="queue-info">
          <span><i class="fas fa-list"></i> Queue: {{ queueCount }} {{ queueCount === 1 ? 'track' : 'tracks' }}</span>
        </div>
      </div>
      <div class="modal-actions">
        <button type="button" class="btn btn-secondary" @click="addToQueue.close()">Cancel</button>
        <button type="button" class="btn btn-primary" @click="addToQueue.addToQueue()">Add to Queue</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useAddToQueue } from '../composables/useAddToQueue'

const addToQueue = useAddToQueue()

const track = computed(() => addToQueue.trackToAdd.value)
const queueCount = computed(() => addToQueue.playerStore.queue.length)
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal {
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.08) 0%, rgba(255, 255, 255, 0.02) 100%);
  border: 1px solid rgba(255, 255, 255, 0.15);
  border-radius: 1.25rem;
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  padding: 0;
  width: 90%;
  max-width: 400px;
  color: white;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.1rem;
  font-weight: 600;
}

.modal-close {
  background: none;
  border: none;
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  font-size: 1.25rem;
  transition: color 0.2s;
  padding: 0;
}

.modal-close:hover {
  color: white;
}

.modal-track {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-track-art {
  width: 64px;
  height: 64px;
  border-radius: 0.5rem;
  overflow: hidden;
  flex-shrink: 0;
}

.modal-track-art img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.modal-track-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.modal-track-title {
  font-weight: 600;
  font-size: 0.95rem;
  margin-bottom: 0.25rem;
  line-height: 1.2;
}

.modal-track-artist {
  font-size: 0.85rem;
  color: rgba(255, 255, 255, 0.7);
}

.modal-content {
  padding: 1.5rem;
  flex: 1;
}

.modal-content p {
  margin: 0 0 1rem;
  color: rgba(255, 255, 255, 0.8);
}

.queue-info {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1rem;
  background: rgba(109, 220, 255, 0.1);
  border: 1px solid rgba(109, 220, 255, 0.2);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  color: rgba(109, 220, 255, 0.9);
}

.modal-actions {
  display: flex;
  gap: 0.75rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn {
  flex: 1;
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 0.95rem;
}

.btn-primary {
  background: var(--primary-color, #ff0060);
  color: white;
}

.btn-primary:hover {
  opacity: 0.9;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

@media (max-width: 480px) {
  .modal {
    max-width: 90vw;
  }
}
</style>
