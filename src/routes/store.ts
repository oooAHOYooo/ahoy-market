import { FastifyInstance, FastifyPluginAsync, FastifyRequest, FastifyReply } from 'fastify';
import { z } from 'zod';
import { MarketStore, UserSession } from '../db.js';
import { config } from '../config.js';
import { createHmac, timingSafeEqual } from 'node:crypto';
import { Readable } from 'node:stream';

const purchaseInput = z.object({
  release_id: z.string().min(1),
  track_id: z.string().optional(),
  amount_cents: z.number().int().positive().optional(),
  payment_method: z.enum(['instant_sovereign', 'test_card', 'stripe']).default('instant_sovereign'),
  recipient_ahoy_id: z.string().optional(),
  format: z.enum(['digital_master', 'usb_album', 'burned_cd', 'nfc_card']).default('digital_master'),
  shipping: z.object({
    name: z.string().min(1).optional(),
    address: z.string().min(1).optional(),
    city: z.string().min(1).optional(),
    state: z.string().min(1).optional(),
    zip: z.string().min(1).optional(),
    inscription_note: z.string().max(500).optional(),
  }).optional(),
});

const burnedCdInput = z.object({
  cd_title: z.string().max(100).optional(),
  track_ids: z.array(z.string().min(1)).min(1, 'Burned CD must contain at least 1 track'),
  marker_color: z.string().max(50).optional(),
  payment_method: z.enum(['instant_sovereign', 'test_card', 'stripe']).default('instant_sovereign'),
  recipient_ahoy_id: z.string().optional(),
  shipping: z.object({
    name: z.string().min(1, 'Recipient name is required'),
    address: z.string().min(1, 'Street address is required'),
    city: z.string().min(1, 'City is required'),
    state: z.string().min(1, 'State is required'),
    zip: z.string().min(1, 'ZIP is required'),
    country: z.string().default('US').optional(),
    inscription_note: z.string().max(500).optional(),
  }),
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
    if (!config.isProduction && typeof xAhoyId === 'string' && /^ahoy_[A-Za-z0-9_-]{3,}$/.test(xAhoyId)) {
      return { ahoy_id: xAhoyId };
    }

    return null;
  };

  // GET /api/market/latest -> Combined initial/latest market state in 1 round trip
  app.get('/api/market/latest', async (request: FastifyRequest) => {
    const auth = getAuthUser(request);
    const releases = store.getReleasesWithTracks();
    const artists = store.getArtists().map(({ total_boost_cents: _total, boost_count: _count, ...artist }) => artist);
    const leaderboard = store.getGlobalBoostersLeaderboard(10)
      .map(({ total_cents: _total, boost_count: _count, rank: _rank, ...supporter }) => supporter)
      .sort((a, b) => a.supporter_name.localeCompare(b.supporter_name));
    const library = auth ? store.getEntitlements(auth.ahoy_id) : [];
    const boostStats = auth ? store.getUserBoostStats(auth.ahoy_id) : null;

    return {
      user: auth ? { authenticated: true, user: auth } : { authenticated: false },
      releases,
      artists,
      leaderboard,
      library,
      boost_stats: boostStats,
    };
  });

  // GET /api/releases -> List all available releases in store
  app.get('/api/releases', async () => {
    const releases = store.getReleasesWithTracks();
    return { releases };
  });

  // GET /api/releases/:idOrSlug -> Get single release
  app.get('/api/releases/:idOrSlug', async (request: FastifyRequest<{ Params: { idOrSlug: string } }>, reply: FastifyReply) => {
    const release = store.getRelease(request.params.idOrSlug);
    if (!release) return reply.code(404).send({ error: 'release_not_found' });
    return { release };
  });

  // GET /api/artists -> Public artist catalog; supporter totals stay private
  app.get('/api/artists', async () => {
    const artists = store.getArtists().map(({ total_boost_cents: _total, boost_count: _count, ...artist }) => artist);
    return { artists };
  });

  // GET /api/artists/:idOrSlug -> Get single artist with releases & stats
  app.get('/api/artists/:idOrSlug', async (request: FastifyRequest<{ Params: { idOrSlug: string } }>, reply: FastifyReply) => {
    const artist = store.getArtist(request.params.idOrSlug);
    if (!artist) return reply.code(404).send({ error: 'artist_not_found' });
    const { total_boost_cents: _total, boost_count: _count, ...publicArtist } = artist;
    return { artist: publicArtist };
  });

  // GET /api/artists/:slug/boosts -> Get recent boosts for an artist
  app.get('/api/artists/:slug/boosts', async (request: FastifyRequest<{ Params: { slug: string }; Querystring: { limit?: string } }>, reply: FastifyReply) => {
    const limit = parseInt(request.query.limit || '20', 10);
    const boosts = store.getArtistBoosts(request.params.slug, limit);
    return {
      artist_slug: request.params.slug,
      count: boosts.length,
      boosts: boosts.map(({ amount_cents: _amount, ...boost }) => boost),
    };
  });

  // POST /api/boost -> Boost / Tip an artist directly with AHOY ID
  app.post('/api/boost', async (request: FastifyRequest, reply: FastifyReply) => {
    if (config.isProduction) return reply.code(403).send({ error: 'boost_checkout_unavailable' });
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
    const leaderboard = store.getGlobalBoostersLeaderboard(limit)
      .map(({ total_cents: _total, boost_count: _count, rank: _rank, ...supporter }) => supporter);
    leaderboard.sort((a, b) => a.supporter_name.localeCompare(b.supporter_name));
    return {
      leaderboard,
    };
  });

  // POST /api/checkout/purchase -> Buy a song or album with AHOY ID
  app.post('/api/checkout/purchase', async (request: FastifyRequest, reply: FastifyReply) => {
    if (config.isProduction) return reply.code(403).send({ error: 'use_stripe_checkout' });
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

  // Digital purchases are priced on the server and remain pending until Stripe confirms payment.
  app.post('/api/checkout/stripe', async (request: FastifyRequest, reply: FastifyReply) => {
    const auth = getAuthUser(request);
    if (!auth) return reply.code(401).send({ error: 'authentication_required' });
    if (!config.stripeSecretKey || !config.stripeWebhookSecret) return reply.code(503).send({ error: 'stripe_not_configured' });
    const parsed = z.object({ release_id: z.string().min(1), track_id: z.string().optional() }).safeParse(request.body);
    if (!parsed.success) return reply.code(400).send({ error: 'invalid_checkout_payload' });
    const release = store.getRelease(parsed.data.release_id);
    if (!release) return reply.code(404).send({ error: 'release_not_found' });
    const track = parsed.data.track_id ? release.tracks.find(t => t.id === parsed.data.track_id) : null;
    if (parsed.data.track_id && !track) return reply.code(400).send({ error: 'track_not_in_release' });
    // Singles and albums currently use the release's catalog price.
    const amount = release.price_cents;
    const params = new URLSearchParams({
      mode: 'payment',
      success_url: `${config.publicBaseUrl}/?checkout=success&session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${config.publicBaseUrl}/?checkout=cancelled`,
      'line_items[0][price_data][currency]': 'usd',
      'line_items[0][price_data][unit_amount]': String(amount),
      'line_items[0][price_data][product_data][name]': `${release.artist} — ${track?.title || release.title} (digital)`,
      'line_items[0][quantity]': '1',
      client_reference_id: auth.ahoy_id,
    });
    if (auth.email) params.set('customer_email', auth.email);
    let stripeResponse: Response;
    try {
      stripeResponse = await fetch('https://api.stripe.com/v1/checkout/sessions', {
        method: 'POST',
        headers: { Authorization: `Bearer ${config.stripeSecretKey}`, 'Content-Type': 'application/x-www-form-urlencoded' },
        body: params,
      });
    } catch { return reply.code(502).send({ error: 'stripe_unavailable' }); }
    if (!stripeResponse.ok) return reply.code(502).send({ error: 'stripe_checkout_failed' });
    const session = await stripeResponse.json() as { id?: string; url?: string };
    if (!session.id || !session.url) return reply.code(502).send({ error: 'stripe_checkout_failed' });
    store.saveStripeCheckout({ session_id: session.id, ahoy_id: auth.ahoy_id, email: auth.email,
      release_id: release.id, track_id: track?.id, amount_cents: amount });
    return { checkout_url: session.url };
  });

  app.get('/api/checkout/stripe/:sessionId', async (request: FastifyRequest<{ Params: { sessionId: string } }>, reply: FastifyReply) => {
    const auth = getAuthUser(request);
    if (!auth) return reply.code(401).send({ error: 'authentication_required' });
    const status = store.getStripeCheckoutStatus(request.params.sessionId, auth.ahoy_id);
    if (!status) return reply.code(404).send({ error: 'checkout_not_found' });
    return { status };
  });

  app.post('/api/stripe/webhook', async (request: FastifyRequest, reply: FastifyReply) => {
    const raw = (request as FastifyRequest & { rawBody?: Buffer }).rawBody;
    const signature = request.headers['stripe-signature'];
    if (!config.stripeWebhookSecret || !raw || typeof signature !== 'string') return reply.code(400).send({ error: 'invalid_signature' });
    const parts = Object.fromEntries(signature.split(',').map(part => part.split('=', 2)));
    const timestamp = Number(parts.t);
    if (!Number.isFinite(timestamp) || Math.abs(Date.now() / 1000 - timestamp) > 300) return reply.code(400).send({ error: 'invalid_signature' });
    const expected = createHmac('sha256', config.stripeWebhookSecret).update(`${timestamp}.${raw.toString('utf8')}`).digest('hex');
    const candidate = Buffer.from(parts.v1 || '', 'hex');
    if (candidate.length !== 32 || !timingSafeEqual(candidate, Buffer.from(expected, 'hex'))) return reply.code(400).send({ error: 'invalid_signature' });
    const event = request.body as { type?: string; data?: { object?: { id?: string; payment_status?: string; amount_total?: number; currency?: string } } };
    if (event.type === 'checkout.session.completed' || event.type === 'checkout.session.async_payment_succeeded') {
      const session = event.data?.object;
      if (session?.id) store.completeStripeCheckout({ id: session.id, payment_status: session.payment_status,
        amount_total: session.amount_total, currency: session.currency });
    }
    return { received: true };
  });

  // POST /api/checkout/burned-cd -> Custom Mixtape Burned CD Wizard order
  app.post('/api/checkout/burned-cd', async (request: FastifyRequest, reply: FastifyReply) => {
    if (config.isProduction) return reply.code(403).send({ error: 'physical_checkout_unavailable' });
    const auth = getAuthUser(request);
    if (!auth) {
      return reply.code(401).send({
        error: 'authentication_required',
        message: 'You must sign in with your AHOY ID to craft and purchase a Burned CD.',
        login_url: `${config.publicBaseUrl}/api/auth/login`,
      });
    }

    const parsed = burnedCdInput.safeParse(request.body);
    if (!parsed.success) {
      return reply.code(400).send({ error: 'invalid_burned_cd_payload', details: parsed.error.format() });
    }

    try {
      const order = store.recordBurnedCdOrder({
        ahoy_id: auth.ahoy_id,
        recipient_ahoy_id: parsed.data.recipient_ahoy_id,
        email: auth.email,
        cd_title: parsed.data.cd_title,
        track_ids: parsed.data.track_ids,
        marker_color: parsed.data.marker_color,
        payment_method: parsed.data.payment_method,
        shipping: parsed.data.shipping,
      });

      const isTransfer = Boolean(parsed.data.recipient_ahoy_id && parsed.data.recipient_ahoy_id.trim() !== auth.ahoy_id);

      return reply.code(201).send({
        success: true,
        purchase_id: order.purchaseId,
        ahoy_id: auth.ahoy_id,
        granted_to: order.grantedTo,
        is_transfer: isTransfer,
        cd_title: order.cdTitle,
        track_count: order.trackCount,
        tracks: order.tracks,
        music_cents: order.musicCents,
        burn_fee_cents: order.burnFeeCents,
        amount_cents: order.totalAmountCents,
        format: 'burned_cd',
        fulfillment_status: order.fulfillmentStatus,
        artist_attributions: order.artistAttributions,
        player_url: `${config.playerUrl}?ahoy_id=${encodeURIComponent(order.grantedTo)}`,
      });
    } catch (err: any) {
      if (err.message && err.message.startsWith('track_not_found')) {
        return reply.code(404).send({ error: 'track_not_found', message: err.message });
      }
      if (err.message === 'no_tracks_selected') {
        return reply.code(400).send({ error: 'no_tracks_selected', message: 'You must select at least one track to burn.' });
      }
      throw err;
    }
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
    const effectiveAhoyId = auth?.ahoy_id || (!config.isProduction ? queryAhoyId : undefined);

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
    const effectiveAhoyId = auth?.ahoy_id || (!config.isProduction ? queryAhoyId : undefined);

    const isEntitled = effectiveAhoyId ? store.hasEntitlement(effectiveAhoyId, trackId) : false;
    if (!isEntitled) {
      return reply.code(403).send({
        error: 'entitlement_required',
        message: 'You must own this release to download the master audio file.',
      });
    }

    // Serve the file from this origin so the browser receives attachment headers.
    // A redirect to the audio host can discard Content-Disposition and open a player instead.
    let audioResponse: Response;
    try {
      audioResponse = await fetch(track.full_audio_url, { signal: AbortSignal.timeout(30_000) });
    } catch {
      return reply.code(502).send({ error: 'download_unavailable' });
    }
    if (!audioResponse.ok || !audioResponse.body) return reply.code(502).send({ error: 'download_unavailable' });
    const filename = `${track.artist} - ${track.title}.mp3`.replace(/[/\\?%*:|"<>]/g, '-');
    const asciiFilename = filename.replace(/[^\x20-\x7e]/g, '_');
    reply.header('Content-Disposition', `attachment; filename="${asciiFilename}"; filename*=UTF-8''${encodeURIComponent(filename)}`);
    reply.header('Content-Type', 'audio/mpeg');
    reply.header('Cache-Control', 'private, no-store');
    return reply.send(Readable.fromWeb(audioResponse.body as import('node:stream/web').ReadableStream));
  });
};
