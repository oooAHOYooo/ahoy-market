# Ahoy Console — Farmers Market Sales Guide

Selling Ahoy hardware at farmers markets starting May 2026. This guide covers pricing, demo setup, customer flow, and inventory.

## Pricing & margins

```
Console only:  $50 (mfg cost ~$26–27, margin $23–24)
Remote only:   $20 (mfg cost ~$12, margin $8–9)
Bundle:        $65 (mfg cost ~$38–39, margin $26–27)
```

- Lead with $50 console (everyone gets the core device)
- Suggest +$20 remote as add-on ("control it from the couch")
- Offer bundle discount if they're interested in both

## Table setup (farmers market)

```
┌─────────────────────────────────────┐
│  AHOY CONSOLE — Live Demo           │
│  [HDMI cable to TV running the app] │
│  Remote demonstrating click/scroll  │
│  Demo video playing (music/shows)   │
├─────────────────────────────────────┤
│ $50      $20       $65              │
│ CONSOLE  REMOTE   BUNDLE            │
│ (box in [USB dongle +              │
│  stock)  battery]    (both)        │
├─────────────────────────────────────┤
│ "Works with your WiFi at home"      │
│ Quick-start card sample             │
└─────────────────────────────────────┘
```

### Display details
- **TV/monitor**: Plug into a demo TV showing a looping video (e.g., Poets & Friends, a curated show)
- **Demo remote**: Have one paired, working remote on display so people can click/scroll and see it work
- **Packaging**: Stack 5–10 boxes to show what they'll get
- **Price signage**: Large, clear handwritten or printed cards ($50, $20, $65)

## Sales script

**Customer approaches:** "Hi! This is the Ahoy Console — it's a little box that turns your TV into a music/show/artist player. Plug it in at home, set up your WiFi once, and you're done. Fully independent — no cables, no subscriptions."

**If they ask "What is it?"**
> "It's a Raspberry Pi — tiny computer — running Ahoy, which is an independent music and video platform. Poets, shows, artists, live sessions. Kinda like YouTube, but for creative folks."

**If they ask "What's included?"**
> "The console itself, HDMI cable, a little adapter, and a card showing how to set it up. The remote is separate — you can use any USB keyboard or mouse, or get one of these for $20 if you want something compact."

**If they ask "How do I set it up?"**
> "Plug it in, look for 'Ahoy-Setup' WiFi on your phone, enter your home WiFi password, it reboots, and Ahoy loads on your TV. Takes about 5 minutes. You don't need to know anything technical."

**If they ask "What's the difference between this and Chromecast?"**
> "Ahoy is independent and not owned by Google. It's all artist-friendly. Plus you own the device — no accounts, no tracking."

**If they ask "Will it work with my [brand] TV?"**
> "Yep, any TV with HDMI from the last 10 years. Standard connector."

**If they ask "What if WiFi goes down?"**
> "Then you can't access Ahoy — it streams from the internet like YouTube does. But we're working on local playback for the future."

## Upsell flow

1. **Lead:** $50 console
2. **Objection/hesitation?** → Show demo on the TV, let them try the remote
3. **Interest:** Discuss use case ("Living room streaming," "artist discovery," etc.)
4. **Closing:** "How's your WiFi at home? Cool. $50 for the console, and I've got remotes for $20 if you want one."
5. **Add-on:** If they're ready to buy: "Bundle with the remote is $65 — saves you $5."

## Inventory & logistics

### Day-of setup
- Bring: 20–30 consoles (boxed), 15 remotes (packaged), demo unit (assembled, HDMI connected to loaned TV)
- Spares: 2–3 extra OTG adapters, 1 extra HDMI cable, 2 extra remotes for demo failures
- Change: Start with $100–200 in small bills (no one carries exact cash)
- Bags: Small tissue boxes or branded bags for customer purchases

### After each market
- Restock: Replenish consoles if sales > 5 units
- Inspect demo box: Verify WiFi portal still works, no dust, HDMI connections clean
- Remote batteries: Charge overnight if demoed heavily

## Customer questions & answers

| Q | A |
|---|---|
| "Does it require an internet connection?" | Yes, it streams from the internet like YouTube. No internet = no Ahoy. |
| "Can I use it without WiFi?" | Not yet — we're working on a download-and-play mode for the future. |
| "What about parental controls?" | There aren't built-in controls yet, but the device itself is just a browser pointing at app.ahoy.ooo. No special content. |
| "Can I sideload content?" | The Pi runs Linux — power users can SSH in and do whatever, but it's not supported yet. |
| "Will this ever be a smarter device (voice control, etc.)?" | Maybe! Right now it's intentionally simple. We're focused on the experience, not feature creep. |
| "Is there a warranty?" | [Your policy here] — probably no formal warranty, but if it DOA within 30 days, I'll replace it. |
| "Can I return it?" | [Your policy here] — Once it's set up with WiFi creds, it's yours. But if it's DOA, let me know. |

## Post-sale support

Provide quick-start card with contact info:

```
┌─────────────────────────────────────┐
│ AHOY CONSOLE QUICK START            │
│                                     │
│ 1. Plug HDMI into TV                │
│ 2. Plug power (5V USB charger)      │
│ 3. Join "Ahoy-Setup" WiFi           │
│ 4. Enter your home WiFi password    │
│ 5. Reboot (automatic)               │
│ 6. Enjoy!                           │
│                                     │
│ Questions? Email: ...@ahoy.ooo      │
│ Bugs? GitHub issues or Discord      │
└─────────────────────────────────────┘
```

## Competitive positioning

| Platform | Pros | Cons |
|---|---|---|
| **Ahoy Console** | Independent, artist-owned, no subscriptions, simple setup, hackable | No smart features, new platform, small catalog |
| Chromecast | Cheap, familiar, many apps | Google-owned, limited to apps |
| Apple TV | Premium, polished | Expensive, locked ecosystem |
| Roku | Huge app ecosystem | Ad-heavy, limited to apps |
| HTPC (PC on TV) | Full control | Requires tech knowledge, power usage |

**Your angle:** "Supporting independent creators through a device you actually own."

## Talking points (why Ahoy?)

- **Artist-first:** Revenue goes to artists, not platforms
- **Independent:** Not owned by Google, Apple, or Amazon
- **Simple:** No smart features you don't need, just works
- **Open:** Run on any TV with HDMI
- **Growing:** New content added regularly from the community
- **Hackable:** If you know Linux, tinker away (SSH enabled)

## Budget & break-even

Assuming you sell at farmers markets 4 times in May (Sundays):

| Metric | Amount |
|---|---|
| Initial inventory (25 units) | $675 mfg |
| Table fee (4 × $30) | $120 |
| Gas / transport | $30 |
| Signage / bags (one-time) | $20 |
| **Total cost** | **~$845** |
| Avg sale (50% bundle, 50% console) | $57.50 |
| Break-even units | ~15 units |
| **Profit at 20 units sold** | ~$305 |
| **Profit at 30 units sold** | ~$885 |

This assumes no restocking costs after the first order. Scale from there.

## Follow-ups for future markets

- **Discord/email list:** Capture emails for "Ahoy Console updates"
- **Pre-order system:** For next batch (if you do a second run), take pre-orders
- **Feedback:** Ask customers what content they want, report back to the platform
- **Testimonials:** After a few weeks, ask buyers for a short testimonial or photo (social proof)
