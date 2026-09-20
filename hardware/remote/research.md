# Remote Control Options

For Ahoy Console, we need a **combo keyboard + trackpad** that:
- Connects via USB 2.4GHz dongle (Pi Zero 2W has 1 USB OTG port)
- Works in Chromium for keyboard input (WiFi password) and trackpad (browse)
- Costs $8–12 at bulk (25+ units)
- Is durable and responsive

## Recommended: Rii Mini i8+

**Model:** Rii Mini i8+ Wireless Keyboard+Trackpad (2.4GHz)

- **Cost:** $8–12 USD per unit (AliExpress/Amazon at bulk, 25+ qty)
- **Features:**
  - USB dongle (no pairing needed, just plug in)
  - Qwerty keyboard
  - Integrated touchpad
  - Rechargeable (USB-C or micro USB, varies by batch)
  - Works on Linux/RPi without drivers
- **Availability:** Stock on AliExpress, Amazon, typically 5–10 day shipping (AliExpress), 2 day (Amazon Prime)
- **Notes:**
  - Multiple clones exist; order from verified sellers with 100+ sales
  - Some versions have backlight (nice for dark rooms), some don't
  - Trackpad is small but adequate for TV navigation

### Where to buy (bulk)
- **AliExpress:** Search "Rii Mini i8+" — filter by "ships from China" + 50+ sold, expect $7–10/unit, 7–14 day lead
- **Amazon:** $12–15/unit, Prime eligible (2 day shipping if needed for testing)
- **Alibaba:** 100+ unit bulk pricing, ~$6–8/unit but 30+ day lead (too late for May)

### Testing checklist
- [ ] Powers on when USB dongle inserted
- [ ] Keyboard types characters in Chromium address bar
- [ ] Trackpad click + drag works in Ahoy app (scroll, tap video)
- [ ] Battery lasts 4+ hours on a charge
- [ ] No lag/responsiveness issues

---

## Alternatives (if Rii unavailable)

### Budget option: Generic 2.4GHz combos (~$5–7/unit)

**Example:** Generic "Wireless Keyboard Touchpad" on AliExpress

- Pros: Cheap, works in Linux
- Cons: Variable quality, lag issues, may have dead pixels or buttons
- **Recommendation:** Test one sample before bulk order

### Premium option: Rii Mini i7 (~$12–15/unit)

- Backlit keyboard (better in dark rooms)
- Slightly better build quality
- Still keyboard-first (not gaming-focused)

### Non-recommended: Standard mouse + keyboard combo

- Requires USB hub (adds cost, complexity, power draw)
- Worse for single-hand use on couch
- Skip this for Ahoy

---

## Integration notes

### Pi Zero 2W USB connectivity

- Pi has 1 micro USB data port (+ 1 power-only port)
- Rii dongle is full-size USB-A
- **You need:** Micro USB to USB-A OTG adapter ($1)
- Dongle plugs directly into adapter on the Pi

### Chromium input handling

- Rii dongle is a standard HID keyboard + mouse device
- No drivers needed on Linux (it's handled by kernel)
- Trackpad registers as a mouse (works in Chromium web app)
- Keyboard shortcuts work:
  - Ctrl+W or Alt+F4 to close Chromium (only if you enable it in settings, otherwise you're stuck in kiosk mode)
  - Tab/arrow keys work for navigation

### Testing the remote

```bash
# SSH into Pi
ssh ahoy@ahoy.local

# Check if dongle is recognized
lsusb  # Should show the remote device

# Test keyboard input
cat /dev/input/event0  # Press keys, should see input events
# Ctrl+C to exit

# In Chromium, just type or move trackpad to test
```

---

## Stocking strategy for May

**Initial batch (20–30 units):**
- Buy 25 Rii Mini i8+ at bulk pricing ($8–10/unit)
- Expect ~50–70% of console buyers to add a remote
- 20 consoles × 60% attachment = ~12 remotes sold
- Keep 5 remotes as buffer + spares

**If you run out:**
- Reorder mid-May (next AliExpress batch lands in ~10 days)
- Premium pricing: charge $25 for "emergency stock" (vs. $20 standard)

**For future runs:**
- Lock in Rii Mini i8+ as the standard
- Order remotes with console shipment (same supplier)
- Consider bundling if margins allow
