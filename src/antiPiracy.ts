import { createHmac, timingSafeEqual } from 'node:crypto';
import { config } from './config.js';
import { Track } from './db.js';

export interface InscriptionMetadata {
  trackId: string;
  trackTitle: string;
  artist: string;
  ownerAhoyId: string;
  entitlementId?: string;
  grantedAt?: string;
}

export interface ProvenanceReceipt {
  standard: string;
  owner_ahoy_id: string;
  track_id: string;
  title: string;
  artist: string;
  entitlement_id: string;
  inscribed_at: string;
  forensic_signature: string;
  license: string;
}

/**
 * Strips private master audio URLs from public track objects so that scrapers
 * and unauthenticated visitors cannot leech full-length masters.
 */
export function sanitizePublicTrack(track: Track): Omit<Track, 'full_audio_url'> {
  const { full_audio_url: _discard, ...publicTrack } = track;
  return publicTrack;
}

/**
 * Generate a short-lived, tamper-proof download token bound to a track and user.
 * Valid for 15 minutes by default.
 */
export function generateDownloadToken(trackId: string, ahoyId: string, expiresInSeconds = 900): string {
  const expiresAt = Math.floor(Date.now() / 1000) + expiresInSeconds;
  const payload = `${trackId}:${ahoyId}:${expiresAt}`;
  const sig = createHmac('sha256', config.cookieSecret).update(payload).digest('hex');
  return Buffer.from(`${payload}:${sig}`).toString('base64url');
}

/**
 * Verify a download token. Returns payload if valid and unexpired, or null.
 */
export function verifyDownloadToken(
  token: string,
  expectedTrackId?: string
): { trackId: string; ahoyId: string; expiresAt: number } | null {
  try {
    const raw = Buffer.from(token, 'base64url').toString('utf8');
    const parts = raw.split(':');
    if (parts.length !== 4) return null;
    const [trackId, ahoyId, expiresStr, sig] = parts;
    const expiresAt = parseInt(expiresStr, 10);
    if (!Number.isFinite(expiresAt) || Math.floor(Date.now() / 1000) > expiresAt) {
      return null;
    }
    if (expectedTrackId && trackId !== expectedTrackId) {
      return null;
    }
    if (!/^[0-9a-f]{64}$/i.test(sig)) {
      return null;
    }
    const payload = `${trackId}:${ahoyId}:${expiresAt}`;
    const expectedSig = createHmac('sha256', config.cookieSecret).update(payload).digest('hex');
    const sigBuf = Buffer.from(sig, 'hex');
    const expBuf = Buffer.from(expectedSig, 'hex');
    if (sigBuf.length !== expBuf.length || !timingSafeEqual(sigBuf, expBuf)) {
      return null;
    }
    return { trackId, ahoyId, expiresAt };
  } catch {
    return null;
  }
}

/**
 * Generate a cryptographic HMAC forensic signature tying the audio to the buyer.
 */
export function generateForensicSignature(trackId: string, ownerAhoyId: string, entitlementId = 'direct_grant'): string {
  return createHmac('sha256', config.cookieSecret)
    .update(`ahoy_sovereign_master:${trackId}:${ownerAhoyId}:${entitlementId}`)
    .digest('hex');
}

/**
 * Constructs an ID3v2.3 tag buffer with the provided frames.
 */
function buildId3v2Tag(frames: { id: string; text: string }[]): Buffer {
  const frameBuffers: Buffer[] = [];
  for (const { id, text } of frames) {
    const textBuf = Buffer.from(text, 'utf8');
    // Encoding byte: 0x03 for UTF-8
    const frameContent = Buffer.concat([Buffer.from([0x03]), textBuf]);
    const header = Buffer.alloc(10);
    header.write(id.padEnd(4, ' ').substring(0, 4), 0, 4, 'ascii');
    header.writeUInt32BE(frameContent.length, 4);
    frameBuffers.push(header, frameContent);
  }
  const allFrames = Buffer.concat(frameBuffers);
  const tagSize = allFrames.length;

  // Syncsafe integer for ID3v2 tag size (7 bits per byte)
  const syncsafe = Buffer.alloc(4);
  syncsafe[0] = (tagSize >> 21) & 0x7f;
  syncsafe[1] = (tagSize >> 14) & 0x7f;
  syncsafe[2] = (tagSize >> 7) & 0x7f;
  syncsafe[3] = tagSize & 0x7f;

  const id3Header = Buffer.concat([
    Buffer.from('ID3', 'ascii'),
    Buffer.from([0x03, 0x00]), // ID3v2.3
    Buffer.from([0x00]),       // Flags
    syncsafe,
  ]);

  return Buffer.concat([id3Header, allFrames]);
}

/**
 * Inscribes forensic digital provenance into audio:
 * 1. Standard ID3v2 frames (TOWN [Owner], TCOP [Copyright], COMM [Ledger Comment], TXXX [Proof])
 * 2. Trailing tamper-proof AHOY Sovereign Ledger Provenance block at EOF
 */
export function inscribeAudioProvenance(audioBuffer: Buffer, meta: InscriptionMetadata): Buffer {
  const signature = generateForensicSignature(meta.trackId, meta.ownerAhoyId, meta.entitlementId);
  const entitlementId = meta.entitlementId || 'direct_grant';
  const grantedAt = meta.grantedAt || new Date().toISOString();

  const receipt: ProvenanceReceipt = {
    standard: 'AHOY-SOVEREIGN-PROVENANCE-v1',
    owner_ahoy_id: meta.ownerAhoyId,
    track_id: meta.trackId,
    title: meta.trackTitle,
    artist: meta.artist,
    entitlement_id: entitlementId,
    inscribed_at: grantedAt,
    forensic_signature: signature,
    license: 'Sovereign personal listening license. Commercial redistribution, mass leaking, or unauthorized public re-upload is forensically traceable to this owner.',
  };

  const watermarkFrames = [
    { id: 'TOWN', text: meta.ownerAhoyId },
    { id: 'TCOP', text: `(C) ${meta.artist}. Licensed to ${meta.ownerAhoyId}` },
    { id: 'COMM', text: `AHOY Sovereign Master • Inscribed to ${meta.ownerAhoyId} • Ledger: ${entitlementId} • Sig: ${signature.slice(0, 16)}` },
    { id: 'TXXX', text: `AHOY_PROVENANCE:${meta.ownerAhoyId}:${signature}` },
  ];

  let audioWithTags = audioBuffer;
  // If the audio buffer does not start with an ID3v2 tag, prepend one
  if (audioBuffer.length < 3 || audioBuffer.subarray(0, 3).toString('ascii') !== 'ID3') {
    const id3 = buildId3v2Tag([
      { id: 'TIT2', text: meta.trackTitle },
      { id: 'TPE1', text: meta.artist },
      ...watermarkFrames,
    ]);
    audioWithTags = Buffer.concat([id3, audioBuffer]);
  }

  // Trailing cryptographic ledger trailer at EOF
  const trailerText = `\n\n---BEGIN AHOY SOVEREIGN PROVENANCE LEDGER---\n${JSON.stringify(receipt, null, 2)}\n---END AHOY SOVEREIGN PROVENANCE LEDGER---\n`;
  const trailerBuf = Buffer.from(trailerText, 'utf8');

  return Buffer.concat([audioWithTags, trailerBuf]);
}

/**
 * Extracts the inscribed forensic provenance receipt from an audio buffer if present.
 */
export function extractAudioProvenance(audioBuffer: Buffer): ProvenanceReceipt | null {
  try {
    const content = audioBuffer.toString('utf8');
    const startTag = '---BEGIN AHOY SOVEREIGN PROVENANCE LEDGER---';
    const endTag = '---END AHOY SOVEREIGN PROVENANCE LEDGER---';
    const startIndex = content.lastIndexOf(startTag);
    const endIndex = content.lastIndexOf(endTag);
    if (startIndex === -1 || endIndex === -1 || endIndex <= startIndex) {
      return null;
    }
    const jsonStr = content.substring(startIndex + startTag.length, endIndex).trim();
    return JSON.parse(jsonStr) as ProvenanceReceipt;
  } catch {
    return null;
  }
}

/**
 * In-memory sliding window rate limiter to protect audio endpoints from automated mass scraping/leeching.
 */
export class AntiLeechRateLimiter {
  private requests = new Map<string, number[]>();
  private readonly maxRequests: number;
  private readonly windowMs: number;

  constructor(maxRequests = 20, windowMs = 5 * 60 * 1000) {
    this.maxRequests = maxRequests;
    this.windowMs = windowMs;
  }

  isRateLimited(key: string): { limited: boolean; remaining: number; retryAfterSeconds: number } {
    const now = Date.now();
    const timestamps = (this.requests.get(key) || []).filter(t => now - t < this.windowMs);

    if (timestamps.length >= this.maxRequests) {
      const oldest = timestamps[0];
      const retryAfterSeconds = Math.ceil((oldest + this.windowMs - now) / 1000);
      return { limited: true, remaining: 0, retryAfterSeconds };
    }

    timestamps.push(now);
    this.requests.set(key, timestamps);

    // Housekeeping: prevent memory growth if thousands of unique keys accumulate
    if (this.requests.size > 2000) {
      for (const [k, times] of this.requests.entries()) {
        const valid = times.filter(t => now - t < this.windowMs);
        if (valid.length === 0) this.requests.delete(k);
        else this.requests.set(k, valid);
      }
    }

    return { limited: false, remaining: this.maxRequests - timestamps.length, retryAfterSeconds: 0 };
  }

  reset(): void {
    this.requests.clear();
  }
}

export const antiLeechLimiter = new AntiLeechRateLimiter(20, 5 * 60 * 1000);
