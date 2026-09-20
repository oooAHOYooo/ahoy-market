<template>
  <div
    ref="stageRef"
    class="garden-stage"
    :class="{ 'is-viewfinder-mode': activeTool === 'snap' }"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
    @wheel.prevent="onWheel"
  >
    <!-- Main Game HUD -->
    <div class="garden-hud" v-if="activeTool !== 'snap'">
      <button class="garden-btn garden-btn--circle" @pointerdown.stop @pointerup.stop @click="emit('back')" title="Back to console">
        <i class="fa-solid fa-chevron-left"></i>
      </button>

      <!-- Audio Player Control Button -->
      <button 
        class="garden-btn garden-btn--circle garden-btn--radio"
        :class="{ 'is-active': isRadioAudible }"
        @pointerdown.stop 
        @pointerup.stop 
        @click="emit('toggle-radio')" 
        :title="isRadioAudible ? 'Mute Radio' : 'Tune in / Unmute'"
      >
        <img v-if="stationArt" :src="stationArt" alt="" class="radio-btn-art" />
        <span class="radio-btn-icon">
          <i :class="['fas', radioButtonIcon]"></i>
        </span>
      </button>

      <div class="garden-progress-pill" title="Total crops harvested">
        <span class="stat-label"><i class="fa-solid fa-seedling"></i> Harvested</span>
        <span class="stat-value">{{ progress.totalHarvested }}</span>
      </div>

      <div class="garden-beats-pill" title="Console Beats balance">
        <span class="stat-label"><i class="fa-solid fa-bolt"></i> Beats</span>
        <span class="stat-value">{{ Math.floor(progress.beats) }}</span>
      </div>
    </div>

    <!-- Camera Viewfinder Overlay (Active only during Snap Tool) -->
    <div v-if="activeTool === 'snap'" class="camera-viewfinder">
      <div class="viewfinder-top">
        <div class="rec-indicator"><span class="rec-dot"></span> REC</div>
        <div class="cam-mode">ISO 400</div>
        <button class="cam-close" @pointerdown.stop @pointerup.stop @click="activeTool = 'plant'"><i class="fa-solid fa-xmark"></i></button>
      </div>
      <div class="viewfinder-brackets"></div>
      <div class="viewfinder-bottom">
        <div class="cam-station-stamp">{{ stationTitle }}</div>
        <button class="cam-shutter-btn" @pointerdown.stop @pointerup.stop @click="triggerSnap" :disabled="shutterCooldown">
          <div class="shutter-inner"></div>
        </button>
      </div>
    </div>

    <!-- Instant Camera Screen Flash -->
    <div class="camera-flash" :class="{ 'is-flashing': flashActive }"></div>

    <!-- Polaroid Artifact Popup -->
    <Transition name="polaroid-pop">
      <div v-if="polaroidVisible" class="polaroid-card" @pointerdown.stop @pointerup.stop>
        <div class="polaroid-photo">
          <img v-if="capturedSnapImg" :src="capturedSnapImg" class="captured-snap-img" alt="Pocket Garden Snap" />
          <div v-else class="polaroid-art">
            <i class="fa-solid fa-spinner fa-spin"></i>
            <div class="art-label">PROCESSING...</div>
          </div>
        </div>
        <div class="polaroid-caption">
          <div class="caption-title">Garden Polaroid</div>
          <div class="caption-meta">{{ new Date().toLocaleDateString() }} • +5 Beats</div>
          
          <!-- Multi-choice Action Row -->
          <div class="polaroid-actions">
            <button 
              v-if="!isSavedToGallery" 
              type="button"
              class="polaroid-action-btn save-snap-btn" 
              @click="saveSnapToGallery"
              title="Save to Profile Gallery"
            >
              <i class="fa-solid fa-heart"></i> Save to Profile
            </button>
            <span v-else class="polaroid-saved-status">
              <i class="fa-solid fa-circle-check"></i> Added to Profile!
            </span>
            
            <button 
              type="button" 
              class="polaroid-action-btn close-snap-btn" 
              @click="closePolaroid"
            >
              Done
            </button>
          </div>
        </div>
      </div>
    </Transition>

    <!-- Tool Toolbar -->
    <div class="garden-toolbar-wrapper" v-if="activeTool !== 'snap'">
      <div class="garden-toolbar">
        <button
          v-for="tool in tools"
          :key="tool.id"
          class="tool-btn"
          :class="['tool-btn--' + tool.id, { 'is-active': activeTool === tool.id }]"
          @pointerdown.stop
          @pointerup.stop
          @click="activeTool = tool.id"
          :title="toolHints[tool.id]"
        >
          <div class="tool-icon"><i :class="tool.icon"></i></div>
          <div class="tool-name">{{ tool.name }}</div>
        </button>
      </div>
      <Transition name="hint-slide" mode="out-in">
        <div :key="activeTool" class="tool-hint-pill" :class="'tool-hint--' + activeTool">
          <span class="hint-text">{{ toolHints[activeTool] }}</span>
        </div>
      </Transition>
    </div>

    <!-- Initial Console Controls Guidance Popup -->
    <Transition name="hint-fade">
      <div v-if="showInitialHint && activeTool !== 'snap'" class="garden-splash-hint">
        <div class="hint-icon-stack">
          <div class="hint-circle"><i class="fa-solid fa-hand-pointer"></i></div>
          <div class="drag-arrows"><i class="fa-solid fa-arrows-up-down-left-right"></i></div>
        </div>
        <div class="hint-text-stack">
          <div class="hint-title">Game Controls</div>
          <div class="hint-desc">Swipe to rotate &bull; Pinch or scroll to zoom &bull; Tap to garden</div>
        </div>
      </div>
    </Transition>

    <!-- Tamagotchi & Nursery HUD Overlay -->
    <div class="nursery-banner" v-if="activeTool !== 'snap' && !progress.hasPet">
      <button v-if="!progress.hasEgg" class="nursery-btn" @pointerdown.stop @pointerup.stop @click="buyEgg" :disabled="progress.beats < 15">
        <i class="fa-solid fa-egg"></i> Buy Mystery Egg (15 Beats)
      </button>
      <div v-else class="egg-status-pill">
        <i class="fa-solid fa-egg animate-wobble"></i> Egg needs 3 crops! 
        <button class="feed-egg-btn" @pointerdown.stop @pointerup.stop @click="feedEgg" :disabled="progress.totalHarvested < 1">
          Feed Crop ({{ progress.eggFeeds }}/3)
        </button>
      </div>
    </div>

    <div class="pet-status-card" v-if="activeTool !== 'snap' && progress.hasPet">
      <div class="pet-info">
        <div class="pet-badge"><i class="fa-solid fa-heart"></i> Lvl {{ progress.petLevel }}</div>
        <div class="pet-name">"Beatsprout"</div>
      </div>
      <button class="pet-feed-btn" @pointerdown.stop @pointerup.stop @click="interactWithPet" :disabled="progress.totalHarvested < 1">
        Feed Crop (Exp)
      </button>
    </div>

    <!-- Bottom Message Board / Agent Bubble -->
    <div class="agent-chat-wrapper" v-if="activeTool !== 'snap'" :class="{ 'is-open': chatOpen }" @pointerdown.stop @pointerup.stop @click="toggleChat">
      <div class="agent-chat-avatar">
        <div class="bot-screen"><i class="fa-solid fa-robot"></i></div>
        <div class="bot-pulse"></div>
      </div>
      <div class="agent-bubble">
        <div class="bubble-kicker">AHOY BOT</div>
        <div class="bubble-text">{{ currentMessage }}</div>
        <div class="bubble-hint">tap to chat</div>
      </div>
    </div>

    <!-- Per-plot overlays: harvest badge, thirst drop, growth ring -->
    <template v-if="activeTool !== 'snap'">
      <template v-for="ov in plotOverlays" :key="ov.idx">
        <!-- Harvest ready badge -->
        <div
          v-if="ov.stage === 3"
          class="plot-badge plot-badge--harvest"
          :style="{ left: ov.x + 'px', top: ov.y + 'px' }"
        >✂</div>

        <!-- Thirst drop (growing but not watered) -->
        <div
          v-else-if="(ov.stage === 1 || ov.stage === 2) && !ov.watered"
          class="plot-badge plot-badge--thirst"
          :style="{ left: ov.x + 'px', top: ov.y + 'px' }"
        ><i class="fa-solid fa-droplet"></i></div>

        <!-- Growth ring (growing plots) -->
        <svg
          v-if="ov.stage === 1 || ov.stage === 2"
          class="plot-ring"
          :style="{ left: ov.x + 'px', top: ov.y + 'px' }"
          viewBox="0 0 24 24"
        >
          <circle class="plot-ring-bg" cx="12" cy="12" r="10" />
          <circle
            class="plot-ring-fill"
            :class="ov.watered ? 'is-watered' : ''"
            cx="12" cy="12" r="10"
            :stroke-dasharray="`${ov.growth * 62.8} 62.8`"
          />
        </svg>
      </template>
    </template>

    <!-- First-seed callout: shown until the first plot is planted -->
    <Transition name="hint-fade">
      <div v-if="isFirstSeed && activeTool !== 'snap'" class="first-seed-callout" aria-hidden="true">
        <div class="first-seed-arrow"><i class="fa-solid fa-arrow-up"></i></div>
        <div class="first-seed-label">Tap a soil plot to plant your first seed</div>
      </div>
    </Transition>

    <!-- Particles Counter Increment Popups -->
    <TransitionGroup name="pop-fade">
      <div
        v-for="pop in scorePopups"
        :key="pop.id"
        class="score-popup"
        :style="{ left: pop.x + 'px', top: pop.y + 'px' }"
      >
        +{{ pop.amount }} <span>🌱</span>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  audioDrive: { type: Number, default: 0.2 },
  stationTitle: { type: String, default: 'Live Radio' },
  isRadioAudible: { type: Boolean, default: false },
  radioButtonIcon: { type: String, default: 'fa-play' },
  stationArt: { type: String, default: '' }
})

const emit = defineEmits(['back', 'toggle-radio'])

const stageRef = ref(null)
const chatOpen = ref(false)
const scorePopups = ref([])
let popupIdCounter = 0

// ── State Persistence in localStorage ────────────────────────────────────────
const progress = reactive({
  totalHarvested: 0,
  beats: 15, // starting cash
  hasEgg: false,
  eggFeeds: 0,
  hasPet: false,
  petLevel: 1,
  petExp: 0
})

const currentAudioDrive = ref(0.2)
watch(() => props.audioDrive, (val) => {
  currentAudioDrive.value = val
})

onMounted(() => {
  const saved = localStorage.getItem('ahoy_garden_progress')
  if (saved) {
    try {
      const data = JSON.parse(saved)
      progress.totalHarvested = data.totalHarvested || 0
      progress.beats = data.beats != null ? data.beats : 15
      progress.hasEgg = data.hasEgg || false
      progress.eggFeeds = data.eggFeeds || 0
      progress.hasPet = data.hasPet || false
      progress.petLevel = data.petLevel || 1
      progress.petExp = data.petExp || 0
    } catch (e) { console.error(e) }
  }
})

function saveProgress() {
  localStorage.setItem('ahoy_garden_progress', JSON.stringify(progress))
}

// ── Egg & Tamagotchi Actions ────────────────────────────────────────────────
function buyEgg() {
  if (progress.beats < 15) return
  progress.beats -= 15
  progress.hasEgg = true
  progress.eggFeeds = 0
  currentMessage.value = "Wow! You got a Mystery Egg! Stand it on the pedestal and feed it 3 harvested crops to hatch it!"
  saveProgress()
  syncNurseryVisuals()
}

function feedEgg() {
  if (progress.totalHarvested < 1 || !progress.hasEgg) return
  progress.totalHarvested -= 1
  progress.eggFeeds += 1
  
  currentMessage.value = `Yum! The egg wobbles happily! Feed status: ${progress.eggFeeds}/3`
  
  navigator.vibrate?.(12)
  if (eggMesh) {
    eggMesh.position.y += 0.3
    eggMesh.rotation.z = (Math.random() - 0.5) * 0.4
    setTimeout(() => { if (eggMesh) { eggMesh.rotation.z = 0 } }, 200)
  }
  
  if (progress.eggFeeds >= 3) {
    hatchEgg()
  } else {
    saveProgress()
  }
}

function hatchEgg() {
  progress.hasEgg = false
  progress.eggFeeds = 0
  progress.hasPet = true
  progress.petLevel = 1
  progress.petExp = 0
  
  currentMessage.value = "🐣 CRACK! Congratulations! A cute bouncy 'Beatsprout' pet hatched from the egg!"
  
  saveProgress()
  
  // Trigger particle explosion at egg pedestal
  if (pedestalGroup) {
    triggerExplosion(pedestalGroup.position, 0xff2fb8)
  }
  
  syncNurseryVisuals()
}

function interactWithPet() {
  if (progress.totalHarvested < 1 || !progress.hasPet) return
  progress.totalHarvested -= 1
  progress.petExp += 10
  
  currentMessage.value = "Beatsprout eats the crop! He loves it!"
  
  if (petMeshGroup) {
    petMeshGroup.position.y += 0.5 // jump joyfully!
  }
  
  // Level up at 30 Exp
  if (progress.petExp >= 30) {
    progress.petLevel += 1
    progress.petExp = 0
    currentMessage.value = `🎉 LEVEL UP! Beatsprout grew to Level ${progress.petLevel}!`
    // particle burst
    if (petMeshGroup) {
      triggerExplosion(petMeshGroup.position, 0xffd400)
    }
  }
  
  saveProgress()
}

// ── Snap/Camera Utility ─────────────────────────────────────────────────────
const flashActive = ref(false)
const polaroidVisible = ref(false)
const shutterCooldown = ref(false)
const capturedSnapImg = ref(null)
const isSavedToGallery = ref(false)

function triggerSnap() {
  if (shutterCooldown.value) return
  shutterCooldown.value = true
  
  // 1. Flash Screen
  flashActive.value = true
  setTimeout(() => { flashActive.value = false }, 250)
  
  // 2. Capture Actual Three.js Canvas Content
  if (renderer && scene && camera) {
    try {
      // Double check final frame render before reading
      renderer.render(scene, camera)
      capturedSnapImg.value = renderer.domElement.toDataURL('image/jpeg', 0.82)
    } catch (e) {
      console.error('Failed to capture canvas snap:', e)
      capturedSnapImg.value = null
    }
  }
  isSavedToGallery.value = false

  // 3. Award Economy
  progress.beats += 5
  saveProgress()
  
  // 4. Display user-controlled interactive Polaroid Popup
  polaroidVisible.value = true
}

function saveSnapToGallery() {
  if (!capturedSnapImg.value || isSavedToGallery.value) return
  
  try {
    // Load existing snap gallery from local storage
    const galleryRaw = localStorage.getItem('ahoy_garden_gallery')
    const gallery = galleryRaw ? JSON.parse(galleryRaw) : []
    
    // Limit image footprint (e.g., keep latest 15 snaps max to prevent bloating local storage limit)
    if (gallery.length >= 15) {
      gallery.pop() // remove oldest
    }
    
    // Prepend new snap
    gallery.unshift({
      id: `snap_${Date.now()}`,
      image: capturedSnapImg.value,
      date: new Date().toISOString(),
      title: props.stationTitle || 'Indie Beats Garden',
      totalHarvested: progress.totalHarvested
    })
    
    localStorage.setItem('ahoy_garden_gallery', JSON.stringify(gallery))
    isSavedToGallery.value = true
    
    // Dispatch global event to let Profile/Account view know to re-fetch if mounted
    window.dispatchEvent(new CustomEvent('ahoy_gallery_updated'))
    
    // Trigger success toast if applicable
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Saved to Profile Gallery! 📸', type: 'success' } }))
  } catch (e) {
    console.error('Could not save to profile:', e)
    window.dispatchEvent(new CustomEvent('ahoy:toast', { detail: { message: 'Storage full! Clear some old snaps.', type: 'error' } }))
  }
}

function closePolaroid() {
  polaroidVisible.value = false
  setTimeout(() => {
    shutterCooldown.value = false
    capturedSnapImg.value = null
  }, 400)
}

// ── Tools Configuration ────────────────────────────────────────────────────
const tools = [
  { id: 'plant', name: 'Seed', icon: 'fa-solid fa-leaf' },
  { id: 'water', name: 'Water', icon: 'fa-solid fa-droplet' },
  { id: 'harvest', name: 'Collect', icon: 'fa-solid fa-basket-shopping' },
  { id: 'terraform', name: 'Terraform', icon: 'fa-solid fa-mountain' },
  { id: 'snap', name: 'Snap 📸', icon: 'fa-solid fa-camera' }
]
const activeTool = ref('plant')

// True until the player plants their very first seed
const isFirstSeed = computed(() =>
  activeTool.value === 'plant' && gardenGrid.every(c => c.stage === 0)
)

// ── Guidance Hints configuration ───────────────────────────────────────────
const showInitialHint = ref(true)
const toolHints = {
  plant: 'Tap an empty soil plot to plant a seed (Cost: 2 Beats)',
  water: 'Tap dry brown soil plots to water growing crops',
  harvest: 'Tap glowing ripe plants to collect harvested Beats',
  terraform: 'Tap plots to raise or lower the terrain — sculpt your island!',
  snap: 'Capture a cool angle and press the shutter button for +5 Beats!'
}

onMounted(() => {
  // Automatically fade out initial controls prompt after 4.5s
  setTimeout(() => {
    showInitialHint.value = false
  }, 4500)
})

// ── AI Bot Dialogue ────────────────────────────────────────────────────────
const BOT_QUOTES = [
  "Ahoy there! Listening to indie beats helps plants grow up to 4x faster!",
  "Your pet Beatsprout looks extremely cozy on our island today.",
  "Beep boop! Tap the Snap Tool to photograph your floating paradise!",
  "Make sure to feed harvested crops to your Egg so it hatches into a cute creature!",
  "This station really puts me in a peaceful growing mood.",
  "You earn Beats passively just by listening to the radio station!",
  "Swipe the screen to spin the floating island around in zero-gravity!",
  "Did you know Space Seagulls is now available in the arcade menu? Launch 'em high!",
  "Your garden is fully saved! Feel free to relax and enjoy the rhythm."
]
const currentMessage = ref("Welcome to your persistent Pocket Garden! Let's raise some crops and pets to the rhythm.")

function toggleChat() {
  chatOpen.value = true
  const randomQuote = BOT_QUOTES[Math.floor(Math.random() * BOT_QUOTES.length)]
  currentMessage.value = randomQuote.replace("[stationTitle]", props.stationTitle)
  
  setTimeout(() => { chatOpen.value = false }, 4500)
}

// ── Three.js Constants & Color Palette ──────────────────────────────────────
const GRID_SIZE = 5
const CELL_SIZE = 1.1
const CMYK = {
  island: 0x2c3e50,
  grass: 0x2ecc71,
  dirtDry: 0x8d6e63,
  dirtWet: 0x4e342e,
  cyan: 0x00d7ff,
  magenta: 0xff2fb8,
  yellow: 0xffd400,
  botMetal: 0xe0e0e0,
}

// ── Three.js State ──────────────────────────────────────────────────────────
let renderer, scene, camera
let rafId = 0
let lastTime = 0
let resizeObserver

// 3D Scene Nodes
let islandGroup
let plotMeshes = [] 
let plantMeshes = [] 
let botGroup, botScreenMesh
let pedestalGroup, eggMesh, petMeshGroup

// Orbit controls
let isDragging = false
let prevPointerX = 0, prevPointerY = 0
let targetRotationY = -Math.PI / 6
let targetRotationX = 0.4
let currentRotationY = -Math.PI / 6
let currentRotationX = 0.4
let pointerDownTime = 0
let clickDetected = false

// Zoom
const ZOOM_MIN = 7.0
const ZOOM_MAX = 22.0
let targetZoom = 13.5
let currentZoom = 13.5

// Pinch
const activePointers = new Map()
let prevPinchDist = 0

// Raycaster
const raycaster = new THREE.Raycaster()
const pointer = new THREE.Vector2()

// Per-plot CSS overlays (harvest badge, thirst drop, growth ring)
const plotOverlays = ref([])
const _vec3 = new THREE.Vector3()
function worldToScreen(worldPos) {
  if (!renderer || !camera || !stageRef.value) return null
  _vec3.copy(worldPos)
  _vec3.project(camera)
  const rect = stageRef.value.getBoundingClientRect()
  return {
    x: (_vec3.x * 0.5 + 0.5) * rect.width,
    y: (-_vec3.y * 0.5 + 0.5) * rect.height,
  }
}

function updatePlotOverlays() {
  if (!renderer) return
  const overlays = []
  gardenGrid.forEach((cell, idx) => {
    const holder = plantMeshes[idx]
    if (!holder) return
    // World position slightly above the plot
    const wp = new THREE.Vector3()
    holder.getWorldPosition(wp)
    wp.y += 0.6
    const screen = worldToScreen(wp)
    if (!screen) return
    overlays.push({
      idx,
      x: screen.x,
      y: screen.y,
      stage: cell.stage,
      watered: cell.watered,
      growth: cell.growth,
    })
  })
  plotOverlays.value = overlays
}

// ── Grid State ─────────────────────────────────────────────────────────────
const gardenGrid = reactive([])

function initGridData() {
  gardenGrid.length = 0
  for (let r = 0; r < GRID_SIZE; r++) {
    for (let c = 0; c < GRID_SIZE; c++) {
      gardenGrid.push({
        id: `${r}-${c}`,
        r, c,
        stage: 0, // 0 empty, 1 seed, 2 sprout, 3 harvest-ready
        watered: false,
        growth: 0,
        terrain: 0, // 0 flat, 1 raised (hill), 2 lowered (pond)
      })
    }
  }
}

function loadGridFromStorage() {
  initGridData()
  const saved = localStorage.getItem('ahoy_garden_grid')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      parsed.forEach((savedCell, i) => {
        if (gardenGrid[i]) {
          gardenGrid[i].stage = savedCell.stage ?? 0
          gardenGrid[i].watered = savedCell.watered ?? false
          gardenGrid[i].growth = savedCell.growth ?? 0
          gardenGrid[i].terrain = savedCell.terrain ?? 0
        }
      })
    } catch (e) { console.error(e) }
  }
}

function saveGridToStorage() {
  localStorage.setItem('ahoy_garden_grid', JSON.stringify(gardenGrid))
}

// ── Scene Setup ─────────────────────────────────────────────────────────────
function buildScene() {
  scene = new THREE.Scene()
  scene.background = null // css gradient shows through

  camera = new THREE.PerspectiveCamera(40, 1, 0.1, 100)
  camera.position.set(0, 7.5, 13.5)
  camera.lookAt(0, 0, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.shadowMap.enabled = true
  stageRef.value.appendChild(renderer.domElement)

  // Lights
  scene.add(new THREE.AmbientLight(0xffffff, 0.85))
  const dirLight = new THREE.DirectionalLight(0xffffff, 1.4)
  dirLight.position.set(6, 12, 6)
  dirLight.castShadow = true
  scene.add(dirLight)

  const fillLight = new THREE.DirectionalLight(CMYK.cyan, 0.5)
  fillLight.position.set(-6, 3, 3)
  scene.add(fillLight)

  islandGroup = new THREE.Group()
  scene.add(islandGroup)

  buildIslandGeometry()
  buildBot()
  buildNurseryPedestal()

  syncPlotVisuals()
  syncNurseryVisuals()
}

function buildIslandGeometry() {
  const totalW = GRID_SIZE * CELL_SIZE + 0.9
  
  // Floating Top
  const grass = new THREE.Mesh(
    new THREE.BoxGeometry(totalW, 0.8, totalW),
    new THREE.MeshStandardMaterial({ color: CMYK.grass, roughness: 0.8 })
  )
  grass.position.y = -0.4
  grass.receiveShadow = true
  islandGroup.add(grass)

  // Floating Bottom
  const stone = new THREE.Mesh(
    new THREE.BoxGeometry(totalW - 0.4, 1.5, totalW - 0.4),
    new THREE.MeshStandardMaterial({ color: CMYK.island, roughness: 0.9 })
  )
  stone.position.y = -1.55
  stone.receiveShadow = true
  islandGroup.add(stone)

  // 5x5 plot tiles
  plotMeshes = []
  const startOffset = -((GRID_SIZE - 1) / 2) * CELL_SIZE
  const plotGeo = new THREE.BoxGeometry(0.95, 0.06, 0.95)

  gardenGrid.forEach((cell) => {
    const plot = new THREE.Mesh(plotGeo, new THREE.MeshStandardMaterial({ color: CMYK.dirtDry, roughness: 1.0 }))
    const px = startOffset + cell.c * CELL_SIZE
    const pz = startOffset + cell.r * CELL_SIZE
    plot.position.set(px, 0.04, pz)
    plot.receiveShadow = true
    plot.userData = { index: cell.r * GRID_SIZE + cell.c }
    islandGroup.add(plot)
    plotMeshes.push(plot)

    const pGroup = new THREE.Group()
    pGroup.position.set(px, 0.06, pz)
    islandGroup.add(pGroup)
    plantMeshes.push(pGroup)
  })
}

function buildBot() {
  botGroup = new THREE.Group()
  botGroup.position.set(3.8, 1.5, -2.0) // Hover offset
  scene.add(botGroup)

  const body = new THREE.Mesh(
    new THREE.SphereGeometry(0.5, 16, 16),
    new THREE.MeshStandardMaterial({ color: CMYK.botMetal, roughness: 0.3, metalness: 0.6 })
  )
  botGroup.add(body)

  // Cyan screen face
  botScreenMesh = new THREE.Mesh(
    new THREE.BoxGeometry(0.45, 0.3, 0.1),
    new THREE.MeshStandardMaterial({ color: 0x0b0b0b, emissive: CMYK.cyan, emissiveIntensity: 0.5 })
  )
  botScreenMesh.position.set(-0.3, 0.08, 0.3)
  botScreenMesh.rotation.y = -Math.PI / 4
  botGroup.add(botScreenMesh)

  // Eyes
  const eyeGeo = new THREE.BoxGeometry(0.06, 0.06, 0.05)
  const eyeMat = new THREE.MeshBasicMaterial({ color: CMYK.yellow })
  const lEye = new THREE.Mesh(eyeGeo, eyeMat)
  lEye.position.set(-0.4, 0.12, 0.4)
  lEye.rotation.y = -Math.PI / 4
  botGroup.add(lEye)

  const rEye = new THREE.Mesh(eyeGeo, eyeMat)
  rEye.position.set(-0.25, 0.12, 0.25)
  rEye.rotation.y = -Math.PI / 4
  botGroup.add(rEye)

  // Antenna
  const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.02, 0.02, 0.4), new THREE.MeshStandardMaterial({ color: CMYK.botMetal }))
  ant.position.y = 0.6
  botGroup.add(ant)
  const tip = new THREE.Mesh(new THREE.SphereGeometry(0.06), new THREE.MeshBasicMaterial({ color: CMYK.magenta }))
  tip.position.y = 0.8
  botGroup.add(tip)
}

// ── 3D Nursery: Eggs & Creatures ────────────────────────────────────────────
function buildNurseryPedestal() {
  pedestalGroup = new THREE.Group()
  // Corner of the island
  pedestalGroup.position.set(-3.4, 0.2, -3.4)
  islandGroup.add(pedestalGroup)

  // Pedestal base
  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(0.6, 0.7, 0.4, 6),
    new THREE.MeshStandardMaterial({ color: 0x7f8c8d, roughness: 0.9 })
  )
  base.position.y = -0.2
  pedestalGroup.add(base)
}

function syncNurseryVisuals() {
  // 1. Render Egg
  if (eggMesh) {
    pedestalGroup.remove(eggMesh)
    if (eggMesh.geometry) eggMesh.geometry.dispose()
    eggMesh = null
  }

  if (progress.hasEgg) {
    const eggGeo = new THREE.SphereGeometry(0.4, 16, 16)
    const eggMat = new THREE.MeshStandardMaterial({ 
      color: 0xffffff, 
      roughness: 0.4,
      emissive: CMYK.magenta,
      emissiveIntensity: 0.1 
    })
    eggMesh = new THREE.Mesh(eggGeo, eggMat)
    eggMesh.scale.set(1, 1.35, 1)
    eggMesh.position.y = 0.3
    pedestalGroup.add(eggMesh)
  }

  // 2. Render Pet Group
  if (petMeshGroup) {
    scene.remove(petMeshGroup)
    petMeshGroup = null
  }

  if (progress.hasPet) {
    petMeshGroup = new THREE.Group()
    // Start at random center
    petMeshGroup.position.set(0, 0.2, 0)
    islandGroup.add(petMeshGroup)

    // Leaf Slime: Soft lime-green sphere
    const slimeBody = new THREE.Mesh(
      new THREE.SphereGeometry(0.38, 16, 14),
      new THREE.MeshStandardMaterial({ color: 0xa3e4d7, roughness: 0.2 })
    )
    petMeshGroup.add(slimeBody)

    // Eyes
    const eyeMat = new THREE.MeshBasicMaterial({ color: 0x1a252f })
    const l = new THREE.Mesh(new THREE.SphereGeometry(0.04), eyeMat)
    l.position.set(0.12, 0.1, 0.32)
    petMeshGroup.add(l)

    const r = new THREE.Mesh(new THREE.SphereGeometry(0.04), eyeMat)
    r.position.set(-0.12, 0.1, 0.32)
    petMeshGroup.add(r)

    // Little pink cheeks
    const cheekMat = new THREE.MeshBasicMaterial({ color: CMYK.magenta })
    const lc = new THREE.Mesh(new THREE.SphereGeometry(0.03), cheekMat)
    lc.position.set(0.22, 0.02, 0.28)
    petMeshGroup.add(lc)
    
    const rc = new THREE.Mesh(new THREE.SphereGeometry(0.03), cheekMat)
    rc.position.set(-0.22, 0.02, 0.28)
    petMeshGroup.add(rc)

    // 3D Leaf Crown
    const leafGeo = new THREE.BoxGeometry(0.12, 0.35, 0.04)
    const leafMat = new THREE.MeshStandardMaterial({ color: CMYK.grass })
    
    const leafL = new THREE.Mesh(leafGeo, leafMat)
    leafL.position.set(0.1, 0.4, 0)
    leafL.rotation.z = 0.4
    petMeshGroup.add(leafL)

    const leafR = new THREE.Mesh(leafGeo, leafMat)
    leafR.position.set(-0.1, 0.4, 0)
    leafR.rotation.z = -0.4
    petMeshGroup.add(leafR)
  }
}

// ── Crop Visuals Sync ──────────────────────────────────────────────────────
function syncPlotVisuals() {
  gardenGrid.forEach((cell, idx) => {
    const plot = plotMeshes[idx]
    const holder = plantMeshes[idx]
    if (!plot || !holder) return

    // Terrain height
    const terrainY = cell.terrain === 1 ? 0.28 : cell.terrain === 2 ? -0.18 : 0.04
    plot.position.y = terrainY
    plantMeshes[idx].position.y = terrainY + 0.02

    // Plot Soil base color
    const isPond = cell.terrain === 2 && cell.stage === 0
    plot.material.color.setHex(
      isPond ? 0x1a6fa8
      : cell.stage === 0 ? CMYK.dirtDry
      : cell.watered ? CMYK.dirtWet : CMYK.dirtDry
    )

    // Clear old plant mesh
    while(holder.children.length > 0) {
      const child = holder.children[0]
      holder.remove(child)
      if (child.geometry) child.geometry.dispose()
    }

    // Render stage models
    if (cell.stage === 1) {
      // Seed
      const sd = new THREE.Mesh(new THREE.SphereGeometry(0.06, 6, 6), new THREE.MeshStandardMaterial({ color: 0x5d4037 }))
      sd.position.set(0.05, 0.02, -0.05)
      holder.add(sd)
    }
    else if (cell.stage === 2) {
      // Sprout
      const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.02, 0.3, 6), new THREE.MeshStandardMaterial({ color: 0x48c9b0 }))
      stem.position.y = 0.12
      holder.add(stem)
      
      const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.08, 6, 6), new THREE.MeshStandardMaterial({ color: 0x2ecc71 }))
      leaf.scale.set(1.4, 0.4, 1)
      leaf.position.set(0.08, 0.2, 0)
      leaf.rotation.z = 0.4
      holder.add(leaf)
    }
    else if (cell.stage === 3) {
      // Mature Tree with Glowing Fruits
      const bush = new THREE.Mesh(new THREE.SphereGeometry(0.3, 10, 10), new THREE.MeshStandardMaterial({ color: 0x27ae60, roughness: 0.8 }))
      bush.position.y = 0.28
      bush.scale.set(1.0, 1.2, 1.0)
      holder.add(bush)

      const fruitMat = new THREE.MeshStandardMaterial({ color: CMYK.yellow, emissive: CMYK.yellow, emissiveIntensity: 0.4 })
      const f1 = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 8), fruitMat)
      f1.position.set(0.15, 0.4, 0.15)
      holder.add(f1)

      const f2 = new THREE.Mesh(new THREE.SphereGeometry(0.12, 8, 8), fruitMat)
      f2.position.set(-0.15, 0.3, -0.15)
      holder.add(f2)
    }
  })
}

// ── Pointer Raycast & Orbit Helpers ─────────────────────────────────────────
function getPinchDist() {
  const pts = [...activePointers.values()]
  if (pts.length < 2) return 0
  const dx = pts[0].x - pts[1].x
  const dy = pts[0].y - pts[1].y
  return Math.sqrt(dx * dx + dy * dy)
}

function onPointerDown(e) {
  activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY })
  if (activePointers.size === 1) {
    isDragging = true
    prevPointerX = e.clientX
    prevPointerY = e.clientY
    pointerDownTime = Date.now()
    clickDetected = true
  } else if (activePointers.size === 2) {
    // Starting a pinch — cancel any pending tap
    clickDetected = false
    isDragging = false
    prevPinchDist = getPinchDist()
  }
}

function onPointerMove(e) {
  activePointers.set(e.pointerId, { x: e.clientX, y: e.clientY })

  if (activePointers.size >= 2) {
    // Pinch zoom
    const dist = getPinchDist()
    if (prevPinchDist > 0) {
      const delta = prevPinchDist - dist
      targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, targetZoom + delta * 0.06))
    }
    prevPinchDist = dist
    return
  }

  if (!isDragging) return
  const dx = e.clientX - prevPointerX
  const dy = e.clientY - prevPointerY

  if (Math.abs(dx) > 3 || Math.abs(dy) > 3) clickDetected = false

  targetRotationY += dx * 0.008
  targetRotationX = Math.max(0.12, Math.min(1.15, targetRotationX + dy * 0.008))

  prevPointerX = e.clientX
  prevPointerY = e.clientY
}

function onPointerUp(e) {
  activePointers.delete(e.pointerId)
  if (activePointers.size < 2) prevPinchDist = 0
  if (activePointers.size === 0) {
    isDragging = false
    if (clickDetected && (Date.now() - pointerDownTime < 350)) {
      handleScreenTap(e)
    }
  }
}

function onWheel(e) {
  targetZoom = Math.max(ZOOM_MIN, Math.min(ZOOM_MAX, targetZoom + e.deltaY * 0.02))
}

function handleScreenTap(e) {
  if (!stageRef.value || activeTool.value === 'snap') return
  const rect = stageRef.value.getBoundingClientRect()
  pointer.x = ((e.clientX - rect.left) / rect.width) * 2 - 1
  pointer.y = -((e.clientY - rect.top) / rect.height) * 2 + 1

  raycaster.setFromCamera(pointer, camera)

  // 1. Hit Pedestal/Egg?
  if (progress.hasEgg && eggMesh) {
    const eggHit = raycaster.intersectObjects(pedestalGroup.children, true)
    if (eggHit.length > 0) {
      feedEgg()
      return
    }
  }

  // 2. Hit Bot?
  const botHit = raycaster.intersectObjects(botGroup.children, true)
  if (botHit.length > 0) {
    toggleChat()
    botGroup.position.y += 0.5 // happy pop
    return
  }

  // 3. Hit Pet?
  if (progress.hasPet && petMeshGroup) {
    const petHit = raycaster.intersectObjects(petMeshGroup.children, true)
    if (petHit.length > 0) {
      interactWithPet()
      return
    }
  }

  // 4. Hit Grid plot?
  const intersects = raycaster.intersectObjects(plotMeshes)
  if (intersects.length > 0) {
    const index = intersects[0].object.userData.index
    const cell = gardenGrid[index]
    executeTool(cell, e.clientX, e.clientY, index)
  }
}

function executeTool(cell, sX, sY, idx) {
  if (activeTool.value === 'plant') {
    if (cell.stage !== 0) return
    if (progress.beats < 2) {
      currentMessage.value = "You need at least 2 Beats to buy premium Seeds!"
      return
    }
    progress.beats -= 2
    cell.stage = 1
    cell.growth = 0
    cell.watered = false
    navigator.vibrate?.(8)
    plantMeshes[idx].scale.setScalar(0.1)
  }
  else if (activeTool.value === 'water') {
    if (cell.stage === 0 || cell.stage === 3) return
    if (cell.watered) return
    cell.watered = true
    navigator.vibrate?.(6)
    // Flash plot
    const orig = plotMeshes[idx].material.color.getHex()
    plotMeshes[idx].material.color.setHex(CMYK.cyan)
    setTimeout(() => { if (plotMeshes[idx]?.material) plotMeshes[idx].material.color.setHex(CMYK.dirtWet) }, 100)
  }
  else if (activeTool.value === 'harvest') {
    if (cell.stage !== 3) return
    cell.stage = 0
    cell.growth = 0
    cell.watered = false

    progress.totalHarvested += 1
    progress.beats += 10 // collect payload!

    navigator.vibrate?.([10, 20, 15])
    createScorePopup(sX, sY, 10)
    triggerExplosion(plantMeshes[idx].position, CMYK.yellow)
  }
  else if (activeTool.value === 'terraform') {
    // Cycle: flat → hill → pond → flat. Clear crops when changing terrain.
    cell.terrain = (cell.terrain + 1) % 3
    if (cell.stage !== 0) {
      cell.stage = 0
      cell.growth = 0
      cell.watered = false
    }
    const colors = [CMYK.dirtDry, 0x8b6914, 0x1a6fa8]
    triggerExplosion(plotMeshes[idx].position, colors[cell.terrain])
  }

  syncPlotVisuals()
  saveGridToStorage()
  saveProgress()
}

function createScorePopup(x, y, amount) {
  const pop = { id: popupIdCounter++, x, y, amount }
  scorePopups.value.push(pop)
  setTimeout(() => { scorePopups.value = scorePopups.value.filter(p => p.id !== pop.id) }, 1500)
}

let particles = []
function triggerExplosion(pos, colorHex) {
  const pMat = new THREE.MeshBasicMaterial({ color: colorHex })
  const pGeo = new THREE.SphereGeometry(0.07, 4, 4)
  
  for (let i = 0; i < 14; i++) {
    const m = new THREE.Mesh(pGeo, pMat)
    m.position.copy(pos)
    m.position.y += 0.3
    islandGroup.add(m)
    particles.push({
      mesh: m,
      vx: (Math.random() - 0.5) * 3.5,
      vy: Math.random() * 3.5 + 2.0,
      vz: (Math.random() - 0.5) * 3.5,
      life: 0.7 + Math.random() * 0.4
    })
  }
}

// ── Animation Loop & Simulation ─────────────────────────────────────────────
let growAccumulator = 0
let petHopTimer = 0
let petTargetX = 0
let petTargetZ = 0

function tick(now) {
  rafId = requestAnimationFrame(tick)
  const dt = lastTime ? Math.min((now - lastTime) / 1000, 0.05) : 0
  lastTime = now

  // 1. Island Camera Orbit + Zoom
  currentRotationY += (targetRotationY - currentRotationY) * 0.12
  currentRotationX += (targetRotationX - currentRotationX) * 0.12
  currentZoom += (targetZoom - currentZoom) * 0.10
  if (islandGroup) {
    islandGroup.rotation.y = currentRotationY
    islandGroup.rotation.x = currentRotationX
  }
  if (camera) camera.position.z = currentZoom

  // 2. Bot Hovering & Antenna Beat Pulse
  if (botGroup) {
    const driveMul = currentAudioDrive.value * 2.6
    botGroup.position.y = 1.45 + Math.sin(now * 0.0025) * 0.18 + driveMul * 0.14
    if (botScreenMesh) {
      botScreenMesh.material.emissiveIntensity = 0.4 + Math.abs(Math.sin(now * 0.005)) * 0.4 + driveMul * 0.9
    }
  }

  // 3. Wobbling Egg
  if (eggMesh && progress.hasEgg) {
    eggMesh.position.y = 0.3 + Math.abs(Math.sin(now * 0.004 + 0.5)) * 0.05
    eggMesh.rotation.z = Math.sin(now * 0.006) * 0.12
  }

  // 4. Tamagotchi Pet Hopping Logic!
  if (petMeshGroup && progress.hasPet) {
    petHopTimer += dt
    if (petHopTimer > 4.5) {
      petHopTimer = 0
      // Pick new random coordinate on island
      petTargetX = (Math.random() - 0.5) * 4.5
      petTargetZ = (Math.random() - 0.5) * 4.5
    }

    // Smoothly slide position toward targets
    const dirX = petTargetX - petMeshGroup.position.x
    const dirZ = petTargetZ - petMeshGroup.position.z
    const dist = Math.sqrt(dirX * dirX + dirZ * dirZ)

    if (dist > 0.1) {
      // Move
      petMeshGroup.position.x += dirX * 0.015
      petMeshGroup.position.z += dirZ * 0.015
      // Bouncing Hop height based on movement
      petMeshGroup.position.y = 0.15 + Math.abs(Math.sin(now * 0.008)) * 0.32
      // Face walking direction
      const angle = Math.atan2(dirX, dirZ)
      petMeshGroup.rotation.y = angle
    } else {
      // Idle standing breath
      petMeshGroup.position.y = 0.15 + Math.sin(now * 0.004) * 0.03
    }
    // Beat pulse scaler for pet
    const scaleBeat = 1.0 + currentAudioDrive.value * 0.15
    petMeshGroup.scale.setScalar(scaleBeat)
  }

  // 5a. Plant pop-in tween — scale up from 0.1 to 1 smoothly after planting
  for (const holder of plantMeshes) {
    if (!holder) continue
    const s = holder.scale.x
    if (s > 0 && s < 0.98) {
      const next = s + (1 - s) * Math.min(dt * 7, 1)
      holder.scale.setScalar(next)
    }
  }

  // 5. Simulating Crop growth (1s intervals)
  growAccumulator += dt
  if (growAccumulator >= 1.0) {
    growAccumulator = 0
    simulateCropGrowth()
  }

  // 6. Particle lifecycle
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.life -= dt
    if (p.life <= 0) {
      islandGroup.remove(p.mesh)
      p.mesh.geometry.dispose()
      particles.splice(i, 1)
      continue
    }
    p.vy -= 9.8 * dt // gravity
    p.mesh.position.x += p.vx * dt
    p.mesh.position.y += p.vy * dt
    p.mesh.position.z += p.vz * dt
  }

  // 7. Pulse empty plots when no seed has been planted yet
  if (isFirstSeed.value) {
    const pulse = 0.18 + Math.abs(Math.sin(now * 0.0025)) * 0.45
    plotMeshes.forEach((plot, idx) => {
      if (gardenGrid[idx]?.stage === 0) {
        plot.material.emissive = plot.material.emissive || new THREE.Color()
        plot.material.emissive.setHex(0x44cc66)
        plot.material.emissiveIntensity = pulse
      }
    })
  } else {
    // Clear emissive once planted
    plotMeshes.forEach((plot) => {
      if (plot.material.emissiveIntensity > 0) {
        plot.material.emissiveIntensity = 0
      }
    })
  }

  // 8. Animate newly planted growing scaling pop
  plantMeshes.forEach((h) => {
    if (h.scale.x < 1.0) {
      h.scale.x += (1.0 - h.scale.x) * 0.15
      h.scale.y = h.scale.x
      h.scale.z = h.scale.x
    }
  })

  renderer.render(scene, camera)
  updatePlotOverlays()
}

function simulateCropGrowth() {
  let didChange = false
  // Listening to music boosts speed dramatically
  const multiplier = 1.0 + (currentAudioDrive.value * 6.0)

  // Passively earn micro-beats for listening in the garden!
  progress.beats += 0.025 * multiplier

  gardenGrid.forEach((c) => {
    if (c.stage === 1 || c.stage === 2) {
      const waterFac = c.watered ? 1.0 : 0.08
      c.growth += 0.085 * waterFac * multiplier
      
      if (c.growth >= 1.0) {
        c.stage += 1
        c.growth = 0
        c.watered = false // dry soil again
        didChange = true
      }
    }
  })

  if (didChange) {
    syncPlotVisuals()
    saveGridToStorage()
  }
  saveProgress()
}

// ── Resize ──────────────────────────────────────────────────────────────────
function handleResize() {
  if (!renderer || !stageRef.value) return
  const r = stageRef.value.getBoundingClientRect()
  const w = Math.max(1, r.width)
  const h = Math.max(1, r.height)
  
  renderer.setSize(w, h, false)
  camera.aspect = w / h
  camera.updateProjectionMatrix()
}

// ── Lifecycles ──────────────────────────────────────────────────────────────
onMounted(() => {
  loadGridFromStorage()
  buildScene()
  handleResize()

  resizeObserver = new ResizeObserver(handleResize)
  resizeObserver.observe(stageRef.value)

  rafId = requestAnimationFrame(tick)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  renderer?.dispose()
  scene?.traverse((o) => {
    if (o.geometry) o.geometry.dispose()
    if (o.material) {
      if (Array.isArray(o.material)) o.material.forEach(m => m.dispose())
      else o.material.dispose()
    }
  })
})
</script>

<style scoped>
.garden-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
  background: linear-gradient(180deg, #091420 0%, #132f44 100%);
  touch-action: none;
  user-select: none;
}

.garden-stage canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

/* ── Viewfinder Mode Style Tweaks ── */
.is-viewfinder-mode {
  cursor: crosshair;
}

/* ── Top HUD ── */
.garden-hud {
  position: absolute;
  top: 0.75rem;
  left: 0.75rem;
  right: 0.75rem;
  padding-right: 34px; /* Avoid overlap with global Top-Right Fullscreen Toggle! */
  z-index: 10;
  display: flex;
  align-items: center;
  gap: 0.6rem;
  pointer-events: none;
}

.garden-btn {
  pointer-events: auto;
  display: grid;
  place-items: center;
  background: rgba(12, 12, 12, 0.85);
  border: 2px solid #00d7ff;
  color: #ffd400;
  cursor: pointer;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  transition: all 0.2s;
}

.garden-btn--circle {
  width: 42px;
  height: 42px;
  border-radius: 50%;
  font-size: 0.9rem;
}

.garden-btn:hover {
  transform: scale(1.06);
  background: #000;
}

.garden-btn--radio {
  position: relative;
  overflow: hidden;
  border-color: #00d7ff;
}

.garden-btn--radio.is-active {
  border-color: #ffd400;
  box-shadow: 0 8px 24px rgba(255, 212, 0, 0.25), 0 0 12px rgba(255, 212, 0, 0.1);
}

.radio-btn-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.65;
  filter: brightness(0.85);
  transition: opacity 0.25s, transform 0.25s;
}

.garden-btn--radio:hover .radio-btn-art {
  opacity: 0.85;
  transform: scale(1.1);
}

.radio-btn-icon {
  position: relative;
  z-index: 2;
  display: grid;
  place-items: center;
  width: 25px;
  height: 25px;
  border-radius: 50%;
  background: rgba(255, 212, 0, 0.95);
  font-size: 0.7rem;
  color: #0b0b0b;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
}

.garden-progress-pill,
.garden-beats-pill {
  pointer-events: auto;
  display: flex;
  flex-direction: column;
  padding: 0.45rem 0.8rem;
  background: rgba(12, 12, 12, 0.85);
  border: 2px solid #44cc66;
  border-radius: 14px;
  box-shadow: 0 8px 16px rgba(0,0,0,0.28);
  backdrop-filter: blur(8px);
}

.garden-beats-pill {
  border-color: #ff2fb8;
  margin-left: auto;
}

.stat-label {
  font-size: 0.5rem;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: rgba(255, 255, 255, 0.7);
  display: flex;
  align-items: center;
  gap: 4px;
}

.garden-progress-pill .stat-label i { color: #44cc66; }
.garden-beats-pill .stat-label i { color: #ff2fb8; }

.stat-value {
  font-size: 0.9rem;
  font-weight: 900;
  color: #ffd400;
  margin-top: 2px;
  line-height: 1;
}

/* ── Nursery & Pet UI Cards ── */
.nursery-banner {
  position: absolute;
  top: 4.4rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 12;
  display: flex;
  justify-content: center;
  width: 90%;
}

.nursery-btn {
  background: #ff2fb8;
  color: #fff;
  border: 2px solid #fff;
  padding: 0.5rem 0.9rem;
  border-radius: 30px;
  font-size: 0.62rem;
  font-weight: 800;
  text-transform: uppercase;
  box-shadow: 0 6px 16px rgba(255, 47, 184, 0.35);
  cursor: pointer;
  transition: all 0.2s;
}

.nursery-btn:disabled {
  background: #555;
  box-shadow: none;
  opacity: 0.7;
}

.egg-status-pill {
  background: rgba(12, 12, 12, 0.9);
  border: 2px solid #ff2fb8;
  color: #fff;
  padding: 0.4rem 0.7rem;
  border-radius: 20px;
  font-size: 0.62rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6px;
}

.feed-egg-btn, .pet-feed-btn {
  background: #ffd400;
  color: #0b0b0b;
  border: none;
  font-size: 0.55rem;
  font-weight: 900;
  padding: 0.25rem 0.6rem;
  border-radius: 12px;
  cursor: pointer;
  text-transform: uppercase;
}

.feed-egg-btn:disabled, .pet-feed-btn:disabled {
  background: #555;
  color: #aaa;
}

.pet-status-card {
  position: absolute;
  top: 4.4rem;
  left: 0.75rem;
  right: 0.75rem;
  z-index: 12;
  background: rgba(0, 215, 255, 0.15);
  border: 2px solid #00d7ff;
  border-radius: 18px;
  padding: 0.5rem 0.8rem;
  backdrop-filter: blur(10px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 8px 24px rgba(0, 215, 255, 0.1);
}

.pet-info {
  display: flex;
  flex-direction: column;
}

.pet-badge {
  font-size: 0.48rem;
  font-weight: 900;
  background: #00d7ff;
  color: #0b0b0b;
  padding: 2px 6px;
  border-radius: 6px;
  align-self: flex-start;
  text-transform: uppercase;
}

.pet-name {
  font-size: 0.8rem;
  font-weight: 800;
  color: #fff;
  margin-top: 2px;
}

/* ── Camera Viewfinder Overlay ── */
.camera-viewfinder {
  position: absolute;
  inset: 0;
  z-index: 30;
  display: flex;
  flex-direction: column;
  pointer-events: none;
  border: 12px solid #000;
}

.viewfinder-top {
  padding: 1rem 1.2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #fff;
  font-size: 0.7rem;
  font-family: monospace;
  pointer-events: auto;
  background: linear-gradient(to bottom, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%);
}

.rec-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  background: red;
  border-radius: 50%;
  margin-right: 5px;
  animation: blink 1s infinite alternate;
}

@keyframes blink { from { opacity: 1; } to { opacity: 0.2; } }

.cam-close {
  background: none;
  border: none;
  color: #fff;
  font-size: 1.1rem;
  cursor: pointer;
}

.viewfinder-brackets {
  flex: 1;
  border: 2px solid rgba(255, 255, 255, 0.3);
  margin: 2rem;
  position: relative;
}

.viewfinder-bottom {
  padding: 1rem 0 2.5rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  pointer-events: auto;
  background: linear-gradient(to top, rgba(0,0,0,0.8) 0%, rgba(0,0,0,0) 100%);
}

.cam-station-stamp {
  color: #ffd400;
  font-size: 0.6rem;
  font-weight: 800;
  text-transform: uppercase;
  margin-bottom: 1rem;
  opacity: 0.7;
  letter-spacing: 1px;
}

.cam-shutter-btn {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #fff;
  border: 4px solid rgba(255,255,255,0.3);
  display: grid;
  place-items: center;
  cursor: pointer;
  box-shadow: 0 0 20px rgba(255,255,255,0.4);
  transition: transform 0.1s;
}

.cam-shutter-btn:active { transform: scale(0.9); }

.shutter-inner {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  border: 2px solid #000;
}

/* ── Flash & Polaroid Overlay ── */
.camera-flash {
  position: absolute;
  inset: 0;
  background: #ffffff;
  opacity: 0;
  z-index: 99;
  pointer-events: none;
  transition: opacity 0.05s;
}

.camera-flash.is-flashing {
  opacity: 1;
  transition: none;
}

.polaroid-card {
  position: absolute;
  top: 45%;
  left: 50%;
  z-index: 100;
  transform: translate(-50%, -50%) rotate(-4deg);
  background: #fcfcfc;
  width: 220px;
  padding: 12px 12px 16px;
  border-radius: 6px;
  box-shadow: 0 28px 64px rgba(0,0,0,0.7), 0 0 20px rgba(0,0,0,0.2);
}

.polaroid-pop-enter-active { animation: polaroid-slide-in 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
.polaroid-pop-leave-active { animation: polaroid-slide-out 0.4s cubic-bezier(0.6, -0.28, 0.735, 0.045) forwards; }

@keyframes polaroid-slide-in {
  0% { transform: translate(-50%, 100%) rotate(-15deg); opacity: 0; }
  100% { transform: translate(-50%, -50%) rotate(-4deg); opacity: 1; }
}
@keyframes polaroid-slide-out {
  100% { transform: translate(-50%, -200%) rotate(12deg); opacity: 0; }
}

.polaroid-photo {
  width: 100%;
  aspect-ratio: 1 / 1;
  background: #0f141c;
  border: 1.5px solid #d5d5d5;
  display: grid;
  place-items: center;
  color: #fff;
  overflow: hidden;
  border-radius: 2px;
}

.captured-snap-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.polaroid-art {
  display: flex;
  flex-direction: column;
  align-items: center;
  font-size: 1.5rem;
  color: #666;
}

.art-label { font-size: 0.45rem; font-weight: 900; letter-spacing: 1.5px; margin-top: 6px; color: #888; }

.polaroid-caption {
  margin-top: 10px;
  text-align: center;
  color: #333;
}

.caption-title {
  font-family: 'Georgia', serif;
  font-style: italic;
  font-weight: bold;
  font-size: 0.88rem;
  color: #222;
}

.caption-meta {
  font-size: 0.52rem;
  color: #666;
  font-weight: 800;
  margin-top: 2px;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

.polaroid-actions {
  margin-top: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  width: 100%;
}

.polaroid-action-btn {
  border: none;
  border-radius: 6px;
  padding: 7px 10px;
  font-size: 0.68rem;
  font-weight: 800;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
}

.save-snap-btn {
  background: #ff2fb8;
  color: white;
  box-shadow: 0 4px 10px rgba(255, 47, 184, 0.25);
}
.save-snap-btn:hover {
  background: #e620a3;
  transform: translateY(-1px);
  box-shadow: 0 6px 12px rgba(255, 47, 184, 0.35);
}
.save-snap-btn:active { transform: translateY(0); }

.close-snap-btn {
  background: #e0e0e0;
  color: #444;
}
.close-snap-btn:hover {
  background: #d4d4d4;
  color: #222;
}

.polaroid-saved-status {
  font-size: 0.68rem;
  font-weight: 800;
  color: #2ecc71;
  background: rgba(46, 204, 113, 0.12);
  padding: 7px 10px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  animation: saved-pop 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

@keyframes saved-pop {
  0% { transform: scale(0.92); opacity: 0; }
  100% { transform: scale(1); opacity: 1; }
}

/* ── Bottom Toolbar System ── */
.garden-toolbar-wrapper {
  position: absolute;
  bottom: 6.4rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 15;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.4rem;
  pointer-events: none;
  width: 90%;
  max-width: 360px;
}

.tool-hint-pill {
  pointer-events: none;
  display: inline-flex;
  align-items: center;
  padding: 0.28rem 0.7rem;
  background: rgba(10, 15, 22, 0.82);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  font-size: 0.55rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
  transition: border-color 0.3s ease;
  text-align: center;
  letter-spacing: 0.02em;
}

/* Match the accent colors of each Tool Hint with the buttons */
.tool-hint--plant { border-color: rgba(46, 204, 113, 0.45); }
.tool-hint--plant .hint-icon i { color: #2ecc71; }

.tool-hint--water { border-color: rgba(0, 215, 255, 0.45); }
.tool-hint--water .hint-icon i { color: #00d7ff; }

.tool-hint--harvest { border-color: rgba(255, 212, 0, 0.45); }
.tool-hint--harvest .hint-icon i { color: #ffd400; }

.tool-hint--snap { border-color: rgba(255, 47, 184, 0.45); }
.tool-hint--snap .hint-icon i { color: #ff2fb8; }

.garden-toolbar {
  pointer-events: auto; /* re-enable button clicks */
  display: flex;
  background: rgba(10, 15, 22, 0.85);
  border: 1.5px solid rgba(255, 255, 255, 0.18);
  border-radius: 22px;
  padding: 0.35rem;
  gap: 0.4rem;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.65), inset 0 1px 0 rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
}

/* Initial Game Control Guidance Popup */
.garden-splash-hint {
  position: absolute;
  top: 42%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 50;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  pointer-events: none;
  background: rgba(10, 15, 22, 0.9);
  border: 2.5px solid #00d7ff;
  border-radius: 26px;
  padding: 1.3rem 1.8rem;
  box-shadow: 0 24px 64px rgba(0, 0, 0, 0.7), 0 0 32px rgba(0, 215, 255, 0.3);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
}

.hint-icon-stack {
  position: relative;
  width: 46px;
  height: 46px;
  margin-bottom: 0.8rem;
  display: grid;
  place-items: center;
}

.hint-circle {
  font-size: 1.3rem;
  color: #00d7ff;
  z-index: 2;
}

.drag-arrows {
  position: absolute;
  inset: -8px;
  border: 2px dashed rgba(0, 215, 255, 0.5);
  border-radius: 50%;
  color: rgba(0, 215, 255, 0.7);
  font-size: 0.6rem;
  display: grid;
  place-items: center;
  animation: spin 10s linear infinite;
}

.hint-text-stack {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.hint-title {
  font-size: 0.8rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.12em;
  color: #ffd400;
  text-shadow: 0 2px 4px rgba(0,0,0,0.4);
}

.hint-desc {
  font-size: 0.68rem;
  font-weight: 800;
  color: rgba(255, 255, 255, 0.9);
  white-space: nowrap;
  letter-spacing: 0.01em;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* Guidance Transitions */
.hint-slide-enter-active,
.hint-slide-leave-active {
  transition: all 0.24s cubic-bezier(0.16, 1, 0.3, 1);
}

.hint-slide-enter-from {
  opacity: 0;
  transform: translateY(10px) scale(0.95);
}

.hint-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px) scale(0.95);
}

.hint-fade-enter-active,
.hint-fade-leave-active {
  transition: opacity 0.6s cubic-bezier(0.25, 1, 0.5, 1), transform 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

.hint-fade-enter-from {
  opacity: 0;
  transform: translate(-50%, -42%) scale(0.92);
}

.hint-fade-leave-to {
  opacity: 0;
  transform: translate(-50%, -58%) scale(0.88);
}

/* ── First-seed callout ── */
.first-seed-callout {
  position: absolute;
  bottom: 7.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 8;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  pointer-events: none;
}

.first-seed-arrow {
  font-size: 1.6rem;
  color: #44cc66;
  text-shadow: 0 0 12px rgba(68, 204, 102, 0.8);
  animation: seed-bounce 0.9s ease-in-out infinite;
}

.first-seed-label {
  font-size: 0.68rem;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #44cc66;
  text-shadow: 0 0 10px rgba(68, 204, 102, 0.6), 0 1px 4px rgba(0, 0, 0, 0.8);
  white-space: nowrap;
  padding: 0.3rem 0.7rem;
  border: 1.5px solid rgba(68, 204, 102, 0.4);
  border-radius: 999px;
  background: rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
}

@keyframes seed-bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-8px); }
}

.tool-btn {
  width: 48px;
  height: 46px;
  border-radius: 13px;
  border: 1.5px solid transparent;
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.45);
  cursor: pointer;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 2px;
  transition: all 0.2s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.tool-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.tool-btn:active {
  transform: scale(0.93);
  transition: all 0.07s ease;
}

.tool-btn.is-active {
  transform: scale(1.12);
  color: #fff;
}

.tool-btn--plant.is-active   { background: #2ecc71; color: #051d0e; border-color: #2ecc71; box-shadow: 0 4px 14px rgba(46,204,113,0.5); }
.tool-btn--water.is-active   { background: #00d7ff; color: #002d36; border-color: #00d7ff; box-shadow: 0 4px 14px rgba(0,215,255,0.5); }
.tool-btn--harvest.is-active { background: #ffd400; color: #2e2600; border-color: #ffd400; box-shadow: 0 4px 14px rgba(255,212,0,0.5); }
.tool-btn--terraform.is-active { background: #a07840; color: #1a0e00; border-color: #c89a50; box-shadow: 0 4px 14px rgba(160,120,64,0.5); }
.tool-btn--snap.is-active    { background: #ff2fb8; color: #fff;    border-color: #ff2fb8; box-shadow: 0 4px 14px rgba(255,47,184,0.5); }

/* Extra protection to shield tool-icon and its child icons from any global CSS overrides */
.tool-icon { 
  font-size: 1.05rem; 
  display: flex; 
  align-items: center; 
  justify-content: center; 
  width: auto !important;
  height: auto !important;
  min-width: 0 !important;
  min-height: 0 !important;
  background: none !important;
  border: none !important;
  border-radius: 0 !important;
  margin: 0 !important;
  padding: 0 !important;
  box-shadow: none !important;
  line-height: 1 !important;
}

.tool-icon i {
  background: none !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 0 !important;
  margin: 0 !important;
  width: auto !important;
  height: auto !important;
  box-shadow: none !important;
  color: inherit !important; /* Inherits button color so it reverses correctly when active */
}

.tool-name {
  font-size: 0.45rem;
  font-weight: 900;
  text-transform: uppercase;
  letter-spacing: 0.02em;
}

/* ── Score Pops ── */
.score-popup {
  position: fixed;
  z-index: 999;
  pointer-events: none;
  font-size: 1.1rem;
  font-weight: 900;
  color: #ffd400;
  text-shadow: 0 2px 8px rgba(0,0,0,0.6);
  transform: translate(-50%, -50%);
}

.pop-fade-enter-active { animation: pop-upwards 1.2s cubic-bezier(0.25, 1, 0.5, 1) forwards; }
@keyframes pop-upwards {
  0% { opacity: 1; transform: translate(-50%, -50%) scale(0.8); }
  100% { opacity: 0; transform: translate(-50%, -140%) scale(1.3); }
}

/* ── Agent/Bot Overlay ── */
.agent-chat-wrapper {
  position: absolute;
  bottom: 0.8rem;
  left: 0.75rem;
  right: 0.75rem;
  z-index: 20;
  display: flex;
  align-items: center;
  gap: 0.8rem;
  background: rgba(9, 22, 32, 0.94);
  border: 2px solid #00d7ff;
  border-radius: 20px;
  padding: 0.7rem;
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.45);
  cursor: pointer;
  backdrop-filter: blur(12px);
  transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.15);
}

.agent-chat-wrapper:hover, .agent-chat-wrapper.is-open {
  border-color: #ff2fb8;
  transform: translateY(-3px);
  box-shadow: 0 16px 32px rgba(0, 0, 0, 0.4), 0 0 24px rgba(255, 47, 184, 0.2);
}

.bot-screen {
  width: 42px;
  height: 42px;
  border-radius: 12px;
  background: #0b0b0b;
  border: 2px solid #00d7ff;
  display: grid;
  place-items: center;
  font-size: 1.3rem;
  color: #00d7ff;
}

.agent-chat-wrapper:hover .bot-screen {
  color: #ff2fb8;
  border-color: #ff2fb8;
}

.bot-pulse {
  position: absolute;
  inset: -2px;
  border-radius: 14px;
  border: 2px solid #00d7ff;
  animation: p-glow 2s infinite linear;
  opacity: 0;
}

@keyframes p-glow {
  0% { transform: scale(1); opacity: 0.6; }
  100% { transform: scale(1.3); opacity: 0; }
}

.agent-bubble { flex: 1; display: flex; flex-direction: column; min-width: 0; }
.bubble-kicker {
  font-size: 0.48rem;
  font-weight: 900;
  text-transform: uppercase;
  color: #ff2fb8;
  letter-spacing: 0.12em;
}

.bubble-text {
  font-size: 0.65rem;
  font-weight: 600;
  color: #fff;
  line-height: 1.4;
  margin-top: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.is-open .bubble-text { white-space: normal; }
.bubble-hint {
  font-size: 0.45rem;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.4);
  text-transform: uppercase;
  align-self: flex-end;
}

.animate-wobble {
  display: inline-block;
  animation: wobble 2.5s infinite alternate ease-in-out;
}

@keyframes wobble {
  0% { transform: rotate(-10deg); }
  100% { transform: rotate(10deg); }
}

/* ── Plot overlays (projected from 3D world to CSS) ── */
.plot-badge {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 6;
  font-size: 0.7rem;
  font-weight: 900;
  line-height: 1;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
}

.plot-badge--harvest {
  background: #ffd400;
  color: #1a1000;
  box-shadow: 0 0 8px rgba(255, 212, 0, 0.7);
  animation: harvest-pop 1.1s ease-in-out infinite;
}

.plot-badge--thirst {
  background: rgba(0, 150, 215, 0.85);
  color: #fff;
  font-size: 0.55rem;
  box-shadow: 0 0 6px rgba(0, 180, 255, 0.5);
  animation: thirst-pulse 2s ease-in-out infinite;
}

@keyframes harvest-pop {
  0%, 100% { transform: translate(-50%, -50%) scale(1); }
  50% { transform: translate(-50%, -65%) scale(1.15); }
}

@keyframes thirst-pulse {
  0%, 100% { opacity: 0.7; }
  50% { opacity: 1; }
}

.plot-ring {
  position: absolute;
  transform: translate(-50%, -50%);
  pointer-events: none;
  z-index: 5;
  width: 22px;
  height: 22px;
  overflow: visible;
}

.plot-ring-bg {
  fill: none;
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 2.5;
}

.plot-ring-fill {
  fill: none;
  stroke: rgba(255, 212, 0, 0.75);
  stroke-width: 2.5;
  stroke-linecap: round;
  transform: rotate(-90deg);
  transform-origin: 12px 12px;
  transition: stroke-dasharray 0.4s ease;
}

.plot-ring-fill.is-watered {
  stroke: rgba(0, 215, 255, 0.85);
}
</style>
