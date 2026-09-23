import path from 'node:path';
import { fileURLToPath } from 'node:url';
import Fastify, { FastifyInstance } from 'fastify';
import cookie from '@fastify/cookie';
import cors from '@fastify/cors';
import fastifyStatic from '@fastify/static';
import { MarketStore } from './db.js';
import { config } from './config.js';
import { authRoutes } from './auth.js';
import { storeRoutes } from './routes/store.js';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

export function buildApp(storeOption?: MarketStore): FastifyInstance {
  const store = storeOption || new MarketStore(config.databasePath);
  const app = Fastify({ logger: false });

  // Plugins
  app.register(cors, {
    origin: true,
    credentials: true,
  });

  app.register(cookie, {
    secret: config.cookieSecret,
  });

  // Serve static files from public/
  const publicDir = path.resolve(__dirname, '../public');
  app.register(fastifyStatic, {
    root: publicDir,
    prefix: '/',
  });

  // Health check
  const healthHandler = async () => ({
    status: 'ok',
    service: 'ahoy-market',
    version: '0.1.0',
    ahoy_id_service: config.ahoyIdUrl,
  });
  app.get('/health', healthHandler);
  app.get('/ops/selftest', healthHandler);

  // Register API routes
  app.register(authRoutes(store));
  app.register(storeRoutes(store));

  app.addHook('onClose', () => {
    if (!storeOption) store.close();
  });

  return app;
}
