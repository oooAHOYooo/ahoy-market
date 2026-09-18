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
    expect(body.releases[0].title).toBe('Moonlight Tides');
  });

  it('requires AHOY ID authentication to purchase', async () => {
    const res = await app.inject({
      method: 'POST',
      url: '/api/checkout/purchase',
      payload: { release_id: 'rel_samuel_witch_1' },
    });
    expect(res.statusCode).toBe(401);
    expect(res.json().error).toBe('authentication_required');
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
    expect(libBody.tracks[0].title).toBe('Moonlight Tides');

    // 4. Verify Player Entitlements API query
    const playerEntRes = await app.inject({
      method: 'GET',
      url: `/api/entitlements?ahoy_id=${encodeURIComponent(ahoyId)}`,
    });
    expect(playerEntRes.statusCode).toBe(200);
    const playerEntBody = playerEntRes.json();
    expect(playerEntBody.count).toBe(1);
    expect(playerEntBody.tracks[0].id).toBe('trk_moonlight_tides_1');
    expect(playerEntBody.tracks[0].stream_url).toContain('trk_moonlight_tides_1');

    // 5. Stream endpoint redirect for entitled user
    const streamRes = await app.inject({
      method: 'GET',
      url: `/api/stream/trk_moonlight_tides_1?ahoy_id=${encodeURIComponent(ahoyId)}`,
    });
    expect(streamRes.statusCode).toBe(302);
    expect(streamRes.headers.location).toBe('https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3');
  });
});
