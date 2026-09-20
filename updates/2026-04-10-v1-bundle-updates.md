# Ahoy Indie Media v1.0.0 Bundle Updates
*Timestamp: 2026-04-10 10:15 EST*

This file summarizes the changes made to transition the Ahoy Indie Media Android project from a web-wrapper pointing at `https://app.ahoy.ooo` to a true bundled and offline-ready application.

## 1. Local Device Bundling
- **File:** `capacitor.config.ts`
- **Change:** Removed the `server` block (`server: { url: 'https://app.ahoy.ooo', cleartext: false }`). 
- **Reason:** This forces Capacitor to serve files from the local app bundle (`spa-dist` folder) instead of acting as a web view to a remote server. The app base UI will now load locally from the device even offline.

## 2. API Environment Variables for Bundled SPA
- **File:** `spa/.env.production` (Created)
- **Change:** Added `VITE_API_BASE=https://app.ahoy.ooo`
- **Reason:** Now that the app loads from the bundled device `localhost`, relative API paths (e.g. `/api/music`) won't work since the backend isn't bundled. Setting `VITE_API_BASE` ensures that Vite embeds the production API URL into the network requests inside the app bundle. The offline strategy in `useApi.js` remains perfectly intact.

## 3. Asset Integrity Fixes
- **File:** Renamed `spa/public/static/AHOY INDIE MEDIA RETRO.png` -> `spa/public/static/ahoy-retro.png`
- **File:** `spa/src/components/AppFooter.vue`
- **Change:** Updated references to match the new image naming conventions.
- **Reason:** Ensuring that Android bundler processes and generic web packagers do not silently break or miss the image due to uppercase characters and spaces.

## 4. Play Store V1 Version Bumps
- **File:** `package.json`
- **Change:** `"version": "0.2.4"` -> `"version": "1.0.0"`
- **File:** `android/app/build.gradle`
- **Change:** `versionName "0.2.4+...` -> `versionName "1.0.0+...`

## Note to Developer (or Claude!)
The system relies on CORS from the backend to fetch live content. Since the web bundle now runs locally on-device and reaches out cross-origin to `app.ahoy.ooo`, the Flask server needs `flask-cors` properly configured to accept requests with credentials from `capacitor://localhost` and `http://localhost`.
