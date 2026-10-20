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

  // Preserve Stripe's exact signed bytes while keeping normal JSON parsing for API routes.
  app.removeContentTypeParser('application/json');
  app.addContentTypeParser('application/json', { parseAs: 'buffer' }, (request, body, done) => {
    try {
      if (request.url.startsWith('/api/stripe/webhook')) (request as typeof request & { rawBody: Buffer }).rawBody = body as Buffer;
      done(null, JSON.parse((body as Buffer).toString('utf8')));
    } catch (error) { done(error as Error); }
  });

  // Plugins
  const allowedOrigins = new Set([
    config.publicBaseUrl,
    config.playerUrl,
    config.streamerUrl,
    config.ahoyIdUrl,
  ]);

  app.register(cors, {
    origin: (origin, cb) => {
      // Allow requests with no origin (e.g. server-to-server, curl, mobile native)
      if (!origin) return cb(null, true);
      if (allowedOrigins.has(origin)) return cb(null, true);
      // In development / test mode, allow loopback origins
      if (!config.isProduction) {
        try {
          const parsed = new URL(origin);
          if (parsed.hostname === 'localhost' || parsed.hostname === '127.0.0.1') {
            return cb(null, true);
          }
        } catch {
          // Fall through to reject
        }
      }
      return cb(null, false);
    },
    credentials: true,
  });

  // Standard HTTP security response headers
  app.addHook('onSend', async (_request, reply) => {
    reply.header('X-Content-Type-Options', 'nosniff');
    reply.header('X-Frame-Options', 'SAMEORIGIN');
    reply.header('Referrer-Policy', 'strict-origin-when-cross-origin');
    reply.header('X-XSS-Protection', '0');
  });

  app.register(cookie, {
    secret: config.cookieSecret,
  });

  // Serve static files from public/ with browser asset caching
  const publicDir = path.resolve(__dirname, '../public');
  app.register(fastifyStatic, {
    root: publicDir,
    prefix: '/',
    cacheControl: false,
    setHeaders: (res, filePath) => {
      if (filePath.endsWith('.html') || filePath.endsWith('sw.js') || filePath.endsWith('manifest.json')) {
        res.setHeader('Cache-Control', 'no-cache');
      } else {
        res.setHeader('Cache-Control', 'public, max-age=86400, stale-while-revalidate=604800');
      }
    },
  });

  // Health and readiness checks with database probe
  const healthHandler = async (_request: unknown, reply: { code: (n: number) => { send: (payload: unknown) => unknown } }) => {
    try {
      const dbHealthy = store.checkHealth();
      if (!dbHealthy) {
        return reply.code(503).send({ status: 'unhealthy', service: 'ahoy-market', database: 'disconnected' });
      }
      return {
        status: 'ok',
        service: 'ahoy-market',
        version: '0.1.0',
        database: 'connected',
        ahoy_id_service: config.ahoyIdUrl,
      };
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'database_error';
      return reply.code(503).send({ status: 'unhealthy', service: 'ahoy-market', error: message });
    }
  };
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
