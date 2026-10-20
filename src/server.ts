import { buildApp } from './app.js';
import { config } from './config.js';

const app = buildApp();

async function start() {
  try {
    const address = await app.listen({ port: config.port, host: config.host });
    console.log(`🌊 AHOY Market listening at ${address}`);
    console.log(`🔑 Connected to AHOY ID at: ${config.ahoyIdUrl}`);
    console.log(`🎵 Player link target: ${config.playerUrl}`);
  } catch (err) {
    console.error('Failed to start AHOY Market:', err);
    process.exit(1);
  }
}

for (const signal of ['SIGINT', 'SIGTERM'] as const) {
  process.on(signal, async () => {
    console.log(`\n🌊 Received ${signal}, closing server gracefully...`);
    try {
      await app.close();
      process.exit(0);
    } catch (err) {
      console.error('Error during shutdown:', err);
      process.exit(1);
    }
  });
}

start();
