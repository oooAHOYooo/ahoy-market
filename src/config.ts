import dotenv from 'dotenv';
dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3020', 10),
  host: process.env.HOST || '0.0.0.0',
  databasePath: process.env.DATABASE_PATH || './market.db',
  cookieSecret: process.env.COOKIE_SECRET || 'ahoy-market-session-secret-key-32chars-min',
  ahoyIdUrl: (process.env.AHOY_ID_URL || 'https://id.ahoy.ooo').replace(/\/$/, ''),
  clientId: process.env.AHOY_CLIENT_ID || 'app.ahoy.market',
  clientSecret: process.env.AHOY_CLIENT_SECRET || undefined,
  redirectUri: process.env.AHOY_REDIRECT_URI || 'http://127.0.0.1:3020/api/auth/callback',
  publicBaseUrl: (process.env.PUBLIC_BASE_URL || 'http://127.0.0.1:3020').replace(/\/$/, ''),
  playerUrl: (process.env.AHOY_PLAYER_URL || 'https://player.ahoy.ooo').replace(/\/$/, ''),
  streamerUrl: (process.env.AHOY_STREAMER_URL || 'https://app.ahoy.ooo').replace(/\/$/, ''),
  isProduction: process.env.NODE_ENV === 'production',
  stripeSecretKey: process.env.STRIPE_SECRET_KEY || '',
  stripeWebhookSecret: process.env.STRIPE_WEBHOOK_SECRET || '',

  // Audio Vault & Pre-Signing (AWS S3 / Cloudflare R2 / CloudFront)
  s3Bucket: process.env.AWS_S3_BUCKET || process.env.S3_BUCKET || '',
  s3Region: process.env.AWS_REGION || process.env.S3_REGION || 'us-east-2',
  s3AccessKeyId: process.env.AWS_ACCESS_KEY_ID || process.env.S3_ACCESS_KEY_ID || '',
  s3SecretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || process.env.S3_SECRET_ACCESS_KEY || '',
  s3Endpoint: (process.env.S3_ENDPOINT || '').replace(/\/$/, ''),
  s3UrlExpirationSeconds: parseInt(process.env.S3_URL_EXPIRATION_SECONDS || '900', 10), // 15 minutes default
  cloudFrontDomain: (process.env.CLOUDFRONT_DOMAIN || '').replace(/\/$/, '').replace(/^https?:\/\//, ''),
  cloudFrontKeyId: process.env.CLOUDFRONT_KEY_ID || '',
  cloudFrontPrivateKey: (process.env.CLOUDFRONT_PRIVATE_KEY || '').replace(/\\n/g, '\n'),
};

if (config.isProduction && !process.env.COOKIE_SECRET) {
  console.warn('⚠️ [SECURITY] COOKIE_SECRET is unset in production. Please set COOKIE_SECRET in your environment.');
}
