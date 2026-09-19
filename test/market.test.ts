import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { buildApp } from '../src/app.js';
import { MarketStore } from '../src/db.js';
import { FastifyInstance } from 'fastify';

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

  it('lists catalog releases with tracks', async () => {
    const res = await app.inject({ method: 'GET', url: '/api/releases' });
    expect(res.statusCode).toBe(200);
    const body = res.json();
    expect(body.releases.length).toBeGreaterThan(0);
    expect(body.releases[0].tracks.length).toBeGreaterThan(0);
    expect(body.releases[0].title).toBe('Seen Better Days');
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
});
