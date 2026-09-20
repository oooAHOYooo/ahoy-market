<template>
  <div class="contact-page">
    <div class="contact-container">
      <h1 class="contact-title">Contact Support</h1>

      <div class="contact-section">
        <h3>Get in Touch</h3>
        <p>We'd love to hear from you. Whether you have a question, suggestion, or need support, reach out:</p>

        <div class="contact-methods">
          <div class="contact-method">
            <i class="fas fa-envelope"></i>
            <div>
              <h4>Email</h4>
              <a href="mailto:support@ahoyindie.com">support@ahoyindie.com</a>
              <p class="contact-time">Response time: 24-48 hours</p>
            </div>
          </div>

          <div class="contact-method">
            <i class="fas fa-message"></i>
            <div>
              <h4>Feedback Form</h4>
              <p>Share feature requests and product feedback directly in the app.</p>
              <router-link to="/feedback" class="contact-btn">Submit Feedback</router-link>
            </div>
          </div>

          <div class="contact-method">
            <i class="fas fa-bug"></i>
            <div>
              <h4>Report a Bug</h4>
              <p>Found an issue? Email support@ahoyindie.com with "BUG:" in the subject line and we'll investigate.</p>
            </div>
          </div>

          <div class="contact-method">
            <i class="fas fa-lock"></i>
            <div>
              <h4>Security Issue?</h4>
              <p>Report vulnerabilities responsibly to support@ahoyindie.com. Do not post publicly.</p>
            </div>
          </div>
        </div>
      </div>

      <div class="contact-section">
        <h3>Frequently Asked Questions</h3>
        <div class="faq-item">
          <h4>How do I delete my account?</h4>
          <p>Go to Account settings → Security → Delete Account. Your data will be permanently removed (except financial records required by law).</p>
        </div>
        <div class="faq-item">
          <h4>Can I get a refund?</h4>
          <p>Wallet funds and boosts are final, but we offer refunds for duplicate charges or unauthorized transactions within 90 days.</p>
        </div>
        <div class="faq-item">
          <h4>How do I cancel a subscription or recurring payment?</h4>
          <p>Go to Account → Payments, or email support@ahoyindie.com and we'll help.</p>
        </div>
        <div class="faq-item">
          <h4>Is my data safe?</h4>
          <p>Yes, we use industry-standard encryption and security practices. See our <router-link to="/privacy">Privacy Policy</router-link> for details.</p>
        </div>
      </div>

      <div class="contact-links">
        <router-link to="/privacy" class="footer-link">Privacy Policy</router-link>
        <router-link to="/terms" class="footer-link">Terms of Service</router-link>
        <router-link to="/" class="footer-link">Back to Ahoy</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.contact-page { padding-bottom: 3rem; }
.contact-container { max-width: 720px; margin: 0 auto; padding: 1.5rem; color: rgba(255,255,255,0.85); line-height: 1.7; }
.contact-title { font-size: 2rem; font-weight: 700; margin: 0 0 1.5rem; color: white; }

.contact-section { margin: 2rem 0; }
.contact-section h3 { font-size: 1.3rem; font-weight: 600; margin: 0 0 1rem; color: white; }
.contact-section p { margin: 0.75rem 0; }

.contact-methods {
  display: grid;
  gap: 1.5rem;
  margin: 1rem 0;
}

.contact-method {
  display: flex;
  gap: 1rem;
  padding: 1.25rem;
  background: rgba(255,255,255,0.04);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 0.75rem;
}

.contact-method i {
  font-size: 1.5rem;
  color: var(--accent-primary, #6ddcff);
  flex-shrink: 0;
  margin-top: 0.25rem;
}

.contact-method h4 {
  margin: 0 0 0.5rem;
  color: white;
  font-size: 1rem;
}

.contact-method p { margin: 0.4rem 0; font-size: 0.95rem; }
.contact-time { font-size: 0.85rem; color: rgba(255,255,255,0.6); }

.contact-method a {
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
}

.contact-method a:hover { text-decoration: underline; }

.contact-btn {
  display: inline-block;
  margin-top: 0.5rem;
  padding: 0.5rem 1rem;
  background: var(--accent-primary, #6ddcff);
  color: #111;
  border-radius: 0.5rem;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.2s;
}

.contact-btn:hover { opacity: 0.85; }

.faq-item {
  margin: 1.5rem 0;
  padding: 1rem;
  background: rgba(255,255,255,0.02);
  border-left: 3px solid var(--accent-primary, #6ddcff);
  border-radius: 0.5rem;
}

.faq-item h4 {
  margin: 0 0 0.5rem;
  color: white;
  font-size: 1rem;
}

.faq-item p { margin: 0; font-size: 0.95rem; }

.contact-links {
  display: flex;
  gap: 1.5rem;
  flex-wrap: wrap;
  margin-top: 2rem;
  padding-top: 2rem;
  border-top: 1px solid rgba(255,255,255,0.1);
}

.footer-link {
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s;
}

.footer-link:hover { opacity: 0.8; }
</style>
