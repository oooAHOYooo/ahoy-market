# Ahoy Console Hardware Project — Setup Complete

You've got a full hardware initiative scaffolded for the Ahoy Console farmers market launch in May 2026.

## What's been created

### Core Documentation
- **`hardware/README.md`** — Overview, quick-start, BOM, troubleshooting for manufacturers
- **`hardware/bom.md`** — Detailed bill of materials, suppliers, bulk pricing, break-even analysis
- **`hardware/FARMERS_MARKET.md`** — Sales script, pricing, demo setup, customer flow, inventory planning
- **`HARDWARE_SETUP.md`** — This file (navigation guide)

### Software (Pi-side)
- **`hardware/pi-image/build.sh`** — Complete setup script for Pi OS Lite → kiosk mode
  - Installs Chromium, Openbox, WiFi provisioning portal
  - Configures systemd services for first-boot setup + kiosk mode
  - Disables unnecessary services to save RAM
  - One command to set up a fresh Pi

### Hardware Research
- **`hardware/remote/research.md`** — Remote control options, Rii Mini i8+ specs, bulk pricing, testing checklist

### Packaging
- **`hardware/packaging/design-brief.md`** — Box dimensions, printing spec, color palette, messaging
- **`hardware/packaging/unboxing-order.md`** — Physical layout, packing sequence, quick-start card template

## Architecture overview

```
Pi Zero 2 W boots
  ↓
Does /etc/wpa_supplicant/wpa_supplicant.conf exist?
  ├─ YES → ahoy-kiosk.service → Chromium → app.ahoy.ooo
  └─ NO  → ahoy-setup.service → Flask portal on "Ahoy-Setup" WiFi
             ↓ (customer enters home WiFi credentials)
             ↓ (saves config, reboots)
             → ahoy-kiosk.service (on next boot)
```

**The Pi is purely a thin client.** No Flask app running locally (except the WiFi setup portal). All content comes from `app.ahoy.ooo` over the internet.

## Next steps (in order)

### 1. **Test the software (THIS WEEK)**
   - Order or find a spare Pi Zero 2 W + microSD card
   - Flash with Raspberry Pi OS Lite (64-bit, SSH enabled)
   - SSH in: `ssh pi@<hostname>.local`
   - Run: `curl -sL https://raw.githubusercontent.com/oooAHOYooo/ahoy-little-platform/main/hardware/pi-image/build.sh | bash`
   - Reboot and verify "Ahoy-Setup" WiFi appears, portal works, then loads app.ahoy.ooo
   - **Fix any bugs in `build.sh` based on what you learn** (systemd service issues, slow boot, etc.)
   - Time: ~1 hour for first test, 20 min for subsequent iterations

### 2. **Order long-lead items (BY MARCH 31)**
   - **Pi Zero 2 W**: 30 units (Adafruit, RS Electronics, or official distributors)
   - **Cardboard boxes**: 30 units (order from local print shop or Packhelp)
   - **MicroSD cards**: 35 units (bulk from Amazon/Newegg)
   - **HDMI cables**: 35 units (Monoprice or local electronics)
   - **OTG adapters**: 35 units (bulk from AliExpress or Amazon)
   - **Rii Mini i8+ remotes**: 20–25 units (AliExpress bulk or Amazon)
   - Time: ~30 min to research suppliers, place orders, track delivery dates

### 3. **Finalize design (BY APRIL 7)**
   - Design 2-color cardboard box graphic (use Canva or local designer)
   - Finalize quick-start card copy & design
   - Print samples from your chosen vendor
   - Approve final design with printer

### 4. **Test & refine software (APRIL 7–13)**
   - Boot multiple Pi consoles (test hardware variance, HDMI modes)
   - Test WiFi portal on different phone models (iOS, Android)
   - Test video playback on the TV
   - Test remote pairing and input
   - **Document any tweaks** back into `build.sh`

### 5. **Assembly day (APRIL 21–27)**
   - Assemble 20–30 units with quick-start cards
   - Test each one end-to-end (WiFi setup + app load)
   - Box them up

### 6. **Demo dry-run (APRIL 28–MAY 4)**
   - Set up a TV demo at home or a friend's place
   - Test your sales pitch and flow
   - Verify pricing cards are clear
   - Plan table layout and signage

### 7. **Go live (MAY)**
   - Set up farmers market table
   - Sell Ahoy Consoles 🎉

## Budget & timeline checklist

### Materials (for 25–30 units)
- [ ] Pi Zero 2 W × 30: ~$450 (Adafruit/official)
- [ ] MicroSD 16GB × 35: ~$105 (bulk)
- [ ] HDMI cables × 35: ~$70 (bulk)
- [ ] OTG adapters × 35: ~$35 (bulk)
- [ ] Cardboard boxes × 30: ~$90 (local print)
- [ ] Rii remotes × 25: ~$200 (bulk, optional for initial inventory)
- **Total: ~$950–1,150**

### Revenue (conservative estimate)
- Assume 20 units sold in May
- 50% console only ($50), 50% bundle ($65)
- Average: $57.50/unit × 20 = **$1,150**
- Profit: ~$200 (after materials, before labor)

Scale to 30 units sold: **$1,050 profit** (52 hours of assembly + marketing, so ~$20/hour)

### Critical path items
- **Pi availability** (order ASAP—often out of stock)
- **Cardboard printing** (2–3 week lead time—design now)
- **Your software testing time** (2–3 weeks to work out bugs)

Everything else is flexible (remotes, cables, etc.).

## What to do RIGHT NOW

1. **Read `hardware/README.md`** to understand the full picture
2. **Order one Pi Zero 2 W + test the `build.sh` script** to confirm software works
3. **Research cardboard vendors** and get 1–2 sample prices
4. **Check Pi Zero 2 W availability** at your preferred distributors (place the bulk order the day they have stock)

## File structure reference

```
hardware/
├── README.md                          ← Start here for manufacturers
├── bom.md                             ← Cost breakdown & suppliers
├── FARMERS_MARKET.md                  ← Sales pitch & demo setup
├── pi-image/
│   ├── build.sh                       ← THE critical script (run on fresh Pi OS)
│   ├── setup-portal/
│   │   ├── app.py                     (embedded in build.sh for now)
│   │   └── templates/index.html       (embedded in build.sh for now)
│   └── services/
│       └── [systemd files]            (embedded in build.sh for now)
├── remote/
│   └── research.md                    ← Rii Mini i8+ specs & testing
└── packaging/
    ├── design-brief.md                ← Box printing spec
    └── unboxing-order.md              ← Packing guide
```

---

**Questions or blockers?** All the details are in the markdown files above. Start with `hardware/README.md` for the full technical overview.

Good luck at the farmers market! 🎬
