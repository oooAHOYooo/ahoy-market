import { mkdirSync, readdirSync, copyFileSync, cpSync } from 'node:fs'
import { join, resolve } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = resolve(fileURLToPath(import.meta.url), '../../..')
const pub = resolve(fileURLToPath(import.meta.url), '../..')

const dataOut = join(pub, 'public/static/data')
const imgOut = join(pub, 'public/static/img')

mkdirSync(dataOut, { recursive: true })
mkdirSync(imgOut, { recursive: true })

// Copy *.json from static/data
const dataIn = join(root, 'static/data')
for (const file of readdirSync(dataIn)) {
  if (file.endsWith('.json')) copyFileSync(join(dataIn, file), join(dataOut, file))
}

// Copy all of static/img (recursive)
cpSync(join(root, 'static/img'), imgOut, { recursive: true })

console.log('prebuild: static assets copied')
