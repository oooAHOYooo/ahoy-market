<template>
  <div class="policy-page">
    <div class="policy-container">
      <h1 class="policy-title">Privacy Policy</h1>
      <p class="policy-date">Last updated: April 2026</p>

      <div class="policy-content">
        <h3>1. Information We Collect</h3>
        <p>We collect information you provide directly when you:</p>
        <ul>
          <li>Create an account (email, username, display name, password)</li>
          <li>Use wallet or payment features (processed securely via Stripe)</li>
          <li>Add bookmarks, playlists, or interact with content</li>
          <li>Submit feedback or contact support</li>
          <li>Use our service (automatically collected)</li>
        </ul>
        <p><strong>Automatic data:</strong> Device type, browser info, listening history, playback timestamps, IP address, and analytics events (via PostHog).</p>

        <h3>2. How We Use Your Information</h3>
        <p>We use your data to:</p>
        <ul>
          <li>Provide, maintain, and improve the Ahoy service</li>
          <li>Personalize your experience and recommendations</li>
          <li>Process payments and manage your wallet</li>
          <li>Send service updates, newsletters, and support responses</li>
          <li>Analyze usage patterns to improve features</li>
          <li>Comply with legal obligations</li>
        </ul>
        <p>Data used for "Now Playing" feeds and leaderboards is anonymized. You control sharing via Account settings.</p>

        <h3>3. Data Sharing & Third Parties</h3>
        <p>We do not sell your personal data. We share information only with:</p>
        <ul>
          <li><strong>Stripe:</strong> For secure payment processing</li>
          <li><strong>PostHog:</strong> For anonymized usage analytics and product analytics</li>
          <li><strong>Resend:</strong> For email delivery (transactional only)</li>
          <li><strong>Legal authorities:</strong> When required by law</li>
        </ul>

        <h3>4. Data Retention & Deletion</h3>
        <p>We retain your data while your account is active. You can delete your account anytime via Account settings, which removes:</p>
        <ul>
          <li>Profile, username, email</li>
          <li>Bookmarks, playlists, saved content</li>
          <li>Listening history and preferences</li>
        </ul>
        <p>Financial records are retained as required by law (typically 7 years). Deletion requests are processed within 30 days.</p>

        <h3>5. GDPR & Your Rights (EU/UK Users)</h3>
        <p>You have the right to:</p>
        <ul>
          <li>Access your personal data</li>
          <li>Correct inaccurate data</li>
          <li>Request deletion (right to be forgotten)</li>
          <li>Export your data (portability)</li>
          <li>Withdraw consent at any time</li>
        </ul>
        <p>Contact support@ahoyindie.com to exercise these rights.</p>

        <h3>6. Security</h3>
        <p>We implement industry-standard security:</p>
        <ul>
          <li>HTTPS/TLS encryption for data in transit</li>
          <li>Password hashing (bcrypt) for account protection</li>
          <li>Secure authentication with session tokens</li>
          <li>Regular security reviews</li>
        </ul>
        <p>No system is 100% secure. Report security vulnerabilities to support@ahoyindie.com.</p>

        <h3>7. Children's Privacy</h3>
        <p>Ahoy is not intended for users under 13. We do not knowingly collect data from children. If we learn we've collected from a user under 13, we will delete that data immediately.</p>

        <h3>8. Changes to This Policy</h3>
        <p>We may update this policy. Material changes will be announced in-app. Continued use of Ahoy constitutes acceptance.</p>

        <h3>9. Contact Us</h3>
        <p>Questions about privacy? Email <a href="mailto:support@ahoyindie.com">support@ahoyindie.com</a> or visit our <router-link to="/contact">contact page</router-link>.</p>

        <router-link to="/" class="policy-back">Back to Ahoy</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.policy-page { padding-bottom: 3rem; }
.policy-container { max-width: 720px; margin: 0 auto; padding: 1.5rem; }
.policy-title { font-size: 2rem; font-weight: 700; margin: 0 0 0.5rem; color: white; }
.policy-date { font-size: 0.9rem; color: rgba(255,255,255,0.6); margin: 0 0 2rem; }
.policy-content { color: rgba(255,255,255,0.85); line-height: 1.7; }
.policy-content h3 { font-size: 1.2rem; font-weight: 600; margin: 1.5rem 0 0.75rem; color: white; }
.policy-content p { margin: 0.75rem 0; }
.policy-content ul { margin: 0.75rem 0; padding-left: 1.5rem; }
.policy-content li { margin: 0.4rem 0; }
.policy-content a { color: var(--accent-primary, #6ddcff); text-decoration: none; }
.policy-content a:hover { text-decoration: underline; }
.policy-back { display: inline-block; margin-top: 2rem; color: var(--accent-primary); text-decoration: none; font-weight: 600; }
.policy-back:hover { text-decoration: underline; }
</style>
