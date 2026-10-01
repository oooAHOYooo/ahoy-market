import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { buildApp } from '../src/app.js';
import { MarketStore } from '../src/db.js';
import { FastifyInstance } from 'fastify';
import { createHmac } from 'node:crypto';
import { config } from '../src/config.js';

describe('AHOY Market API & Entitlement Flow', () => {
  let store: MarketStore;
  let app: FastifyInstance;

  beforeEach(async () => {
    store = new MarketStore(':memory:');
    app = buildApp(store);
    await app.ready();
  });

  afterEach(async () => {
    await app.close();
  });

  it('serves health endpoint', async () => {
    const res = await app.inject({ method: 'GET', url: '/health' });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.service).toBe('ahoy-market');
  });

  it('grants a digital purchase only after a signed paid Stripe event and ignores replays', async () => {
    const originalKey = config.stripeSecretKey;
    const originalSecret = config.stripeWebhookSecret;
    const originalFetch = globalThis.fetch;
    config.stripeSecretKey = 'sk_test_local';
    config.stripeWebhookSecret = 'whsec_local';
    globalThis.fetch = async () => new Response(JSON.stringify({ id: 'cs_test_local_1', url: 'https://checkout.stripe.com/test' }), { status: 200 });
    try {
      const login = await app.inject({ method: 'POST', url: '/api/auth/dev-login', payload: { ahoy_id: 'ahoy_stripe_buyer' } });
      const cookie = login.cookies.find(c => c.name === 'ahoy_market_session')!;
      const checkout = await app.inject({ method: 'POST', url: '/api/checkout/stripe',
        cookies: { ahoy_market_session: cookie.value }, payload: { release_id: 'rel_samuel_witch_1', amount_cents: 1 } });
      expect(checkout.statusCode).toBe(200);
      expect(checkout.json().checkout_url).toBe('https://checkout.stripe.com/test');
      expect(store.getEntitlements('ahoy_stripe_buyer')).toHaveLength(0);
      const release = store.getRelease('rel_samuel_witch_1')!;
      const event = JSON.stringify({ type: 'checkout.session.completed', data: { object: {
        id: 'cs_test_local_1', payment_status: 'paid', amount_total: release.price_cents, currency: 'usd' } } });
      const timestamp = Math.floor(Date.now() / 1000);
      const signature = `t=${timestamp},v1=${createHmac('sha256', config.stripeWebhookSecret).update(`${timestamp}.${event}`).digest('hex')}`;
      const invalid = await app.inject({ method: 'POST', url: '/api/stripe/webhook', headers: { 'stripe-signature': 't=1,v1=bad', 'content-type': 'application/json' }, payload: event });
      expect(invalid.statusCode).toBe(400);
      expect(store.getEntitlements('ahoy_stripe_buyer')).toHaveLength(0);
      const paid = await app.inject({ method: 'POST', url: '/api/stripe/webhook', headers: { 'stripe-signature': signature, 'content-type': 'application/json' }, payload: event });
      expect(paid.statusCode).toBe(200);
      expect(store.getEntitlements('ahoy_stripe_buyer')).toHaveLength(release.tracks.length);
      await app.inject({ method: 'POST', url: '/api/stripe/webhook', headers: { 'stripe-signature': signature, 'content-type': 'application/json' }, payload: event });
      expect(store.getEntitlements('ahoy_stripe_buyer')).toHaveLength(release.tracks.length);
    } finally {
      config.stripeSecretKey = originalKey;
      config.stripeWebhookSecret = originalSecret;
      globalThis.fetch = originalFetch;
    }
  });

  it('lists catalog releases with tracks', async () => {
    const res = await app.inject({ method: 'GET', url: '/api/releases' });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.releases.length).toBeGreaterThan(0);
    expect(body.releases[0].tracks.length).toBeGreaterThan(0);
    expect(body.releases[0].title).toBe('Seen Better Days');
  });

  it('serves combined market state from /api/market/latest in 1 round trip', async () => {
    // 1. Unauthenticated request
    const anonRes = await app.inject({ method: 'GET', url: '/api/market/latest' });
    expect(anonRes.statusCode).toBe(200);
    const anonBody = anonRes.json();
    expect(anonBody.user.authenticated).toBe(false);
    expect(anonBody.releases.length).toBeGreaterThan(0);
    expect(anonBody.releases[0].tracks.length).toBeGreaterThan(0);
    expect(anonBody.artists.length).toBe(5);
    expect(Array.isArray(anonBody.leaderboard)).toBe(true);
    expect(anonBody.library).toEqual([]);
    expect(anonBody.boost_stats).toBeNull();

    // 2. Authenticated request with session
    const patronId = 'ahoy_latest_tester';
    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: patronId, name: 'Latest Tester' },
    });
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session')!;

    const authRes = await app.inject({
      method: 'GET',
      url: '/api/market/latest',
      cookies: { ahoy_market_session: cookie.value },
    });
    expect(authRes.statusCode).toBe(200);
    const authBody = authRes.json();
    expect(authBody.user.authenticated).toBe(true);
    expect(authBody.user.user.ahoy_id).toBe(patronId);
    expect(authBody.releases.length).toBeGreaterThan(0);
    expect(Array.isArray(authBody.library)).toBe(true);
    expect(authBody.boost_stats).toBeDefined();
    expect(authBody.boost_stats.ahoy_id).toBe(patronId);
  });

  it('lists artists and retrieves individual artist details', async () => {
    const res = await app.inject({ method: 'GET', url: '/api/artists' });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.artists.length).toBe(5);
    expect(body.artists.some((a: any) => a.slug === 'samuel-dylan-witch')).toBe(true);

    const singleRes = await app.inject({ method: 'GET', url: '/api/artists/samuel-dylan-witch' });
    expect(singleRes.statusCode).toBe(200);
    const singleBody = singleRes.json();
    expect(singleBody.artist.name).toBe('Samuel Dylan Witch');
    expect(singleBody.artist.releases.length).toBe(2);
  });

  it('requires AHOY ID authentication to purchase and boost', async () => {
    const buyRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/purchase',
      payload: { release_id: 'rel_samuel_witch_1' },
    });
    expect(buyRes.statusCode).toBe(401);
    expect(buyRes.json().error).toBe('authentication_required');

    const boostRes = await app.inject({
      method: 'POST',
      url: '/api/boost',
      payload: { artist_slug: 'samuel-dylan-witch', amount_cents: 500 },
    });
    expect(boostRes.statusCode).toBe(401);
    expect(boostRes.json().error).toBe('authentication_required');
  });

  it('records artist boosts, calculates stats, and updates leaderboard', async () => {
    const ahoyId = 'ahoy_patron_sailor_1';

    // 1. Authenticate with dev-login
    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: ahoyId, name: 'First Mate Jack' },
    });
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session')!;
    expect(cookie).toBeDefined();

    // 2. Send boost to Samuel Dylan Witch ($10.00)
    const boost1 = await app.inject({
      method: 'POST',
      url: '/api/boost',
      cookies: { ahoy_market_session: cookie.value },
      payload: {
        artist_slug: 'samuel-dylan-witch',
        amount_cents: 1000,
        message: 'Keep making wonderful coastal sea shanties!',
      },
    });
    expect(boost1.statusCode).toBe(201);
    const boost1Body = boost1.json();
    expect(boost1Body.success).toBe(true);
    expect(boost1Body.boost.amount_cents).toBe(1000);
    expect(boost1Body.user_stats.total_cents).toBe(1000);
    expect(boost1Body.user_stats.patron_level).toBe('Silver Patron');

    // 3. Send boost to Cambell Rice ($15.00)
    const boost2 = await app.inject({
      method: 'POST',
      url: '/api/boost',
      cookies: { ahoy_market_session: cookie.value },
      payload: {
        artist_slug: 'cambell-rice',
        amount_cents: 1500,
        message: 'Sunflower is on repeat on the boat.',
      },
    });
    expect(boost2.statusCode).toBe(201);
    expect(boost2.json().user_stats.total_cents).toBe(2500);
    expect(boost2.json().user_stats.patron_level).toBe('Gold Patron');

    // 4. Query artist boosts endpoint
    const artistBoostsRes = await app.inject({
      method: 'GET',
      url: '/api/artists/samuel-dylan-witch/boosts',
    });
    expect(artistBoostsRes.statusCode).toBe(200);
    const artistBoostsBody = artistBoostsRes.json();
    expect(artistBoostsBody.count).toBe(1);
    expect(artistBoostsBody.boosts[0].supporter_name).toBe('First Mate Jack');

    // 5. Query user stats
    const statsRes = await app.inject({
      method: 'GET',
      url: `/api/me/boost-stats?ahoy_id=${ahoyId}`,
    });
    expect(statsRes.statusCode).toBe(200);
    const statsBody = statsRes.json();
    expect(statsBody.stats.total_cents).toBe(2500);
    expect(statsBody.stats.boost_count).toBe(2);
    expect(statsBody.stats.unique_artists).toBe(2);

    // 6. Query leaderboard
    const leaderRes = await app.inject({
      method: 'GET',
      url: '/api/leaderboard/boosters',
    });
    expect(leaderRes.statusCode).toBe(200);
    const leaderBody = leaderRes.json();
    expect(leaderBody.leaderboard.length).toBe(1);
    expect(leaderBody.leaderboard[0].ahoy_id).toBe(ahoyId);
    expect(leaderBody.leaderboard[0].supporter_name).toBe('First Mate Jack');
    expect(leaderBody.leaderboard[0].total_cents).toBe(2500);
    expect(leaderBody.leaderboard[0].rank).toBe(1);
  });

  it('completes purchase for authenticated user and grants sovereign entitlement', async () => {
    const ahoyId = 'ahoy_test_sailor_99';

    // 1. Dev login to create session
    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: ahoyId, name: 'Captain Test' },
    });
    expect(loginRes.statusCode).toBe(200);
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session');
    expect(cookie).toBeDefined();

    // 2. Buy release
    const buyRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/purchase',
      cookies: { ahoy_market_session: cookie!.value },
      payload: { release_id: 'rel_samuel_witch_1' },
    });
    expect(buyRes.statusCode).toBe(201);
    const buyBody = buyRes.json();
    expect(buyBody.success).toBe(true);
    expect(buyBody.ahoy_id).toBe(ahoyId);
    expect(buyBody.entitlement_count).toBe(1);

    // 3. Verify user library
    const libRes = await app.inject({
      method: 'GET',
      url: '/api/me/library',
      cookies: { ahoy_market_session: cookie!.value },
    });
    expect(libRes.statusCode).toBe(200);
    const libBody = libRes.json();
    expect(libBody.tracks.length).toBe(1);
    expect(libBody.tracks[0].title).toBe('Seen Better Days');

    // 4. Verify Player Entitlements API query
    const playerEntRes = await app.inject({
      method: 'GET',
      url: `/api/entitlements?ahoy_id=${encodeURIComponent(ahoyId)}`,
    });
    expect(playerEntRes.statusCode).toBe(200);
    const playerEntBody = playerEntRes.json();
    expect(playerEntBody.count).toBe(1);
    expect(playerEntBody.tracks[0].id).toBe('trk_seen_better_days');
    expect(playerEntBody.tracks[0].stream_url).toContain('trk_seen_better_days');

    // 5. Stream endpoint redirect for entitled user
    const streamRes = await app.inject({
      method: 'GET',
      url: `/api/stream/trk_seen_better_days?ahoy_id=${encodeURIComponent(ahoyId)}`,
    });
    expect(streamRes.statusCode).toBe(302);
    expect(streamRes.headers.location).toBe('https://ahoycollection.s3.us-east-2.amazonaws.com/01%20I%27ve%20Seen%20Better%20Days.mp3');

    // 6. Download endpoint redirect & content disposition for entitled user
    const dlRes = await app.inject({
      method: 'GET',
      url: `/api/download/trk_seen_better_days?ahoy_id=${encodeURIComponent(ahoyId)}`,
    });
    expect(dlRes.statusCode).toBe(302);
    expect(dlRes.headers['content-disposition']).toContain('attachment');
    expect(dlRes.headers.location).toBe('https://ahoycollection.s3.us-east-2.amazonaws.com/01%20I%27ve%20Seen%20Better%20Days.mp3');

    // 7. Download endpoint rejects unentitled user
    const unentitledDlRes = await app.inject({
      method: 'GET',
      url: '/api/download/trk_seen_better_days?ahoy_id=ahoy_random_stranger',
    });
    expect(unentitledDlRes.statusCode).toBe(403);
    expect(unentitledDlRes.json().error).toBe('entitlement_required');
  });

  it('allows purchasing and directly transferring entitlement to another AHOY ID', async () => {
    const buyerId = 'ahoy_buyer_person';
    const recipientId = 'ahoy_friend_recipient';

    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: buyerId, name: 'Generous Buyer' },
    });
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session');

    // Buyer purchases for recipient
    const buyRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/purchase',
      cookies: { ahoy_market_session: cookie!.value },
      payload: {
        release_id: 'rel_cambell_rice_1',
        recipient_ahoy_id: recipientId,
        payment_method: 'instant_sovereign',
      },
    });
    expect(buyRes.statusCode).toBe(201);
    const buyBody = buyRes.json();
    expect(buyBody.success).toBe(true);
    expect(buyBody.ahoy_id).toBe(buyerId);
    expect(buyBody.granted_to).toBe(recipientId);
    expect(buyBody.is_transfer).toBe(true);

    // Verify recipient has the entitlement
    const recEntRes = await app.inject({
      method: 'GET',
      url: `/api/entitlements?ahoy_id=${encodeURIComponent(recipientId)}`,
    });
    expect(recEntRes.statusCode).toBe(200);
    const recEntBody = recEntRes.json();
    expect(recEntBody.count).toBe(1);
    expect(recEntBody.tracks[0].title).toBe('Sunflower');
  });

  it('handles physical AHOY USB Album and custom Burned CD orders with shipping info', async () => {
    const patronId = 'ahoy_patron_collector';
    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: patronId, name: 'Collector Patron' },
    });
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session');

    // 1. Purchase physical Lossless USB Album edition
    const usbOrderRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/purchase',
      cookies: { ahoy_market_session: cookie!.value },
      payload: {
        release_id: 'rel_samuel_witch_1',
        amount_cents: 1500,
        format: 'usb_album',
        shipping: {
          name: 'Jane Doe',
          address: '42 Harbor Lane',
          city: 'Mystic',
          state: 'CT',
          zip: '06355',
          country: 'US',
          inscription_note: 'AHOY Mixtape on USB - For Jane.',
        },
      },
    });
    expect(usbOrderRes.statusCode).toBe(201);
    const usbBody = usbOrderRes.json();
    expect(usbBody.success).toBe(true);
    expect(usbBody.format).toBe('usb_album');
    expect(usbBody.fulfillment_status).toBe('queued_for_crafting');
    expect(usbBody.entitlement_count).toBe(1);

    // 2. Purchase physical Burned CD edition
    const cdOrderRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/purchase',
      cookies: { ahoy_market_session: cookie!.value },
      payload: {
        release_id: 'rel_samuel_witch_1',
        amount_cents: 1500,
        format: 'burned_cd',
        shipping: {
          name: 'Jane Doe',
          address: '42 Harbor Lane',
          city: 'Mystic',
          state: 'CT',
          zip: '06355',
          country: 'US',
          inscription_note: 'For Jane - with love from the shoreline.',
        },
      },
    });
    expect(cdOrderRes.statusCode).toBe(201);
    const cdBody = cdOrderRes.json();
    expect(cdBody.success).toBe(true);
    expect(cdBody.format).toBe('burned_cd');
    expect(cdBody.fulfillment_status).toBe('queued_for_crafting');
    expect(cdBody.entitlement_count).toBe(1);
  });

  it('handles interactive Burned CD wizard order with $5 flat fee on top of selected music going to artists', async () => {
    const patronId = 'ahoy_dj_mixtape_curator';
    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: patronId, name: 'Mixtape DJ' },
    });
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session');

    // 1. Submit custom Burned CD with 3 songs from different artists
    // tracks: 'trk_seen_better_days' (100c), 'trk_sunflower' (100c), 'trk_summer_bummer' (100c)
    // total = 300 cents music + 500 cents flat craft fee = 800 cents ($8.00)
    const wizardRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/burned-cd',
      cookies: { ahoy_market_session: cookie!.value },
      payload: {
        cd_title: 'Mystic Summer Coast Mix',
        marker_color: 'coral',
        track_ids: ['trk_seen_better_days', 'trk_sunflower', 'trk_summer_bummer'],
        shipping: {
          name: 'Marina Shore',
          address: '88 Lighthouse Pt',
          city: 'Mystic',
          state: 'CT',
          zip: '06355',
          country: 'US',
          inscription_note: 'Hand-burned for road trips down Route 1.',
        },
      },
    });

    expect(wizardRes.statusCode).toBe(201);
    const body = wizardRes.json();
    expect(body.success).toBe(true);
    expect(body.cd_title).toBe('Mystic Summer Coast Mix');
    expect(body.track_count).toBe(3);
    expect(body.music_cents).toBe(300); // 3 tracks * $1.00
    expect(body.burn_fee_cents).toBe(500); // $5 flat fee
    expect(body.amount_cents).toBe(800); // $8.00 total
    expect(body.format).toBe('burned_cd');
    expect(body.fulfillment_status).toBe('queued_for_crafting');
    expect(body.artist_attributions.length).toBe(3); // 3 distinct artists receiving splits

    // 2. Verify sovereign entitlements were granted for all 3 tracks to the curator
    const entRes = await app.inject({
      method: 'GET',
      url: `/api/entitlements?ahoy_id=${encodeURIComponent(patronId)}`,
    });
    expect(entRes.statusCode).toBe(200);
    const entBody = entRes.json();
    expect(entBody.count).toBe(3);
    const titles = entBody.tracks.map((t: any) => t.title);
    expect(titles).toContain('Seen Better Days');
    expect(titles).toContain('Sunflower');
    expect(titles).toContain('Summer Bummer');
  });

  it('handles gifting custom Burned CD to a friend and grants friend the entitlements', async () => {
    const patronId = 'ahoy_gifter_patron';
    const recipientId = 'ahoy_lucky_bestie';

    const loginRes = await app.inject({
      method: 'POST',
      url: '/api/auth/dev-login',
      payload: { ahoy_id: patronId, name: 'Gift Giver' },
    });
    const cookie = loginRes.cookies.find(c => c.name === 'ahoy_market_session');

    const giftRes = await app.inject({
      method: 'POST',
      url: '/api/checkout/burned-cd',
      cookies: { ahoy_market_session: cookie!.value },
      payload: {
        cd_title: 'Birthday Folk Compilation',
        recipient_ahoy_id: recipientId,
        track_ids: ['trk_seen_better_days', 'trk_beneath_the_willow_tree'],
        shipping: {
          name: 'Lucky Bestie',
          address: '100 Ocean Ave',
          city: 'New London',
          state: 'CT',
          zip: '06320',
          country: 'US',
          inscription_note: 'Happy 25th Birthday! Love your tunes.',
        },
      },
    });

    expect(giftRes.statusCode).toBe(201);
    const giftBody = giftRes.json();
    expect(giftBody.success).toBe(true);
    expect(giftBody.is_transfer).toBe(true);
    expect(giftBody.granted_to).toBe(recipientId);
    expect(giftBody.music_cents).toBe(200); // 2 tracks * $1.00
    expect(giftBody.burn_fee_cents).toBe(500); // $5 flat fee
    expect(giftBody.amount_cents).toBe(700); // $7.00 total

    // Verify recipient received entitlements
    const friendEnt = await app.inject({
      method: 'GET',
      url: `/api/entitlements?ahoy_id=${encodeURIComponent(recipientId)}`,
    });
    expect(friendEnt.statusCode).toBe(200);
    expect(friendEnt.json().count).toBe(2);
  });
});
