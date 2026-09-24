# Yeet (`gay.geeks.Yeet`)

> **Wayland-native, GNOME HIG-compliant interactive stream throwing system and 2D physics overlay for OBS Studio.**
> A modern, open-source Linux alternative to Twitch Integrated Throwing System (T.I.T.S.).

---

## 🎯 Overview

**Yeet** allows livestreamers and VTubers to configure customizable 2D collision targets (where thrown items hit a streamer's avatar or camera feed), set up multiple throwable items with collision sound effects and realistic trajectories, trigger throws via a local HTTP REST API, and render the physics overlay through an HTML5 browser source inside OBS Studio.

Built with **GTK4** and **Libadwaita**, Yeet adheres strictly to the **GNOME Human Interface Guidelines (HIG)**, running natively on pure Wayland sessions with zero legacy X11 dependencies.

---

## ✨ Features

- **Pure Wayland Desktop App (GTK4 + Libadwaita):**
  - Designed according to GNOME HIG (`AdwApplicationWindow`, `AdwHeaderBar`, `AdwPreferencesPage`, `AdwActionRow`, `AdwClamp`).
  - Interactive coordinate mapper (`GtkDrawingArea`) with direct mouse manipulation (drag centers to move, corners to resize, top arm to rotate, vertices to reshape).
  - Supports loading stream screenshots / avatar backdrops directly into the mapper for precision alignment.
  - One-click button to copy the OBS Browser Source URL to clipboard with desktop toast notifications (`AdwToastOverlay`).
- **Resolution-Independent Coordinates:**
  - All spatial dimensions, coordinates, velocities, and collider geometries use **normalized relative units (0.0 to 1.0)**.
  - Consistent physics and collision behavior across 1080p, 1440p, 4K, or custom stream canvas aspect ratios.
- **Collision Target Template Shapes:**
  - **Capsule / Pill:** Standard for VTuber torsos, necks, and heads.
  - **Rectangle / Box:** Ideal for webcams, chat boxes, and desktop windows.
  - **Circle / Ellipse:** Perfect for avatars, badges, and circular masks.
  - **Custom Polygon (Convex Hull):** Draggable anchor points with interactive vertex insertion (double-click) and deletion.
- **Spawn Behaviors & Trajectories:**
  - **Screen Edges:** Top, Bottom, Left, Right, or Random edge.
  - **Aimed Arc:** Calculates exact ballistic trajectory aimed directly at the target center.
  - **Rain / Dropping:** Top-down drop with world gravity.
  - **Point-Source Spray:** Spawns from a custom origin point with adjustable spread angle.
- **Throwable Items Inventory:**
  - Supports custom 2D images in PNG, WebP, GIF, and SVG formats.
  - Configurable properties: scale, mass, restitution (bounciness), spin / rotational speed, gravity scale, and lifetime.
  - Ships with preset items: Ripe Tomato, Red Brick, Cream Pie, Rubber Duck, Water Balloon, and Heart Plushie.
- **Low-Latency Polyphonic Audio Engine:**
  - Powered by the Web Audio API with procedural sound synthesis ("squish", "bonk", "thud", "pop", "clang") or custom audio files (`.wav`, `.mp3`, `.ogg`).
  - Real-time pitch randomization on every impact to prevent repetitive ear fatigue.
  - Built-in sound debounce and master `DynamicsCompressorNode` limiter to prevent digital clipping during high-volume barrage throws.
- **Embedded Local Daemon (HTTP REST & WebSocket):**
  - Lightweight async server running on `127.0.0.1:49122`.
  - Real-time two-way synchronization: configuration changes and target repositioning in GTK reflect immediately in OBS without reloading the browser source.
  - Clean REST API for bots (Streamer.bot, MixItUp, SAMMI, Twitch channel points, curl).

---

## 📡 REST API Reference

The local HTTP server listens by default on `http://127.0.0.1:49122`.

### 1. Trigger a Throw
- **Endpoint:** `POST /api/v1/throw`
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  {
    "item": "brick",
    "amount": 5,
    "spawn_direction": "left",
    "force": 1.2,
    "spread": 15.0
  }
  ```
  - `item` *(optional)*: Item ID or name (`"beachball"`, `"brick"`, `"tomato"`, `"pie"`, `"rubber_duck"`, `"water_balloon"`, `"heart"`), `"random"`, or `"random_mix"`.
  - `items` *(optional for random_mix)*: `"all"` or comma-separated list / JSON array of item IDs or names (e.g. `items=pie,beachball,brick`).
  - `group` / `item_group` *(optional)*: Filter candidate pool by item group tag (e.g. `group=summer`, `group=food`).
  - `item_exclude` / `group_exclude` / `exclude` *(optional)*: Exclude items or entire groups. Supports comma-separated values (e.g. `item_exclude=winter,food`) or repeated query parameters.
  - `amount` *(optional, default: 1)*: Number of items to spawn.
  - `spawn_direction` *(optional, default: configured)*: `"left"`, `"right"`, `"top"`, `"bottom"`, `"random"`, `"aimed"`, `"rain"`, or `"spray"`.
  - `force` *(optional, default: 1.0)*: Velocity multiplier.
  - `spread` *(optional, default: 15.0)*: Angle variance in degrees.

**Example 1: POST with JSON Body (Streamer.bot / Webhooks / Scripts)**
```bash
curl -X POST http://127.0.0.1:49122/api/v1/throw \
  -H "Content-Type: application/json" \
  -d '{"item": "beachball", "amount": 3, "spawn_direction": "aimed", "force": 1.2}'
```

**Example 2: GET with URL Query Parameters (Browser Bookmarks / Chat Bots / Quick Links)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=beachball&amount=3&spawn_direction=rain&force=1.2"
```

**Example 3: Random Mix (All items excluding a group, e.g. winter)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&item_exclude=winter&amount=5"
```

**Example 4: Random Mix from a specific item group (e.g. summer)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&group=summer&amount=4"
```

**Example 5: Random Mix excluding multiple groups (comma-separated)**
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&item_exclude=winter,food&amount=6"
```

> **Note:** In `random_mix` mode, each individual projectile in the barrage is randomly selected independently from the resolved pool. Parameters can be passed via either JSON payload or URL query string, on both `POST` and `GET` requests.

### 2. Trigger a Collision Event (GET & POST)
- **Endpoint:** `GET /api/v1/collision` or `POST /api/v1/collision`
- Simulates an immediate collision directly on an avatar target (e.g. for channel point redeems like "!slap" or "!bonk" without waiting for projectile flight time). Plays the collision sound effect with pitch randomization and spawns an impact particle burst in OBS!
- **Query Parameters / JSON:**
  - `target` *(optional)*: Target ID or name (e.g. `"VTuber Head"`, `"target_vtuber_body"`). Defaults to primary target if omitted.
  - `item` *(optional)*: Item to simulate impact for (e.g. `"beachball"`, `"brick"`, `"tomato"`).
  - `sound` *(optional)*: Sound effect override (`"pop"`, `"bonk"`, `"squish"`, `"thud"`, `"clang"`).
  - `volume` *(optional)*: Volume multiplier ($0.0$ to $1.0$).

```bash
# Direct collision via GET
curl "http://127.0.0.1:49122/api/v1/collision?target=VTuber+Head&item=beachball&sound=pop"

# Direct collision via POST
curl -X POST http://127.0.0.1:49122/api/v1/collision \
  -H "Content-Type: application/json" \
  -d '{"target": "VTuber Head", "item": "pie", "sound": "squish"}'
```

### 3. Collision Statistics & Counters
- **Endpoint:** `GET /api/v1/collisions`
- Returns total impact counts, breakdown by target, breakdown by item, and the recent collision log. Ideal for chat commands like `!hits` or stream leaderboard overlays.
- Reset counter endpoint: `GET /api/v1/collisions/reset` or `POST /api/v1/collisions/reset`.

```bash
curl http://127.0.0.1:49122/api/v1/collisions
```

### 4. Clear Active Items
- **Endpoint:** `POST /api/v1/clear` or `GET /api/v1/clear`
- Immediately removes all active physics bodies from all connected OBS browser sources.

```bash
curl http://127.0.0.1:49122/api/v1/clear
```

### 5. List Throwable Items
- **Endpoint:** `GET /api/v1/items`
- Returns an array of configured items and their physical/audio parameters.

```bash
curl http://127.0.0.1:49122/api/v1/items
```

### 6. Health & Status Check
- **Endpoint:** `GET /api/v1/status`
- Returns daemon uptime, active target count, total collisions, and connected OBS overlay count.

```bash
curl http://127.0.0.1:49122/api/v1/status
```

### 7. First Hit & Last Hit Collision Webhooks
Yeet features an intelligent **barrage settling engine** that triggers outbound HTTP requests to external software (such as VTube Studio, VNyan, Lumia Stream, Streamer.bot, or smart lights):
- **First Hit URL:** Fired **immediately** upon the very first impact of a throw or barrage (e.g., trigger a shocked/hurt expression or scream sound).
- **Barrage Debounce:** Intermediate impacts occurring while items are continuously pelting the target will *not* flood your external webhooks.
- **Last Hit URL:** Fired once the barrage settles and no new collisions occur for the configured **Settling Delay** (default: `2.0` seconds). Perfect for restoring a neutral VTuber expression, turning studio lights back to normal, or reporting the final count of hits!

#### URL Template Placeholders
Both GET and POST URLs support dynamic string interpolation:
- `{target}`: Target name (URL encoded, e.g. `VTuber+Head`)
- `{item}`: Item name that made the impact (e.g. `Beach+Ball`)
- `{hits}`: Total number of collisions accumulated during this barrage
- `{event}`: `"first_hit"` or `"last_hit"`

#### Example Use Cases
- **VTube Studio Expression Switching:**
  - First Hit: `POST http://127.0.0.1:8001/vts/hotkey?id=Expression_Dizzy`
  - Last Hit: `POST http://127.0.0.1:8001/vts/hotkey?id=Expression_Neutral`
- **Streamer.bot / Home Assistant Lighting:**
  - First Hit: Flash lights red on first impact
  - Last Hit: Restore ambient lighting after barrage settles

#### Webhook API Endpoints
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
   - **URL:** `http://127.0.0.1:49122/overlay` (or click **Copy URL** in Yeet's header bar).
   - **Width:** `1920` (or your stream canvas width).
   - **Height:** `1080` (or your stream canvas height).
   - **Custom frame rate:** Checked, set to `60` FPS.
   - **Shutdown source when not visible:** **UNCHECKED** *(crucial to keep WebSocket alive)*.
   - **Refresh browser when scene becomes active:** **UNCHECKED**.
5. Click **OK**.
6. Switch to Yeet and click **Test Throw** in the header bar or Physics playground to see items hit your target!

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

# Compile and run test suite (validates desktop & metainfo files)
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
├── data/
│   ├── gay.geeks.Yeet.desktop.in       # FreeDesktop application entry
│   ├── gay.geeks.Yeet.metainfo.xml.in  # AppStream metainfo specification
│   └── icons/
│       ├── gay.geeks.Yeet.svg          # 128x128 GNOME HIG compliant application icon
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
│   ├── app.py                          # Adw.Application subclass
│   ├── config.py                       # ~/.config/yeet/config.json persistence
│   ├── models.py                       # Target, Item, Physics data structures
│   ├── server.py                       # aiohttp REST API & WebSocket daemon
│   └── ui/
│       ├── __init__.py
│       ├── window.py                   # AdwApplicationWindow with ToastOverlay & ViewStack
│       ├── mapper_canvas.py            # Interactive GTK4/Cairo normalized coordinate mapper
│       ├── target_view.py              # Collision boundary setup & handles
│       ├── items_view.py               # Item inventory & audio controls
│       ├── physics_view.py             # Spawns, gravity, and test throw playground
│       └── server_view.py              # Daemon status, URL copy, & REST API guide
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
