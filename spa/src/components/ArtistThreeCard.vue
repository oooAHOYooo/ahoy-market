<template>
  <div 
    ref="container" 
    class="three-container" 
    @mousemove="handleMouseMove" 
    @mouseleave="handleMouseLeave"
  ></div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import * as THREE from 'three'

const props = defineProps({
  imageUrl: { type: String, required: true }
})

const container = ref(null)
let scene, camera, renderer, mesh, light
let clock = new THREE.Clock()
let animationId = null

const targetRotation = { x: 0, y: 0 }
const currentRotation = { x: 0, y: 0 }

function init() {
  if (!container.value) return
  
  // Standardized bounding box for 3D rendering
  const width = container.value.clientWidth || 220
  const height = container.value.clientHeight || 220

  scene = new THREE.Scene()
  
  camera = new THREE.PerspectiveCamera(45, width / height, 0.1, 1000)
  camera.position.z = 5

  renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true })
  renderer.setSize(width, height)
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
  container.value.appendChild(renderer.domElement)

  // Simple ambient lighting for soft global illumination
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.8)
  scene.add(ambientLight)
  
  light = new THREE.DirectionalLight(0xffffff, 0.6)
  light.position.set(2, 2, 4)
  scene.add(light)

  // Construct rounded rectangle for smooth 3D card edges
  const shape = new THREE.Shape()
  const size = 3.2
  const radius = 0.35
  const x = -size/2, y = -size/2
  
  shape.moveTo(x, y + radius)
  shape.lineTo(x, y + size - radius)
  shape.quadraticCurveTo(x, y + size, x + radius, y + size)
  shape.lineTo(x + size - radius, y + size)
  shape.quadraticCurveTo(x + size, y + size, x + size, y + size - radius)
  shape.lineTo(x + size, y + radius)
  shape.quadraticCurveTo(x + size, y, x + size - radius, y)
  shape.lineTo(x + radius, y)
  shape.quadraticCurveTo(x, y, x, y + radius)

  const geometry = new THREE.ShapeGeometry(shape, 32)
  
  // Explicit UV generation so the texture stretches seamlessly across the generated shape
  const pos = geometry.attributes.position
  const bBox = new THREE.Box3().setFromObject(new THREE.Mesh(geometry))
  const uvAttribute = new THREE.BufferAttribute(new Float32Array(pos.count * 2), 2)
  for (let i = 0; i < pos.count; i++) {
    uvAttribute.setXY(i, 
      (pos.getX(i) - bBox.min.x) / (bBox.max.x - bBox.min.x),
      (pos.getY(i) - bBox.min.y) / (bBox.max.y - bBox.min.y)
    )
  }
  geometry.setAttribute('uv', uvAttribute)

  const material = new THREE.MeshStandardMaterial({
    color: 0xffffff,
    roughness: 0.3,
    metalness: 0.1,
    side: THREE.DoubleSide,
    transparent: true,
    opacity: 0
  })

  mesh = new THREE.Mesh(geometry, material)
  scene.add(mesh)

  loadTexture(props.imageUrl)
  animate()
}

const textureCache = new Map()

function loadTexture(url) {
  if (!mesh) return
  
  const loader = new THREE.TextureLoader()
  loader.setCrossOrigin('anonymous')
  
  // Trigger exit/reset animation state
  mesh.scale.set(0.4, 0.4, 0.4)
  mesh.material.opacity = 0
  
  // Short timeout delay gives viewer transition cycles breathing room
  const startTransition = (tex) => {
    mesh.material.map = tex
    mesh.material.needsUpdate = true
    
    let start = Date.now()
    const duration = 750
    
    function runIntro() {
      const elapsed = Date.now() - start
      const t = Math.min(elapsed / duration, 1)
      
      // Optimized elastic/bouncy overshoot function for premium physics feeling
      const c1 = 1.70158
      const c3 = c1 + 1
      const bounce = 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2)
      
      mesh.scale.set(bounce, bounce, bounce)
      mesh.material.opacity = Math.min(t * 1.5, 1)
      
      if (t < 1) requestAnimationFrame(runIntro)
    }
    requestAnimationFrame(runIntro)
  }

  if (textureCache.has(url)) {
    startTransition(textureCache.get(url))
  } else {
    loader.load(url, (tex) => {
      tex.colorSpace = THREE.SRGBColorSpace
      tex.minFilter = THREE.LinearFilter
      textureCache.set(url, tex)
      startTransition(tex)
    }, undefined, () => {
      // Catch async failure gracefully
      mesh.material.color.setHex(0x1a1a1a)
      mesh.material.opacity = 1
      mesh.scale.set(1, 1, 1)
    })
  }
}

function handleMouseMove(e) {
  if (!container.value) return
  const rect = container.value.getBoundingClientRect()
  const x = (e.clientX - rect.left) / rect.width * 2 - 1
  const y = -((e.clientY - rect.top) / rect.height * 2 - 1)
  
  // Moderate rotation threshold for subtle reactive depth
  targetRotation.y = x * 0.35
  targetRotation.x = y * 0.35
}

function handleMouseLeave() {
  targetRotation.x = 0
  targetRotation.y = 0
}

function animate() {
  animationId = requestAnimationFrame(animate)
  if (mesh) {
    const time = clock.getElapsedTime()
    
    // Low-pass smoothing interpolation for rotational friction/momentum
    currentRotation.x += (targetRotation.x - currentRotation.x) * 0.08
    currentRotation.y += (targetRotation.y - currentRotation.y) * 0.08
    
    // Combined parametric sine oscillations for organic float
    mesh.position.y = Math.sin(time * 2.2) * 0.04
    mesh.rotation.x = currentRotation.x
    mesh.rotation.y = currentRotation.y
    mesh.rotation.z = Math.cos(time * 1.2) * 0.015
  }
  if (renderer && scene && camera) {
    renderer.render(scene, camera)
  }
}

function handleResize() {
  if (!container.value || !camera || !renderer) return
  const width = container.value.clientWidth
  const height = container.value.clientHeight
  if (width === 0 || height === 0) return
  camera.aspect = width / height
  camera.updateProjectionMatrix()
  renderer.setSize(width, height)
}

watch(() => props.imageUrl, (newVal) => {
  loadTexture(newVal)
})

onMounted(() => {
  // Brief microtask delay so computed dom sizes execute first
  setTimeout(init, 60)
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (animationId) cancelAnimationFrame(animationId)
  if (renderer) {
    renderer.dispose()
    if (renderer.domElement?.parentNode) {
      renderer.domElement.parentNode.removeChild(renderer.domElement)
    }
  }
  if (mesh) {
    mesh.geometry.dispose()
    mesh.material.dispose()
  }
  textureCache.forEach(t => t.dispose())
  textureCache.clear()
})
</script>

<style scoped>
.three-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: visible;
  position: relative;
}

/* Soft contextual backglow */
.three-container::after {
  content: '';
  position: absolute;
  width: 55%;
  height: 55%;
  background: radial-gradient(circle, rgba(109, 220, 255, 0.22) 0%, transparent 68%);
  z-index: -1;
  pointer-events: none;
  transform: translateZ(-1px);
}
</style>
