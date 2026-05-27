# Pico SpellSpinner

A physical D&D spell reference device built on a Raspberry Pi Pico 2 W. Three screens — a start splash, a randomised spell card, and a scrollable details page — wired together by a tunable router (instant cuts by default; a retro curtain wipe is one knob away). All on a tiny 240×135 LCD that mounts directly on the Pico.

```
   Start ────A──▶ Spell Card ────A──▶ Details
     ▲             │ ▲   ▲             │
     └──────B──────┘ │   │             │
                    ◀┘   └──LEFT/RIGHT─┤
                    SHAKE              │
                                       │
                       ◀───────B───────┘
```

| Key | On the spell card | On the details page |
|---|---|---|
| `A` | Open details | — |
| `B` | Back to start | Back to spell card |
| `LEFT` / `RIGHT` | Roll a new random spell (with curtain) | — |
| `SHAKE` | Roll a new random spell *(MPU not yet wired — see Roadmap v2; use LEFT / RIGHT in the meantime)* | — |
| `UP` / `DOWN` | — | Scroll the description |

---

## Hardware

| Component | Role |
|---|---|
| Raspberry Pi Pico 2 W | Brain — RP2350, 520 KB RAM, 4 MB flash, Wi-Fi/BT |
| 1.14" IPS LCD (240×135, ST7789VW, SPI) | Display — mounts on top of the Pico |
| MPU-6050 6DOF IMU (I2C) | Shake detection via 3-axis accelerometer — **driver is code-ready, but the IMU is not yet physically wired in this build.** If the I2C init fails at boot, shake is silently disabled and the rest of the device runs normally. Wiring planned for v2. |
| Acrylic case | Houses the stack |

**Pin map (display — Waveshare layout)**
`CS=GP9 · DC=GP8 · CLK=GP10 · MOSI=GP11 · RST=GP12 · BL=GP13`

**Input (display module onboard)**
`UP=GP2 · DOWN=GP18 · LEFT=GP16 · RIGHT=GP20 · CTR=GP3 · A=GP15 · B=GP17`

**MPU-6050** connects via I2C (address `0x68`) on GP4 (SDA) / GP5 (SCL).

---

## Language

**MicroPython.** No compile step — save a file, it runs. Fast to iterate and a natural home for a small in-house design system — screens designed in Figma, rendered through a token-driven UI kit.

---

## Tech Stack

| Tool / Library | Why | How it's used |
|---|---|---|
| **MicroPython** | Runs on the Pico — no compile step, direct hardware access | All on-device code (`main.py`, `lib/`, `data/`) |
| **Python 3.10+** | Runs build scripts and the simulator on desktop | `tools/`, `simulator/` |
| **pico-ui-kit** | UI library — tokens, drawing primitives, components, bitmap fonts | Vendored as a git submodule at `pico-ui-kit/` |
| **pygame** | Desktop window for the simulator | `simulator/display.py` renders the 240×135 frame at 3× scale |
| **Pillow** | Image processing for icon conversion | `tools/build_icons.py` reads PNGs and converts to 1-bit bitmaps |
| **Silkscreen** | Pixel font — fixed pitch, designed for low-res screens | Bold 16px for spell name + title, Regular 8px elsewhere — pre-baked into pico-ui-kit |
| **mpremote** | USB file transfer + REPL for the Pico | `tools/deploy.py` and one-off commands |

---

## Tokens

All colours, spacing, and radii are defined as JSON in `pico-ui-kit/tokens/src/` and built into Python modules consumed by every component. No raw colour or pixel value lives in component or drawing code.

```
tokens/src/  (JSON sources)
  └── python3 tokens/build_tokens.py
        ├── tokens/primitive.py        ← raw color/number values
        ├── tokens/semantic_light.py   ← named role aliases — light palette
        ├── tokens/semantic_dark.py    ← named role aliases — dark palette
        ├── tokens/semantic.py         ← re-exports light or dark via colormode.py
        ├── tokens/colormode.py        ← boot-time selector (reads mode.cfg)
        └── tokens/viewport.py         ← spacing, type scale, radii for XS screen
              └── imported by components — no hardcoded values anywhere
```

### Switching theme palette (build-time)

The token build script regenerates `primitive.py`, `semantic_light.py`, `semantic_dark.py`, and `viewport.py` for a chosen colour-theme index and viewport size:

```bash
cd pico-ui-kit
python3 tokens/build_tokens.py                       # default: theme 1, viewport xs
python3 tokens/build_tokens.py --theme 2             # switch to theme palette 2
python3 tokens/build_tokens.py --viewport sm         # xs | sm | md | lg | xl
python3 tokens/build_tokens.py --theme 2 --viewport sm
```

### Switching light ↔ dark (runtime)

The active mode (light / dark) is selected at boot from a `mode.cfg` file at the device root. `tokens/colormode.py` reads it and re-exports the matching `semantic_light` or `semantic_dark` module through `tokens.semantic`:

```bash
# On the Pico (via mpremote REPL or by editing the file directly):
echo "dark" > mode.cfg     # or 'light'
# then reset the device
```

If `mode.cfg` is absent or unreadable, `light` is used.

---

## Data

Source: `Spell sheet.xlsx` — sheet `Spell List Descriptions`.

### Columns used on-device

| Column | Display use |
|---|---|
| `Spell Name` | Primary heading on spell card (wraps to 2 lines) + heading on details page |
| `Option_A` (level) | Level badge (top-left) — header was unnamed in the latest sheet export; the build script recovers it |
| `Ritual` | Sparkles icon badge next to the level badge (shown when Yes) |
| `Components` | V · S · M badges (top-right of spell card) |
| `Casting Time` | Meta row under the spell name |
| `Use` | Meta row (Damage / Healing / Utility) |
| `Page No.` | Page reference badge (bottom-right of spell card) |
| `School` | School icon (left of spell card) + accent colour of the level badge and bar — header is blank in the export, the build script renames the second blank column |
| `Discription` | Full body shown on the details page (typo preserved — that's the CSV column name) |

### Columns not used on-device

`Material`, `Cast condition`, `Save/Attack Roll`, `Utility Effect`, `Duration`, `Damage Type`, `Letter`, class flags — not yet surfaced.

---

## Screen Layout

Three screens, all 240×135:

### Start (`screens/start.py`)

```
┌─────────────────────────────────────────┐
│                                         │
│                [V0.0.1]                 │  ← version badge (semantic info)
│              SPELL                      │
│             SPINNER                     │  ← title (16px bold)
│             [Start (A)]                 │  ← primary button + option_a icon
│                                         │
└─────────────────────────────────────────┘
```

### Spell Card (`screens/spell_card.py`)

```
┌─────────────────────────────────────────┐
│ [Level] [✦]              [V] · [S] · [M]│  ← row 1: level + ritual + components
│                                         │
│   🔮  Acid Splash                       │  ← row 2: 36×36 school icon
│       ▬▬▬▬                              │            spell name (16px bold)
│       Action · Damage                   │            school accent bar (40×2)
│                                         │            meta row (casting · use)
│ [details (A)]                  p.259    │  ← row 3: details button + page badge
└─────────────────────────────────────────┘
```

### Details (`screens/details.py`)

```
┌─────────────────────────────────────────┐
│ ┌─────────────────────────────────────┐ │  ← surface level 2 card
│ │ Acid Splash                         │ │     (top row hidden — title moved up)
│ │ You create an acidic bubble at a    │ │
│ │ point within range, where it        │ │
│ │ explodes in a 5-foot-radius Sphere. │ │
│ │ [(B) Back]                          │ │
│ └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Conventions

- **Level badge + accent bar** use the school's accent slot. Sampled from the source PNG, so re-export an icon to change a school's colour.
- **V / S / M badges** are always semantic-neutral, ghost emphasis.
- **School icon** is a 1-bit silhouette drawn in the dominant colour sampled from its source PNG. No stud wrapper — the icon sits directly on the surface.
- **Screen transitions** are routed through `screens/transitions.py`. Default is an instant cut (`_STEPS = 0`); set `_STEPS > 0` to enable the retro curtain wipe — bars converge from top and bottom, the new screen renders behind them, and the bars retract.
- **School → accent slot** mapping (`_SCHOOL_ACCENT` in `screens/spell_card.py`):
  `Evocation=001 · Conjuration=002 · Enchantment=003 · Illusion=004 · Divination=005 · Abjuration=006 · Necromancy=007 · Transmutation=009` (slot 008 unused).

---

## Dev Setup

### Clone

```bash
git clone --recurse-submodules https://github.com/j-igrec/pico-spellspinner
```

`--recurse-submodules` initialises and clones `pico-ui-kit` automatically. On an existing clone without it, run:

```bash
git submodule update --init
```

### Prerequisites

```bash
pip install pygame pillow mpremote
pip install font-to-py   # only needed to regenerate fonts from TTF
```

| Tool | Purpose |
|---|---|
| Python 3.10+ | Runs the simulator and build scripts |
| `pygame` | Simulator display |
| `Pillow` | Icon PNG → 1-bit bitmap conversion (`tools/build_icons.py`) |
| `mpremote` | USB file transfer to the Pico (`tools/deploy.py`) |
| `font-to-py` | Converts TTF → MicroPython bitmap font modules (pre-baked, only re-run if fonts change) |

### Running the simulator

```bash
python3 pico-ui-kit/simulator/run.py main.py           # full app entry
# or, to run the screen file directly without going through main.py:
python3 pico-ui-kit/simulator/run.py screens/spell_card.py
```

The simulator renders on a 240×135 pygame window at 3× scale.

| Key | Maps to | Effect |
|---|---|---|
| `A` | A button | Enter / open details |
| `B` | B button | Back |
| Arrow keys | Joystick UP / DOWN / LEFT / RIGHT | Scroll details · roll random spell |
| Space | Joystick centre press | (reserved) |
| `S` | Simulated shake | Roll random spell on the card |
| Escape | — | Quit simulator |

### Hardware target

**Raspberry Pi Pico 2 W** running MicroPython. Files are deployed via `tools/deploy.py` which copies both `pico-ui-kit/` and the app files onto the Pico over USB. No internet access required on the device.

**What to deploy to the Pico** (`tools/deploy.py` already handles this list):

From the project:
- `main.py`, `config.py`, `mode.cfg`
- `screens/__init__.py`, `screens/router.py`, `screens/transitions.py`, `screens/start.py`, `screens/spell_card.py`, `screens/details.py`
- `data/__init__.py`, `data/spells.py`
- `lib/st7789.py`, `lib/mpu6050.py`, `lib/school_icons.py`

From the `pico-ui-kit/` submodule:
- `tokens/__init__.py`, `primitive.py`, `semantic.py`, `semantic_light.py`, `semantic_dark.py`, `colormode.py`, `viewport.py`
- `drawing/` — `rect.py`, `text.py`, `line.py`, `icon.py`
- `components/` — `badge.py`, `button.py`, `status_dot.py`
- `icons/` — `option_a.py`, `option_b.py`, `sparkles.py` (only the icons we use)
- `fonts/` — bitmap font modules

Do **not** deploy `simulator/`, `tokens/src/`, `tokens/build_tokens.py`, `adapter.py`, or unused icons — these are desktop-only or unused on-device.

### Pulling library updates

```bash
git submodule update --remote pico-ui-kit
```

---

## Updating Spell Data

1. Edit `Spell sheet.xlsx`
2. Export the spell sheet as CSV → save to `data/src/spell-sheet.csv`
3. Rebuild:
   ```bash
   python3 tools/build_spells.py
   ```

## Updating School Icons

1. Provide each school icon as a PNG with transparency (36px or larger). Keep the artwork in its school colour — the build script samples the dominant opaque pixel and stores it alongside the bitmap, so on-device the icon renders in that colour without any extra lookup.
2. Name files exactly: `Evocation.png`, `Enchantment.png`, `Illusion.png`, `Divination.png`, `Abjuration.png`, `Conjuration.png`, `Transmutation.png`, `Necromancy.png`
3. Drop them into `data/src/icons/`
4. Rebuild:
   ```bash
   python3 tools/build_icons.py
   ```

Each entry in `lib/school_icons.py` is `(width, height, bitmap, (r, g, b))`. To change a school's accent colour on the spell card, re-export the PNG in the new colour and rerun.

## Updating Tokens

1. Edit the token JSON in `pico-ui-kit/tokens/src/`
2. Rebuild:
   ```bash
   cd pico-ui-kit
   python3 tokens/build_tokens.py                       # defaults: theme 1, viewport xs
   # or pick a different palette / viewport size:
   python3 tokens/build_tokens.py --theme 2 --viewport sm
   ```

This regenerates `primitive.py`, `semantic_light.py`, `semantic_dark.py`, and `viewport.py`. To switch the **runtime** light/dark mode on the device, see *Switching light ↔ dark (runtime)* above.

---

## Configuration

`config.py` holds all tuneable constants — no need to touch `main.py` for hardware changes.

| Constant | Default | Notes |
|---|---|---|
| `LCD_SPI` … `LCD_BL` | see file | SPI bus and GPIO pins for the display |
| `IMU_I2C` / `IMU_SDA` / `IMU_SCL` | bus 0, GP4/GP5 | I2C bus for the MPU-6050 |
| `BTN_A` / `BTN_B` | GP15 / GP17 | Action buttons — active-low with internal pull-up |
| `JOY_UP` / `DOWN` / `LEFT` / `RIGHT` / `CTR` | GP2 / GP18 / GP16 / GP20 / GP3 | Joystick directions + centre press — active-low with internal pull-up |
| `BTN_DEBOUNCE` | `200` ms | Minimum gap between two input triggers (shared by all buttons + joystick). |
| `SHAKE_THRESHOLD` | `2.5` g | Total acceleration magnitude to trigger. Compared as `mag² > threshold²` internally to avoid a per-tick `sqrt`. |
| `SHAKE_DEBOUNCE` | `1000` ms | Minimum gap between two shake triggers. |

---

## Hardware Drivers

`lib/mpu6050.py` and `lib/st7789.py` are included in this repo. Both expose the same API as `simulator/display.py` so all components run unchanged on hardware and desktop.

### ST7789 display offsets

The ST7789VW chip has a 240×320 frame memory; the 1.14" panel is a 240×135 window into it. In landscape mode the window starts at column 40, row 53. These are hardcoded in `lib/st7789.py`:

```python
_X_OFFSET = 40
_Y_OFFSET = 53
```

If the image appears shifted on your board, those are the two numbers to adjust (they are in `lib/st7789.py`, not `config.py`).

### Color format

All tokens and component calls use `(r, g, b)` tuples. `lib/st7789.py` converts them to RGB565 internally on `show()` — you never deal with packed integers in component code.

---

## Reference Documentation

### MPU-6050

| Resource | What it covers |
|---|---|
| [MPU-6000 Register Map](https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Register-Map1.pdf) | Authoritative register reference — `0x6B` (power), `0x3B` (accel data) |
| [MicroPython `machine.I2C`](https://docs.micropython.org/en/latest/library/machine.I2C.html) | `writeto_mem` / `readfrom_mem` API |
| [MicroPython `struct`](https://docs.micropython.org/en/latest/library/struct.html) | `'>hhh'` format: big-endian, 3 × signed 16-bit int |

### ST7789 display

| Resource | What it covers |
|---|---|
| ST7789 datasheet (search "ST7789 datasheet Sitronix") | Init command sequence, CASET / RASET / RAMWR protocol |
| [MicroPython `machine.SPI`](https://docs.micropython.org/en/latest/library/machine.SPI.html) | SPI bus init and `write()` |
| [font_to_py by Peter Hinch](https://github.com/peterhinch/micropython-font-to-py) | How bitmap fonts are structured — explains the glyph format used in `write()` |

### MicroPython & hardware

| Resource | What it covers |
|---|---|
| [MicroPython docs](https://docs.micropython.org/en/latest/) | Full standard library; RP2-specific page under "Quick reference for the RP2" |
| [Raspberry Pi Pico 2 W documentation](https://www.raspberrypi.com/documentation/microcontrollers/pico-series.html) | Pinout, datasheet, hardware design files |

---

## Planned Features

### v1 — Shake to Spin ✓
- Boot to random spell
- LEFT / RIGHT joystick → new random spell

### v2 — Start screen, details, and hardware shake
- ✓ Title screen with `Start (A)` button
- ✓ Details page with scrollable spell description (UP / DOWN joystick)
- ✓ Tunable transitions (`screens/transitions.py`) — instant cut by default, curtain wipe available
- ⏳ Wire up the MPU-6050 so the SHAKE input fires on real hardware (driver code is ready and gracefully no-ops when the sensor is absent)

### v3 — Filter by Class
- Select a class (Bard, Cleric, Druid, Paladin, Ranger, Sorcerer, Warlock, Wizard)
- Shake or browse only spells for that class

### v4 — Filter by Level / Type
- Filter by spell level (Cantrip, 1–9)
- Filter by use type (Damage / Healing / Utility)

### v5 — Loot Table
- Separate mode triggered by a button combo
- Roll on a loot table, display using the same card layout

### Future ideas
- Wi-Fi sync to pull updated spell/loot data
- Save a favourites list to flash
- Re-enable the details page top row (level + components) with a long-press toggle

---

## Project Structure

```
pico-spellspinner/
├── README.md
├── .gitmodules                # declares pico-ui-kit submodule
├── Spell sheet.xlsx           # source data (not deployed to Pico)
├── config.py                  # pin assignments (display, IMU, A/B, joystick), debounce
├── main.py                    # hardware entry — sys.path + loop, delegates to router
├── mode.cfg                   # 'light' | 'dark' — picked up at boot by tokens/colormode.py
├── screens/
│   ├── __init__.py
│   ├── router.py              # goto() / dispatch() — owns the active screen
│   ├── transitions.py         # curtain effect — top + bottom bars converge then retract
│   ├── start.py               # title screen — A enters
│   ├── spell_card.py          # spell card — A=details, B=start, LEFT/RIGHT/SHAKE=random
│   └── details.py             # scrollable description — UP/DOWN scroll, B back
├── data/
│   ├── __init__.py
│   ├── spells.py              # generated spell table (includes description) — deployed
│   └── src/
│       ├── spell-sheet.csv    # exported from Spell sheet.xlsx
│       └── icons/             # school icon PNGs — colour preserved (sampled at build time)
├── lib/
│   ├── st7789.py              # ST7789 display driver (framebuffer, RGB tuple API)
│   ├── mpu6050.py             # MPU-6050 driver — .accel → (ax, ay, az) in g
│   └── school_icons.py        # generated — (w, h, bitmap, (r,g,b)) per school
├── tools/
│   ├── build_spells.py        # CSV → data/spells.py (recovers blank School + Option_A headers)
│   ├── build_icons.py         # PNGs → lib/school_icons.py (samples dominant colour)
│   └── deploy.py              # copies pico-ui-kit/ + app onto the Pico via USB
└── pico-ui-kit/               # git submodule
    ├── tokens/
    │   ├── src/               # JSON token sources (not deployed to Pico)
    │   ├── build_tokens.py    # desktop only — regenerates the token modules
    │   ├── primitive.py       # generated — raw colors/numbers
    │   ├── semantic.py        # generated — re-exports light or dark via colormode
    │   ├── semantic_light.py  # generated — light palette
    │   ├── semantic_dark.py   # generated — dark palette
    │   ├── colormode.py       # boot-time selector reading mode.cfg
    │   └── viewport.py        # generated — spacing/type/radii (default: xs)
    ├── drawing/
    │   ├── rect.py            # fill_rect, rounded_rect, fill_rounded_rect
    │   ├── text.py            # write, word_wrap
    │   ├── line.py            # hline, vline, dot
    │   └── icon.py            # draw_icon — tint a 1-bit bitmap with any colour
    ├── fonts/
    │   ├── monob16.py         # Silkscreen Bold 16px (bitmap)
    │   ├── monob8.py          # Silkscreen Bold 8px
    │   ├── monor16.py         # Silkscreen Regular 16px
    │   └── monor8.py          # Silkscreen Regular 8px
    ├── components/
    │   ├── badge.py           # token-driven badge component
    │   ├── button.py          # primary / secondary button with optional lead/trail icons
    │   └── status_dot.py      # 4×4 status dot (used by badge)
    ├── icons/                 # generated 8×8 icon modules — only option_a, option_b, sparkles are deployed
    ├── adapter.py             # desktop-only Display adapter
    └── simulator/             # desktop only — not deployed to Pico
        ├── display.py         # pygame-backed Display matching the ST7789 API
        └── run.py             # simulator entry point
```
