<template>
  <div
    ref="stageRef"
    class="birds-stage"
    @pointerdown="onPointerDown"
    @pointermove="onPointerMove"
    @pointerup="onPointerUp"
    @pointercancel="onPointerUp"
  >
    <div class="birds-hud">
      <button class="birds-back" @pointerdown.stop @click="emit('back')">
        <i class="fas fa-arrow-left"></i>
      </button>
      <div class="birds-score-block">
        <div class="birds-score">{{ score }}</div>
        <div class="birds-level">LVL {{ levelNumber }}</div>
      </div>
      <div class="birds-hud-right">
        <div class="birds-birds-left">
          <span v-for="n in birdsLeft" :key="n" class="bird-pip">●</span>
        </div>
        <button
          class="birds-radio-btn"
          :class="{ 'is-active': isRadioAudible }"
          @pointerdown.stop
          @click="emit('toggle-radio')"
          title="Toggle radio"
        >
          <img v-if="stationArt" :src="stationArt" alt="" class="birds-radio-art" />
          <span class="birds-radio-icon"><i :class="['fas', radioButtonIcon]"></i></span>
        </button>
      </div>
    </div>

    <Transition name="overlay-fade">
      <div v-if="gameOver" class="birds-overlay">
        <div class="birds-result">{{ allPigsDead ? '🚀 LEVEL CLEAR!' : 'GAME OVER' }}</div>
        <div v-if="allPigsDead" class="birds-stars">
          <span v-for="n in 3" :key="n" class="birds-star" :class="{ lit: n <= levelStars }">★</span>
        </div>
        <div class="birds-result-sub">{{ score }} pts{{ allPigsDead ? ` · next: lvl ${levelNumber + 1}` : '' }}</div>
        <button class="birds-btn" @click="resetLevel(allPigsDead)">{{ allPigsDead ? 'Next Level' : 'Try Again' }}</button>
        <button class="birds-btn birds-btn--ghost" @click="emit('back')">Console</button>
      </div>
    </Transition>

    <Transition name="hint-fade">
      <div v-if="showAimHint" class="birds-hint">drag to aim</div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, reactive } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  audioDrive: { type: Number, default: 0.3 },
  isRadioAudible: { type: Boolean, default: false },
  radioButtonIcon: { type: String, default: 'fa-volume-high' },
  stationArt: { type: String, default: '' },
})

const emit = defineEmits(['back', 'collect', 'toggle-radio', 'score'])

const stageRef = ref(null)
const score = ref(0)
const birdsLeft = ref(5)
const gameOver = ref(false)
const allPigsDead = ref(false)
const showAimHint = ref(true)
const levelNumber = ref(1)
const birdsTotal = ref(5)

const levelStars = computed(() => {
  const ratio = birdsLeft.value / birdsTotal.value
  if (ratio >= 0.6) return 3
  if (ratio >= 0.3) return 2
  return 1
})

// ── Constants ──────────────────────────────────────────────────────────────
const GRAVITY = -22
const GROUND_Y = -4.0
const SLING_X = -5.0
const FORK_LEFT_X = -5.3
const FORK_RIGHT_X = -4.7
const FORK_Y = GROUND_Y + 2.0
const BIRD_R = 0.38
const PIG_R = 0.44
const BOX_HW = 0.52
const BOX_HH = 0.42
const MAX_DRAG = 2.2
const LAUNCH_POWER = 6.2
const HALF_H = 6.0
const TOTAL_BIRDS = 5

const CMYK = {
  black: 0x0b0b0b,
  cyan: 0x00d7ff,
  magenta: 0xff2fb8,
  yellow: 0xffd400,
  green: 0x44cc66,
  sling: 0x7a4020,
  ground: 0x1a3322,
  groundEdge: 0x00d7ff,
  sky: 0x0b0b1a,
}

// ── Three.js state ─────────────────────────────────────────────────────────
let renderer, scene, camera
let halfW = HALF_H * (4 / 3)
let halfH = HALF_H
let rafId = 0
let lastTime = 0
let resizeObserver

// Camera panning + feel
let cameraX = SLING_X + 2.5
let cameraTargetX = SLING_X + 2.5
const CAMERA_REST_X = SLING_X + 2.5
let cameraY = GROUND_Y + 2.0
let cameraTargetY = GROUND_Y + 2.0
const CAMERA_BASE_Y = GROUND_Y + 2.0

// Screen shake
let shakeTimer = 0
let shakeMag = 0

// Portrait half-width: zoomed in when idle, wider during flight
const HALF_W_IDLE = 5.0
const HALF_W_FLIGHT = 7.5
let portraitHalfW = HALF_W_IDLE  // current portrait halfW target

let birdMesh = null
let bandLine = null
let bandPositions = null
let dotMeshes = []
let particles = []

// game objects
let boxes = []
let pigs = []

// bird physics
let birdX = SLING_X
let birdY = FORK_Y
let birdVX = 0
let birdVY = 0
let birdInFlight = ref(false)
let birdDead = false

// drag
let dragging = false
let dragStartX = 0
let dragStartY = 0

// auto-settle timer
let settleTimeout = null
let hintTimeout = null
let currentLevel = 0
let idleTime = 0  // drives bird bob animation

// ── Level data ─────────────────────────────────────────────────────────────
const LEVELS = [
  // 0 — Classic towers (introductory)
  (G, BH, BW) => ({
    boxes: [
      { x: 2.2, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 2.2, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 4.8, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.0, y: G+BH,   hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 7.0, y: G+BH*3, hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 7.0, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
    ],
    pigs: [
      { x: 2.2, y: G+BH*4+PIG_R },
      { x: 4.8, y: G+BH*2+PIG_R },
      { x: 7.0, y: G+BH*6+PIG_R },
    ],
  }),

  // 1 — Pyramid: wide base, narrow top
  (G, BH, BW) => ({
    boxes: [
      { x: 2.0, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 3.6, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 5.2, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 6.8, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 2.8, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 6.0, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 4.4, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.yellow },
    ],
    pigs: [
      { x: 2.0, y: G+BH*2+PIG_R },
      { x: 6.8, y: G+BH*2+PIG_R },
      { x: 4.4, y: G+BH*6+PIG_R },
    ],
  }),

  // 2 — Fortress: pig hiding behind thick walls
  (G, BH, BW) => ({
    boxes: [
      { x: 3.5, y: G+BH,   hw: BW*1.4, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 3.5, y: G+BH*3, hw: BW*1.4, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 3.5, y: G+BH*5, hw: BW*1.4, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 6.5, y: G+BH,   hw: BW*1.4, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 6.5, y: G+BH*3, hw: BW*1.4, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 6.5, y: G+BH*5, hw: BW*1.4, hh: BH, hp: 3, color: CMYK.magenta },
    ],
    pigs: [
      { x: 3.5, y: G+BH*6+PIG_R },
      { x: 5.0, y: G+BH*2+PIG_R },
      { x: 6.5, y: G+BH*6+PIG_R },
    ],
  }),

  // 3 — Scattered: lots of single blocks, 4 pigs
  (G, BH, BW) => ({
    boxes: [
      { x: 2.0, y: G+BH,   hw: BW, hh: BH, hp: 1, color: CMYK.yellow },
      { x: 3.4, y: G+BH,   hw: BW, hh: BH, hp: 1, color: CMYK.magenta },
      { x: 4.8, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 6.2, y: G+BH,   hw: BW, hh: BH, hp: 1, color: CMYK.yellow },
      { x: 7.6, y: G+BH,   hw: BW, hh: BH, hp: 1, color: CMYK.magenta },
      { x: 2.7, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 6.9, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
    ],
    pigs: [
      { x: 2.0, y: G+BH*2+PIG_R },
      { x: 4.8, y: G+BH*2+PIG_R },
      { x: 7.6, y: G+BH*2+PIG_R },
      { x: 4.8, y: G+BH*4+PIG_R },
    ],
  }),

  // 4 — High castle: one tall tower, pig on top
  (G, BH, BW) => ({
    boxes: [
      { x: 5.0, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 5.0, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 5.0, y: G+BH*5, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 5.0, y: G+BH*7, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 3.0, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
      { x: 7.0, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
    ],
    pigs: [
      { x: 3.0, y: G+BH*2+PIG_R },
      { x: 5.0, y: G+BH*8+PIG_R },
      { x: 7.0, y: G+BH*2+PIG_R },
    ],
  }),

  // 5 — Two castles: symmetrical duel
  (G, BH, BW) => ({
    boxes: [
      { x: 2.5, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 2.5, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 2.5, y: G+BH*5, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.5, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.5, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.5, y: G+BH*5, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 5.0, y: G+BH,   hw: BW*0.6, hh: BH*0.6, hp: 1, color: CMYK.yellow },
    ],
    pigs: [
      { x: 2.5, y: G+BH*6+PIG_R },
      { x: 5.0, y: G+BH*2+PIG_R },
      { x: 7.5, y: G+BH*6+PIG_R },
    ],
  }),

  // 6 — Staircase: ascending platforms
  (G, BH, BW) => ({
    boxes: [
      { x: 2.0, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 3.8, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 3.8, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 5.6, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 5.6, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 5.6, y: G+BH*5, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 7.4, y: G+BH,   hw: BW, hh: BH, hp: 3, color: CMYK.yellow },
      { x: 7.4, y: G+BH*3, hw: BW, hh: BH, hp: 3, color: CMYK.yellow },
      { x: 7.4, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 7.4, y: G+BH*7, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
    ],
    pigs: [
      { x: 2.0, y: G+BH*2+PIG_R },
      { x: 3.8, y: G+BH*4+PIG_R },
      { x: 5.6, y: G+BH*6+PIG_R },
      { x: 7.4, y: G+BH*8+PIG_R },
    ],
  }),

  // 7 — Bunker: pigs buried under heavy stacked slabs
  (G, BH, BW) => ({
    boxes: [
      { x: 3.0, y: G+BH,     hw: BW*1.8, hh: BH,     hp: 3, color: CMYK.cyan },
      { x: 3.0, y: G+BH*3,   hw: BW*1.8, hh: BH,     hp: 3, color: CMYK.cyan },
      { x: 3.0, y: G+BH*5,   hw: BW*1.8, hh: BH*0.6, hp: 4, color: CMYK.magenta },
      { x: 6.8, y: G+BH,     hw: BW*1.8, hh: BH,     hp: 3, color: CMYK.cyan },
      { x: 6.8, y: G+BH*3,   hw: BW*1.8, hh: BH,     hp: 3, color: CMYK.cyan },
      { x: 6.8, y: G+BH*5,   hw: BW*1.8, hh: BH*0.6, hp: 4, color: CMYK.magenta },
    ],
    pigs: [
      { x: 3.0, y: G+BH*2+PIG_R },
      { x: 5.0, y: G+BH*1+PIG_R },
      { x: 6.8, y: G+BH*2+PIG_R },
    ],
  }),

  // 8 — Zigzag: offset columns forcing angle shots
  (G, BH, BW) => ({
    boxes: [
      { x: 1.8, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
      { x: 1.8, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 3.6, y: G+BH*2, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 3.6, y: G+BH*4, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 5.4, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
      { x: 5.4, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 7.2, y: G+BH*2, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.2, y: G+BH*4, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
    ],
    pigs: [
      { x: 1.8, y: G+BH*4+PIG_R },
      { x: 3.6, y: G+BH*5+PIG_R },
      { x: 5.4, y: G+BH*4+PIG_R },
      { x: 7.2, y: G+BH*5+PIG_R },
    ],
  }),

  // 9 — Moat: ground-level pigs flanked by tall outer walls
  (G, BH, BW) => ({
    boxes: [
      { x: 2.0, y: G+BH,   hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 2.0, y: G+BH*3, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 2.0, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 2.0, y: G+BH*7, hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 8.0, y: G+BH,   hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 8.0, y: G+BH*3, hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 8.0, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 8.0, y: G+BH*7, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 5.0, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
    ],
    pigs: [
      { x: 3.5, y: G+BH*1+PIG_R },
      { x: 5.0, y: G+BH*2+PIG_R },
      { x: 6.5, y: G+BH*1+PIG_R },
    ],
  }),

  // 10 — Maze: interlocking L-shapes create pockets
  (G, BH, BW) => ({
    boxes: [
      { x: 2.2, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 2.2, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
      { x: 3.8, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 3.8, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 3.8, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 5.6, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
      { x: 5.6, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.4, y: G+BH,   hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
      { x: 7.4, y: G+BH*3, hw: BW, hh: BH, hp: 2, color: CMYK.yellow },
      { x: 7.4, y: G+BH*5, hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
    ],
    pigs: [
      { x: 2.2, y: G+BH*4+PIG_R },
      { x: 3.8, y: G+BH*6+PIG_R },
      { x: 5.6, y: G+BH*4+PIG_R },
      { x: 7.4, y: G+BH*6+PIG_R },
    ],
  }),

  // 11 — Gauntlet: long dense row of cheap blocks, 5 pigs hiding inside
  (G, BH, BW) => ({
    boxes: [
      { x: 1.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.yellow },
      { x: 2.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.cyan },
      { x: 3.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.yellow },
      { x: 4.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.cyan },
      { x: 5.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.yellow },
      { x: 6.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.cyan },
      { x: 7.5, y: G+BH,   hw: BW*0.7, hh: BH, hp: 1, color: CMYK.yellow },
      { x: 2.0, y: G+BH*3, hw: BW,     hh: BH, hp: 2, color: CMYK.magenta },
      { x: 4.0, y: G+BH*3, hw: BW,     hh: BH, hp: 2, color: CMYK.magenta },
      { x: 6.0, y: G+BH*3, hw: BW,     hh: BH, hp: 2, color: CMYK.magenta },
    ],
    pigs: [
      { x: 1.5, y: G+BH*2+PIG_R },
      { x: 3.0, y: G+BH*2+PIG_R },
      { x: 4.5, y: G+BH*4+PIG_R },
      { x: 6.0, y: G+BH*2+PIG_R },
      { x: 7.5, y: G+BH*2+PIG_R },
    ],
  }),

  // 12 — Skyscraper: one impossibly tall tower, sparse guards
  (G, BH, BW) => ({
    boxes: [
      { x: 5.5, y: G+BH,    hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 5.5, y: G+BH*3,  hw: BW, hh: BH, hp: 3, color: CMYK.cyan },
      { x: 5.5, y: G+BH*5,  hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 5.5, y: G+BH*7,  hw: BW, hh: BH, hp: 3, color: CMYK.magenta },
      { x: 5.5, y: G+BH*9,  hw: BW, hh: BH, hp: 4, color: CMYK.yellow },
      { x: 5.5, y: G+BH*11, hw: BW, hh: BH, hp: 4, color: CMYK.yellow },
      { x: 2.5, y: G+BH,    hw: BW, hh: BH, hp: 2, color: CMYK.magenta },
      { x: 8.5, y: G+BH,    hw: BW, hh: BH, hp: 2, color: CMYK.cyan },
    ],
    pigs: [
      { x: 2.5, y: G+BH*2+PIG_R },
      { x: 5.5, y: G+BH*12+PIG_R },
      { x: 8.5, y: G+BH*2+PIG_R },
    ],
  }),
]

function getLevelDef() {
  const G = GROUND_Y
  const BH = BOX_HH
  const BW = BOX_HW
  const def = LEVELS[currentLevel % LEVELS.length](G, BH, BW)
  // Normalize pig Y to sit exactly on top of whatever's below
  return def
}

// ── Scene building ─────────────────────────────────────────────────────────
function buildScene() {
  scene = new THREE.Scene()
  scene.background = new THREE.Color(CMYK.sky)
  scene.fog = new THREE.Fog(CMYK.sky, 18, 35)

  camera = new THREE.OrthographicCamera(-halfW, halfW, halfH, -halfH, 0.1, 100)
  camera.position.set(cameraX, GROUND_Y + 2.0, 20)

  renderer = new THREE.WebGLRenderer({ antialias: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  stageRef.value.appendChild(renderer.domElement)

  const hemi = new THREE.HemisphereLight(0x334455, 0x0b0b0b, 1.6)
  scene.add(hemi)
  const key = new THREE.DirectionalLight(CMYK.cyan, 1.2)
  key.position.set(-3, 6, 8)
  scene.add(key)
  const fill = new THREE.DirectionalLight(CMYK.magenta, 0.6)
  fill.position.set(6, -2, 5)
  scene.add(fill)

  buildGround()
  buildSlingshot()
}

function buildGround() {
  // Main ground - deep enough to fill bottom of vertical screens
  const gm = new THREE.Mesh(
    new THREE.BoxGeometry(halfW * 2 + 100, 40, 2),
    new THREE.MeshToonMaterial({ color: CMYK.ground }),
  )
  gm.position.set(0, GROUND_Y - 20, -0.5)
  scene.add(gm)

  // Glowing edge strip
  const edge = new THREE.Mesh(
    new THREE.BoxGeometry(halfW * 2 + 20, 0.06, 0.5),
    new THREE.MeshBasicMaterial({ color: CMYK.groundEdge }),
  )
  edge.position.set(0, GROUND_Y, 0.1)
  scene.add(edge)

  // Stars (Increased count but smaller and transparent for subtle depth)
  const starGeo = new THREE.BufferGeometry()
  const starPts = []
  for (let i = 0; i < 450; i++) {
    starPts.push(
      (Math.random() - 0.5) * halfW * 2.5,
      GROUND_Y + 1.5 + Math.random() * 30,
      -5 - Math.random() * 8,
    )
  }
  starGeo.setAttribute('position', new THREE.Float32BufferAttribute(starPts, 3))
  scene.add(new THREE.Points(starGeo, new THREE.PointsMaterial({ 
    color: 0xffffff, 
    size: 0.045, 
    transparent: true, 
    opacity: 0.55 
  })))
}

function buildSlingshot() {
  const mat = new THREE.MeshToonMaterial({ color: CMYK.sling })

  function prong(x1, y1, x2, y2) {
    const dx = x2 - x1, dy = y2 - y1
    const len = Math.sqrt(dx * dx + dy * dy)
    const ang = Math.atan2(dy, dx) - Math.PI / 2
    const m = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.1, len, 8), mat)
    m.position.set((x1 + x2) / 2, (y1 + y2) / 2, 0)
    m.rotation.z = ang
    scene.add(m)
  }

  // Handle / base
  prong(SLING_X, GROUND_Y, SLING_X, FORK_Y - 0.3)
  // Left fork
  prong(SLING_X, FORK_Y - 0.3, FORK_LEFT_X - 0.1, FORK_Y)
  // Right fork
  prong(SLING_X, FORK_Y - 0.3, FORK_RIGHT_X + 0.1, FORK_Y)

  // Fork tips
  const tipMat = new THREE.MeshToonMaterial({ color: CMYK.sling })
  const tipGeo = new THREE.SphereGeometry(0.1, 8, 6)
  const lt = new THREE.Mesh(tipGeo, tipMat)
  lt.position.set(FORK_LEFT_X - 0.1, FORK_Y, 0)
  scene.add(lt)
  const rt = new THREE.Mesh(tipGeo, tipMat)
  rt.position.set(FORK_RIGHT_X + 0.1, FORK_Y, 0)
  scene.add(rt)

  // Elastic band — 3-point line: left tip → bird → right tip
  const bandGeo = new THREE.BufferGeometry()
  bandPositions = new Float32Array(9) // 3 points × 3 coords
  bandPositions[0] = FORK_LEFT_X - 0.1; bandPositions[1] = FORK_Y; bandPositions[2] = 0
  bandPositions[3] = birdX; bandPositions[4] = birdY; bandPositions[5] = 0
  bandPositions[6] = FORK_RIGHT_X + 0.1; bandPositions[7] = FORK_Y; bandPositions[8] = 0
  bandGeo.setAttribute('position', new THREE.BufferAttribute(bandPositions, 3))
  bandLine = new THREE.Line(bandGeo, new THREE.LineBasicMaterial({ color: CMYK.sling, linewidth: 2 }))
  scene.add(bandLine)
}

function buildBird() {
  if (birdMesh) { scene.remove(birdMesh); birdMesh = null }

  const group = new THREE.Group()

  // Body (White Seagull)
  const body = new THREE.Mesh(
    new THREE.SphereGeometry(BIRD_R, 18, 14),
    new THREE.MeshToonMaterial({ color: 0xffffff }),
  )
  group.add(body)

  // Gray Wings
  const wingGeo = new THREE.BoxGeometry(0.15, 0.25, 0.4)
  const wingMat = new THREE.MeshToonMaterial({ color: 0x7f8c8d })
  const wingL = new THREE.Mesh(wingGeo, wingMat)
  wingL.position.set(-BIRD_R * 0.85, -0.05, 0)
  wingL.rotation.z = 0.25
  group.add(wingL)

  const wingR = new THREE.Mesh(wingGeo, wingMat)
  wingR.position.set(BIRD_R * 0.85, -0.05, 0)
  wingR.rotation.z = -0.25
  group.add(wingR)

  // Gray back feathers
  const backGeo = new THREE.SphereGeometry(BIRD_R * 0.7, 12, 10)
  const back = new THREE.Mesh(backGeo, wingMat)
  back.position.set(0, 0.1, -0.15)
  group.add(back)

  // Eyes
  const eyeWhite = new THREE.MeshBasicMaterial({ color: 0xffffff })
  const eyePupil = new THREE.MeshBasicMaterial({ color: 0x111111 })
  function addEye(xOff) {
    const w = new THREE.Mesh(new THREE.SphereGeometry(0.11, 8, 6), eyeWhite)
    w.position.set(xOff, 0.12, BIRD_R * 0.85)
    group.add(w)
    const p = new THREE.Mesh(new THREE.SphereGeometry(0.06, 6, 5), eyePupil)
    p.position.set(xOff + 0.02, 0.11, BIRD_R * 0.98)
    group.add(p)
  }
  addEye(-0.1)
  addEye(0.1)

  // Angry brow (darker for seagull contrast)
  const browMat = new THREE.MeshBasicMaterial({ color: 0x222222 })
  const browGeo = new THREE.BoxGeometry(0.15, 0.04, 0.04)
  const browL = new THREE.Mesh(browGeo, browMat)
  browL.position.set(-0.1, 0.26, BIRD_R * 0.82)
  browL.rotation.z = 0.4
  group.add(browL)
  const browR = new THREE.Mesh(browGeo, browMat)
  browR.position.set(0.1, 0.26, BIRD_R * 0.82)
  browR.rotation.z = -0.4
  group.add(browR)

  // Seagull Beak (longer, deep orange-yellow cone)
  const beakMat = new THREE.MeshToonMaterial({ color: 0xffc107 })
  const beak = new THREE.Mesh(new THREE.ConeGeometry(0.09, 0.38, 6), beakMat)
  beak.position.set(0, 0.02, BIRD_R * 1.15)
  beak.rotation.x = Math.PI / 2
  group.add(beak)
  
  // Signature red spot on lower beak
  const spotMat = new THREE.MeshBasicMaterial({ color: 0xd32f2f })
  const spot = new THREE.Mesh(new THREE.SphereGeometry(0.04, 6, 4), spotMat)
  spot.position.set(0, -0.04, BIRD_R * 1.25)
  group.add(spot)

  group.position.set(birdX, birdY, 0)
  birdMesh = group
  scene.add(birdMesh)
}

function buildLevel() {
  // Clear old
  for (const b of boxes) scene.remove(b.mesh)
  for (const p of pigs) scene.remove(p.mesh)
  boxes = []
  pigs = []

  const def = getLevelDef()

  for (const bd of def.boxes) {
    const mesh = new THREE.Mesh(
      new THREE.BoxGeometry(bd.hw * 2, bd.hh * 2, 0.55),
      new THREE.MeshToonMaterial({ color: bd.color }),
    )
    mesh.position.set(bd.x, bd.y, 0)
    scene.add(mesh)

    // Outline
    const outline = new THREE.Mesh(
      new THREE.BoxGeometry(bd.hw * 2 + 0.06, bd.hh * 2 + 0.06, 0.6),
      new THREE.MeshBasicMaterial({ color: CMYK.black, side: THREE.BackSide }),
    )
    outline.position.copy(mesh.position)
    scene.add(outline)

    boxes.push({ ...bd, mesh, outlineMesh: outline, alive: true, vx: 0, vy: 0, kinematic: false })
  }

  for (const pd of def.pigs) {
    const group = new THREE.Group()

    const crabRed = 0xe74c3c
    const crabDarkRed = 0xc0392b

    // Crab Body (Squashed sphere shell)
    const body = new THREE.Mesh(
      new THREE.SphereGeometry(PIG_R, 18, 14),
      new THREE.MeshToonMaterial({ color: crabRed }),
    )
    body.scale.set(1.2, 0.8, 0.8)
    group.add(body)

    // Eyes on stalks
    const stalkGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.25, 6)
    const stalkMat = new THREE.MeshToonMaterial({ color: crabRed })
    
    const eyeW = new THREE.MeshBasicMaterial({ color: 0xffffff })
    const eyeP = new THREE.MeshBasicMaterial({ color: 0x111111 })

    function addCrabEye(xOff) {
      const stalk = new THREE.Mesh(stalkGeo, stalkMat)
      stalk.position.set(xOff, 0.18, PIG_R * 0.4)
      stalk.rotation.z = -xOff * 0.6 // lean outward
      group.add(stalk)

      const w = new THREE.Mesh(new THREE.SphereGeometry(0.1, 8, 6), eyeW)
      w.position.set(xOff * 1.4, 0.3, PIG_R * 0.45)
      group.add(w)
      
      const p = new THREE.Mesh(new THREE.SphereGeometry(0.055, 6, 5), eyeP)
      p.position.set(xOff * 1.4 + 0.015, 0.31, PIG_R * 0.55)
      group.add(p)
    }
    addCrabEye(-0.15)
    addCrabEye(0.15)

    // Crab Claws (Left & Right Chelae)
    const clawGeo = new THREE.SphereGeometry(0.16, 12, 10)
    const clawMat = new THREE.MeshToonMaterial({ color: crabRed })
    
    const clawL = new THREE.Mesh(clawGeo, clawMat)
    clawL.scale.set(1, 1.4, 0.8)
    clawL.position.set(-PIG_R * 1.1, 0.1, PIG_R * 0.5)
    clawL.rotation.z = -0.5
    group.add(clawL)
    
    const innerClawL = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 6), new THREE.MeshToonMaterial({ color: crabDarkRed }))
    innerClawL.position.set(-PIG_R * 1.22, 0.25, PIG_R * 0.52)
    group.add(innerClawL)

    const clawR = new THREE.Mesh(clawGeo, clawMat)
    clawR.scale.set(1, 1.4, 0.8)
    clawR.position.set(PIG_R * 1.1, 0.1, PIG_R * 0.5)
    clawR.rotation.z = 0.5
    group.add(clawR)
    
    const innerClawR = new THREE.Mesh(new THREE.SphereGeometry(0.09, 8, 6), new THREE.MeshToonMaterial({ color: crabDarkRed }))
    innerClawR.position.set(PIG_R * 1.22, 0.25, PIG_R * 0.52)
    group.add(innerClawR)

    // Legs (3 pairs)
    const legGeo = new THREE.CylinderGeometry(0.025, 0.02, 0.3, 6)
    function addLeg(xDir, angle, zOff, yOff) {
      const leg = new THREE.Mesh(legGeo, stalkMat)
      leg.position.set(xDir * PIG_R * 0.9, -0.25 + yOff, zOff)
      leg.rotation.z = xDir * angle
      group.add(leg)
    }
    addLeg(-1, 0.8, -0.2, 0)
    addLeg(-1, 1.0, 0.0, -0.05)
    addLeg(-1, 1.2, 0.2, -0.1)
    addLeg(1, -0.8, -0.2, 0)
    addLeg(1, -1.0, 0.0, -0.05)
    addLeg(1, -1.2, 0.2, -0.1)

    group.position.set(pd.x, pd.y, 0)
    scene.add(group)
    pigs.push({ ...pd, mesh: group, alive: true, hp: 2, vy: 0 })
  }
}

function buildTrajectoryDots() {
  for (const d of dotMeshes) scene.remove(d)
  dotMeshes = []
  const dotMat = new THREE.MeshBasicMaterial({ color: CMYK.yellow, transparent: true, opacity: 0.55 })
  for (let i = 0; i < 28; i++) {
    const m = new THREE.Mesh(new THREE.SphereGeometry(0.07, 6, 4), dotMat)
    m.visible = false
    scene.add(m)
    dotMeshes.push(m)
  }
}

// ── Helpers ────────────────────────────────────────────────────────────────
function pointerToWorld(e) {
  const rect = stageRef.value.getBoundingClientRect()
  const ndcX = (e.clientX - rect.left) / rect.width * 2 - 1
  const ndcY = -((e.clientY - rect.top) / rect.height) * 2 + 1
  return {
    x: ndcX * halfW + camera.position.x,
    y: ndcY * halfH + camera.position.y,
  }
}

function distSq(ax, ay, bx, by) {
  return (ax - bx) ** 2 + (ay - by) ** 2
}

function sphereAABB(sx, sy, sr, bx, by, bw, bh) {
  const cx = Math.max(bx - bw, Math.min(bx + bw, sx))
  const cy = Math.max(by - bh, Math.min(by + bh, sy))
  return (sx - cx) ** 2 + (sy - cy) ** 2 < sr * sr
}

function triggerShake(magnitude = 0.18) {
  shakeMag = Math.max(shakeMag, magnitude)
  shakeTimer = 0.3
}

function spawnParticles(x, y, color, count = 12) {
  for (let i = 0; i < count; i++) {
    const m = new THREE.Mesh(
      new THREE.BoxGeometry(0.09, 0.09, 0.05),
      new THREE.MeshBasicMaterial({ color }),
    )
    m.position.set(x, y, 0.2)
    scene.add(m)
    const angle = Math.random() * Math.PI * 2
    const speed = 2 + Math.random() * 4
    particles.push({
      mesh: m,
      vx: Math.cos(angle) * speed,
      vy: Math.sin(angle) * speed,
      life: 0.55 + Math.random() * 0.3,
    })
  }
}

function updateTrajectoryDots(vx, vy) {
  const dt = 0.055
  let x = birdX, y = birdY, vxi = vx, vyi = vy
  for (let i = 0; i < dotMeshes.length; i++) {
    vyi += GRAVITY * dt
    x += vxi * dt
    y += vyi * dt
    if (y < GROUND_Y || x > halfW + 2) {
      dotMeshes[i].visible = false
      continue
    }
    dotMeshes[i].position.set(x, y, 0)
    dotMeshes[i].visible = i % 2 === 0 // every other dot for spacing
  }
}

function hideDots() {
  for (const d of dotMeshes) d.visible = false
}

function updateBand() {
  if (!bandPositions) return
  bandPositions[3] = birdX
  bandPositions[4] = birdY
  bandLine.geometry.attributes.position.needsUpdate = true
  // hide band when in flight
  bandLine.visible = !birdInFlight.value
}

// ── Input ──────────────────────────────────────────────────────────────────
function onPointerDown(e) {
  if (gameOver.value || birdInFlight.value) return
  const w = pointerToWorld(e)
  if (distSq(w.x, w.y, birdX, birdY) < 1.4) {
    dragging = true
    stageRef.value.setPointerCapture(e.pointerId)
    showAimHint.value = false
  }
}

function onPointerMove(e) {
  if (!dragging) return
  const w = pointerToWorld(e)
  // Offset from fork center, clamped
  let dx = w.x - SLING_X
  let dy = w.y - FORK_Y
  const dist = Math.sqrt(dx * dx + dy * dy)
  if (dist > MAX_DRAG) {
    dx = (dx / dist) * MAX_DRAG
    dy = (dy / dist) * MAX_DRAG
  }
  birdX = SLING_X + dx
  birdY = FORK_Y + dy
  birdMesh.position.set(birdX, birdY, 0)
  updateBand()

  // Trajectory preview
  const launchVX = -dx * LAUNCH_POWER / MAX_DRAG
  const launchVY = -dy * LAUNCH_POWER / MAX_DRAG
  updateTrajectoryDots(launchVX, launchVY)
}

function onPointerUp(e) {
  if (!dragging) return
  dragging = false
  hideDots()

  const dx = birdX - SLING_X
  const dy = birdY - FORK_Y
  const dist = Math.sqrt(dx * dx + dy * dy)

  if (dist < 0.3) {
    // Snap back without launch
    birdX = SLING_X; birdY = FORK_Y
    birdMesh.position.set(birdX, birdY, 0)
    updateBand()
    return
  }

  const powerBoost = 1 + props.audioDrive * 0.22
  birdVX = -dx * LAUNCH_POWER * powerBoost / MAX_DRAG
  birdVY = -dy * LAUNCH_POWER * powerBoost / MAX_DRAG
  birdInFlight.value = true
  navigator.vibrate?.(22)
  birdDead = false
  birdsLeft.value = Math.max(0, birdsLeft.value - 1)
  updateBand()
}

// ── Physics tick ───────────────────────────────────────────────────────────
function tick(now) {
  rafId = requestAnimationFrame(tick)
  const dt = lastTime ? Math.min((now - lastTime) / 1000, 0.04) : 0
  lastTime = now

  updateBirdPhysics(dt)
  updateObjects(dt)
  updateParticles(dt)

  // Bird stretch/squash + idle bob
  if (birdMesh && birdInFlight.value && !birdDead) {
    const speed = Math.sqrt(birdVX * birdVX + birdVY * birdVY)
    const stretchFactor = Math.min(1 + speed * 0.022, 1.5)
    const angle = Math.atan2(birdVY, birdVX)
    birdMesh.rotation.z = angle
    birdMesh.scale.set(stretchFactor, 1 / stretchFactor, 1)
    birdMesh.rotation.x += birdVX * dt * 0.4
    idleTime = 0
  } else if (birdMesh && !dragging) {
    birdMesh.scale.lerp(new THREE.Vector3(1, 1, 1), Math.min(dt * 8, 1))
    birdMesh.rotation.z *= (1 - Math.min(dt * 8, 1))
    // Gentle idle bob on slingshot
    idleTime += dt
    birdMesh.position.y = birdY + Math.sin(idleTime * 2.4) * 0.06
    birdMesh.rotation.z = Math.sin(idleTime * 1.8) * 0.08
  }

  // Band tension: color shifts as pull distance increases
  if (bandLine && dragging) {
    const dx = birdX - SLING_X, dy = birdY - FORK_Y
    const t = Math.sqrt(dx*dx + dy*dy) / MAX_DRAG  // 0..1
    const r = Math.round(t * 255)
    const g = Math.round((1 - t) * 122 + t * 64)
    bandLine.material.color.setRGB(r/255, g/255, (1-t)*0.25)
  } else if (bandLine) {
    bandLine.material.color.setHex(CMYK.sling)
  }

  // Pig proximity fear: wobble when bird passes close
  if (birdInFlight.value && !birdDead) {
    for (const pig of pigs) {
      if (!pig.alive) continue
      const d = Math.sqrt(distSq(birdX, birdY, pig.x, pig.y))
      if (d < 2.2) {
        pig.mesh.rotation.z = (Math.random() - 0.5) * 0.18 * (1 - d / 2.2)
      } else {
        pig.mesh.rotation.z *= 0.85
      }
    }
  }

  // Smooth camera pan — follow bird in flight, return to slingshot area when idle
  const inFlight = birdInFlight.value && !birdDead
  cameraTargetX = inFlight ? birdX : CAMERA_REST_X
  cameraTargetY = inFlight ? Math.max(CAMERA_BASE_Y, birdY * 0.5 + CAMERA_BASE_Y * 0.5) : CAMERA_BASE_Y
  cameraX += (cameraTargetX - cameraX) * Math.min(dt * 3.5, 1)
  cameraY += (cameraTargetY - cameraY) * Math.min(dt * 3.0, 1)

  // Portrait zoom: wider during flight so target comes into frame
  const isPortrait = (stageRef.value?.clientWidth ?? 1) < (stageRef.value?.clientHeight ?? 1)
  if (isPortrait) {
    portraitHalfW += ((inFlight ? HALF_W_FLIGHT : HALF_W_IDLE) - portraitHalfW) * Math.min(dt * 3, 1)
    halfW = portraitHalfW
    camera.left = -halfW; camera.right = halfW
    camera.updateProjectionMatrix()
  }

  // Screen shake decay + apply
  if (shakeTimer > 0) {
    shakeTimer -= dt
    const s = shakeMag * (shakeTimer / 0.3)
    camera.position.set(
      cameraX + (Math.random() - 0.5) * s * 2,
      cameraY + (Math.random() - 0.5) * s,
      20,
    )
  } else {
    camera.position.set(cameraX, cameraY, 20)
  }

  renderer.render(scene, camera)
}

function updateBirdPhysics(dt) {
  if (!birdInFlight.value || birdDead) return

  birdVY += GRAVITY * dt
  birdX += birdVX * dt
  birdY += birdVY * dt
  birdMesh.position.set(birdX, birdY, 0)

  // Ground hit
  if (birdY - BIRD_R <= GROUND_Y) {
    birdY = GROUND_Y + BIRD_R
    birdVY = -birdVY * 0.3
    birdVX *= 0.6
    spawnParticles(birdX, GROUND_Y, 0xffffff, 6)
    triggerShake(0.10)
    navigator.vibrate?.(8)
    // squash on impact
    if (birdMesh) birdMesh.scale.set(1.5, 0.6, 1)
    if (Math.abs(birdVY) < 0.8) killBird()
  }

  // Off screen
  if (birdX > halfW + 2 || birdX < -halfW - 2 || birdY < GROUND_Y - 3) {
    killBird()
    return
  }

  // Box collisions
  for (const box of boxes) {
    if (!box.alive) continue
    if (sphereAABB(birdX, birdY, BIRD_R, box.x, box.y, box.hw, box.hh)) {
      const speed = Math.sqrt(birdVX * birdVX + birdVY * birdVY)
      hitBox(box, speed)
      // Bird bounces off, loses most momentum
      birdVX *= -0.2
      birdVY = Math.abs(birdVY) * 0.25
      spawnParticles(birdX, birdY, box.mesh.material.color.getHex(), 10)
      if (speed > 2) killBird()
    }
  }

  // Pig collisions
  for (const pig of pigs) {
    if (!pig.alive) continue
    const d = Math.sqrt(distSq(birdX, birdY, pig.x, pig.y))
    if (d < BIRD_R + PIG_R) {
      hitPig(pig, Math.sqrt(birdVX * birdVX + birdVY * birdVY))
      birdVX *= -0.15
      birdVY = Math.abs(birdVY) * 0.2
      spawnParticles(pig.x, pig.y, 0xe74c3c, 14)
      killBird()
    }
  }
}

function updateObjects(dt) {
  for (const box of boxes) {
    if (!box.alive || !box.kinematic) continue
    box.vy += GRAVITY * dt
    box.vx *= 0.97
    box.x += box.vx * dt
    box.y += box.vy * dt
    if (box.y - box.hh <= GROUND_Y) {
      box.y = GROUND_Y + box.hh
      box.vy = -box.vy * 0.25
      box.vx *= 0.55
      if (Math.abs(box.vy) < 0.4) { box.vy = 0; box.kinematic = false }
      // Damage pigs it lands on
      for (const pig of pigs) {
        if (!pig.alive) continue
        if (sphereAABB(pig.x, pig.y, PIG_R, box.x, box.y, box.hw, box.hh + 0.1)) {
          hitPig(pig, 4)
          spawnParticles(pig.x, pig.y, 0xe74c3c, 8)
        }
      }
    }
    box.mesh.position.set(box.x, box.y, 0)
    if (box.outlineMesh) box.outlineMesh.position.set(box.x, box.y, 0)
    box.mesh.rotation.z += box.vx * dt * 0.12
    if (box.outlineMesh) box.outlineMesh.rotation.z = box.mesh.rotation.z
  }

  for (const pig of pigs) {
    if (!pig.alive) continue
    if (pig.vy !== 0) {
      pig.vy += GRAVITY * dt * 0.5
      pig.y += pig.vy * dt
      if (pig.y - PIG_R <= GROUND_Y) {
        pig.y = GROUND_Y + PIG_R
        pig.vy = 0
      }
      pig.mesh.position.y = pig.y
    }
  }
}

function updateParticles(dt) {
  for (let i = particles.length - 1; i >= 0; i--) {
    const p = particles[i]
    p.life -= dt
    if (p.life <= 0) { scene.remove(p.mesh); particles.splice(i, 1); continue }
    p.vy += GRAVITY * dt
    p.mesh.position.x += p.vx * dt
    p.mesh.position.y += p.vy * dt
    p.mesh.material.opacity = p.life / 0.7
    p.mesh.rotation.z += dt * 8
  }
}

function hitBox(box, speed) {
  box.hp -= speed > 5 ? 2 : 1
  triggerShake(speed > 5 ? 0.22 : 0.12)
  navigator.vibrate?.(speed > 5 ? 18 : 10)
  if (box.hp <= 0) {
    box.alive = false
    scene.remove(box.mesh)
    if (box.outlineMesh) scene.remove(box.outlineMesh)
    score.value += 10
    emit('collect')
  } else {
    const orig = box.mesh.material.color.getHex()
    box.mesh.material.color.setHex(0xffffff)
    setTimeout(() => { if (box.mesh.material) box.mesh.material.color.setHex(orig) }, 80)
    box.kinematic = true
    box.vx = (birdVX * 0.4) + (Math.random() - 0.5) * 1.5
    box.vy = Math.abs(birdVY) * 0.25 + 1.5
  }
}

function hitPig(pig, speed) {
  pig.hp -= speed > 4 ? 2 : 1
  triggerShake(0.35)
  if (pig.hp <= 0) {
    pig.alive = false
    scene.remove(pig.mesh)
    score.value += 100
    navigator.vibrate?.([12, 40, 25])
    emit('collect')
    emit('collect')
    checkWinLose()
  } else {
    navigator.vibrate?.(15)
    const orig = pig.mesh.children[0].material.color.getHex()
    pig.mesh.children[0].material.color.setHex(0xffffff)
    setTimeout(() => {
      if (pig.mesh.children[0]?.material) pig.mesh.children[0].material.color.setHex(orig)
    }, 100)
    pig.vy = 2
  }
}

function killBird() {
  if (birdDead) return
  birdDead = true
  birdInFlight.value = false
  // Remove mesh briefly then reset
  setTimeout(nextBird, 900)
}

function nextBird() {
  if (gameOver.value) return
  if (birdsLeft.value === 0) {
    checkWinLose()
    return
  }
  birdX = SLING_X
  birdY = FORK_Y
  birdVX = 0
  birdVY = 0
  birdDead = false
  if (birdMesh) birdMesh.position.set(birdX, birdY, 0)
  birdMesh.rotation.set(0, 0, 0)
  updateBand()
}

function checkWinLose() {
  const anyPigAlive = pigs.some(p => p.alive)
  if (!anyPigAlive) {
    allPigsDead.value = true
    score.value += birdsLeft.value * 500
    gameOver.value = true
    emit('score', score.value)
  } else if (birdsLeft.value === 0 && !birdInFlight.value) {
    allPigsDead.value = false
    gameOver.value = true
    emit('score', score.value)
  }
}

function birdsForLevel(lvl) {
  // Levels 0-1: 5 birds. Levels 2-3: 5. Levels 4+: scale up to 7 for harder layouts
  const def = LEVELS[lvl % LEVELS.length](GROUND_Y, BOX_HH, BOX_HW)
  return Math.max(5, Math.min(7, def.pigs.length + 2))
}

function resetLevel(advance = true) {
  if (advance && allPigsDead.value) currentLevel++
  gameOver.value = false
  allPigsDead.value = false
  score.value = 0
  levelNumber.value = currentLevel + 1
  const bCount = birdsForLevel(currentLevel)
  birdsLeft.value = bCount
  birdsTotal.value = bCount
  birdX = SLING_X; birdY = FORK_Y
  birdVX = 0; birdVY = 0
  birdDead = false
  birdInFlight.value = false
  dragging = false
  cameraX = CAMERA_REST_X; cameraTargetX = CAMERA_REST_X
  cameraY = CAMERA_BASE_Y; cameraTargetY = CAMERA_BASE_Y
  shakeTimer = 0; shakeMag = 0
  portraitHalfW = HALF_W_IDLE
  if (camera) camera.position.set(cameraX, cameraY, 20)

  for (const p of particles) scene.remove(p.mesh)
  particles = []

  buildLevel()
  if (birdMesh) {
    birdMesh.position.set(birdX, birdY, 0)
    birdMesh.rotation.set(0, 0, 0)
  }
  updateBand()
  showAimHint.value = true
}

// ── Resize ─────────────────────────────────────────────────────────────────
function resize() {
  if (!renderer || !stageRef.value) return
  const rect = stageRef.value.getBoundingClientRect()
  const w = Math.max(1, rect.width)
  const h = Math.max(1, rect.height)

  const aspect = w / h

  if (aspect >= 1.0) {
    // Landscape / wide: show full vertical game height
    halfH = HALF_H  // 6.0
    halfW = halfH * aspect
  } else {
    // Portrait mobile: zoom in so bird and nearby structures are large and clear.
    // Show ~5 world units wide — slingshot + 1-2 towers fill the frame nicely.
    halfW = 5.0
    halfH = halfW / aspect
  }

  renderer.setSize(w, h, false)
  camera.left = -halfW
  camera.right = halfW
  camera.top = halfH
  camera.bottom = -halfH
  camera.updateProjectionMatrix()
}

// ── Lifecycle ──────────────────────────────────────────────────────────────
onMounted(() => {
  birdsTotal.value = birdsForLevel(0)
  buildScene()
  buildLevel()
  buildBird()
  buildTrajectoryDots()
  resize()

  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(stageRef.value)

  hintTimeout = setTimeout(() => { showAimHint.value = false }, 3000)
  rafId = requestAnimationFrame(tick)
})

onUnmounted(() => {
  cancelAnimationFrame(rafId)
  resizeObserver?.disconnect()
  clearTimeout(settleTimeout)
  clearTimeout(hintTimeout)
  renderer?.dispose()
})
</script>

<style scoped>
.birds-stage {
  position: absolute;
  inset: 0;
  overflow: hidden;
  cursor: crosshair;
  user-select: none;
  touch-action: none;
}

.birds-stage canvas {
  display: block;
  width: 100% !important;
  height: 100% !important;
}

.birds-hud {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 3;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.65rem 0.75rem;
}

.birds-back {
  display: grid;
  place-items: center;
  width: 38px;
  height: 38px;
  border: 2px solid #00d7ff;
  border-radius: 999px;
  background: rgba(11, 11, 11, 0.7);
  color: #ffd400;
  cursor: pointer;
  pointer-events: auto;
  backdrop-filter: blur(6px);
  font-size: 0.8rem;
  flex-shrink: 0;
}

.birds-score-block {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1px;
}

.birds-score {
  font-size: 1.1rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  color: #ffd400;
  text-shadow: 0 2px 8px rgba(0,0,0,0.8);
}

.birds-level {
  font-size: 0.55rem;
  font-weight: 900;
  letter-spacing: 0.1em;
  color: #00d7ff;
  opacity: 0.85;
}

.birds-hud-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6px;
  margin-right: 36px; /* Prevent overlap with global Top-Right Fullscreen Toggle! */
}

.birds-birds-left {
  display: flex;
  gap: 3px;
  align-items: center;
}

.birds-radio-btn {
  position: relative;
  display: grid;
  place-items: center;
  width: 32px;
  height: 32px;
  border: 2px solid rgba(0, 215, 255, 0.5);
  border-radius: 999px;
  background: rgba(11, 11, 11, 0.7);
  color: #00d7ff;
  cursor: pointer;
  pointer-events: auto;
  overflow: hidden;
  backdrop-filter: blur(6px);
  transition: border-color 0.2s, box-shadow 0.2s;
}

.birds-radio-btn.is-active {
  border-color: #00d7ff;
  box-shadow: 0 0 8px rgba(0, 215, 255, 0.4);
}

.birds-radio-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0.45;
}

.birds-radio-icon {
  position: relative;
  z-index: 1;
  font-size: 0.65rem;
}

.bird-pip {
  font-size: 0.75rem;
  color: #ffd400;
  text-shadow: 0 0 8px rgba(255, 212, 0, 0.8);
}

.birds-overlay {
  position: absolute;
  inset: 0;
  z-index: 10;
  background: rgba(11, 11, 11, 0.9);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.85rem;
  backdrop-filter: blur(8px);
}

.birds-result {
  font-size: clamp(1.3rem, 5vw, 2rem);
  font-weight: 900;
  letter-spacing: 0.06em;
  color: #ffd400;
  text-shadow: 0 0 20px rgba(255,212,0,0.5);
}

.birds-stars {
  display: flex;
  gap: 0.3rem;
}

.birds-star {
  font-size: 2rem;
  color: rgba(255, 212, 0, 0.2);
  transition: color 0.3s ease, text-shadow 0.3s ease;
}

.birds-star.lit {
  color: #ffd400;
  text-shadow: 0 0 14px rgba(255, 212, 0, 0.7);
}

.birds-result-sub {
  font-size: 0.9rem;
  font-weight: 700;
  color: #00d7ff;
}

.birds-btn {
  padding: 0.6rem 1.4rem;
  border: 2px solid #ffd400;
  border-radius: 999px;
  background: rgba(255, 212, 0, 0.1);
  color: #ffd400;
  font-size: 0.82rem;
  font-weight: 900;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  cursor: pointer;
  transition: background 0.15s;
}

.birds-btn:hover { background: rgba(255, 212, 0, 0.22); }

.birds-btn--ghost {
  border-color: #00d7ff;
  color: #00d7ff;
  background: rgba(0, 215, 255, 0.08);
}

.birds-btn--ghost:hover { background: rgba(0, 215, 255, 0.18); }

.birds-hint {
  position: absolute;
  bottom: 1.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 4;
  padding: 0.38rem 0.7rem;
  border: 2px solid #00d7ff;
  border-radius: 999px;
  background: rgba(11, 11, 11, 0.78);
  color: #ffd400;
  font-size: 0.65rem;
  font-weight: 900;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  pointer-events: none;
}

.overlay-fade-enter-active { transition: opacity 0.3s ease; }
.overlay-fade-leave-active { transition: opacity 0.2s ease; }
.overlay-fade-enter-from,
.overlay-fade-leave-to { opacity: 0; }

.hint-fade-enter-active { transition: opacity 0.3s ease; }
.hint-fade-leave-active { transition: opacity 0.8s ease; }
.hint-fade-enter-from,
.hint-fade-leave-to { opacity: 0; }
</style>
