import { FastifyInstance, FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { MarketStore, UserSession } from '../db.js';
import { config } from '../config.js';

const purchaseInput = z.object({
  release_id: z.string().min(1),
  track_id: z.string().optional(),
  amount_cents: z.number().int().positive().optional(),
  payment_method: z.enum(['instant_sovereign', 'test_card', 'stripe']).default('instant_sovereign'),
  recipient_ahoy_id: z.string().optional(),
  format: z.enum(['digital_master', 'nfc_card', 'burned_cd']).default('digital_master'),
  shipping: z.object({
    name: z.string().min(1).optional(),
    address: z.string().min(1).optional(),
    city: z.string().min(1).optional(),
    state: z.string().min(1).optional(),
    zip: z.string().min(1).optional(),
    country: z.string().default('US').optional(),
    inscription_note: z.string().max(500).optional(),
  }).optional(),
});

const boostInput = z.object({
  artist_slug: z.string().min(1),
  amount_cents: z.number().int().min(50, 'Minimum boost is $0.50'),
  supporter_name: z.string().max(100).optional(),
  message: z.string().max(500).optional(),
  payment_method: z.enum(['instant_sovereign', 'test_card', 'stripe']).default('instant_sovereign'),
});

export const storeRoutes = (store: MarketStore): FastifyPluginAsync => async (app: FastifyInstance) => {
  // Helper to extract session or ahoy_id from request
  const getAuthUser = (request: FastifyRequest): { ahoy_id: string; email?: string | null; name?: string | null } | null => {
    // 1. Bearer Token
    const authHeader = request.headers.authorization;
    if (authHeader && authHeader.startsWith('Bearer ')) {
      const sess = store.getSession(authHeader.substring(7));
      if (sess) return { ahoy_id: sess.ahoy_id, email: sess.email, name: sess.name };
    }

    // 2. Cookie
    const cookieToken = request.cookies['ahoy_market_session'];
    if (cookieToken) {
      const sess = store.getSession(cookieToken);
      if (sess) return { ahoy_id: sess.ahoy_id, email: sess.email, name: sess.name };
    }

    // 3. Header (e.g. from AHOY Player with user's verified ahoy_id)
    const xAhoyId = request.headers['x-ahoy-id'];
    if (typeof xAhoyId === 'string' && /^ahoy_[A-Za-z0-9_-]{3,}$/.test(xAhoyId)) {
      return { ahoy_id: xAhoyId };
    }

    return null;
  };

  // GET /api/releases -> List all available releases in store
  app.get('/api/releases', async () => {
    const releases = store.getReleases();
    return {
      releases: releases.map(r => store.getRelease(r.id)),
    };
  });

  // GET /api/releases/:idOrSlug -> Get single release
  app.get('/api/releases/:idOrSlug', async (request: FastifyRequest<{ Params: { idOrSlug: string } }>, reply: FastifyReply) => {
    const release = store.getRelease(request.params.idOrSlug);
    if (!release) return reply.code(404).send({ error: 'release_not_found' });
    return { release };
  });

  // GET /api/artists -> List artists with boost totals
  app.get('/api/artists', async () => {
    const artists = store.getArtists();
    return { artists };
  });

  // GET /api/artists/:idOrSlug -> Get single artist with releases & stats
  app.get('/api/artists/:idOrSlug', async (request: FastifyRequest<{ Params: { idOrSlug: string } }>, reply: FastifyReply) => {
    const artist = store.getArtist(request.params.idOrSlug);
    if (!artist) return reply.code(404).send({ error: 'artist_not_found' });
    return { artist };
  });

  // GET /api/artists/:slug/boosts -> Get recent boosts for an artist
  app.get('/api/artists/:slug/boosts', async (request: FastifyRequest<{ Params: { slug: string }; Querystring: { limit?: string } }>, reply: FastifyReply) => {
    const limit = parseInt(request.query.limit || '20', 10);
    const boosts = store.getArtistBoosts(request.params.slug, limit);
    return {
      artist_slug: request.params.slug,
      count: boosts.length,
      boosts,
    };
  });

  // POST /api/boost -> Boost / Tip an artist directly with AHOY ID
  app.post('/api/boost', async (request: FastifyRequest, reply: FastifyReply) => {
    const auth = getAuthUser(request);
    if (!auth) {
      return reply.code(401).send({
        error: 'authentication_required',
        message: 'You must sign in with your Sovereign AHOY ID to boost an artist.',
        login_url: `${config.publicBaseUrl}/api/auth/login`,
      });
    }

    const parsed = boostInput.safeParse(request.body);
    if (!parsed.success) {
      return reply.code(400).send({ error: 'invalid_boost_payload', details: parsed.error.format() });
    }

    const artist = store.getArtist(parsed.data.artist_slug);
    if (!artist) {
      return reply.code(404).send({ error: 'artist_not_found' });
    }

    const supporterName = parsed.data.supporter_name || auth.name || auth.ahoy_id;
    const boost = store.recordBoost({
      ahoy_id: auth.ahoy_id,
      artist_slug: artist.slug,
      amount_cents: parsed.data.amount_cents,
      supporter_name: supporterName,
      message: parsed.data.message || null,
      payment_method: parsed.data.payment_method,
    });

    const userStats = store.getUserBoostStats(auth.ahoy_id);

    return reply.code(201).send({
      success: true,
      boost,
      artist: {
        slug: artist.slug,
        name: artist.name,
      },
      user_stats: userStats,
    });
  });

  // GET /api/me/boost-stats -> Get user's total boost patronage & badge
  app.get('/api/me/boost-stats', async (request: FastifyRequest<{ Querystring: { ahoy_id?: string } }>, reply: FastifyReply) => {
    const auth = getAuthUser(request);
    const queryAhoyId = request.query.ahoy_id;
    const effectiveAhoyId = queryAhoyId || auth?.ahoy_id;

    if (!effectiveAhoyId) {
      return reply.code(401).send({ error: 'authentication_required' });
    }

    const stats = store.getUserBoostStats(effectiveAhoyId);
    return { stats };
  });

  // GET /api/leaderboard/boosters -> Global top patrons leaderboard
  app.get('/api/leaderboard/boosters', async (request: FastifyRequest<{ Querystring: { limit?: string } }>) => {
    const limit = parseInt(request.query.limit || '10', 10);
    const leaderboard = store.getGlobalBoostersLeaderboard(limit);
    return {
      leaderboard,
    };
  });

  // POST /api/checkout/purchase -> Buy a song or album with AHOY ID
  app.post('/api/checkout/purchase', async (request: FastifyRequest, reply: FastifyReply) => {
    const auth = getAuthUser(request);
    if (!auth) {
      return reply.code(401).send({
        error: 'authentication_required',
        message: 'You must sign in with your AHOY ID to purchase music.',
        login_url: `${config.publicBaseUrl}/api/auth/login`,
      });
    }

    const parsed = purchaseInput.safeParse(request.body);
    if (!parsed.success) {
      return reply.code(400).send({ error: 'invalid_purchase_payload', details: parsed.error.format() });
    }

    const release = store.getRelease(parsed.data.release_id);
    if (!release) {
      return reply.code(404).send({ error: 'release_not_found' });
    }

    const amountCents = parsed.data.amount_cents || release.price_cents;
    const paymentRef = `pay_${Date.now()}_${Math.random().toString(36).substring(2, 8)}`;
    const recipientAhoyId = parsed.data.recipient_ahoy_id?.trim() || null;

    const { purchaseId, entitlementCount, grantedTo, format, fulfillmentStatus } = store.recordPurchase({
      ahoy_id: auth.ahoy_id,
      recipient_ahoy_id: recipientAhoyId,
      email: auth.email,
      release_id: release.id,
      track_id: parsed.data.track_id || null,
      amount_cents: amountCents,
      payment_method: parsed.data.payment_method,
      payment_ref: paymentRef,
      format: parsed.data.format,
      shipping: parsed.data.shipping,
    });

    const isTransfer = Boolean(recipientAhoyId && recipientAhoyId !== auth.ahoy_id);

    return reply.code(201).send({
      success: true,
      purchase_id: purchaseId,
      ahoy_id: auth.ahoy_id,
      granted_to: grantedTo,
      is_transfer: isTransfer,
      format,
      fulfillment_status: fulfillmentStatus,
      release: {
        id: release.id,
        title: release.title,
        artist: release.artist,
      },
      entitlement_count: entitlementCount,
      player_url: `${config.playerUrl}?ahoy_id=${encodeURIComponent(grantedTo)}`,
    });
  });

  // GET /api/me/library -> Get user's purchased songs
  app.get('/api/me/library', async (request: FastifyRequest, reply: FastifyReply) => {
    const auth = getAuthUser(request);
    if (!auth) {
      return reply.code(401).send({ error: 'authentication_required' });
    }

    const entitlements = store.getEntitlements(auth.ahoy_id);
    return {
      ahoy_id: auth.ahoy_id,
      tracks: entitlements,
    };
  });

  // GET /api/entitlements -> Public/Player Entitlements query
  // Player at player.ahoy.ooo calls this with `?ahoy_id=...` or `x-ahoy-id`
  app.get('/api/entitlements', async (request: FastifyRequest<{ Querystring: { ahoy_id?: string } }>, reply: FastifyReply) => {
    const queryAhoyId = request.query.ahoy_id;
    const auth = getAuthUser(request);
    const effectiveAhoyId = queryAhoyId || auth?.ahoy_id;

    if (!effectiveAhoyId) {
      return reply.code(400).send({
        error: 'missing_ahoy_id',
        message: 'Provide ahoy_id query parameter or authenticate with AHOY ID.',
      });
    }

    const entitlements = store.getEntitlements(effectiveAhoyId);
    return {
      ahoy_id: effectiveAhoyId,
      count: entitlements.length,
      tracks: entitlements.map(e => ({
        id: e.track_id,
        title: e.title,
        artist: e.artist,
        artwork_url: e.artwork_url,
        stream_url: `${config.publicBaseUrl}/api/stream/${e.track_id}?ahoy_id=${encodeURIComponent(effectiveAhoyId)}`,
        direct_audio_url: e.full_audio_url,
        duration_seconds: e.duration_seconds,
        unlocked_at: e.granted_at,
        source: 'market.ahoy.ooo',
      })),
    };
  });

  // GET /api/stream/:trackId -> Stream audio for entitled user
  app.get('/api/stream/:trackId', async (request: FastifyRequest<{ Params: { trackId: string }; Querystring: { ahoy_id?: string } }>, reply: FastifyReply) => {
    const { trackId } = request.params;
    const track = store.getTrack(trackId);
    if (!track) return reply.code(404).send({ error: 'track_not_found' });

    const auth = getAuthUser(request);
    const queryAhoyId = request.query.ahoy_id;
    const effectiveAhoyId = auth?.ahoy_id || queryAhoyId;

    const isEntitled = effectiveAhoyId ? store.hasEntitlement(effectiveAhoyId, trackId) : false;

    if (isEntitled) {
      return reply.redirect(track.full_audio_url);
    }

    // If not entitled, fallback to preview
    return reply.redirect(track.preview_url);
  });

  // GET /api/download/:trackId -> Download raw audio file for entitled user
  app.get('/api/download/:trackId', async (request: FastifyRequest<{ Params: { trackId: string }; Querystring: { ahoy_id?: string } }>, reply: FastifyReply) => {
    const { trackId } = request.params;
    const track = store.getTrack(trackId);
    if (!track) return reply.code(404).send({ error: 'track_not_found' });

    const auth = getAuthUser(request);
    const queryAhoyId = request.query.ahoy_id;
    const effectiveAhoyId = auth?.ahoy_id || queryAhoyId;

    const isEntitled = effectiveAhoyId ? store.hasEntitlement(effectiveAhoyId, trackId) : false;
    if (!isEntitled) {
      return reply.code(403).send({
        error: 'entitlement_required',
        message: 'You must own this release to download the master audio file.',
      });
    }

    // Set download headers and redirect to full audio
    const filename = `${track.artist} - ${track.title}.mp3`.replace(/[/\\?%*:|"<>]/g, '-');
    reply.header('Content-Disposition', `attachment; filename="${encodeURIComponent(filename)}"`);
    return reply.redirect(track.full_audio_url);
  });
};
