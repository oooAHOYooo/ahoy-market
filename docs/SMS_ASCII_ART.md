# SMS ASCII Art & Emoji Design Options

SMS messages can include emoji and ASCII art to make them more visually appealing!

## Current Default

By default, all SMS includes a simple anchor header:

```
⚓ AHOY ⚓
New Music Release
Check out latest tracks...
https://ahoy.ooo/whats-new
```

Use `--no-art` flag to remove it:
```bash
python scripts/send_whats_new_sms.py \
  --title "New Music" \
  --description "Check it out" \
  --no-art
```

## ASCII Art Options

Here are some examples you could use (just edit `services/sms.py`):

### Option 1: Waves & Anchor (Current Default)
```
⚓ AHOY ⚓
[content]
```

### Option 2: Music Note
```
♫ NEW MUSIC ♫
[content]
```

### Option 3: Film Strip
```
🎬 NEW VIDEO 🎬
[content]
```

### Option 4: Emoji Variety
```
✨ AHOY NEWS ✨
[content]
```

### Option 5: Multi-line ASCII
```
 🌊 AHOY 🌊
  SOMETHING
    NEW!
[content]
```

### Option 6: Simple Divider
```
━━━ AHOY ━━━
[content]
```

### Option 7: Stars
```
⭐ AHOY ⭐
[content]
```

## How to Customize

Edit `services/sms.py` in the `notify_whats_new_sms()` function:

**Current:**
```python
if use_art:
    message = "⚓ AHOY ⚓\n"
else:
    message = ""
```

**Change to (example with music):**
```python
if use_art:
    message = "♫ NEW MUSIC ♫\n"
else:
    message = ""
```

## SMS Character Limits

- **Standard SMS**: 160 characters (with ASCII/emojis)
- **Our format**: ~130 chars after header + title + description + link

**Example breakdown:**
```
⚓ AHOY ⚓                          (12 chars)
New Music Release                  (20 chars)
Check out our latest tracks...     (34 chars)
https://ahoy.ooo/whats-new        (28 chars)
───────────────────────────────────
Total: ~94 characters (fits in 1 SMS)
```

## Emoji Support on Different Phones

- ✅ Modern smartphones: Full emoji support
- ⚠️ Older phones: May show as `?` or blanks
- ✅ Recommended: Stick with common emoji (music ♫, stars ⭐, waves 🌊)

## Testing Different Styles

To test different ASCII art, edit the send script temporarily:

1. Open `services/sms.py`
2. Change line in `notify_whats_new_sms()`:
   ```python
   if use_art:
       message = "♫ AHOY ♫\n"  # Try different text here
   ```
3. Test: `python scripts/send_whats_new_sms.py --title "Test" --description "Hello"`

## Recommendations

**Keep it simple:**
- Single emoji line (⚓ or ♫ or ✨)
- Avoid fancy ASCII box art (takes too many characters)
- Use common emoji that work on older phones

**Current recommendation:** Stick with `⚓ AHOY ⚓` — it's:
- Simple and clear
- Fits the nautical "Ahoy" branding
- Works on all phones
- Only 12 characters

## Examples in the Wild

Here's how your SMS would look to recipients:

**With art (current):**
```
⚓ AHOY ⚓
New Music Release
Check out latest tracks...
https://ahoy.ooo/whats-new
```

**Without art (`--no-art`):**
```
New Music Release
Check out latest tracks...
https://ahoy.ooo/whats-new
```

**With music emoji:**
```
♫ NEW MUSIC ♫
New Music Release
Check out latest tracks...
https://ahoy.ooo/whats-new
```

## To Change the Default

If you want a different header for all messages:

1. Edit `services/sms.py`, function `notify_whats_new_sms()`
2. Change: `message = "⚓ AHOY ⚓\n"` to whatever you want
3. Also change in `scripts/send_whats_new_sms.py` (same function)
4. Both places must match so preview shows correctly

## Command Line Options

```bash
# With art (default)
python scripts/send_whats_new_sms.py --title "New Video" --description "Check it"

# Without art
python scripts/send_whats_new_sms.py --title "New Video" --description "Check it" --no-art
```

Done! Your SMS messages are now more visually interesting while staying under character limits.
