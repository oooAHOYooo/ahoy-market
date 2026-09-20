# Ahoy Console — Hardware Build Guide

A Raspberry Pi Zero 2 W media console that boots directly to `app.ahoy.ooo` on your TV. Sold at farmers markets May 2026.

## What's in the box

- Raspberry Pi Zero 2 W
- 1m mini HDMI → HDMI cable
- Micro USB OTG adapter
- Quick-start setup card

**Remote sold separately** — Rii Mini i8+ or compatible 2.4GHz USB keyboard+trackpad

## Quick start (customer)

1. Plug HDMI cable into TV
2. Plug USB power (any 5V 2A+ phone charger) into Pi
3. On your phone, look for WiFi network `Ahoy-Setup` and connect
4. A setup page should appear automatically (captive portal)
5. Select your home WiFi and enter password
6. Pi will reboot and load Ahoy on your TV
7. (Optional) Plug in the remote via OTG adapter

## Build & assembly (manufacturer)

### Prerequisite: Flash one master SD card

```bash
# 1. Flash Raspberry Pi OS Lite (64-bit) using Raspberry Pi Imager
# - Set hostname: ahoy
# - Set username: ahoy
# - Enable SSH

# 2. SSH into the Pi and run the setup script
ssh ahoy@ahoy.local
curl -sL https://raw.githubusercontent.com/oooAHOYooo/ahoy-little-platform/main/hardware/pi-image/build.sh | bash

# 3. Verify the first-boot WiFi setup works
# - Pi should broadcast "Ahoy-Setup" WiFi
# - Connect phone, fill in home WiFi, verify reboot

# 4. Verify kiosk mode loads app.ahoy.ooo after WiFi is set
```

### Clone SD cards (once master is confirmed)

```bash
# 1. Power off Pi, remove SD card
# 2. On your computer:
dd if=/dev/sdX of=ahoy-master.img bs=4M status=progress
# 3. For each new unit:
dd if=ahoy-master.img of=/dev/sdY bs=4M status=progress
```

**Time per unit:** ~20 min first card, ~5 min per clone

### Assembly

1. Insert SD card into Pi Zero 2 W
2. Insert mini HDMI cable into Pi
3. Insert OTG adapter into the single micro USB data port (NOT the power port)
4. Place Pi + cables in branded cardboard box
5. Include quick-start card and OTG adapter in box
6. Seal

## Hardware specifications

| Component | Model | Cost | Notes |
|---|---|---|---|
| Compute | Raspberry Pi Zero 2 W | $15 | 1GHz ARM Cortex-A53 × 4, 512MB RAM, WiFi 802.11ac |
| Storage | MicroSD 16GB Class 10 | $3 | Boot drive + OS |
| Video | Mini HDMI → HDMI cable, 1m | $2 | Adapter, not just cable (Pi has mini HDMI) |
| Input | Micro USB OTG adapter | $1 | Connects USB dongle for remote |
| Packaging | Kraft cardboard + insert | $3 | Printed 2-color |
| **Total** | | **$24** | + $9 remote (optional add-on) |

## DIY Build & Alternative Hardware

Want to build your own Ahoy Console instead of buying one at the farmers market? You can easily source the parts yourself based on the hardware specifications table above.

### Sourcing Parts Yourself
All parts are standard and readily available on sites like Amazon, AliExpress, or at specialty electronics retailers (e.g., Adafruit, Micro Center).
1. Purchase a **Raspberry Pi Zero 2 W**.
2. Grab a **16GB (or larger) Class 10 MicroSD card**.
3. Pick up a **Mini HDMI to HDMI cable** and a **Micro USB OTG adapter**.
4. Use any old 5V 2A+ phone charger you have around the house.
5. Follow the **Build & assembly (manufacturer)** instructions above to flash the SD card.

### Banana Pi BPI-M2 Zero Alternative
If the Raspberry Pi Zero 2 W is out of stock, the **Banana Pi BPI-M2 Zero** is an almost exact physical clone and a highly viable alternative.

**Hardware Compatibility:**
- **Identical Form Factor:** Uses the same ports (Mini HDMI, Micro USB OTG, Micro USB Power). The cables and adapters listed in the BOM will work perfectly.
- **Power:** Standard 5V 2A power supply is sufficient.

**Software Differences (Important):**
The software setup (`pi-image/build.sh`) will require modifications because the Banana Pi uses a different processor (Allwinner H3 vs Broadcom).
- **Base OS:** You cannot use Raspberry Pi Imager. You must flash an OS built for the Banana Pi (like Armbian) using a tool like BalenaEtcher.
- **Boot Configuration:** Rather than editing `/boot/config.txt` (which is Pi-specific), boot parameters are configured in `/boot/armbianEnv.txt` or `/boot/uEnv.txt`.
- **Video Acceleration:** The BPI-M2 Zero uses a Mali-400 GPU, meaning Chromium might require different graphics drivers (like `fbturbo` or `lima`) or startup flags for smooth UI rendering in kiosk mode.
- **Networking:** Ensure your network interface names in Armbian (e.g., `nmcli` and `wpa_supplicant` configurations) align with what the captive portal expects.

## Directory structure

```
hardware/
├── README.md (you are here)
├── bom.md                  # Line-item costs, suppliers
├── FARMERS_MARKET.md       # Sales tips, pricing, demo script
├── pi-image/               # What runs on the device
│   ├── build.sh            # Install script (run on fresh Pi OS Lite)
│   ├── config.txt          # /boot/config.txt
│   ├── cmdline-append.txt  # Additions to /boot/cmdline.txt
│   ├── setup-portal/       # First-boot WiFi provisioning app
│   │   ├── app.py
│   │   ├── templates/index.html
│   │   └── hostapd.conf
│   ├── services/           # systemd service files
│   │   ├── ahoy-first-boot.service
│   │   ├── ahoy-setup.service
│   │   └── ahoy-kiosk.service
│   └── kiosk.sh            # Chromium launcher
├── remote/
│   └── research.md         # Remote model options & bulk pricing
└── packaging/
    ├── design-brief.md     # Box dimensions, print specs
    └── unboxing-order.md   # What goes in the box & where
```

## Troubleshooting

### Pi doesn't boot
- Confirm SD card flashing succeeded: `diskutil verify` (macOS) or `fsck` (Linux)
- Try flashing with `Raspberry Pi Imager` directly (fallback method)

### WiFi portal doesn't appear
- Verify `ahoy-setup.service` is running: `systemctl status ahoy-setup`
- Check `hostapd` logs: `journalctl -u hostapd -n 20`
- Reboot Pi, immediately scan for "Ahoy-Setup" on phone

### Chromium doesn't load app.ahoy.ooo
- Verify home WiFi is configured: Check `wpa_supplicant.conf` exists
- Verify network online: `ip route show`
- Manually test: `curl -I https://app.ahoy.ooo`
- Check Chromium logs: `journalctl -u ahoy-kiosk -n 50`

### Remote not detected
- Plug OTG adapter into the *data* micro USB port (the one NOT used for power)
- Pair remote per its manual
- Test keyboard input: Press a key, check `journalctl -k -n 20`

## Support links

- [Raspberry Pi Zero 2 W docs](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/)
- [Raspberry Pi OS setup](https://www.raspberrypi.com/software/)
