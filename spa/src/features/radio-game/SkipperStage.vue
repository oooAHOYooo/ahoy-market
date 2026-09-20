<template>
  <div
    ref="stageRef"
    class="trampoline-stage"
    :class="{ 'is-playing': isPlaying, 'is-jumping': game.airborne }"
  >
    <div class="ninja-smoke ninja-smoke--left"></div>
    <div class="ninja-smoke ninja-smoke--right"></div>
    <div class="ninja-speed-lines"></div>
    <div class="ninja-shuriken-field">
      <span v-for="shuriken in shurikens" :key="shuriken" class="ninja-shuriken"></span>
    </div>
    <div class="trampoline-stage-vignette"></div>
    <div class="trampoline-stage-score" aria-hidden="true">
      <span>{{ game.score }}</span>
    </div>
    <Transition name="best-pop">
      <div v-if="showNewBest" class="new-best-banner" aria-hidden="true">NEW BEST {{ game.bestFlip }}×</div>
    </Transition>
    <Transition name="best-pop">
      <div v-if="perfectFlash" class="perfect-banner" aria-hidden="true">PERFECT ★</div>
    </Transition>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  isPlaying: { type: Boolean, default: false },
  controlIntent: { type: Object, default: null },
  activeTrick: { type: String, default: null },
  audioDrive: { type: Number, default: 0.3 },
  audioPhase: { type: Number, default: 0 },
})

const emit = defineEmits(['status', 'collect', 'lock', 'impact', 'pop'])

const stageRef = ref(null)
const shurikens = Array.from({ length: 6 }, (_, index) => index)
const showNewBest = ref(false)
let newBestTimeout = null

function flashNewBest() {
  showNewBest.value = true
  clearTimeout(newBestTimeout)
  newBestTimeout = setTimeout(() => { showNewBest.value = false }, 1800)
}
const game = reactive({
  score: 0,
  jumps: 0,
  bestFlip: 0,
  lastFlipCount: 0,
  height: 0,
  airborne: false,
})

let renderer
let scene
let camera
let ninja
let trampoline
let trampolineMat
let moon
let rafId = 0
let lastTime = 0
let velocityY = 0
let velocityX = 0
let bodyY = 0
let bodyX = 0
let spin = 0
let spinVelocity = 0
let flipCarry = 0
let airTime = 0
let airBoosts = 0
let takeoffSquash = 0
let landingBounce = 0
let lastJumpToken = 0
let statusAccumulator = 0
let isRagdoll = false
let ragdollTime = 0
let inMat = false
// Perfect-timing bonus
let landedAt = -999
let perfectFlash = ref(false)
let perfectTimeout = null
// Edge danger
const EDGE_LIMIT = 1.9
let blinkTimer = 0
let blinkDuration = 0
let blinkInterval = 2.8
const ninjaParts = {
  body: null,
  head: null,
  leftArm: null,
  rightArm: null,
  leftLeg: null,
  rightLeg: null,
  leftEyelid: null,
  rightEyelid: null,
  mouth: null,
}
const physicsParams = reactive({
  gravity: 12.4,
  damping: 0.993,
  jumpForce: 7.2,
  spinForce: 4.4,
})
let resizeObserver
let confetti = []
let trailMeshes = []   // spin trail ghost copies
let trailTimer = 0
let slashes = []
let stageWidth = 1024

const signal = computed(() => Math.max(0.22, Math.min(1, 0.45 + props.audioDrive * 0.5)))

function makeMat(color, roughness = 0.55, metalness = 0.02) {
  return new THREE.MeshToonMaterial({ color, gradientMap: null })
}

function makeStandardMat(color, roughness = 0.55, metalness = 0.02) {
  return new THREE.MeshStandardMaterial({ color, roughness, metalness })
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value))
}

function lerp(a, b, t) {
  return a + (b - a) * t
}

const CMYK = {
  black: 0x0b0b0b,
  space: 0x07050e, // Deep cosmic space background!
  cyan: 0x00d7ff,
  magenta: 0xff2fb8,
  yellow: 0xffd400,
}

function addMesh(parent, geometry, material, position, rotation = [0, 0, 0], scale = [1, 1, 1]) {
  const mesh = new THREE.Mesh(geometry, material)
  mesh.position.set(...position)
  mesh.rotation.set(...rotation)
  mesh.scale.set(...scale)
  mesh.castShadow = true
  mesh.receiveShadow = true
  parent.add(mesh)
  return mesh
}

function buildNinja() {
  const group = new THREE.Group()
  
  // Cyber Panda Color Palette
  const bodyMat = makeMat(0xffffff) // white fur
  const darkMat = makeMat(0x0c0c14) // midnight panda fur
  const eyeMat = new THREE.MeshBasicMaterial({ color: CMYK.cyan }) // glowing cyber cyan eyes
  const bellyMat = makeMat(CMYK.cyan)
  const blushMat = makeMat(CMYK.magenta) // blushing pink cheeks
  const catchMat = new THREE.MeshBasicMaterial({ color: 0xffffff }) // anime reflections

  // 1. Chubby Body
  ninjaParts.body = addMesh(group, new THREE.SphereGeometry(0.38, 20, 16), bodyMat, [0, 1.1, 0], [0, 0, 0], [1.1, 1, 0.9])
  
  // 2. Big Round Head
  ninjaParts.head = addMesh(group, new THREE.SphereGeometry(0.42, 22, 18), bodyMat, [0, 1.7, 0], [0, 0, 0], [1.05, 0.95, 1])

  // 3. Neon Belly Badge
  addMesh(group, new THREE.SphereGeometry(0.18, 12, 12), bellyMat, [0, 1.1, 0.28], [0, 0, 0], [1, 1, 0.2])

  // 4. Round Dark Panda Ears (added to head)
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.14, 12, 12), darkMat, [-0.32, 0.35, -0.05])
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.14, 12, 12), darkMat, [0.32, 0.35, -0.05])

  // 5. Dark Panda Limbs
  ninjaParts.leftArm = addMesh(group, new THREE.SphereGeometry(0.12, 10, 10), darkMat, [-0.35, 1.2, 0.1], [0, 0, 0.6])
  ninjaParts.rightArm = addMesh(group, new THREE.SphereGeometry(0.12, 10, 10), darkMat, [0.35, 1.2, 0.1], [0, 0, -0.6])
  ninjaParts.leftLeg = addMesh(group, new THREE.SphereGeometry(0.14, 10, 10), darkMat, [-0.18, 0.75, 0.05])
  ninjaParts.rightLeg = addMesh(group, new THREE.SphereGeometry(0.14, 10, 10), darkMat, [0.18, 0.75, 0.05])

  // 6. Slanted Iconic Panda Eye Patches (added to head)
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.14, 14, 10), darkMat, [-0.16, 0.02, 0.34], [0, 0, 0.25], [1.25, 0.9, 0.3])
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.14, 14, 10), darkMat, [0.16, 0.02, 0.34], [0, 0, -0.25], [1.25, 0.9, 0.3])

  // 7. Glowing Anime Eyes inside Patches
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.04, 12, 12), eyeMat, [-0.15, 0.04, 0.38])
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.04, 12, 12), eyeMat, [0.15, 0.04, 0.38])
  // Sparkle gleams
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.015, 6, 6), catchMat, [-0.16, 0.05, 0.41])
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.015, 6, 6), catchMat, [0.14, 0.05, 0.41])

  // 8. Blush & Nose
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.06, 8, 8), blushMat, [-0.26, -0.12, 0.34], [0, 0, 0], [1.2, 0.6, 0.4])
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.06, 8, 8), blushMat, [0.26, -0.12, 0.34], [0, 0, 0], [1.2, 0.6, 0.4])
  addMesh(ninjaParts.head, new THREE.SphereGeometry(0.025, 6, 6), darkMat, [0, -0.05, 0.41])

  // 9. Eyelids (dark flat ellipsoids, hidden by default — slide down to blink)
  ninjaParts.leftEyelid = addMesh(ninjaParts.head, new THREE.SphereGeometry(0.055, 10, 6), darkMat, [-0.15, 0.04, 0.39], [0, 0, 0], [1.3, 0.55, 0.25])
  ninjaParts.rightEyelid = addMesh(ninjaParts.head, new THREE.SphereGeometry(0.055, 10, 6), darkMat, [0.15, 0.04, 0.39], [0, 0, 0], [1.3, 0.55, 0.25])
  ninjaParts.leftEyelid.visible = false
  ninjaParts.rightEyelid.visible = false

  // 10. Mouth (small bar, grows + curves when flipping)
  const mouthMat = makeMat(0x111111)
  ninjaParts.mouth = addMesh(ninjaParts.head, new THREE.CapsuleGeometry(0.018, 0.075, 4, 8), mouthMat, [0, -0.19, 0.38], [0, 0, 0], [1, 1, 1])

  // Scale entire character group down to be compact & cute!
  group.scale.setScalar(0.82)
  group.position.set(0, 0.28, 0)

  // Bold outline pass for vector readability.
  const outlineMat = new THREE.MeshBasicMaterial({ color: CMYK.black, side: THREE.BackSide })
  const meshes = []
  group.traverse((obj) => {
    if (obj.isMesh) meshes.push(obj)
  })
  meshes.forEach((obj) => {
    const outline = new THREE.Mesh(obj.geometry, outlineMat)
    outline.scale.setScalar(1.07)
    outline.renderOrder = -1
    obj.add(outline)
  })

  return group
}

function buildScene() {
  scene = new THREE.Scene()
  scene.background = null // Transparent canvas reveals high-contrast CSS neon backgrounds!
  scene.fog = new THREE.Fog(CMYK.space, 6, 32)

  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 80)
  camera.position.set(0, 3.4, 9.4)
  camera.lookAt(0, 1.35, 0)

  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.shadowMap.enabled = true
  renderer.shadowMap.type = THREE.PCFSoftShadowMap
  stageRef.value.appendChild(renderer.domElement)

  const hemi = new THREE.HemisphereLight(CMYK.cyan, CMYK.space, 1.1) // Darker ambient for richer contrast
  scene.add(hemi)

  const key = new THREE.DirectionalLight(CMYK.magenta, 3.6) // Brighter rim light for dramatic model pops
  key.position.set(-3, 8, 5)
  key.castShadow = true
  key.shadow.mapSize.set(1024, 1024)
  key.shadow.camera.left = -5
  key.shadow.camera.right = 5
  key.shadow.camera.top = 14
  key.shadow.camera.bottom = -5
  key.shadow.camera.near = 0.5
  key.shadow.camera.far = 25
  key.shadow.bias = -0.0015
  scene.add(key)

  // Cosmic CMYK Starfield system
  const starGeo = new THREE.BufferGeometry()
  const starCount = 120
  const starPos = new Float32Array(starCount * 3)
  for (let i = 0; i < starCount; i++) {
    starPos[i * 3] = (Math.random() - 0.5) * 25
    starPos[i * 3 + 1] = Math.random() * 15 - 2
    starPos[i * 3 + 2] = -Math.random() * 18 - 4
  }
  starGeo.setAttribute('position', new THREE.BufferAttribute(starPos, 3))
  const starMat = new THREE.PointsMaterial({ 
    color: 0xffffff, 
    size: 0.09, // Slightly larger star blobs
    sizeAttenuation: true, 
    transparent: true, 
    opacity: 0.85 // Brighter star rendering for ultimate galactic contrast
  })
  const starfield = new THREE.Points(starGeo, starMat)
  scene.add(starfield)

  moon = addMesh(
    scene,
    new THREE.SphereGeometry(1.05, 28, 20),
    new THREE.MeshBasicMaterial({ color: CMYK.yellow }),
    [-4.6, 5.1, -7],
    [0, 0, 0],
  )

  const floorMat = makeStandardMat(CMYK.space, 0.8)
  const floor = addMesh(scene, new THREE.PlaneGeometry(34, 34), floorMat, [0, -0.04, -1.2], [-Math.PI / 2, 0, 0])
  floor.receiveShadow = true

  trampoline = new THREE.Group()
  trampolineMat = makeMat(CMYK.space)
  addMesh(trampoline, new THREE.CylinderGeometry(1.95, 2.15, 0.2, 64), trampolineMat, [0, 0.06, 0])
  addMesh(trampoline, new THREE.TorusGeometry(2.08, 0.12, 16, 72), makeMat(CMYK.cyan, 0.35, 0.08), [0, 0.2, 0], [Math.PI / 2, 0, 0])
  for (let i = 0; i < 8; i += 1) {
    const angle = (i / 8) * Math.PI * 2
    const x = Math.cos(angle) * 1.7
    const z = Math.sin(angle) * 1.7
    addMesh(trampoline, new THREE.CylinderGeometry(0.035, 0.035, 1.1, 12), makeMat(CMYK.yellow), [x, -0.38, z], [0.16 * Math.sin(angle), 0, 0.16 * Math.cos(angle)])
  }
  scene.add(trampoline)

  ninja = buildNinja()
  scene.add(ninja)

  const colors = [CMYK.cyan, CMYK.magenta, CMYK.yellow]
  for (let i = 0; i < 12; i += 1) {
    const slash = addMesh(
      scene,
      new THREE.BoxGeometry(0.08, 1.7 + (i % 3) * 0.2, 0.02),
      new THREE.MeshBasicMaterial({ color: colors[i % colors.length] }),
      [Math.cos((i / 12) * Math.PI * 2) * 5.8, 3 + (i % 3) * 0.3, Math.sin((i / 12) * Math.PI * 2) * 5.8 - 2],
      [0, 0, Math.PI / 4],
    )
    slashes.push({ mesh: slash, phase: i * 0.4, drift: 0.12 + (i % 4) * 0.02 })
  }

  for (let i = 0; i < 40; i += 1) {
    const piece = addMesh(
      scene,
      new THREE.BoxGeometry(0.08, 0.08, 0.02),
      new THREE.MeshBasicMaterial({ color: colors[i % colors.length] }),
      [0, -20, 0],
    )
    piece.visible = false
    confetti.push({ mesh: piece, life: 0, velocity: new THREE.Vector3() })
  }
}

function resize() {
  if (!renderer || !camera || !stageRef.value) return
  const rect = stageRef.value.getBoundingClientRect()
  const width = Math.max(1, rect.width)
  const height = Math.max(1, rect.height)
  stageWidth = width
  renderer.setSize(width, height, false)
  camera.aspect = width / height
  camera.position.z = width < 720 ? 10.8 : 9.4
  camera.updateProjectionMatrix()
}

function emitStatus() {
  emit('status', {
    modeKey: 'trampoline-flip',
    modeLabel: 'Trampoline Flip',
    drift: game.jumps,
    score: game.score,
    combo: Math.max(1, game.lastFlipCount || game.bestFlip),
    signal: signal.value,
    wake: game.airborne ? 1 : 0.35,
    charge: game.airborne ? Math.min(1, game.height / 4.6) : 0,
    speed: Math.abs(velocityY) + Math.abs(spinVelocity),
  })
}

function burstConfetti() {
  for (const item of confetti) {
    item.life = 0.75 + Math.random() * 0.5
    item.mesh.visible = true
    item.mesh.position.set((Math.random() - 0.5) * 0.5, 2.1 + Math.random() * 0.9, (Math.random() - 0.5) * 0.5)
    item.mesh.rotation.set(Math.random() * Math.PI, Math.random() * Math.PI, Math.random() * Math.PI)
    item.velocity.set((Math.random() - 0.5) * 4.2, 2.2 + Math.random() * 2.4, (Math.random() - 0.5) * 4.2)
  }
}

function randomizePhysics() {
  physicsParams.gravity = 11.5 + Math.random() * 2.4
  physicsParams.damping = 0.990 + Math.random() * 0.006
  physicsParams.jumpForce = 6.8 + Math.random() * 1.4
  physicsParams.spinForce = 3.8 + Math.random() * 1.2
}

function resetNinjaParts() {
  isRagdoll = false
  ragdollTime = 0
  if (ninjaParts.mouth) { ninjaParts.mouth.scale.set(1, 0.9, 1) }
  if (ninjaParts.leftEyelid) ninjaParts.leftEyelid.visible = false
  if (ninjaParts.rightEyelid) ninjaParts.rightEyelid.visible = false
  if (ninjaParts.leftArm) {
    ninjaParts.leftArm.rotation.set(0, 0, 0.6)
    ninjaParts.leftArm.position.set(-0.35, 1.2, 0.1)
  }
  if (ninjaParts.rightArm) {
    ninjaParts.rightArm.rotation.set(0, 0, -0.6)
    ninjaParts.rightArm.position.set(0.35, 1.2, 0.1)
  }
  if (ninjaParts.head) {
    ninjaParts.head.rotation.set(0, 0, 0)
    ninjaParts.head.position.set(0, 1.7, 0)
  }
  if (ninjaParts.leftLeg) {
    ninjaParts.leftLeg.rotation.set(0, 0, 0)
    ninjaParts.leftLeg.position.set(-0.18, 0.75, 0.05)
  }
  if (ninjaParts.rightLeg) {
    ninjaParts.rightLeg.rotation.set(0, 0, 0)
    ninjaParts.rightLeg.position.set(0.18, 0.75, 0.05)
  }
}

function triggerRagdoll() {
  isRagdoll = true
  inMat = false
  ragdollTime = 0
  game.airborne = false
  game.height = 0
  bodyY = 0
  bodyX = 0
  velocityY = 0
  velocityX = 0
  spinVelocity = 0
  takeoffSquash = 0
  landingBounce = 1.4
  navigator.vibrate?.([30, 20, 15])
  emit('impact')
  emit('lock')
}

function launchFlip() {
  if (!props.isPlaying) return
  const clickX = clamp(props.controlIntent?.clickX ?? 0.5, 0, 1)
  const clickY = clamp(props.controlIntent?.clickY ?? 0.5, 0, 1)
  const charge = clamp(props.controlIntent?.charge ?? 0, 0, 1)
  const biasX = (clickX - 0.5) * 2
  const biasY = 1 - clickY
  const centered = 1 - Math.abs(biasX)
  if (game.airborne || inMat) {
    airBoosts += 1
    // Add spin in whichever direction the panda is already rotating (or rightward by default)
    const spinDir = Math.sign(spinVelocity) || 1
    spinVelocity += spinDir * (4.5 + airBoosts * 0.6)
    velocityY += 1.4 + biasY * 0.5
    takeoffSquash = Math.max(takeoffSquash, 0.22)
    emit('pop')
    return
  }
  // Allow recovering from ragdoll — tap again to get back up
  if (isRagdoll) {
    ninja.rotation.x = 0
    ninja.rotation.z = 0
    ninja.position.y = 0.28
    ninja.position.x = 0
    spin = 0
  }

  resetNinjaParts()
  randomizePhysics()
  inMat = false
  game.airborne = true
  game.jumps += 1
  airTime = 0
  airBoosts = 0
  takeoffSquash = 1
  landingBounce = 0
  // Don't zero bodyX — let horizontal position persist from previous landing
  navigator.vibrate?.(18)

  // Perfect-timing bonus: reward re-launch within 150 ms of landing
  const timeSinceLand = performance.now() - landedAt
  const isPerfect = timeSinceLand < 150 && landedAt > 0
  const perfectMult = isPerfect ? 1.4 : 1.0
  if (isPerfect) {
    clearTimeout(perfectTimeout)
    perfectFlash.value = true
    perfectTimeout = setTimeout(() => { perfectFlash.value = false }, 900)
    navigator.vibrate?.([8, 12, 8])
  }

  velocityY = (physicsParams.jumpForce + biasY * 2.4 + centered * 1.2 + props.audioDrive * 0.9 + charge * 2.2) * perfectMult
  // Horizontal bias from tap position — player can steer drift direction
  velocityX = biasX * 2.2
  const spinDir = biasX >= 0 ? 1 : -1
  spinVelocity = spinDir * (5.8 + Math.abs(biasX) * physicsParams.spinForce + props.audioDrive * 1.2 + charge * 1.8)
  flipCarry = 0
  emit('pop')
}

function settleLanding() {
  const flipCount = Math.max(1, Math.floor((flipCarry + Math.PI * 0.58) / (Math.PI * 2)))
  const grace = Math.max(0, 1 - Math.abs(((spin + Math.PI) % (Math.PI * 2)) - Math.PI) / Math.PI)
  const points = flipCount * 10 + airBoosts * 4 + Math.round(grace * 8)
  game.score += points
  if (flipCount > game.bestFlip) {
    game.bestFlip = flipCount
    try { localStorage.setItem('ahoy_trampoline_best', String(flipCount)) } catch (e) { /* ignore */ }
    flashNewBest()
  }
  game.lastFlipCount = flipCount
  game.airborne = false
  game.height = 0
  bodyY = 0
  bodyX = 0
  velocityY = 0
  velocityX = 0
  spin = 0
  spinVelocity = 0
  takeoffSquash = 0
  landingBounce = 1
  ninja.rotation.x = 0
  ninja.rotation.z = 0
  resetNinjaParts()
  navigator.vibrate?.(flipCount >= 3 ? [12, 15, 20] : 12)
  burstConfetti()
  emit('collect', { kind: 'flip', score: points })
  emit('lock')
}

function updatePhysics(dt) {
  const pulse = Math.sin(props.audioPhase * Math.PI * 2) * props.audioDrive
  moon.scale.setScalar(1 + pulse * 0.03)
  takeoffSquash = Math.max(0, takeoffSquash - dt * 3.8)
  landingBounce = Math.max(0, landingBounce - dt * 3.2)
  const isMobile = stageWidth < 720

  if (game.airborne) {
    airTime += dt
    velocityY -= physicsParams.gravity * dt
    velocityX *= 0.985  // gentle air resistance on horizontal drift
    bodyY += velocityY * dt
    bodyX += velocityX * dt

    // Edge danger — drift past the mat edge triggers ragdoll
    if (Math.abs(bodyX) > EDGE_LIMIT) {
      triggerRagdoll()
      return
    }

    // Spin tuck/spread: fast spin = arms tuck (low drag); slow spin = arms spread (high drag)
    if (!inMat) {
      const absSpV = Math.abs(spinVelocity)
      const tuck = clamp((absSpV - 3) / 8, 0, 1)   // 0=spread, 1=tucked
      const drag = lerp(0.022, 0.003, tuck)
      spinVelocity -= spinVelocity * drag * (1 / Math.max(dt, 0.001)) * dt
      const hang = clamp((velocityY + 1.6) / 4.6, 0, 1)
      const spinStep = spinVelocity * (0.72 + hang * 0.35) * dt
      spin += spinStep
      flipCarry += Math.abs(spinStep)

      // Drive limb visuals from tuck
      if (ninjaParts.leftArm && ninjaParts.rightArm) {
        const armZ = lerp(0.6, 0.12, tuck)
        ninjaParts.leftArm.rotation.z  = lerp(ninjaParts.leftArm.rotation.z,   armZ, dt * 12)
        ninjaParts.rightArm.rotation.z = lerp(ninjaParts.rightArm.rotation.z, -armZ, dt * 12)
      }
      if (ninjaParts.leftLeg && ninjaParts.rightLeg) {
        const legX = lerp(0, 0.5, tuck)
        ninjaParts.leftLeg.rotation.x  = lerp(ninjaParts.leftLeg.rotation.x,   legX, dt * 10)
        ninjaParts.rightLeg.rotation.x = lerp(ninjaParts.rightLeg.rotation.x, -legX, dt * 10)
      }
    }

    // First contact with trampoline mat
    if (bodyY <= 0 && !inMat) {
      const grace = Math.max(0, 1 - Math.abs(((spin + Math.PI) % (Math.PI * 2)) - Math.PI) / Math.PI)
      if (grace < 0.52) {
        triggerRagdoll()
      } else {
        inMat = true
        landedAt = performance.now()
        if (flipCarry > Math.PI * 0.5) {
          const flipCount = Math.max(1, Math.floor((flipCarry + Math.PI * 0.58) / (Math.PI * 2)))
          const gracePoints = Math.max(0, 1 - Math.abs(((spin + Math.PI) % (Math.PI * 2)) - Math.PI) / Math.PI)
          const points = flipCount * 10 + airBoosts * 4 + Math.round(gracePoints * 8)
          game.score += points
          if (flipCount > game.bestFlip) {
            game.bestFlip = flipCount
            try { localStorage.setItem('ahoy_trampoline_best', String(flipCount)) } catch (e) { /* ignore */ }
            flashNewBest()
          }
          game.lastFlipCount = flipCount
          burstConfetti()
          emit('collect', { kind: 'flip', score: points })
        }
        flipCarry = 0
        spinVelocity *= 0.55
        ninja.rotation.x = 0
        ninja.rotation.z = 0
        resetNinjaParts()
      }
    }

    // Quadratic spring: deeper compression = more energy stored → higher skilled launches
    if (inMat) {
      const compression = Math.max(0, -bodyY)
      const springF = (90 + compression * 130) * compression
      const dampF = -9 * velocityY
      velocityY += (springF + dampF) * dt
      bodyY = Math.max(bodyY, -0.55)

      if (bodyY >= -0.01 && velocityY > 0) {
        inMat = false
        airTime = 0
        airBoosts = 0
        if (velocityY < 0.7) {
          game.airborne = false
          bodyY = 0
          velocityY = 0
          spinVelocity = 0
        }
      }
      if (Math.abs(velocityY) < 0.25 && compression < 0.04) {
        inMat = false
        game.airborne = false
        bodyY = 0
        velocityY = 0
        spinVelocity = 0
      }
    }
  } else if (!isRagdoll) {
    bodyY = Math.max(0, Math.sin(performance.now() * 0.004) * 0.05 + props.audioDrive * 0.08)
    spin = Math.sin(performance.now() * 0.003) * 0.04
    bodyX = lerp(bodyX, 0, dt * (isMobile ? 3.2 : 1.6))
  }

  if (isRagdoll) {
    ragdollTime += dt
    const collapseSpeed = 7.5
    game.height = 0
    
    // Fall on face: rotate body forward and down
    ninja.rotation.x = lerp(ninja.rotation.x, Math.PI / 2.05, dt * collapseSpeed)
    ninja.rotation.z = lerp(ninja.rotation.z, Math.PI * 0.12, dt * collapseSpeed)
    
    ninja.position.y = lerp(ninja.position.y, 0.16, dt * collapseSpeed)
    ninja.position.x = lerp(ninja.position.x, 0, dt * collapseSpeed)
    ninja.scale.set(1, 1, 1)
    
    // Collapse limbs and head forward/down
    if (ninjaParts.leftArm) {
      ninjaParts.leftArm.rotation.z = lerp(ninjaParts.leftArm.rotation.z, -1.9, dt * collapseSpeed)
      ninjaParts.leftArm.rotation.x = lerp(ninjaParts.leftArm.rotation.x, 0.6, dt * collapseSpeed)
    }
    if (ninjaParts.rightArm) {
      ninjaParts.rightArm.rotation.z = lerp(ninjaParts.rightArm.rotation.z, 1.9, dt * collapseSpeed)
      ninjaParts.rightArm.rotation.x = lerp(ninjaParts.rightArm.rotation.x, 0.6, dt * collapseSpeed)
    }
    if (ninjaParts.head) {
      ninjaParts.head.rotation.x = lerp(ninjaParts.head.rotation.x, 0.75, dt * collapseSpeed)
      ninjaParts.head.position.y = lerp(ninjaParts.head.position.y, 1.55, dt * collapseSpeed)
      ninjaParts.head.position.z = lerp(ninjaParts.head.position.z, 0.22, dt * collapseSpeed)
    }
    if (ninjaParts.leftLeg) {
      ninjaParts.leftLeg.rotation.x = lerp(ninjaParts.leftLeg.rotation.x, 0.65, dt * collapseSpeed)
    }
    if (ninjaParts.rightLeg) {
      ninjaParts.rightLeg.rotation.x = lerp(ninjaParts.rightLeg.rotation.x, -0.65, dt * collapseSpeed)
    }
  } else {
    game.height = Math.max(0, bodyY)
    const matDepth = inMat ? Math.max(0, -bodyY) : 0
    const arcLean = game.airborne ? Math.sin(clamp(airTime / 1.4, 0, 1) * Math.PI) : 0
    // Squash panda into mat as it sinks
    const matSquashY = inMat ? Math.max(0.72, 1 - matDepth * 1.1) : 1
    const matSquashX = inMat ? Math.min(1.28, 1 + matDepth * 0.7) : 1
    const squashY = matSquashY - takeoffSquash * 0.18
    const squashX = matSquashX + takeoffSquash * 0.12
    ninja.position.x = bodyX   // horizontal drift is now live
    ninja.position.y = 0.28 + bodyY
    ninja.rotation.x = spin
    ninja.rotation.z = Math.sin(spin * 0.5) * 0.16 + arcLean * 0.12
    ninja.scale.set(squashX, squashY, squashX)
  }

  // Trampoline reacts to compression; flashes warning when ninja drifts toward edge
  const matDepthVis = inMat ? Math.max(0, -bodyY) : 0
  trampoline.position.y = -matDepthVis * 0.55 - takeoffSquash * 0.06
  trampoline.scale.y = Math.max(0.45, 1 - matDepthVis * 1.1 - takeoffSquash * 0.1)
  trampoline.scale.x = 1 + matDepthVis * 0.18
  trampoline.scale.z = 1 + matDepthVis * 0.18
  const edgeDanger = clamp((Math.abs(bodyX) - 0.8) / (EDGE_LIMIT - 0.8), 0, 1)
  const matColor = edgeDanger > 0
    ? new THREE.Color(CMYK.cyan).lerp(new THREE.Color(0xff2fb8), edgeDanger)
    : (game.airborne || inMat) ? new THREE.Color(CMYK.cyan) : new THREE.Color(CMYK.black)
  trampolineMat.color.copy(matColor)

  // Blink
  blinkTimer += dt
  if (blinkTimer >= blinkInterval) {
    blinkTimer = 0
    blinkInterval = 2.5 + Math.random() * 3
    blinkDuration = 0.13
  }
  blinkDuration = Math.max(0, blinkDuration - dt)
  const eyesClosed = blinkDuration > 0
  if (ninjaParts.leftEyelid) ninjaParts.leftEyelid.visible = eyesClosed
  if (ninjaParts.rightEyelid) ninjaParts.rightEyelid.visible = eyesClosed

  // Smile — grows when flipping, relaxes when idle
  if (ninjaParts.mouth) {
    const smileTarget = (game.airborne && !inMat) ? 2.2 : 1.0
    const smileYTarget = (game.airborne && !inMat) ? 1.5 : 0.9
    ninjaParts.mouth.scale.x = lerp(ninjaParts.mouth.scale.x, smileTarget, dt * 7)
    ninjaParts.mouth.scale.y = lerp(ninjaParts.mouth.scale.y, smileYTarget, dt * 5)
  }

  camera.position.x = 0
  camera.position.y = 3.4 + game.height * 0.18 + landingBounce * 0.12
  camera.lookAt(0, 1.35 + game.height * 0.08, 0)

  for (const slash of slashes) {
    slash.phase += slash.drift * dt
    slash.mesh.position.x += Math.sin(slash.phase * 0.8) * dt * 0.14
    slash.mesh.position.y = 3 + Math.sin(slash.phase * 1.3) * 0.16
    slash.mesh.rotation.z += dt * 0.9
  }

  for (const item of confetti) {
    if (item.life <= 0) continue
    item.life -= dt
    item.velocity.y -= 5.8 * dt
    item.mesh.position.addScaledVector(item.velocity, dt)
    item.mesh.rotation.x += dt * 5
    item.mesh.rotation.z += dt * 7
    if (item.life <= 0) item.mesh.visible = false
  }

  // Spin trail — spawn a ghost copy every 0.05s during fast spins
  const absSpinV = Math.abs(spinVelocity)
  if (game.airborne && absSpinV > 6) {
    trailTimer -= dt
    if (trailTimer <= 0) {
      trailTimer = 0.05
      const ghost = ninja.clone()
      ghost.position.copy(ninja.position)
      ghost.rotation.copy(ninja.rotation)
      ghost.scale.copy(ninja.scale)
      ghost.traverse(c => {
        if (c.isMesh) {
          c.material = c.material.clone()
          c.material.transparent = true
          c.material.opacity = 0.35
          c.material.color.setHex(0x00d7ff)
        }
      })
      scene.add(ghost)
      trailMeshes.push({ mesh: ghost, life: 0.18 })
    }
  }
  for (let i = trailMeshes.length - 1; i >= 0; i--) {
    const t = trailMeshes[i]
    t.life -= dt
    t.mesh.traverse(c => { if (c.isMesh) c.material.opacity = Math.max(0, t.life / 0.18) * 0.35 })
    if (t.life <= 0) { scene.remove(t.mesh); trailMeshes.splice(i, 1) }
  }
}

function tick(now) {
  const dt = lastTime ? Math.min((now - lastTime) / 1000, 0.04) : 0
  lastTime = now

  updatePhysics(dt)
  renderer.render(scene, camera)

  statusAccumulator += dt
  if (statusAccumulator > 0.16) {
    statusAccumulator = 0
    emitStatus()
  }

  rafId = window.requestAnimationFrame(tick)
}

watch(
  () => props.controlIntent?.jumpToken,
  (next) => {
    if (!next || next === lastJumpToken) return
    lastJumpToken = next
    launchFlip()
  },
)

onMounted(() => {
  try {
    const saved = localStorage.getItem('ahoy_trampoline_best')
    if (saved) game.bestFlip = parseInt(saved, 10) || 0
  } catch (e) { /* ignore */ }
  buildScene()
  resize()
  resizeObserver = new ResizeObserver(resize)
  resizeObserver.observe(stageRef.value)
  emitStatus()
  rafId = window.requestAnimationFrame(tick)
})

onUnmounted(() => {
  if (rafId) window.cancelAnimationFrame(rafId)
  clearTimeout(newBestTimeout)
  clearTimeout(perfectTimeout)
  resizeObserver?.disconnect()
  renderer?.dispose()
  renderer?.domElement?.remove()
  scene?.traverse((object) => {
    object.geometry?.dispose?.()
    if (Array.isArray(object.material)) object.material.forEach((material) => material.dispose?.())
    else object.material?.dispose?.()
  })
})
</script>

<style scoped>
.trampoline-stage {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 100vh;
  overflow: hidden;
  background:
    radial-gradient(circle at 28% 30%, rgba(0, 215, 255, 0.22), transparent 18rem),
    radial-gradient(circle at 72% 26%, rgba(255, 47, 184, 0.20), transparent 20rem),
    linear-gradient(180deg, #05020c 0%, #11061e 100%);
  touch-action: manipulation;
  user-select: none;
}

.trampoline-stage canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  display: block;
}

.trampoline-stage-vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at 50% 72%, transparent 0 42%, rgba(255, 47, 184, 0.18) 100%);
}

.ninja-speed-lines,
.ninja-shuriken-field,
.ninja-smoke,
.ninja-jump-burst {
  position: absolute;
  pointer-events: none;
}

.ninja-speed-lines {
  inset: 0;
  opacity: 0;
  background:
    repeating-linear-gradient(
      104deg,
      transparent 0 8vw,
      rgba(0, 215, 255, 0.72) 8vw calc(8vw + 2px),
      transparent calc(8vw + 2px) 16vw
    );
  transition: opacity 0.18s ease;
}

.is-jumping .ninja-speed-lines {
  opacity: 0.34;
  animation: ninja-speed 0.34s linear infinite;
}

.ninja-smoke {
  z-index: 1;
  width: 14rem;
  height: 4.5rem;
  border-radius: 999px;
  background: rgba(0, 215, 255, 0.18);
  opacity: 0.85;
  filter: blur(6px);
}

.ninja-smoke--left {
  left: -1.5rem;
  top: 16%;
  animation: ninja-smoke-left 17s ease-in-out infinite;
}

.ninja-smoke--right {
  right: -1.8rem;
  top: 28%;
  animation: ninja-smoke-right 20s ease-in-out infinite;
}

.ninja-shuriken-field {
  inset: 0;
  z-index: 2;
  overflow: hidden;
}

.ninja-shuriken {
  --shuriken-color: #00d7ff;
  position: absolute;
  top: -10%;
  left: calc(var(--shuriken-x, 50) * 1%);
  width: 1.05rem;
  height: 1.05rem;
  transform: rotate(45deg);
  background: #0b0b0b;
  border: 2px solid var(--shuriken-color);
  box-shadow: 0 0 0 2px rgba(11, 11, 11, 0.65);
  animation: ninja-shuriken-fall var(--shuriken-speed, 8s) linear infinite;
  animation-delay: var(--shuriken-delay, 0s);
}

.ninja-shuriken::before,
.ninja-shuriken::after {
  content: "";
  position: absolute;
  inset: 24%;
  background: var(--shuriken-color);
}

.ninja-shuriken::after {
  transform: rotate(45deg);
}

.ninja-shuriken:nth-child(1) { --shuriken-x: 8;  --shuriken-color: #00d7ff; --shuriken-speed: 7s;   --shuriken-delay: -1s; }
.ninja-shuriken:nth-child(2) { --shuriken-x: 24; --shuriken-color: #ff2fb8; --shuriken-speed: 9s;   --shuriken-delay: -4s; }
.ninja-shuriken:nth-child(3) { --shuriken-x: 40; --shuriken-color: #ffd400; --shuriken-speed: 8s;   --shuriken-delay: -2s; }
.ninja-shuriken:nth-child(4) { --shuriken-x: 56; --shuriken-color: #00d7ff; --shuriken-speed: 10s;  --shuriken-delay: -7s; }
.ninja-shuriken:nth-child(5) { --shuriken-x: 72; --shuriken-color: #ff2fb8; --shuriken-speed: 7.4s; --shuriken-delay: -3s; }
.ninja-shuriken:nth-child(6) { --shuriken-x: 88; --shuriken-color: #ffd400; --shuriken-speed: 8.6s; --shuriken-delay: -5s; }

.ninja-jump-burst {
  left: 50%;
  top: 27%;
  z-index: 4;
  transform: translateX(-50%) rotate(-8deg);
  padding: 0.18rem 0.62rem 0.24rem;
  border: 3px solid #00d7ff;
  border-radius: 0.16rem;
  background: #ffd400;
  color: #0b0b0b;
  font-size: clamp(1.2rem, 4vw, 2.2rem);
  font-weight: 900;
  line-height: 1;
  text-transform: uppercase;
  box-shadow: 0 0 0 4px rgba(255, 47, 184, 0.32);
}

.trampoline-stage-score {
  position: absolute;
  left: 50%;
  top: 1rem;
  transform: translateX(-50%);
  z-index: 2;
  min-width: 7.5rem;
  padding: 0.45rem 0.8rem;
  border: 3px solid #00d7ff;
  border-radius: 0.22rem;
  background: #0b0b0b;
  color: #ffd400;
  text-align: center;
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.24);
}

.trampoline-stage-score span {
  display: block;
  font-size: 1rem;
  font-weight: 800;
  line-height: 1;
}


.perfect-banner {
  position: absolute;
  top: 7rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 8;
  padding: 0.28rem 0.75rem;
  border-radius: 999px;
  background: rgba(255, 212, 0, 0.15);
  color: #ffd400;
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.14em;
  pointer-events: none;
  white-space: nowrap;
}

.new-best-banner {
  position: absolute;
  top: 4.5rem;
  left: 50%;
  transform: translateX(-50%);
  z-index: 8;
  padding: 0.3rem 0.8rem;
  border-radius: 999px;
  background: rgba(0, 215, 255, 0.15);
  color: #00d7ff;
  font-size: 0.7rem;
  font-weight: 900;
  letter-spacing: 0.12em;
  pointer-events: none;
  white-space: nowrap;
}

.best-pop-enter-active { animation: best-in 0.2s ease-out; }
.best-pop-leave-active { transition: opacity 0.5s ease; }
.best-pop-leave-to     { opacity: 0; }

@keyframes best-in {
  from { transform: translateX(-50%) scale(0.8); opacity: 0; }
  to   { transform: translateX(-50%) scale(1);   opacity: 1; }
}

.ninja-burst-enter-active {
  animation: ninja-burst-in 0.16s ease-out;
}

.ninja-burst-leave-active {
  animation: ninja-burst-out 0.22s ease-in forwards;
}

@keyframes ninja-burst-in {
  from {
    opacity: 0;
    transform: translateX(-50%) rotate(-8deg) scale(0.7);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) rotate(-8deg) scale(1);
  }
}

@keyframes ninja-burst-out {
  to {
    opacity: 0;
    transform: translateX(-50%) translateY(-1.2rem) rotate(-3deg) scale(1.08);
  }
}

@keyframes ninja-speed {
  from { transform: translateY(0); }
  to { transform: translateY(4rem); }
}

@keyframes ninja-smoke-left {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(2rem); }
}

@keyframes ninja-smoke-right {
  0%, 100% { transform: translateX(0); }
  50% { transform: translateX(-2.2rem); }
}

@keyframes ninja-shuriken-fall {
  from {
    transform: translate3d(0, 0, 0) rotate(45deg);
  }
  to {
    transform: translate3d(-10vw, 112vh, 0) rotate(405deg);
  }
}

@media (max-width: 768px) {
  .trampoline-stage {
    min-height: 100dvh;
  }

  .trampoline-stage-score {
    top: 0.8rem;
    min-width: 6.7rem;
    padding: 0.4rem 0.68rem;
  }
}
</style>
