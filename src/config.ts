import dotenv from 'dotenv';
dotenv.config();

export const config = {
  port: parseInt(process.env.PORT || '3020', 10),
  host: process.env.HOST || '0.0.0.0',
  databasePath: process.env.DATABASE_PATH || './market.db',
  cookieSecret: process.env.COOKIE_SECRET || 'ahoy-market-session-secret-key-32chars-min',
  ahoyIdUrl: (process.env.AHOY_ID_URL || 'https://ahoy-id.onrender.com').replace(/\/$/, ''),
  clientId: process.env.AHOY_CLIENT_ID || 'app.ahoy.market',
  clientSecret: process.env.AHOY_CLIENT_SECRET || undefined,
  redirectUri: process.env.AHOY_REDIRECT_URI || 'http://127.0.0.1:3020/api/auth/callback',
  publicBaseUrl: (process.env.PUBLIC_BASE_URL || 'http://127.0.0.1:3020').replace(/\/$/, ''),
  playerUrl: (process.env.AHOY_PLAYER_URL || 'https://player.ahoy.ooo').replace(/\/$/, ''),
  streamerUrl: (process.env.AHOY_STREAMER_URL || 'https://app.ahoy.ooo').replace(/\/$/, ''),
  isProduction: process.env.NODE_ENV === 'production',
};
