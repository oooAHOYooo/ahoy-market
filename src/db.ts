import Database from 'better-sqlite3';
import { randomBytes } from 'node:crypto';

export type Release = {
  id: string;
  slug: string;
  title: string;
  artist: string;
  artist_slug: string;
  description: string;
  price_cents: number;
  artwork_url: string;
  type: 'single' | 'album' | 'ep';
  created_at: string;
};

export type Track = {
  id: string;
  release_id: string;
  track_number: number;
  title: string;
  artist: string;
  duration_seconds: number;
  preview_url: string;
  full_audio_url: string;
};

export type Purchase = {
  id: string;
  ahoy_id: string;
  email: string | null;
  release_id: string;
  track_id: string | null;
  amount_cents: number;
  currency: string;
  payment_method: string;
  payment_ref: string;
  status: string;
  created_at: string;
};

export type Entitlement = {
  id: string;
  ahoy_id: string;
  track_id: string;
  release_id: string;
  title: string;
  artist: string;
  artwork_url: string;
  full_audio_url: string;
  duration_seconds: number;
  granted_at: string;
};

export type UserSession = {
  id: string;
  session_token: string;
  ahoy_id: string;
  email: string | null;
  name: string | null;
  access_token: string | null;
  expires_at: string;
  created_at: string;
};

export type Artist = {
  id: string;
  slug: string;
  name: string;
  bio: string;
  avatar_url: string;
  banner_url: string;
  genre: string;
  created_at: string;
};

export type Boost = {
  id: string;
  ahoy_id: string;
  artist_slug: string;
  amount_cents: number;
  supporter_name: string | null;
  message: string | null;
  payment_method: string;
  payment_ref: string;
  created_at: string;
};

export type BoostStats = {
  ahoy_id: string;
  total_cents: number;
  boost_count: number;
  unique_artists: number;
  patron_level: string;
  recent_boosts: Boost[];
};

export type BoosterLeaderboardEntry = {
  ahoy_id: string;
  supporter_name: string;
  total_cents: number;
  boost_count: number;
  rank: number;
};

export class MarketStore {
  private db: Database.Database;

  constructor(dbPath: string = ':memory:') {
    this.db = new Database(dbPath);
    this.db.pragma('journal_mode = WAL');
    this.initTables();
    this.seedDefaultCatalog();
  }

  private initTables() {
    this.db.exec(`
      CREATE TABLE IF NOT EXISTS artists (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        bio TEXT NOT NULL,
        avatar_url TEXT NOT NULL,
        banner_url TEXT NOT NULL,
        genre TEXT NOT NULL,
        created_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS releases (
        id TEXT PRIMARY KEY,
        slug TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        artist_slug TEXT NOT NULL,
        description TEXT NOT NULL,
        price_cents INTEGER NOT NULL,
        artwork_url TEXT NOT NULL,
        type TEXT NOT NULL,
        created_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS tracks (
        id TEXT PRIMARY KEY,
        release_id TEXT NOT NULL REFERENCES releases(id) ON DELETE CASCADE,
        track_number INTEGER NOT NULL,
        title TEXT NOT NULL,
        artist TEXT NOT NULL,
        duration_seconds INTEGER NOT NULL,
        preview_url TEXT NOT NULL,
        full_audio_url TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS purchases (
        id TEXT PRIMARY KEY,
        ahoy_id TEXT NOT NULL,
        email TEXT,
        release_id TEXT NOT NULL REFERENCES releases(id),
        track_id TEXT,
        amount_cents INTEGER NOT NULL,
        currency TEXT NOT NULL,
        payment_method TEXT NOT NULL,
        payment_ref TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS entitlements (
        id TEXT PRIMARY KEY,
        ahoy_id TEXT NOT NULL,
        track_id TEXT NOT NULL REFERENCES tracks(id),
        release_id TEXT NOT NULL REFERENCES releases(id),
        granted_at TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'active',
        UNIQUE(ahoy_id, track_id)
      );

      CREATE TABLE IF NOT EXISTS boosts (
        id TEXT PRIMARY KEY,
        ahoy_id TEXT NOT NULL,
        artist_slug TEXT NOT NULL,
        amount_cents INTEGER NOT NULL,
        supporter_name TEXT,
        message TEXT,
        payment_method TEXT NOT NULL,
        payment_ref TEXT NOT NULL,
        created_at TEXT NOT NULL
      );

      CREATE TABLE IF NOT EXISTS sessions (
        id TEXT PRIMARY KEY,
        session_token TEXT UNIQUE NOT NULL,
        ahoy_id TEXT NOT NULL,
        email TEXT,
        name TEXT,
        access_token TEXT,
        expires_at TEXT NOT NULL,
        created_at TEXT NOT NULL
      );

      CREATE INDEX IF NOT EXISTS ix_artists_slug ON artists(slug);
      CREATE INDEX IF NOT EXISTS ix_purchases_ahoy_id ON purchases(ahoy_id);
      CREATE INDEX IF NOT EXISTS ix_entitlements_ahoy_id ON entitlements(ahoy_id);
      CREATE INDEX IF NOT EXISTS ix_boosts_ahoy_id ON boosts(ahoy_id);
      CREATE INDEX IF NOT EXISTS ix_boosts_artist_slug ON boosts(artist_slug);
      CREATE INDEX IF NOT EXISTS ix_sessions_session_token ON sessions(session_token);
      CREATE INDEX IF NOT EXISTS ix_tracks_release_id ON tracks(release_id);
    `);
  }

  private seedDefaultCatalog() {
    const existingArtists = this.db.prepare('SELECT COUNT(*) as count FROM artists').get() as { count: number };
    if (existingArtists.count === 0) {
      const artists: Artist[] = [
        {
          id: 'art_samuel_witch',
          slug: 'samuel-dylan-witch',
          name: 'Samuel Dylan Witch',
          bio: 'Atmospheric nautical folk, sea songs, and tape-saturated acoustic harmonies from the Connecticut shoreline.',
          avatar_url: 'https://i.ytimg.com/vi/XDH0X-dF4GM/maxresdefault.jpg',
          banner_url: 'https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1200&q=80',
          genre: 'Nautical Folk / Indie',
          created_at: new Date().toISOString(),
        },
        {
          id: 'art_cambell_rice',
          slug: 'cambell-rice',
          name: 'Cambell Rice',
          bio: 'Vibrant acoustic songwriting, intricate fingerstyle guitar, and sparkling coastal indie folk.',
          avatar_url: 'https://m.media-amazon.com/images/I/61APLxryThL._UXNaN_FMjpg_QL85_.jpg',
          banner_url: 'https://images.unsplash.com/photo-1470225620780-dba8ba36b745?auto=format&fit=crop&w=1200&q=80',
          genre: 'Indie Folk / Singer-Songwriter',
          created_at: new Date().toISOString(),
        },
        {
          id: 'art_youth_xl',
          slug: 'youth-xl',
          name: 'Youth XL',
          bio: 'High-energy sunny indie pop with fuzz pedals, analog synths, and infectious hook-filled anthems.',
          avatar_url: 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=600&q=80',
          banner_url: 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1200&q=80',
          genre: 'Indie Pop / Synth Pop',
          created_at: new Date().toISOString(),
        },
        {
          id: 'art_jake_custer',
          slug: 'jake-custer',
          name: 'Jake Custer',
          bio: 'Roots rock, acoustic balladry, and soulful songwriting crafted in the Northeast woods.',
          avatar_url: 'https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80',
          banner_url: 'https://images.unsplash.com/photo-1465847899084-d164df4dedc6?auto=format&fit=crop&w=1200&q=80',
          genre: 'Roots Rock / Americana',
          created_at: new Date().toISOString(),
        },
        {
          id: 'art_the_tines',
          slug: 'the-tines',
          name: 'The Tines',
          bio: 'Dream pop harmonies, chiming 12-string guitars, and shimmering indie soundscapes.',
          avatar_url: 'https://images.unsplash.com/photo-1464375117522-1311d6a5b81f?auto=format&fit=crop&w=600&q=80',
          banner_url: 'https://images.unsplash.com/photo-1498038432885-c6f3f1b912ee?auto=format&fit=crop&w=1200&q=80',
          genre: 'Dream Pop / Jangle Pop',
          created_at: new Date().toISOString(),
        }
      ];

      const insertArtist = this.db.prepare(`
        INSERT INTO artists (id, slug, name, bio, avatar_url, banner_url, genre, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
      `);

      for (const a of artists) {
        insertArtist.run(a.id, a.slug, a.name, a.bio, a.avatar_url, a.banner_url, a.genre, a.created_at);
      }
    }

    const existing = this.db.prepare('SELECT COUNT(*) as count FROM releases').get() as { count: number };
    if (existing.count > 0) return;

    const releases = [
      {
        id: 'rel_samuel_witch_1',
        slug: 'seen-better-days',
        title: 'Seen Better Days',
        artist: 'Samuel Dylan Witch',
        artist_slug: 'samuel-dylan-witch',
        description: 'Atmospheric nautical folk and tape-saturated harmonies recorded on the Connecticut coastline.',
        price_cents: 100,
        artwork_url: 'https://i.ytimg.com/vi/XDH0X-dF4GM/maxresdefault.jpg',
        type: 'single',
        created_at: new Date().toISOString(),
        tracks: [
          {
            id: 'trk_seen_better_days',
            track_number: 1,
            title: 'Seen Better Days',
            artist: 'Samuel Dylan Witch',
            duration_seconds: 190,
            preview_url: 'https://ahoycollection.s3.us-east-2.amazonaws.com/01%20I%27ve%20Seen%20Better%20Days.mp3',
            full_audio_url: 'https://ahoycollection.s3.us-east-2.amazonaws.com/01%20I%27ve%20Seen%20Better%20Days.mp3',
          }
        ]
      },
      {
        id: 'rel_samuel_witch_2',
        slug: 'beneath-the-willow-tree',
        title: 'Beneath the Willow Tree',
        artist: 'Samuel Dylan Witch',
        artist_slug: 'samuel-dylan-witch',
        description: 'Intimate acoustic ballad with reflective songwriting and vintage warmth.',
        price_cents: 100,
        artwork_url: 'https://i.ytimg.com/vi/koPyEhqksBk/maxresdefault.jpg',
        type: 'single',
        created_at: new Date().toISOString(),
        tracks: [
          {
            id: 'trk_beneath_the_willow_tree',
            track_number: 1,
            title: 'Beneath the Willow Tree',
            artist: 'Samuel Dylan Witch',
            duration_seconds: 197,
            preview_url: 'https://ahoycollection.s3.us-east-2.amazonaws.com/Beneath+the+Willow+Tree.mp3',
            full_audio_url: 'https://ahoycollection.s3.us-east-2.amazonaws.com/Beneath+the+Willow+Tree.mp3',
          }
        ]
      },
      {
        id: 'rel_cambell_rice_1',
        slug: 'sunflower',
        title: 'Sunflower',
        artist: 'Cambell Rice',
        artist_slug: 'cambell-rice',
        description: 'Vibrant indie folk featuring lush acoustic arrangements and sparkling melodies.',
        price_cents: 100,
        artwork_url: 'https://m.media-amazon.com/images/I/61APLxryThL._UXNaN_FMjpg_QL85_.jpg',
        type: 'single',
        created_at: new Date().toISOString(),
        tracks: [
          {
            id: 'trk_sunflower',
            track_number: 1,
            title: 'Sunflower',
            artist: 'Cambell Rice',
            duration_seconds: 130,
            preview_url: 'https://ahoycollection.s3.us-east-2.amazonaws.com/Campbell+Rice-Sunflower.mp3',
            full_audio_url: 'https://ahoycollection.s3.us-east-2.amazonaws.com/Campbell+Rice-Sunflower.mp3',
          }
        ]
      },
      {
        id: 'rel_youth_xl_1',
        slug: 'summer-bummer',
        title: 'Summer Bummer',
        artist: 'Youth XL',
        artist_slug: 'youth-xl',
        description: 'Upbeat indie-pop anthems filled with sun-drenched synths and driving rhythms.',
        price_cents: 100,
        artwork_url: 'https://images.unsplash.com/photo-1518837695005-2083093ee35b?auto=format&fit=crop&w=600&q=80',
        type: 'single',
        created_at: new Date().toISOString(),
        tracks: [
          {
            id: 'trk_summer_bummer',
            track_number: 1,
            title: 'Summer Bummer',
            artist: 'Youth XL',
            duration_seconds: 239,
            preview_url: 'https://ahoycollection.s3.amazonaws.com/Youth+XL+-+Summer+Bummer.mp3',
            full_audio_url: 'https://ahoycollection.s3.amazonaws.com/Youth+XL+-+Summer+Bummer.mp3',
          }
        ]
      }
    ];

    const insertRelease = this.db.prepare(`
      INSERT INTO releases (id, slug, title, artist, artist_slug, description, price_cents, artwork_url, type, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const insertTrack = this.db.prepare(`
      INSERT INTO tracks (id, release_id, track_number, title, artist, duration_seconds, preview_url, full_audio_url)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `);

    const tx = this.db.transaction(() => {
      for (const r of releases) {
        insertRelease.run(r.id, r.slug, r.title, r.artist, r.artist_slug, r.description, r.price_cents, r.artwork_url, r.type, r.created_at);
        for (const t of r.tracks) {
          insertTrack.run(t.id, r.id, t.track_number, t.title, t.artist, t.duration_seconds, t.preview_url, t.full_audio_url);
        }
      }
    });

    tx();
  }

  getArtists(): (Artist & { total_boost_cents: number; boost_count: number })[] {
    const rows = this.db.prepare(`
      SELECT 
        a.*,
        COALESCE(SUM(b.amount_cents), 0) as total_boost_cents,
        COUNT(b.id) as boost_count
      FROM artists a
      LEFT JOIN boosts b ON b.artist_slug = a.slug
      GROUP BY a.id
      ORDER BY a.name ASC
    `).all() as (Artist & { total_boost_cents: number; boost_count: number })[];
    return rows;
  }

  getArtist(slugOrId: string): (Artist & { total_boost_cents: number; boost_count: number; releases: Release[] }) | null {
    const artist = this.db.prepare('SELECT * FROM artists WHERE id = ? OR slug = ?').get(slugOrId, slugOrId) as Artist | undefined;
    if (!artist) return null;

    const stats = this.db.prepare(`
      SELECT 
        COALESCE(SUM(amount_cents), 0) as total_boost_cents,
        COUNT(id) as boost_count
      FROM boosts
      WHERE artist_slug = ?
    `).get(artist.slug) as { total_boost_cents: number; boost_count: number };

    const releases = this.db.prepare('SELECT * FROM releases WHERE artist_slug = ? ORDER BY created_at DESC').all(artist.slug) as Release[];

    return {
      ...artist,
      total_boost_cents: stats.total_boost_cents || 0,
      boost_count: stats.boost_count || 0,
      releases,
    };
  }

  recordBoost(data: {
    ahoy_id: string;
    artist_slug: string;
    amount_cents: number;
    supporter_name?: string | null;
    message?: string | null;
    payment_method?: string;
    payment_ref?: string;
  }): Boost {
    const boostId = `bst_${randomBytes(12).toString('hex')}`;
    const now = new Date().toISOString();
    const paymentMethod = data.payment_method || 'instant_sovereign';
    const paymentRef = data.payment_ref || `pay_bst_${Date.now()}_${randomBytes(4).toString('hex')}`;

    this.db.prepare(`
      INSERT INTO boosts (id, ahoy_id, artist_slug, amount_cents, supporter_name, message, payment_method, payment_ref, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      boostId,
      data.ahoy_id,
      data.artist_slug,
      data.amount_cents,
      data.supporter_name || null,
      data.message || null,
      paymentMethod,
      paymentRef,
      now
    );

    return {
      id: boostId,
      ahoy_id: data.ahoy_id,
      artist_slug: data.artist_slug,
      amount_cents: data.amount_cents,
      supporter_name: data.supporter_name || null,
      message: data.message || null,
      payment_method: paymentMethod,
      payment_ref: paymentRef,
      created_at: now,
    };
  }

  getArtistBoosts(artistSlug: string, limit: number = 20): Boost[] {
    return this.db.prepare(`
      SELECT * FROM boosts
      WHERE artist_slug = ?
      ORDER BY created_at DESC
      LIMIT ?
    `).all(artistSlug, limit) as Boost[];
  }

  getUserBoostStats(ahoyId: string): BoostStats {
    const totalRow = this.db.prepare(`
      SELECT 
        COALESCE(SUM(amount_cents), 0) as total_cents,
        COUNT(id) as boost_count,
        COUNT(DISTINCT artist_slug) as unique_artists
      FROM boosts
      WHERE ahoy_id = ?
    `).get(ahoyId) as { total_cents: number; boost_count: number; unique_artists: number };

    const recent = this.db.prepare(`
      SELECT * FROM boosts
      WHERE ahoy_id = ?
      ORDER BY created_at DESC
      LIMIT 10
    `).all(ahoyId) as Boost[];

    const totalCents = totalRow.total_cents || 0;
    let patronLevel = 'Deckhand Supporter';
    if (totalCents >= 5000) patronLevel = 'Admiral Patron';
    else if (totalCents >= 2000) patronLevel = 'Gold Patron';
    else if (totalCents >= 1000) patronLevel = 'Silver Patron';
    else if (totalCents >= 100) patronLevel = 'Bronze Patron';

    return {
      ahoy_id: ahoyId,
      total_cents: totalCents,
      boost_count: totalRow.boost_count || 0,
      unique_artists: totalRow.unique_artists || 0,
      patron_level: patronLevel,
      recent_boosts: recent,
    };
  }

  getGlobalBoostersLeaderboard(limit: number = 10): BoosterLeaderboardEntry[] {
    const rows = this.db.prepare(`
      SELECT 
        ahoy_id,
        COALESCE(MAX(supporter_name), ahoy_id) as supporter_name,
        SUM(amount_cents) as total_cents,
        COUNT(id) as boost_count
      FROM boosts
      GROUP BY ahoy_id
      ORDER BY total_cents DESC
      LIMIT ?
    `).all(limit) as { ahoy_id: string; supporter_name: string; total_cents: number; boost_count: number }[];

    return rows.map((r, idx) => ({
      ...r,
      rank: idx + 1,
    }));
  }

  getReleases(): Release[] {
    return this.db.prepare('SELECT * FROM releases ORDER BY created_at DESC').all() as Release[];
  }

  getRelease(slugOrId: string): (Release & { tracks: Track[] }) | null {
    const release = this.db.prepare('SELECT * FROM releases WHERE id = ? OR slug = ?').get(slugOrId, slugOrId) as Release | undefined;
    if (!release) return null;
    const tracks = this.db.prepare('SELECT * FROM tracks WHERE release_id = ? ORDER BY track_number ASC').all(release.id) as Track[];
    return { ...release, tracks };
  }

  getTrack(trackId: string): Track | null {
    const track = this.db.prepare('SELECT * FROM tracks WHERE id = ?').get(trackId) as Track | undefined;
    return track || null;
  }

  recordPurchase(data: {
    ahoy_id: string;
    email?: string | null;
    release_id: string;
    track_id?: string | null;
    amount_cents: number;
    payment_method: string;
    payment_ref: string;
  }): { purchaseId: string; entitlementCount: number } {
    const purchaseId = `pur_${randomBytes(12).toString('hex')}`;
    const now = new Date().toISOString();

    const release = this.getRelease(data.release_id);
    if (!release) throw new Error('release_not_found');

    const tx = this.db.transaction(() => {
      this.db.prepare(`
        INSERT INTO purchases (id, ahoy_id, email, release_id, track_id, amount_cents, currency, payment_method, payment_ref, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
      `).run(
        purchaseId,
        data.ahoy_id,
        data.email || null,
        data.release_id,
        data.track_id || null,
        data.amount_cents,
        'USD',
        data.payment_method,
        data.payment_ref,
        'completed',
        now
      );

      const tracksToEntitle = data.track_id
        ? release.tracks.filter(t => t.id === data.track_id)
        : release.tracks;

      const insertEntitlement = this.db.prepare(`
        INSERT OR IGNORE INTO entitlements (id, ahoy_id, track_id, release_id, granted_at, status)
        VALUES (?, ?, ?, ?, ?, 'active')
      `);

      for (const track of tracksToEntitle) {
        const entId = `ent_${randomBytes(12).toString('hex')}`;
        insertEntitlement.run(entId, data.ahoy_id, track.id, release.id, now);
      }

      return tracksToEntitle.length;
    });

    const count = tx();
    return { purchaseId, entitlementCount: count };
  }

  getEntitlements(ahoyId: string): Entitlement[] {
    return this.db.prepare(`
      SELECT 
        e.id,
        e.ahoy_id,
        e.track_id,
        e.release_id,
        e.granted_at,
        t.title,
        t.artist,
        t.duration_seconds,
        t.full_audio_url,
        r.artwork_url
      FROM entitlements e
      JOIN tracks t ON t.id = e.track_id
      JOIN releases r ON r.id = e.release_id
      WHERE e.ahoy_id = ? AND e.status = 'active'
      ORDER BY e.granted_at DESC
    `).all(ahoyId) as Entitlement[];
  }

  hasEntitlement(ahoyId: string, trackId: string): boolean {
    const row = this.db.prepare('SELECT 1 FROM entitlements WHERE ahoy_id = ? AND track_id = ? AND status = \'active\'').get(ahoyId, trackId);
    return Boolean(row);
  }

  saveSession(session: {
    ahoy_id: string;
    email?: string | null;
    name?: string | null;
    access_token?: string | null;
    expiresInDays?: number;
  }): UserSession {
    const token = `mkt_sess_${randomBytes(24).toString('base64url')}`;
    const id = `sess_${randomBytes(12).toString('hex')}`;
    const now = new Date();
    const expires = new Date(now.getTime() + (session.expiresInDays || 30) * 86400 * 1000);

    const userSession: UserSession = {
      id,
      session_token: token,
      ahoy_id: session.ahoy_id,
      email: session.email || null,
      name: session.name || null,
      access_token: session.access_token || null,
      expires_at: expires.toISOString(),
      created_at: now.toISOString(),
    };

    this.db.prepare(`
      INSERT INTO sessions (id, session_token, ahoy_id, email, name, access_token, expires_at, created_at)
      VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    `).run(
      userSession.id,
      userSession.session_token,
      userSession.ahoy_id,
      userSession.email,
      userSession.name,
      userSession.access_token,
      userSession.expires_at,
      userSession.created_at
    );

    return userSession;
  }

  getSession(token: string): UserSession | null {
    const row = this.db.prepare('SELECT * FROM sessions WHERE session_token = ? AND expires_at > ?').get(token, new Date().toISOString()) as UserSession | undefined;
    return row || null;
  }

  deleteSession(token: string): void {
    this.db.prepare('DELETE FROM sessions WHERE session_token = ?').run(token);
  }

  close() {
    this.db.close();
  }
}
