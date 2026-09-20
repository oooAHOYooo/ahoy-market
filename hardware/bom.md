# Bill of Materials: Ahoy Console

## Console BOM (per unit, $24 target)

| Line Item | Model | Unit Cost | Qty | Total | Supplier | Notes |
|---|---|---|---|---|---|---|
| Raspberry Pi Zero 2 W | RPi Zero 2 W | $15 | 1 | $15 | Adafruit, RS Electronics, official distributors | 512MB RAM, WiFi 802.11ac, 1GHz Cortex-A53×4 |
| MicroSD Card | SanDisk 16GB Class 10 | $3 | 1 | $3 | Amazon, Newegg, local retailers | A1 or A2 rated preferred for boot speed |
| Mini HDMI Cable | 1m mini HDMI→HDMI | $2 | 1 | $2 | Amazon, Monoprice, eBay | **MINI HDMI** not micro. Get tested brand (no dead pixels). |
| Micro USB OTG Adapter | USB-A to micro USB OTG | $1 | 1 | $1 | Bulk lots on AliExpress, Amazon | For connecting remote. Test before bulk order. |
| Cardboard Packaging | Custom 2-color kraft box | $3 | 1 | $3 | Local print shop OR Packhelp/Packlane | Include quick-start insert card (printed). ~50 unit min. |
| | | | **Total** | **$24** | | |

## Remote BOM (per unit, sold separately, $20 retail)

| Line Item | Model | Unit Cost | Qty | Total | Supplier | Notes |
|---|---|---|---|---|---|---|
| Combo Keyboard+Trackpad | Rii Mini i8+ or clone | $8–12 | 1 | $10 avg | Bulk vendors (AliExpress, Alibaba, Amazon resellers) | 2.4GHz USB dongle, Qwerty, rechargeable. Test responsiveness. |
| Cardboard Sleeve | Custom printed mini sleeve | $1 | 1 | $1 | Local printer or online | Optional. Branding/unboxing feel. |
| | | | **Total** | **$11 avg** | | |

## Pricing Estimates

### Per-unit manufacturing cost

| Item | Console | Remote | Bundle |
|---|---|---|---|
| BOM | $24 | $11 | $35 |
| Packaging (incl. insert) | Incl. | Incl. | Incl. |
| Labor (assembly, QA) | $2–3 | $1 | $3–4 |
| **Total mfg cost** | **$26–27** | **$12** | **$38–39** |

### Recommended retail pricing

| Product | Retail | Gross Margin | GP% |
|---|---|---|---|
| Console only | $50 | $23–24 | 46–48% |
| Remote only | $20 | $8–9 | 40–45% |
| Bundle (console + remote) | $65 | $26–27 | 40–42% |

**Notes:**
- Gross margin does not include: shipping, packaging design, upstream R&D, platform fees (if sold online), storage
- For farmers market: cash sales, no platform fees, minimal overhead
- Bundle pricing gives customer ~$5 discount vs buying separately (incentivizes upsell without losing much margin)

## Bulk order quantities & timelines

### First batch (20–30 units for May farmers market)

| Component | Qty | Lead time | Notes |
|---|---|---|---|
| Pi Zero 2 W | 30 | 1–2 weeks | Order ASAP — frequently out of stock |
| MicroSD 16GB | 30 | 3–5 days | Keep spare 5 |
| HDMI cables | 30 | 3–5 days | Order 35 (spares) |
| OTG adapters | 35 | 3–5 days | 5 spares for testing |
| Cardboard boxes | 30 | 2–3 weeks | Design + print time. Start NOW if printing custom. |
| Rii remotes | 20 | 5–10 days | For initial inventory (not bundled with console yet) |

**Critical path:** Cardboard printing (2–3 weeks) + Pi Zero 2 W availability (1–2 weeks). Order both this week.

## Where to buy (notes)

### Raspberry Pi Zero 2 W — LIMITED AVAILABILITY
- **Adafruit.com** — Usually in stock, $15 + $5 shipping
- **RS Electronics / Allied Electronics** — Distributor, bulk pricing available at 25+ qty
- **Authorized country distributors** — Check [raspberrypi.com/where-to-buy](https://www.raspberrypi.com/where-to-buy/)
- **Avoid:** eBay/Amazon resellers if significantly above MSRP; usually same stock constraints

### Other components (widely available)
- **MicroSD:** Amazon, Newegg, Best Buy, Micro Center
- **HDMI cables:** Monoprice (good quality), Amazon, local electronics
- **OTG adapter:** AliExpress (bulk pricing, 5–10 day lead), Amazon Prime if urgent
- **Remote:** AliExpress (bulk lots, 7–14 day lead), Amazon (higher price, 2-day shipping)

### Cardboard packaging
- **Local print shops** (~$2–3/unit for 25–50 runs, 2–3 week turnaround, custom design)
- **Packhelp** (~$2–4/unit for 50–100 runs, 5–7 day turnaround, simple design templates)
- **Packlane** (~$2–5/unit, similar to Packhelp, strong design tools)
- **Small batch:** Local box supplier with custom inserts

## Testing checklist before bulk order

- [ ] Pi Zero 2 W boots from SD card in under 60 seconds
- [ ] WiFi portal appears on phone within 10 seconds of power-on
- [ ] HDMI cable works with at least 2 different TV models (different EDID)
- [ ] OTG adapter works with 2 different remotes (Rii + one backup model)
- [ ] Chromium loads `app.ahoy.ooo` fully and renders video player
- [ ] Remote keyboard/trackpad input works in Chromium (type, scroll, click)
- [ ] Box printing sample matches brand colors and design

## Cost saving opportunities (if margin needs padding)

| Idea | Impact | Tradeoff |
|---|---|---|
| Drop HDMI cable, assume user has one | –$2 | Reduces "complete kit" feel; more customer friction |
| Use 8GB SD card instead of 16GB | –$1 | Barely saves cost, Pi OS Lite is small |
| Bulk OTG adapters from AliExpress | –$0.50 | 7–10 day shipping, need to test samples |
| Simpler cardboard (2-color kraft) vs full-color | –$1 | Looks less premium |
| Assembly at home vs hiring help | –$3 | 20–30 hours labor for May batch |

None of these should be necessary; $24 BOM with 52% margin is healthy for hardware.

## Inventory planning

For May 2026 farmers market:
- Target sales: 15–25 units first weekend
- Recommended inventory: 30–40 units (2–3 weeks after market start)
- Remote add-on: stock 20–30 (expect ~50–70% attachment rate)
- Spare parts (SD, HDMI, OTG): keep 10% extras
