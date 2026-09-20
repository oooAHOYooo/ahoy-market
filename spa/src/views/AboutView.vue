<template>
  <div class="about-page">
    <div class="about-content">
      <div class="about-hero">
        <div class="about-logo">
          <img src="/static/img/ahoy_logo.png" alt="Ahoy Indie Media Logo" />
        </div>
        <h1 class="about-title">Ahoy Indie Media</h1>
      </div>

      <div class="about-details">
        <div class="detail-block">
          <h3>Ownership</h3>
          <p>Ahoy Indie Media is owned by <strong>Ahoy Media Group LLC</strong>.</p>
        </div>

        <div class="detail-block">
          <h3>Development & Infrastructure</h3>
          <p>Developed and maintained by <strong>Little Market LLC</strong>.</p>
        </div>

        <div class="detail-block">
          <h3>Founder & Sole Developer</h3>
          <p>
            Created by <router-link to="/artists/alex-gonzalez" class="about-artist-link">Alex Gonzalez</router-link>.
          </p>
        </div>

        <div class="detail-block">
          <h3>Contact</h3>
          <p>Questions or feedback? <router-link to="/contact">Get in touch</router-link>.</p>
        </div>
      </div>

      <div class="about-footer">
        <router-link to="/" class="back-btn">
          <i class="fas fa-arrow-left"></i>
          Back to Explore
        </router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.about-page {
  min-height: 100vh;
  padding-bottom: 4rem;
}

.about-content {
  max-width: 720px;
  margin: 0 auto;
  padding: 4rem 1.5rem;
  text-align: center;
}

.about-hero {
  margin-bottom: 4rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  animation: fadeInDown 0.8s cubic-bezier(0.16, 1, 0.3, 1);
}

.about-logo img {
  width: 140px;
  height: auto;
  filter: drop-shadow(0 0 20px rgba(255, 0, 96, 0.25));
  animation: logoVitality 4s infinite ease-in-out;
}

.about-title {
  font-size: 3.5rem;
  font-weight: 900;
  letter-spacing: -0.03em;
  margin: 0;
  color: #fff;
  line-height: 1;
}

@keyframes logoVitality {
  0%, 100% { 
    transform: scale(1);
    filter: drop-shadow(0 0 20px rgba(255, 0, 96, 0.25));
  }
  50% { 
    transform: scale(1.08);
    filter: drop-shadow(0 0 35px rgba(255, 0, 96, 0.5));
  }
}

@keyframes fadeInDown {
  from {
    opacity: 0;
    transform: translateY(-20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.about-details {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  align-items: center;
}

.detail-block {
  width: 100%;
  padding: 2.25rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 24px;
  backdrop-filter: blur(20px);
  transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
  text-align: center;
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
}

.detail-block:nth-child(1) { animation-delay: 0.1s; }
.detail-block:nth-child(2) { animation-delay: 0.2s; }
.detail-block:nth-child(3) { animation-delay: 0.3s; }
.detail-block:nth-child(4) { animation-delay: 0.4s; }

.detail-block:hover {
  transform: translateY(-8px) scale(1.02);
  border-color: rgba(255, 0, 96, 0.4);
  background: rgba(255, 255, 255, 0.04);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
}

.detail-block h3 {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.2em;
  color: var(--primary-color, #ff0060);
  margin-bottom: 0.75rem;
  opacity: 0.9;
  font-weight: 700;
  mix-blend-mode: screen;
}

.detail-block p {
  font-size: 1.4rem;
  color: #fff;
  line-height: 1.3;
  margin: 0;
  font-weight: 600;
}

.detail-block strong {
  color: var(--accent-primary, #6ddcff);
  font-weight: 800;
}

.detail-block a,
.about-artist-link {
  color: var(--accent-primary, #6ddcff);
  text-decoration: none;
  font-weight: 700;
  position: relative;
  transition: color 0.3s ease;
}

.detail-block a::after,
.about-artist-link::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 0;
  width: 100%;
  height: 2px;
  background: currentColor;
  transform: scaleX(0);
  transition: transform 0.3s cubic-bezier(0.16, 1, 0.3, 1);
  transform-origin: right;
}

.detail-block a:hover::after,
.about-artist-link:hover::after {
  transform: scaleX(1);
  transform-origin: left;
}

.about-footer {
  margin-top: 4rem;
  animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) both;
  animation-delay: 0.6s;
}

.back-btn {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 100px;
  color: #fff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
}

.back-btn:hover {
  background: var(--primary-color, #ff0060);
  border-color: transparent;
  transform: scale(1.05);
  box-shadow: 0 10px 20px rgba(255, 0, 96, 0.3);
}

@media (max-width: 768px) {
  .about-content {
    padding: 3rem 1.25rem;
  }

  .about-title {
    font-size: 2.25rem;
  }

  .detail-block {
    padding: 1.75rem;
  }

  .detail-block p {
    font-size: 1.2rem;
  }
}
</style>
