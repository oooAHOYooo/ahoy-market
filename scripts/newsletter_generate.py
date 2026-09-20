#!/usr/bin/env python3
"""
newsletter_generate.py — Draft a monthly newsletter HTML file from What's New data.

Writes to newsletters/YYYY-mon.html. Open that file in a browser, edit the copy
and personal note, then send it:

  python scripts/newsletter_generate.py                   # current month
  python scripts/newsletter_generate.py --month may --year 2026
  python scripts/newsletter_generate.py --month may --year 2026 --force
"""

import argparse
import json
import os
import sys
from datetime import datetime

REPO_ROOT        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WHATS_NEW_JSON   = os.path.join(REPO_ROOT, "static", "data", "whats_new.json")
NEWSLETTERS_DIR  = os.path.join(REPO_ROOT, "newsletters")

BASE_URL = "https://ahoy.ooo"

MONTH_NAMES = {
    "jan": "January", "feb": "February", "mar": "March",
    "apr": "April",   "may": "May",      "jun": "June",
    "jul": "July",    "aug": "August",   "sep": "September",
    "oct": "October", "nov": "November", "dec": "December",
}

SECTION_ORDER  = ["music", "videos", "artists", "platform", "events", "merch"]
SECTION_LABELS = {
    "music": "Music", "videos": "Videos", "artists": "Artists",
    "platform": "Platform", "events": "Events", "merch": "Merch",
}
SECTION_CTA = {
    "music": "Listen", "videos": "Watch", "events": "Details",
}


def abs_url(path):
    if not path:
        return ""
    if path.startswith("http"):
        return path
    return BASE_URL + "/" + path.lstrip("/")


def escape(text):
    return (text or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def fmt_date(date_str):
    if not date_str:
        return ""
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
        return f"{parsed.strftime('%b')} {parsed.day}"
    except Exception:
        return date_str


SERIF = "Georgia,'Times New Roman',serif"
IMG_FILTER = "grayscale(100%) contrast(1.18) brightness(0.86) sepia(8%)"


def item_rows_html(item, section_key, is_last):
    """Returns outer <tr> block(s). Photo items use the blurred-background / max-height
    widescreen trick. Text-only items render as a simple padded row."""
    title    = escape(item.get("title", ""))
    date_str = fmt_date(item.get("date", ""))
    link     = abs_url(item.get("link", ""))
    thumb    = abs_url(item.get("thumbnail", ""))
    cta      = SECTION_CTA.get(section_key, "Open")

    meta_parts = []
    if date_str:
        meta_parts.append(
            f'<span style="font-family:{SERIF}; font-size:10px; '
            f'letter-spacing:0.06em; color:#888888;">{date_str}</span>'
        )
    if link:
        meta_parts.append(
            f'<a href="{link}" style="font-family:{SERIF}; font-size:10px; '
            f'font-style:italic; color:#0a0a0a; text-decoration:none; '
            f'letter-spacing:0.04em;">{cta}&nbsp;&#8594;</a>'
        )
    meta_html = '<span style="color:#cccccc;">&ensp;&middot;&ensp;</span>'.join(meta_parts)

    bottom_rule = "" if is_last else "border-bottom:1px solid #d8d4cc;"

    if thumb:
        # ── Widescreen blur-background photo block ───────────────────────────
        # The outer <table class="photo-wrap"> carries the raw image as a CSS
        # background-image so email clients fill the 400px tall box. The browser
        # preview <style> block adds a ::before pseudo-element that blurs that
        # same background, creating the letterbox/blur effect. The foreground <img>
        # is centered, grayscale-filtered, and capped at 400px tall.
        return f"""
        <!-- photo item -->
        <tr>
          <td style="padding:24px 0 0; line-height:0; font-size:0;">
            <table role="presentation" class="photo-wrap"
                   width="600" cellpadding="0" cellspacing="0" border="0"
                   style="width:100%; max-width:600px; background-color:#1a1a18;
                          background-image:url('{thumb}'); background-size:cover;
                          background-position:center;">
              <tr>
                <td class="photo-cell" height="400"
                    style="height:400px; text-align:center; vertical-align:middle;
                           padding:0; line-height:0; font-size:0; overflow:hidden;">
                  <img src="{thumb}" class="photo-main" alt=""
                       style="display:inline-block; height:400px; width:auto;
                              max-width:100%; max-height:400px;
                              filter:{IMG_FILTER};
                              -webkit-filter:{IMG_FILTER};" />
                </td>
              </tr>
            </table>
          </td>
        </tr>
        <tr>
          <td style="padding:0 52px 32px; {bottom_rule}">
            <div style="border-top:2px solid #0a0a0a; margin-bottom:9px;"></div>
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="font-family:{SERIF}; font-size:15px; font-weight:bold;
                           color:#0a0a0a; line-height:1.35; padding-right:18px;
                           vertical-align:bottom;">
                  {title}
                </td>
                <td style="vertical-align:bottom; text-align:right; white-space:nowrap;
                           padding-bottom:1px;">
                  {meta_html}
                </td>
              </tr>
            </table>
          </td>
        </tr>"""
    else:
        return f"""
        <!-- text-only item -->
        <tr>
          <td style="padding:0 52px;">
            <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
              <tr>
                <td style="font-family:{SERIF}; font-size:14px; font-weight:bold;
                           color:#0a0a0a; line-height:1.4; padding:13px 18px 13px 0;
                           vertical-align:top; {bottom_rule}">
                  {title}
                </td>
                <td style="padding:13px 0; text-align:right; white-space:nowrap;
                           vertical-align:top; {bottom_rule}">
                  {meta_html}
                </td>
              </tr>
            </table>
          </td>
        </tr>"""


def section_header_html(label):
    """Understated newspaper section divider: thick rule + small label + hairline."""
    return f"""
        <!-- ===== {label} ===== -->
        <tr>
          <td style="padding:44px 52px 0;">
            <div style="border-top:3px solid #0a0a0a; padding-top:10px;">
              <span style="font-family:{SERIF}; font-size:10px; font-weight:bold;
                           letter-spacing:0.34em; text-transform:uppercase;
                           color:#0a0a0a;">&#9670;&ensp;{label}&ensp;&#9670;</span>
            </div>
            <div style="border-top:1px solid #0a0a0a; margin-top:9px;"></div>
          </td>
        </tr>"""


def section_block_html(section_key, section_data):
    # Use the section title from the JSON (e.g. "Music Updates"), fall back to generic label
    raw_title = section_data.get("title") or SECTION_LABELS.get(section_key, section_key.capitalize())
    label     = raw_title.upper()
    items     = section_data.get("items", [])
    header    = section_header_html(label)
    item_blocks = "".join(
        item_rows_html(item, section_key, i == len(items) - 1)
        for i, item in enumerate(items)
    )
    return header + item_blocks


def build_newsletter_html(month_key, year, month_data):
    month_name = MONTH_NAMES.get(month_key, month_key.capitalize())
    month_url  = f"{BASE_URL}/whats-new/{year}/{month_key}"

    active_sections = [s for s in SECTION_ORDER if month_data.get(s, {}).get("items")]
    total = sum(len(month_data.get(s, {}).get("items", [])) for s in SECTION_ORDER)

    sections_html = "".join(
        section_block_html(s, month_data[s]) for s in active_sections
    )

    serif = "Georgia,'Times New Roman',serif"

    return f"""<!DOCTYPE html>
<html lang="en" xmlns="http://www.w3.org/1999/xhtml">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<!--
  ╔══════════════════════════════════════════════════════╗
  ║  AHOY NEWSLETTER — {month_name} {year:<36}║
  ║  Edit this file, preview in browser, then send:     ║
  ║  python scripts/newsletter_send.py newsletters/{year}-{month_key}.html  ║
  ╚══════════════════════════════════════════════════════╝

  QUICK EDIT GUIDE
  ────────────────────────────────────────────────────
  • Subject line   →  change <title> below
  • Inbox preview  →  change the PREHEADER div text
  • Personal note  →  find the "FROM THE EDITOR" block
  • Any headline   →  edit the bold text in each row
-->

<!-- EDIT: becomes the email subject line -->
<title>What's New at Ahoy — {month_name} {year}</title>

<style>
  /* ── BROWSER PREVIEW ONLY ─────────────────────────────────────────
     Styles here are ignored by email clients.
     Inline styles in the body handle email rendering.
     ────────────────────────────────────────────────────────────────── */
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    background: #e8e4dc;
    font-family: Georgia, 'Times New Roman', serif;
  }}

  .preview-bar {{
    position: sticky;
    top: 0;
    z-index: 100;
    background: #fffbe6;
    border-bottom: 1px solid #d4b84a;
    padding: 9px 20px;
    font-family: monospace;
    font-size: 11px;
    color: #6b5c00;
    text-align: center;
  }}
  .preview-bar code {{
    background: rgba(0,0,0,0.06);
    padding: 1px 5px;
    border-radius: 3px;
  }}

  /* ── Widescreen blur-background photo trick (browser only) ──────────────
     The <table class="photo-wrap"> carries background-image so email clients
     see a filled 400px box. In the browser, ::before inherits that background,
     scales it up slightly, and blurs it to fill the letterbox bars. The
     foreground <img class="photo-main"> sits on top at z-index 1.
     ─────────────────────────────────────────────────────────────────────── */
  table.photo-wrap {{
    position: relative;
    overflow: hidden;
    max-height: 400px;
  }}

  table.photo-wrap::before {{
    content: '';
    position: absolute;
    inset: -32px;
    background-image: inherit;
    background-size: cover;
    background-position: center;
    transform: scale(1.06);
    filter: blur(22px) grayscale(100%) brightness(0.42) contrast(1.2) sepia(10%);
    -webkit-filter: blur(22px) grayscale(100%) brightness(0.42) contrast(1.2) sepia(10%);
    z-index: 0;
  }}

  td.photo-cell {{
    position: relative;
    z-index: 1;
  }}

  img.photo-main {{
    position: relative;
    z-index: 1;
  }}
</style>
</head>
<body style="margin:0; padding:0; background:#e8e4dc;
             font-family:Georgia,'Times New Roman',serif;
             -webkit-text-size-adjust:100%; mso-line-height-rule:exactly;">

  <!-- BROWSER PREVIEW BAR — hidden in email -->
  <div class="preview-bar" style="mso-hide:all;">
    <strong>Draft</strong> &mdash; {month_name} {year} &mdash; {total} item(s) &nbsp;|&nbsp;
    Send: <code>python scripts/newsletter_send.py newsletters/{year}-{month_key}.html</code>
  </div>

  <!-- PREHEADER — inbox snippet, invisible in body -->
  <!-- EDIT: customize the inbox preview text below -->
  <div style="display:none; font-size:1px; color:#e8e4dc; line-height:1px;
              max-height:0; max-width:0; opacity:0; overflow:hidden; mso-hide:all;">
    Your {month_name} {year} update from Ahoy &mdash; new music, videos, shows, and more from the indie media platform.
  </div>

  <!-- ══════════════════════════════════════════════ EMAIL BODY -->
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
         style="background:#e8e4dc; padding:40px 16px 64px;">
    <tr><td align="center">
    <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0"
           style="max-width:600px; width:100%; background:#faf9f6;">

      <!-- ══ MASTHEAD ══════════════════════════════════════════════ -->
      <tr>
        <td style="padding:0; border-top:4px solid #0a0a0a; border-bottom:none;">

          <!-- Top rule strip -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding:11px 52px 10px; border-bottom:1px solid #0a0a0a;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="font-family:{serif}; font-size:9px; letter-spacing:0.25em;
                                text-transform:uppercase; color:#555555;">
                      Est.&nbsp;MMXXV &nbsp;&middot;&nbsp; Indie Media
                    </td>
                    <td style="font-family:{serif}; font-size:9px; letter-spacing:0.25em;
                                text-transform:uppercase; color:#555555; text-align:right;">
                      Monthly Edition
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>

          <!-- Nameplate -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding:28px 52px 24px; text-align:center; border-bottom:1px solid #0a0a0a;">
                <div style="font-family:{serif}; font-size:58px; font-weight:bold;
                            color:#0a0a0a; letter-spacing:-0.03em; line-height:0.92;
                            text-transform:uppercase;">
                  Ahoy
                </div>
                <div style="font-family:{serif}; font-size:10px; letter-spacing:0.42em;
                            text-transform:uppercase; color:#0a0a0a; margin-top:12px;">
                  Indie&nbsp; Media&nbsp; Dispatch
                </div>
              </td>
            </tr>
          </table>

          <!-- Date bar -->
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
            <tr>
              <td style="padding:9px 52px 10px; border-bottom:3px solid #0a0a0a;">
                <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                  <tr>
                    <td style="font-family:{serif}; font-size:9px; letter-spacing:0.22em;
                                text-transform:uppercase; color:#0a0a0a;">
                      {month_name.upper()}&nbsp;{year}
                    </td>
                    <td style="font-family:{serif}; font-size:9px; letter-spacing:0.22em;
                                text-transform:uppercase; color:#0a0a0a; text-align:right;">
                      ahoy.ooo
                    </td>
                  </tr>
                </table>
              </td>
            </tr>
          </table>

        </td>
      </tr>

      <!-- ══ FROM THE EDITOR ══════════════════════════════════════ -->
      <tr>
        <td style="padding:40px 52px 0;">
          <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0"
                 style="border:1px solid #0a0a0a;">

            <!-- Header bar -->
            <tr>
              <td style="background:#0a0a0a; padding:6px 20px; text-align:center;">
                <span style="font-family:{serif}; font-size:8px; font-weight:bold;
                             letter-spacing:0.38em; text-transform:uppercase; color:#faf9f6;">
                  From the Editor
                </span>
              </td>
            </tr>

            <!-- Note body -->
            <tr>
              <td style="padding:22px 26px 26px;">
                <!-- EDIT: Replace this with your personal note each month. -->
                <!-- Keep it warm and brief — 2 to 4 sentences. -->
                <div style="font-family:{serif}; font-size:14px; font-style:italic;
                            color:#0a0a0a; line-height:1.9;">
                  Write your personal note here. What made this month worth writing about?
                  Keep it warm, brief, and in your own voice &mdash; this is the part they
                  actually look forward to.
                </div>
              </td>
            </tr>

          </table>
        </td>
      </tr>

      <!-- ══ CONTENT SECTIONS ══════════════════════════════════════ -->
      {sections_html}

      <!-- ══ SPACER ════════════════════════════════════════════════ -->
      <tr>
        <td style="padding:44px 52px 0;">
          <div style="border-top:3px solid #0a0a0a;"></div>
        </td>
      </tr>

      <!-- ══ READ ONLINE ═══════════════════════════════════════════ -->
      <tr>
        <td style="padding:28px 52px; text-align:center;">
          <a href="{month_url}"
             style="font-family:{serif}; font-size:11px; letter-spacing:0.22em;
                    text-transform:uppercase; color:#0a0a0a; text-decoration:none;
                    border-bottom:1px solid #0a0a0a; padding-bottom:2px;">
            Read the full edition at Ahoy &nbsp;&#8594;
          </a>
        </td>
      </tr>

      <!-- ══ FOOTER ════════════════════════════════════════════════ -->
      <tr>
        <td style="padding:0 52px 44px; border-top:1px solid #0a0a0a;">
          <div style="font-family:{serif}; font-size:9px; letter-spacing:0.18em;
                      text-transform:uppercase; color:#888888; text-align:center;
                      margin-top:20px; line-height:2.2;">
            <a href="{BASE_URL}" style="color:#888888; text-decoration:none;">ahoy.ooo</a>
            &nbsp;&middot;&nbsp;
            You are receiving this because you subscribed to Ahoy updates.
          </div>
        </td>
      </tr>

    </table>
    </td></tr>
  </table>

</body>
</html>"""


def main():
    now = datetime.now()
    parser = argparse.ArgumentParser(
        description="Generate a monthly Ahoy newsletter HTML draft"
    )
    parser.add_argument("--month",  default=now.strftime("%b").lower()[:3],
                        help="Month key e.g. may (default: current month)")
    parser.add_argument("--year",   default=str(now.year),
                        help="Year e.g. 2026 (default: current year)")
    parser.add_argument("--force",  action="store_true",
                        help="Overwrite existing file without prompting")
    args = parser.parse_args()

    month_key  = args.month.lower()[:3]
    year       = args.year
    month_name = MONTH_NAMES.get(month_key, month_key.capitalize())

    try:
        with open(WHATS_NEW_JSON, encoding="utf-8") as f:
            wn = json.load(f)
    except FileNotFoundError:
        print(f"ERROR: {WHATS_NEW_JSON} not found.")
        sys.exit(1)

    month_data = wn.get("updates", {}).get(year, {}).get(month_key, {})
    total      = sum(len(month_data.get(s, {}).get("items", [])) for s in SECTION_ORDER)
    active     = [s for s in SECTION_ORDER if month_data.get(s, {}).get("items")]

    os.makedirs(NEWSLETTERS_DIR, exist_ok=True)
    out_path = os.path.join(NEWSLETTERS_DIR, f"{year}-{month_key}.html")

    if os.path.exists(out_path) and not args.force:
        print(f"File already exists: newsletters/{year}-{month_key}.html")
        print("Use --force to overwrite.")
        sys.exit(1)

    html = build_newsletter_html(month_key, year, month_data)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"\nGenerated: newsletters/{year}-{month_key}.html")
    print(f"  {total} item(s) across: {', '.join(active) or 'none'}")
    print(f"\nNext steps:")
    print(f"  1. Open in browser to preview")
    print(f"  2. Edit the personal note and any copy")
    print(f"  3. python scripts/newsletter_send.py newsletters/{year}-{month_key}.html\n")


if __name__ == "__main__":
    main()
