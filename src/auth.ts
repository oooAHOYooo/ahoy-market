import { createHash, randomBytes } from 'node:crypto';
import { FastifyInstance, FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';
import { config } from './config.js';
import { MarketStore, UserSession } from './db.js';

export function generatePkce() {
  const verifier = randomBytes(32).toString('base64url');
  const challenge = createHash('sha256').update(verifier).digest('base64url');
  return { verifier, challenge };
}

export const authRoutes = (store: MarketStore): FastifyPluginAsync => async (app: FastifyInstance) => {
  // In-memory PKCE state cache (expires after 10 min)
  const pkceCache = new Map<string, { verifier: string; returnTo: string; createdAt: number }>();

  // Helper to extract session from request
  const getSessionFromRequest = (request: FastifyRequest): UserSession | null => {
    // 1. Try Bearer token
    const authHeader = request.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const token = authHeader.substring(7);
      const sess = store.getSession(token);
      if (sess) return sess;
    }

    // 2. Try Cookie
    const cookieToken = request.cookies['ahoy_market_session'];
    if (cookieToken) {
      const sess = store.getSession(cookieToken);
      if (sess) return sess;
    }

    // 3. Header fallback for testing or trusted gateway (dev mode)
    if (!config.isProduction) {
      const xAhoyId = request.headers['x-ahoy-id'];
      if (typeof xAhoyId === 'string' && xAhoyId.startsWith('ahoy_')) {
        return {
          id: 'dev_sess',
          session_token: 'dev_token',
          ahoy_id: xAhoyId,
          email: 'dev@ahoy.ooo',
          name: 'Dev User',
          access_token: null,
          expires_at: new Date(Date.now() + 86400000).toISOString(),
          created_at: new Date().toISOString(),
        };
      }
    }

    return null;
  };

  // GET /api/auth/login -> Redirects to AHOY ID OAuth
  app.get('/api/auth/login', async (request: FastifyRequest<{ Querystring: { return_to?: string } }>, reply: FastifyReply) => {
    const { verifier, challenge } = generatePkce();
    const state = randomBytes(16).toString('base64url');
    const returnTo = request.query.return_to || '/';

    pkceCache.set(state, {
      verifier,
      returnTo,
      createdAt: Date.now(),
    });

    // Cleanup old cache entries
    const now = Date.now();
    for (const [k, v] of pkceCache.entries()) {
      if (now - v.createdAt > 600_000) pkceCache.delete(k);
    }

    const authUrl = new URL(`${config.ahoyIdUrl}/oauth/authorize`);
    authUrl.searchParams.set('response_type', 'code');
    authUrl.searchParams.set('client_id', config.clientId);
    authUrl.searchParams.set('redirect_uri', config.redirectUri);
    authUrl.searchParams.set('scope', 'openid profile email');
    authUrl.searchParams.set('code_challenge', challenge);
    authUrl.searchParams.set('code_challenge_method', 'S256');
    authUrl.searchParams.set('state', state);

    return reply.redirect(authUrl.toString());
  });

  // GET /api/auth/callback -> Handles OAuth PKCE callback from AHOY ID
  app.get('/api/auth/callback', async (request: FastifyRequest<{ Querystring: { code?: string; state?: string; error?: string } }>, reply: FastifyReply) => {
    const { code, state, error } = request.query;

    if (error) {
      return reply.redirect(`/?auth_error=${encodeURIComponent(error)}`);
    }

    if (!code || !state) {
      return reply.redirect('/?auth_error=missing_code_or_state');
    }

    const stateData = pkceCache.get(state);
    if (!stateData) {
      return reply.redirect('/?auth_error=invalid_state');
    }
    pkceCache.delete(state);

    try {
      // Exchange code for token with AHOY ID
      const tokenResponse = await fetch(`${config.ahoyIdUrl}/oauth/token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          grant_type: 'authorization_code',
          code,
          redirect_uri: config.redirectUri,
          client_id: config.clientId,
          code_verifier: stateData.verifier,
        }),
      });

      if (!tokenResponse.ok) {
        const errBody = await tokenResponse.text();
        console.error('Token exchange error:', errBody);
        return reply.redirect('/?auth_error=token_exchange_failed');
      }

      const tokenData = await tokenResponse.json() as { access_token?: string; ahoy_id?: string; user?: { id?: string; email?: string; name?: string } };
      const accessToken = tokenData.access_token;

      // Fetch user profile from AHOY ID
      let ahoyId = tokenData.ahoy_id || tokenData.user?.id;
      let email = tokenData.user?.email || null;
      let name = tokenData.user?.name || null;

      if (!ahoyId && accessToken) {
        const userinfoRes = await fetch(`${config.ahoyIdUrl}/oauth/userinfo`, {
          headers: { Authorization: `Bearer ${accessToken}` },
        });
        if (userinfoRes.ok) {
          const userInfo = await userinfoRes.json() as { sub?: string; id?: string; ahoy_id?: string; email?: string; name?: string };
          ahoyId = userInfo.ahoy_id || userInfo.sub || userInfo.id;
          email = userInfo.email || email;
          name = userInfo.name || name;
        }
      }

      if (!ahoyId) {
        return reply.redirect('/?auth_error=no_ahoy_id');
      }

      // Create session in market database
      const session = store.saveSession({
        ahoy_id: ahoyId,
        email,
        name,
        access_token: accessToken || null,
        expiresInDays: 30,
      });

      // Set cookie
      reply.setCookie('ahoy_market_session', session.session_token, {
        path: '/',
        httpOnly: true,
        secure: config.isProduction,
        sameSite: 'lax',
        maxAge: 30 * 86400,
      });

      return reply.redirect(stateData.returnTo || '/');
    } catch (err) {
      console.error('Callback exception:', err);
      return reply.redirect('/?auth_error=callback_exception');
    }
  });

  // GET /api/auth/me -> Returns current user profile and session status
  app.get('/api/auth/me', async (request: FastifyRequest, reply: FastifyReply) => {
    const session = getSessionFromRequest(request);
    if (!session) {
      return reply.code(200).send({
        authenticated: false,
        user: null,
      });
    }

    const entitlements = store.getEntitlements(session.ahoy_id);

    return {
      authenticated: true,
      user: {
        ahoy_id: session.ahoy_id,
        email: session.email,
        name: session.name,
      },
      entitlement_count: entitlements.length,
    };
  });

  // POST /api/auth/logout
  app.post('/api/auth/logout', async (request: FastifyRequest, reply: FastifyReply) => {
    const cookieToken = request.cookies['ahoy_market_session'];
    if (cookieToken) {
      store.deleteSession(cookieToken);
    }
    reply.clearCookie('ahoy_market_session', { path: '/' });
    return { success: true };
  });

  // Local testing login helper (for unit testing and local development)
  app.post('/api/auth/dev-login', async (request: FastifyRequest<{ Body: { ahoy_id?: string; email?: string; name?: string } }>, reply: FastifyReply) => {
    if (config.isProduction) {
      return reply.code(403).send({ error: 'forbidden_in_production' });
    }

    const ahoyId = request.body?.ahoy_id || `ahoy_dev_${randomBytes(8).toString('hex')}`;
    const session = store.saveSession({
      ahoy_id: ahoyId,
      email: request.body?.email || 'test@ahoy.ooo',
      name: request.body?.name || 'Sovereign Test Sailor',
    });

    reply.setCookie('ahoy_market_session', session.session_token, {
      path: '/',
      httpOnly: true,
      secure: false,
      sameSite: 'lax',
      maxAge: 30 * 86400,
    });

    return {
      success: true,
      session_token: session.session_token,
      user: {
        ahoy_id: session.ahoy_id,
        email: session.email,
        name: session.name,
      },
    };
  });
};
