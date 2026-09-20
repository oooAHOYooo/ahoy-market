<template>
  <div class="policy-page">
    <div class="policy-container">
      <h1 class="policy-title">Terms of Service</h1>
      <p class="policy-date">Last updated: April 2026</p>

      <div class="policy-content">
        <h3>1. Acceptance of Terms</h3>
        <p>By accessing and using Ahoy Indie Media ("Service"), you agree to be bound by these Terms of Service. If you do not agree, you may not use the Service.</p>

        <h3>2. User Eligibility & Account Responsibility</h3>
        <p>You must be at least 13 years old to use Ahoy. By creating an account, you certify that:</p>
        <ul>
          <li>You are of legal age to form a contract</li>
          <li>Information you provide is accurate and truthful</li>
          <li>You will keep your password confidential</li>
          <li>You are responsible for all activities on your account</li>
        </ul>
        <p>We are not liable for unauthorized account access. Notify support immediately if compromised.</p>

        <h3>3. Prohibited Conduct</h3>
        <p>You agree not to:</p>
        <ul>
          <li>Violate any applicable law or regulation</li>
          <li>Harass, threaten, or defame others</li>
          <li>Infringe intellectual property rights (copyright, trademark, patent)</li>
          <li>Share unauthorized content or credentials</li>
          <li>Attempt to gain unauthorized access to the Service</li>
          <li>Interfere with the Service's function (hacking, DDoS, etc.)</li>
          <li>Create fraudulent accounts or impersonate others</li>
          <li>Engage in spam or deceptive practices</li>
        </ul>

        <h3>4. Intellectual Property</h3>
        <p>Ahoy respects artist and creator rights. All original content on Ahoy (design, features, code) is owned by Ahoy or licensed partners. User-generated content (playlists, bookmarks) remains your property, but you grant Ahoy a license to use, display, and analyze it.</p>

        <h3>5. Payments, Wallet & Boosts</h3>
        <p>Wallet funds and artist boosts are final once processed. We do not offer refunds except:</p>
        <ul>
          <li>Duplicate charges (within 24 hours, verified)</li>
          <li>Unauthorized transactions (reported within 90 days)</li>
          <li>As required by law</li>
        </ul>
        <p>Stripe processes all payments. Their terms also apply at checkout. Funds expire after 2 years of inactivity.</p>

        <h3>6. Physical Merchandise</h3>
        <p>Merchandise purchases are subject to the return/refund policy displayed at checkout. Shipping times are estimates only. We are not liable for lost, damaged, or delayed shipments.</p>

        <h3>7. Disclaimer of Warranties</h3>
        <p>THE SERVICE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED. WE DISCLAIM ALL WARRANTIES INCLUDING MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, AND TITLE.</p>
        <p>We do not guarantee:</p>
        <ul>
          <li>Uninterrupted or error-free Service</li>
          <li>Availability of specific content</li>
          <li>Streaming quality or uptime</li>
        </ul>

        <h3>8. Limitation of Liability</h3>
        <p>TO THE EXTENT PERMITTED BY LAW, AHOY IS NOT LIABLE FOR:</p>
        <ul>
          <li>Indirect, incidental, or consequential damages</li>
          <li>Lost profits, data, or business interruption</li>
          <li>Any damages exceeding the amount you paid (if any)</li>
        </ul>
        <p>Some jurisdictions do not allow limitations; your rights may vary.</p>

        <h3>9. Account Termination</h3>
        <p>We may suspend or terminate your account for:</p>
        <ul>
          <li>Violation of these Terms</li>
          <li>Illegal activity or fraud</li>
          <li>Abuse of the Service or other users</li>
          <li>Unpaid or fraudulent transactions</li>
        </ul>
        <p>Upon termination, you lose access to your account. We may delete your data after 90 days.</p>

        <h3>10. Modifications to Service & Terms</h3>
        <p>We may change or discontinue features at any time. We will notify you of material changes to these Terms via in-app notification or email. Continued use means acceptance.</p>

        <h3>11. Indemnification</h3>
        <p>You agree to defend and hold harmless Ahoy from any claims arising from:</p>
        <ul>
          <li>Your use of the Service</li>
          <li>Violation of these Terms or any law</li>
          <li>Infringement of third-party rights</li>
        </ul>

        <h3>12. Governing Law</h3>
        <p>These Terms are governed by the laws of the United States, without regard to conflict of law principles. You consent to jurisdiction in the federal and state courts of New York.</p>

        <h3>13. Contact & Support</h3>
        <p>Questions about these Terms? Email <a href="mailto:support@ahoyindie.com">support@ahoyindie.com</a> or visit our <router-link to="/contact">contact page</router-link>.</p>

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
