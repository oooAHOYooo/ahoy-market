import { createHmac, createHash, createSign } from 'node:crypto';
import { config } from './config.js';

function sha256Hex(data: string): string {
  return createHash('sha256').update(data).digest('hex');
}

function hmac(key: Buffer | string, data: string): Buffer {
  return createHmac('sha256', key).update(data).digest();
}

function hmacHex(key: Buffer | string, data: string): string {
  return createHmac('sha256', key).update(data).digest('hex');
}

function getSigV4Key(key: string, dateStamp: string, region: string, service: string): Buffer {
  const kDate = hmac(`AWS4${key}`, dateStamp);
  const kRegion = hmac(kDate, region);
  const kService = hmac(kRegion, service);
  return hmac(kService, 'aws4_request');
}

export function isPrivateStorageConfigured(): boolean {
  const hasS3 = Boolean(config.s3AccessKeyId && config.s3SecretAccessKey);
  const hasCloudFront = Boolean(config.cloudFrontDomain && config.cloudFrontKeyId && config.cloudFrontPrivateKey);
  return hasS3 || hasCloudFront;
}

export function generateS3PresignedUrl(
  rawUrlOrKey: string,
  options?: { expiresInSeconds?: number; region?: string; bucket?: string }
): string {
  if (!config.s3AccessKeyId || !config.s3SecretAccessKey) {
    return rawUrlOrKey;
  }

  const region = options?.region || config.s3Region || 'us-east-2';
  const expiresInSeconds = options?.expiresInSeconds || config.s3UrlExpirationSeconds || 900;

  let host: string;
  let pathname: string;
  let origin: string;

  if (rawUrlOrKey.startsWith('http://') || rawUrlOrKey.startsWith('https://')) {
    const parsed = new URL(rawUrlOrKey);
    host = parsed.host;
    pathname = parsed.pathname;
    origin = parsed.origin;
  } else {
    const key = rawUrlOrKey.replace(/^\//, '');
    const bucket = options?.bucket || config.s3Bucket;
    if (config.s3Endpoint) {
      const endpoint = new URL(config.s3Endpoint);
      host = endpoint.host;
      origin = endpoint.origin;
      pathname = bucket ? `/${bucket}/${key}` : `/${key}`;
    } else {
      host = bucket ? `${bucket}.s3.${region}.amazonaws.com` : `s3.${region}.amazonaws.com`;
      origin = `https://${host}`;
      pathname = `/${key}`;
    }
  }

  const now = new Date();
  const amzDate = now.toISOString().replace(/[:-]|\.\d{3}/g, '');
  const dateStamp = amzDate.substring(0, 8);
  const credentialScope = `${dateStamp}/${region}/s3/aws4_request`;

  const params = new URLSearchParams();
  params.set('X-Amz-Algorithm', 'AWS4-HMAC-SHA256');
  params.set('X-Amz-Credential', `${config.s3AccessKeyId}/${credentialScope}`);
  params.set('X-Amz-Date', amzDate);
  params.set('X-Amz-Expires', String(expiresInSeconds));
  params.set('X-Amz-SignedHeaders', 'host');

  params.sort();
  const canonicalQuery = params.toString();
  const canonicalHeaders = `host:${host}\n`;
  const signedHeaders = 'host';
  const payloadHash = 'UNSIGNED-PAYLOAD';

  const canonicalRequest = [
    'GET',
    pathname,
    canonicalQuery,
    canonicalHeaders,
    signedHeaders,
    payloadHash,
  ].join('\n');

  const stringToSign = [
    'AWS4-HMAC-SHA256',
    amzDate,
    credentialScope,
    sha256Hex(canonicalRequest),
  ].join('\n');

  const signingKey = getSigV4Key(config.s3SecretAccessKey, dateStamp, region, 's3');
  const signature = hmacHex(signingKey, stringToSign);

  return `${origin}${pathname}?${canonicalQuery}&X-Amz-Signature=${signature}`;
}

export function generateCloudFrontSignedUrl(
  rawUrlOrKey: string,
  options?: { expiresInSeconds?: number }
): string {
  if (!config.cloudFrontDomain || !config.cloudFrontKeyId || !config.cloudFrontPrivateKey) {
    return rawUrlOrKey;
  }

  const expiresInSeconds = options?.expiresInSeconds || config.s3UrlExpirationSeconds || 900;
  const expiresEpoch = Math.floor(Date.now() / 1000) + expiresInSeconds;

  let pathname: string;
  if (rawUrlOrKey.startsWith('http://') || rawUrlOrKey.startsWith('https://')) {
    pathname = new URL(rawUrlOrKey).pathname;
  } else {
    pathname = rawUrlOrKey.startsWith('/') ? rawUrlOrKey : `/${rawUrlOrKey}`;
  }

  const resourceUrl = `https://${config.cloudFrontDomain}${pathname}`;
  const cannedPolicy = JSON.stringify({
    Statement: [
      {
        Resource: resourceUrl,
        Condition: {
          DateLessThan: { 'AWS:EpochTime': expiresEpoch },
        },
      },
    ],
  });

  const signer = createSign('RSA-SHA1');
  signer.update(cannedPolicy);
  const signature = signer.sign(config.cloudFrontPrivateKey, 'base64url');

  const urlObj = new URL(resourceUrl);
  urlObj.searchParams.set('Expires', String(expiresEpoch));
  urlObj.searchParams.set('Signature', signature);
  urlObj.searchParams.set('Key-Pair-Id', config.cloudFrontKeyId);

  return urlObj.toString();
}

export function getAuthorizedAudioUrl(
  rawAudioUrl: string,
  options?: { expiresInSeconds?: number }
): string {
  if (!rawAudioUrl) return rawAudioUrl;

  // 1. CloudFront Signed URL (if configured)
  if (config.cloudFrontDomain && config.cloudFrontKeyId && config.cloudFrontPrivateKey) {
    return generateCloudFrontSignedUrl(rawAudioUrl, options);
  }

  // 2. AWS S3 / Cloudflare R2 Pre-Signed URL (if configured)
  if (config.s3AccessKeyId && config.s3SecretAccessKey) {
    return generateS3PresignedUrl(rawAudioUrl, options);
  }

  // 3. Fallback: Return raw audio URL
  return rawAudioUrl;
}
