<template>
  <div class="cast-page">
    <div class="cast-content">
      <div class="cast-card">
        <div class="cast-card-header">
          <h3><i class="fas fa-archive"></i> Legacy Cast</h3>
          <span class="cast-badge-primary">Outdated</span>
        </div>
        <p class="cast-card-text">
          This surface is legacy only and is not part of the v1.0.8 shipment.
          It remains here as a placeholder for future rework, not as an active shipping feature.
        </p>
        <p class="cast-hint">
          <i class="fas fa-info-circle"></i>
          The active app flow does not expose cast controls.
        </p>
      </div>

      <!-- Other Devices -->
      <div class="cast-card">
        <h3><i class="fas fa-tv"></i> Legacy Notes</h3>
        <ul class="cast-options-list">
          <li><strong>AirPlay:</strong> Use Safari, start playing, then tap the AirPlay icon.</li>
          <li><strong>TV browser:</strong> Open <code>app.ahoy.ooo</code> directly on your TV and play from there.</li>
          <li><strong>Desktop browser:</strong> Use your browser's built-in media or tab sharing if needed.</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.cast-page { padding-bottom: 3rem; }
.cast-content { max-width: 640px; margin: 0 auto; padding: 1.5rem; display: flex; flex-direction: column; gap: 1.25rem; }
.cast-card {
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 1.25rem;
}
.cast-card h3 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
  color: #fff;
}
.cast-card-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}
.cast-card-header h3 {
  margin: 0;
}
.cast-badge-primary {
  background: rgba(109, 220, 255, 0.2);
  border: 1px solid rgba(109, 220, 255, 0.3);
  color: #6ddcff;
  padding: 3px 8px;
  border-radius: 6px;
  font-size: 0.75rem;
  font-weight: 600;
  white-space: nowrap;
}
.cast-card-text {
  margin: 0 0 1rem;
  color: rgba(255,255,255,0.8);
  line-height: 1.5;
  font-size: 0.95rem;
}
.cast-options-list {
  margin: 0;
  padding-left: 1.25rem;
  color: rgba(255,255,255,0.8);
  line-height: 1.8;
}
.cast-options-list li {
  margin-bottom: 0.75rem;
}
.cast-options-list code {
  background: rgba(109, 220, 255, 0.1);
  color: #6ddcff;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 0.9em;
}
.cast-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 0.75rem;
}
.cast-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 10px;
  font-weight: 600;
  text-decoration: none;
  border: none;
  cursor: pointer;
  font-size: 14px;
}
.cast-btn.primary {
  background: var(--accent-primary, #6ddcff);
  color: #111;
}
.cast-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.cast-hint {
  margin: 0;
  font-size: 0.85rem;
  color: rgba(255,255,255,0.6);
}
</style>
