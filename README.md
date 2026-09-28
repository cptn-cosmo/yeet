# Yeet (`gay.geeks.Yeet`)

> **Wayland-native, KDE 6 HIG-compliant interactive stream throwing system and 2D physics overlay for OBS Studio.**  
> A modern, open-source Linux alternative to Twitch Integrated Throwing System (T.I.T.S.).

[![License: GPL-3.0-or-later](https://img.shields.io/badge/License-GPL--3.0--or--later-blue.svg)](https://www.gnu.org/licenses/gpl-3.0.html)
[![Documentation: CC0-1.0](https://img.shields.io/badge/Docs-CC0--1.0-lightgrey.svg)](https://creativecommons.org/publicdomain/zero/1.0/)
[![Platform: Linux (Pure Wayland)](https://img.shields.io/badge/Platform-Linux%20Wayland-brightgreen.svg)](https://wayland.freedesktop.org/)
[![Toolkit: Qt6 / KDE 6](https://img.shields.io/badge/UI-Qt6%20%2F%20KDE%206-blue.svg)](https://develop.kde.org/hig/)

---

## 🎯 Overview

**Yeet** allows livestreamers and VTubers to configure customizable 2D collision targets (where thrown items hit a streamer's avatar, webcam, or stream assets), set up multiple throwable items with procedural collision sound effects and realistic trajectories, trigger throws via a local HTTP REST API or chat bot redeems, and render the physics overlay through an HTML5 browser source inside OBS Studio.

Built with **Qt6** and designed according to the **KDE Human Interface Guidelines (HIG)**, Yeet integrates seamlessly into KDE Plasma 6 on pure Wayland sessions with zero legacy X11 dependencies.

> 📖 **Need the complete in-depth technical guide?** Check out the standalone [DOCUMENTATION.md](file:///home/cosmo/Projects/yeet/DOCUMENTATION.md).

---

## ✨ Features

- **Pure Wayland Desktop App (Qt6 / KDE 6 Native):**
  - Designed according to modern KDE 6 HIG with Breeze theme integration, navigation sidebar, card-based section layouts, and status pill badges.
  - Interactive coordinate mapper (`QPainter`) with direct mouse manipulation (drag center to move, corners to resize, top arm to rotate, vertices to reshape).
  - Supports loading stream screenshots / avatar backdrops directly into the mapper for precision collider alignment.
  - One-click button to copy the OBS Browser Source URL to clipboard with desktop toast notifications.
- **Resolution-Independent Coordinates:**
  - All spatial dimensions, coordinates, velocities, and collider geometries use **normalized relative units (0.0 to 1.0)**.
  - Consistent physics and collision behavior across 1080p, 1440p, 4K, or vertical (9:16) stream canvas aspect ratios.
- **Collision Target Template Shapes:**
  - **Capsule / Pill:** Standard for VTuber torsos, necks, and limbs.
  - **Rectangle / Box:** Ideal for webcams, chat boxes, and desktop windows.
  - **Circle / Ellipse:** Perfect for avatars, badges, and circular masks.
  - **Custom Polygon (Convex Hull):** Draggable anchor points with interactive vertex insertion (double-click) and deletion.
- **Spawn Behaviors & Trajectories:**
  - **Aimed Arc:** Calculates exact ballistic trajectory aimed directly at the target center with gravity compensation.
  - **Screen Edges:** Top, Bottom, Left, Right, or Random edge.
  - **Rain / Dropping:** Top-down drop with natural world gravity.
  - **Point-Source Spray:** Spawns from a custom origin point with adjustable spread angle.
- **Throwable Items Inventory & Categorized Groups:**
  - Supports custom 2D images in PNG, WebP, GIF, and SVG formats.
  - Configurable properties: scale, mass, restitution (bounciness), spin / rotational speed, gravity scale, and lifetime.
  - Ships with preset items: Ripe Tomato, Red Brick, Cream Pie, Rubber Duck, Water Balloon, Beach Ball, and Heart Plushie.
  - Full item grouping and filtering (`food`, `construction`, `toys`, `summer`, `cute`).
- **Low-Latency Polyphonic Audio Engine:**
  - Powered by the Web Audio API with procedural sound synthesis ("squish", "bonk", "thud", "pop", "clang") or custom audio files (`.wav`, `.mp3`, `.ogg`).
  - Real-time pitch randomization on every impact to prevent repetitive ear fatigue.
  - Built-in sound debounce and master `DynamicsCompressorNode` limiter to prevent digital clipping during high-volume barrage throws.
- **Embedded Local Daemon (HTTP REST & WebSocket):**
  - Lightweight async server running on `127.0.0.1:49122`.
  - Real-time two-way synchronization: configuration changes and target repositioning reflect immediately in OBS without reloading the browser source.
  - Clean REST API for bots (Streamer.bot, MixItUp, SAMMI, Twitch channel points, curl).
  - Outbound First Hit / Last Hit webhooks with barrage settling detection for VTube Studio and smart lighting.

---

## 📦 Throwable Items & Groups Reference

### Preset Items Catalog

Yeet includes seven carefully tuned projectile presets out of the box:

| Item ID | Display Name | Group | Asset Path | Scale | Mass | Bounciness | Spin | Gravity | Lifetime | Sound | Vol | Pitch Var |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| `tomato` | **Ripe Tomato** | `food` | `/assets/items/tomato.svg` | `0.08` | `0.8` kg | `0.40` | `1.5` | `1.00` | `8.0` s | `squish` | `0.90` | `0.20` |
| `brick` | **Red Brick** | `construction` | `/assets/items/brick.svg` | `0.09` | `2.5` kg | `0.25` | `0.8` | `1.30` | `10.0` s | `thud` | `1.00` | `0.15` |
| `pie` | **Cream Pie** | `food` | `/assets/items/pie.svg` | `0.10` | `0.9` kg | `0.30` | `1.2` | `0.90` | `8.0` s | `squish` | `0.95` | `0.25` |
| `rubber_duck` | **Rubber Duck** | `toys` | `/assets/items/rubber_duck.svg` | `0.08` | `0.5` kg | `0.85` | `2.0` | `0.80` | `12.0` s | `bonk` | `0.85` | `0.30` |
| `water_balloon` | **Water Balloon** | `summer` | `/assets/items/water_balloon.svg` | `0.08` | `0.7` kg | `0.45` | `1.3` | `1.00` | `7.0` s | `squish` | `0.90` | `0.20` |
| `heart` | **Heart Plushie** | `cute` | `/assets/items/heart.svg` | `0.09` | `0.4` kg | `0.70` | `1.0` | `0.70` | `9.0` s | `pop` | `0.80` | `0.25` |
| `beachball` | **Beach Ball** | `summer` | `/assets/items/beachball.svg` | `0.13` | `0.25` kg | `0.92` | `1.5` | `0.45` | `14.0` s | `pop` | `0.85` | `0.25` |

---

### Item Groups & Intended Uses

Groups categorize items so streamers can trigger thematic barrages, allow viewers to choose categories, or exclude certain classes of items:

| Group Name | Included Preset Items | Suggested Stream Uses |
| :--- | :--- | :--- |
| `food` | `tomato`, `pie` | Slapstick food fights, cooking stream channel points, pun punishments |
| `construction` | `brick` | High-impact punishment, raid barrages, big bit cheers |
| `toys` | `rubber_duck` | Playful viewer greetings, cartoon bonks, high-bounce chaos |
| `summer` | `beachball`, `water_balloon` | Beach / pool party streams, floaty low-gravity barrages |
| `cute` | `heart` | Sub gifts, tier milestones, love / hug redeems |
| `default` | *(Fallback group)* | Custom items created without an explicit group tag |

---

### Group Filtering & Exclusion Rules

When invoking the REST API (`/api/v1/throw`), you can control item pools using these rules:
- **Throw by Group:** `group=summer` or `group=food,toys` (aliases: `item_group`, `groups`, `item_groups`).
- **Include Specific Items + Groups:** `items=brick&group=summer` (throws bricks plus beachballs and water balloons).
- **Exclude Groups or Items:** `items=all&group_exclude=construction` or `item_exclude=food,brick` (aliases: `exclude`, `items_exclude`, `exclude_group`, `exclude_item`).
- **Random Mix Mode:** Setting `item=random_mix` causes each projectile in a barrage (`amount > 1`) to be randomly and independently sampled from the resolved candidate pool.

---

## 📡 REST API Reference

The local HTTP server listens by default on `http://127.0.0.1:49122`. All endpoints support **CORS** (`Access-Control-Allow-Origin: *`).

### 1. Trigger a Throw
- **Endpoint:** `POST /api/v1/throw` or `GET /api/v1/throw`
- **Headers:** `Content-Type: application/json` *(for POST)*
- **Parameters (JSON Body or URL Query String):**
  - `item` *(optional, default: "random")*: Item ID (`"brick"`, `"tomato"`, etc.), `"random"`, or `"random_mix"` / `"mix"`.
  - `items` *(optional for random_mix)*: `"all"` or comma-separated list of item IDs/names.
  - `group` / `item_group` *(optional)*: Filter pool by group name (`"summer"`, `"food"`, etc.).
  - `item_exclude` / `group_exclude` / `exclude` *(optional)*: Exclude items or groups.
  - `amount` *(optional, default: 1)*: Number of projectiles (`1` – `100`).
  - `spawn_direction` / `direction` *(optional, default: configured)*: `"aimed"`, `"left"`, `"right"`, `"top"`, `"bottom"`, `"random"`, `"rain"`, or `"spray"`.
  - `force` *(optional, default: 1.0)*: Velocity multiplier (`0.1` – `5.0`).
  - `spread` *(optional, default: 15.0)*: Launch angle variance in degrees.

**Example 1: POST JSON (Streamer.bot / Webhooks / Scripts)**
```bash
curl -X POST http://127.0.0.1:49122/api/v1/throw \
  -H "Content-Type: application/json" \
  -d '{"item": "beachball", "amount": 3, "spawn_direction": "aimed", "force": 1.2}'
```

**Example 2: GET with Query String (Chat Bots / Bookmarks)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=beachball&amount=3&spawn_direction=rain&force=1.2"
```

**Example 3: Random Mix from a specific item group (e.g. summer)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&group=summer&amount=4"
```

**Example 4: Random Mix excluding multiple groups (comma-separated)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&item_exclude=winter,food&amount=6"
```

---

### 2. Trigger an Immediate Collision Event
- **Endpoint:** `GET /api/v1/collision` or `POST /api/v1/collision`
- Simulates an immediate impact directly on an avatar target (e.g. for channel point redeems like "!slap" or "!bonk" without waiting for projectile flight time). Plays the collision sound effect with pitch randomization and spawns an impact particle burst in OBS!
- **Parameters:**
  - `target` / `target_id` *(optional)*: Target ID or name (e.g. `"VTuber Head"`). Defaults to primary target.
  - `item` *(optional)*: Item to simulate impact for (e.g. `"pie"`, `"brick"`).
  - `sound` *(optional)*: Sound override (`"squish"`, `"bonk"`, `"thud"`, `"pop"`, `"clang"`).
  - `volume` *(optional)*: Volume multiplier (`0.0` – `1.0`).

```bash
# Direct slap with Cream Pie
curl "http://127.0.0.1:49122/api/v1/collision?target=VTuber+Head&item=pie&sound=squish"
```

---

### 3. Collision Statistics & Counters
- **Endpoint:** `GET /api/v1/collisions`
- Returns total impact counts, breakdown by target, breakdown by item, and recent collision logs.
- Reset counter endpoint: `GET /api/v1/collisions/reset` or `POST /api/v1/collisions/reset`.

```bash
curl http://127.0.0.1:49122/api/v1/collisions
```

---

### 4. Clear Active Items
- **Endpoint:** `POST /api/v1/clear` or `GET /api/v1/clear`
- Immediately removes all active physics bodies from all connected OBS browser sources.

```bash
curl -X POST http://127.0.0.1:49122/api/v1/clear
```

---

### 5. List Throwable Items
- **Endpoint:** `GET /api/v1/items`
- Returns an array of configured items and their physical/audio parameters. Supports optional `?group=<name>` filtering.

```bash
# All items
curl http://127.0.0.1:49122/api/v1/items

# Filter by group
curl "http://127.0.0.1:49122/api/v1/items?group=summer"
```

---

### 6. Manage Collision Targets
- **Endpoint:** `GET /api/v1/targets` and `POST /api/v1/targets`
- Fetch or update the collision boundaries dynamically.

```bash
curl http://127.0.0.1:49122/api/v1/targets
```

---

### 7. Daemon Status & Client Config
- **Status:** `GET /api/v1/status` (uptime, active targets, connected overlays, total hits)
- **Config:** `GET /api/v1/config` (full client targets, items, and physics configuration)

```bash
curl http://127.0.0.1:49122/api/v1/status
```

---

### 8. First Hit & Last Hit Collision Webhooks
Yeet features an intelligent **barrage settling engine** that triggers outbound HTTP requests to external software (such as VTube Studio, VNyan, Lumia Stream, Streamer.bot, or smart lights):
- **First Hit URL:** Fired **immediately** upon the very first impact of a throw or barrage (e.g. trigger a shocked VTuber expression or flash studio lights red).
- **Barrage Debounce:** Intermediate impacts occurring while items are continuously pelting the target will *not* flood your external webhooks.
- **Last Hit URL:** Fired once the barrage settles and no new collisions occur for the configured **Settling Delay** (default: `2.0` seconds). Perfect for restoring a neutral VTuber expression or returning lights to normal.

#### URL Template Placeholders
Both GET and POST URLs support dynamic string interpolation:
- `{target}`: Target name (URL encoded, e.g. `VTuber+Head`)
- `{item}`: Item name that made the impact (e.g. `Beach+Ball`)
- `{hits}`: Total number of collisions accumulated during this barrage
- `{event}`: `"first_hit"` or `"last_hit"`

#### Webhook Endpoints
- `GET /api/v1/webhooks`: View current webhook settings
- `POST /api/v1/webhooks`: Update webhook settings dynamically
- `GET /api/v1/webhooks/test?event=first_hit`: Test the first hit trigger
- `GET /api/v1/webhooks/test?event=last_hit`: Test the last hit trigger

---

## 🎥 OBS Studio Integration Guide

1. Open **OBS Studio**.
2. Under **Sources**, click **+** and select **Browser**.
3. Name the source (e.g. `Yeet Physics Overlay`).
4. In the properties window:
   - **URL:** `http://127.0.0.1:49122/overlay` (or click **Copy URL** in Yeet's toolbar).
   - **Width:** `1920` (or your stream canvas width).
   - **Height:** `1080` (or your stream canvas height).
   - **Custom frame rate:** Checked, set to `60` FPS.
   - **Shutdown source when not visible:** **UNCHECKED** *(crucial to keep WebSocket alive)*.
   - **Refresh browser when scene becomes active:** **UNCHECKED**.
5. Click **OK**.
6. Switch to Yeet and click **Test Throw** in the toolbar or Physics playground to see items hit your target!

---

## 🛠️ Building & Packaging

### Arch Linux / AUR
Build and install using the included `PKGBUILD`:
```bash
cd yeet
makepkg -si
```

### Manual Build with Meson
```bash
# Configure build
meson setup build --prefix=/usr

# Compile and run test suite (validates desktop, metainfo, and Qt6 UI test suite)
meson compile -C build
meson test -C build

# Install to system
sudo meson install -C build
```

### Running from Source (Development)
You can run Yeet directly without system installation:
```bash
./bin/yeet
```

---

## 📂 Project Architecture

```
yeet/
├── DOCUMENTATION.md                    # Comprehensive technical manual & API reference
├── data/
│   ├── gay.geeks.Yeet.desktop.in       # FreeDesktop application entry (Qt/KDE)
│   ├── gay.geeks.Yeet.metainfo.xml.in  # AppStream metainfo specification
│   └── icons/
│       ├── gay.geeks.Yeet.svg          # Scalable vector application icon
│       └── hicolor/
│           ├── scalable/apps/gay.geeks.Yeet.svg
│           └── symbolic/apps/gay.geeks.Yeet-symbolic.svg
├── overlay/                            # OBS Browser Source HTML5 Engine
│   ├── index.html                      # Transparent canvas entry point
│   ├── overlay.js                      # Matter.js loop, Web Audio API, WebSocket client
│   ├── overlay.css                     # Responsive viewport styling
│   └── matter.min.js                   # Vendored offline 2D physics engine
├── assets/
│   ├── items/                          # Default SVG item presets
│   │   ├── tomato.svg
│   │   ├── brick.svg
│   │   ├── pie.svg
│   │   ├── rubber_duck.svg
│   │   ├── water_balloon.svg
│   │   ├── heart.svg
│   │   └── beachball.svg
│   └── sounds/                         # Custom collision audio samples
├── yeet/
│   ├── __init__.py
│   ├── main.py                         # App entrypoint
│   ├── app.py                          # QApplication subclass
│   ├── qt_compat.py                    # PySide6 & PyQt6 compatibility layer
│   ├── config.py                       # ~/.config/yeet/config.json persistence
│   ├── models.py                       # Target, Item, Physics data structures
│   ├── server.py                       # aiohttp REST API & WebSocket daemon
│   └── ui/
│       ├── __init__.py
│       ├── widgets.py                  # KDE 6 cards, expanders, status badges & toast
│       ├── window.py                   # QMainWindow with Breeze toolbar & navigation sidebar
│       ├── mapper_canvas.py            # Interactive Qt6/QPainter normalized coordinate mapper
│       ├── target_view.py              # Collision boundary setup & handles
│       ├── items_view.py               # Item inventory & audio controls
│       ├── physics_view.py             # Spawns, gravity, and test throw playground
│       ├── server_view.py              # Daemon status, URL copy, & REST API guide
│       └── about_dialog.py             # KDE 6 style About application dialog
├── tests/
│   └── test_yeet_qt.py                 # Automated unit test suite
├── bin/
│   ├── yeet                            # Executable launcher
│   └── yeet.in                         # Meson configured template
├── PKGBUILD                            # Arch Linux packaging script
├── meson.build                         # Meson build definitions
└── meson_options.txt                   # Meson build options
```

---

## ⚖️ License

Yeet is free and open-source software licensed under the **GNU General Public License v3.0 or later** (`GPL-3.0-or-later`).  
The metadata and documentation are licensed under **CC0-1.0**.
