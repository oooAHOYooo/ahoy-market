<template>
  <div class="sitemap-page">
    <div class="sitemap-header">
      <h1>Sitemap</h1>
      <p>Browse all pages on Ahoy Indie Media</p>
    </div>
    <div class="sitemap-container">
      <nav class="sitemap-links">
        <router-link to="/">Home</router-link>
        <router-link to="/music">Music</router-link>
        <router-link to="/podcasts">Podcasts</router-link>
        <router-link to="/videos">Videos</router-link>
        <router-link to="/artists">Artists</router-link>
        <router-link to="/events">Events</router-link>
        <router-link to="/radio">Radio</router-link>
        <router-link to="/live-tv">AHOY TV</router-link>
        <router-link to="/merch">Merch</router-link>
        <router-link to="/my-saves">Saved</router-link>
        <router-link to="/recently-played">Recently Played</router-link>
        <router-link to="/playlists">Playlists</router-link>
        <router-link to="/search">Search</router-link>
        <router-link to="/account">Account</router-link>
        <router-link to="/settings">Settings</router-link>
        <router-link to="/downloads">Downloads</router-link>
        <router-link to="/focus">Focus</router-link>
        <router-link to="/feedback">Feedback</router-link>
        <router-link to="/contact">Contact</router-link>
        <router-link to="/privacy">Privacy</router-link>
        <router-link to="/terms">Terms</router-link>
        <router-link to="/security">Security</router-link>
      </nav>
    </div>
  </div>
</template>

<style scoped>
.sitemap-page { padding-bottom: 3rem; }
.sitemap-header { text-align: center; padding: 2rem 1.5rem 1rem; max-width: 560px; margin: 0 auto; }
.sitemap-header h1 { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; color: white; }
.sitemap-header p { margin: 0; color: rgba(255,255,255,0.6); font-size: 1rem; }
.sitemap-container { max-width: 560px; margin: 0 auto; padding: 1.5rem; }
.sitemap-links { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 0.5rem; }
.sitemap-links a { color: var(--accent-primary, #6ddcff); text-decoration: none; }
.sitemap-links a:hover { text-decoration: underline; }
</style>
