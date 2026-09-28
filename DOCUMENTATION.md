# Yeet — Comprehensive System Documentation & API Reference

> **App ID:** `gay.geeks.Yeet`  
> **Target Platform:** Linux (Pure Wayland, Qt6 / KDE 6 HIG)  
> **License:** GNU General Public License v3.0 or later (`GPL-3.0-or-later`), Documentation CC0-1.0

---

## Table of Contents

1. [Introduction & Architecture](#1-introduction--architecture)
2. [OBS Studio Integration](#2-obs-studio-integration)
3. [Throwable Items & Groups Reference](#3-throwable-items--groups-reference)
   - [Complete Preset Items Catalog](#complete-preset-items-catalog)
   - [Item Groups & Thematic Categorization](#item-groups--thematic-categorization)
   - [Item Physical & Audio Attributes](#item-physical--audio-attributes)
   - [Adding Custom Items & Groups](#adding-custom-items--groups)
4. [Collision Targets & Boundary Shapes](#4-collision-targets--boundary-shapes)
   - [Target Shape Geometries](#target-shape-geometries)
   - [Normalized Relative Coordinates](#normalized-relative-coordinates)
   - [Interactive Qt6 Coordinate Mapper](#interactive-qt6-coordinate-mapper)
5. [Physics Engine & Trajectories](#5-physics-engine--trajectories)
   - [Spawn Trajectories](#spawn-trajectories)
   - [Ballistics & Gravity Compensation](#ballistics--gravity-compensation)
   - [Matter.js Physics Parameters](#matterjs-physics-parameters)
6. [Web Audio Synthesis Engine](#6-web-audio-synthesis-engine)
   - [Procedural Audio Presets](#procedural-audio-presets)
   - [Custom Sound Samples](#custom-sound-samples)
   - [Audio Limiter & Debounce System](#audio-limiter--debounce-system)
7. [Local REST API Reference](#7-local-rest-api-reference)
   - [Triggering Throws (`/api/v1/throw`)](#1-triggering-throws-post--get-apiv1throw)
   - [Random Mix, Group Filters & Exclusions](#2-random-mix-group-filtering--exclusions)
   - [Direct Collision Trigger (`/api/v1/collision`)](#3-direct-collision-trigger-get--post-apiv1collision)
   - [Collision Statistics & Counters (`/api/v1/collisions`)](#4-collision-statistics--counters-get-apiv1collisions)
   - [Reset Collision Stats (`/api/v1/collisions/reset`)](#5-reset-collision-statistics-post--get-apiv1collisionsreset)
   - [List Throwable Items (`/api/v1/items`)](#6-list-throwable-items-get-apiv1items)
   - [Manage Targets (`/api/v1/targets`)](#7-manage-targets-get--post-apiv1targets)
   - [Clear Active Projectiles (`/api/v1/clear`)](#8-clear-active-projectiles-post--get-apiv1clear)
   - [Daemon Health & Status (`/api/v1/status`)](#9-daemon-health--status-get-apiv1status)
   - [Client Config Payload (`/api/v1/config`)](#10-client-config-payload-get-apiv1config)
   - [Webhook Configuration & Testing (`/api/v1/webhooks`)](#11-webhook-configuration--testing-get--post-apiv1webhooks)
8. [Collision Webhooks & Barrage Engine](#8-collision-webhooks--barrage-engine)
   - [First Hit vs. Last Hit Lifecycle](#first-hit-vs-last-hit-lifecycle)
   - [Dynamic URL Interpolation Placeholders](#dynamic-url-interpolation-placeholders)
   - [External Software Integration Recipes (VTube Studio, VNyan, Smart Lights)](#external-software-integration-recipes)
9. [WebSocket Protocol Reference (`/ws`)](#9-websocket-protocol-reference-ws)
10. [Stream Automation & Chat Bot Recipes](#10-stream-automation--chat-bot-recipes)
    - [Streamer.bot](#streamerbot)
    - [SAMMI & MixItUp](#sammi--mixitup)
    - [Twitch Channel Points](#twitch-channel-points)
    - [Nightbot / Cloudbot Chat Commands](#nightbot--cloudbot-chat-commands)
11. [Configuration File Reference (`config.json`)](#11-configuration-file-reference-configjson)
12. [Compilation & Installation](#12-compilation--installation)

---

## 1. Introduction & Architecture

**Yeet** is a Wayland-native, KDE 6 HIG-compliant interactive stream throwing system and 2D physics overlay designed for OBS Studio. It serves as an open-source, native Linux alternative to Twitch Integrated Throwing System (T.I.T.S.).

### High-Level Architecture

```
┌────────────────────────────────────────────────────────┐
│                   Yeet Desktop App                     │
│               (Qt6 / PySide6 / KDE 6)                  │
│  - Interactive Coordinate Mapper (QPainter)            │
│  - Throwable Item & Audio Preset Manager               │
│  - Physics & World Settings Playground                 │
│  - Webhook & Barrage Automation Setup                  │
└──────────────────────────┬─────────────────────────────┘
                           │ Config updates & sync
                           ▼
┌────────────────────────────────────────────────────────┐
│            Embedded Async Local Daemon                 │
│             (Python aiohttp on 127.0.0.1:49122)        │
│  - REST API (POST/GET /api/v1/throw, collision, etc.)  │
│  - WebSocket Server (/ws)                              │
│  - Barrage Tracker & Outbound Webhook Dispatcher       │
│  - Static Asset & HTML5 Overlay Server                 │
└──────────────────────────┬─────────────────────────────┘
                           │ Real-time WS Events & Assets
                           ▼
┌────────────────────────────────────────────────────────┐
│             OBS Studio Browser Source                  │
│             (HTML5 / Canvas / Matter.js)               │
│  - 2D Rigid-Body Physics Engine (Matter.js)            │
│  - Resolution-Independent Normalized Geometry          │
│  - Web Audio API Procedural Synthesizer & Limiter      │
│  - Particle Bursts & Canvas Render Loop                │
└────────────────────────────────────────────────────────┘
```

---

## 2. OBS Studio Integration

The visual and physical rendering of Yeet runs as an HTML5 transparent canvas inside OBS Studio via an OBS Browser Source.

### Step-by-Step Setup

1. Launch the **Yeet** desktop application.
2. In the navigation sidebar, switch to the **Server & OBS** tab.
3. Click **Copy URL** (default: `http://127.0.0.1:49122/overlay`).
4. In **OBS Studio**, navigate to your streaming scene.
5. In the **Sources** dock, click **+** and choose **Browser**.
6. Set a name (e.g. `Yeet Overlay`) and configure the properties:
   - **URL:** `http://127.0.0.1:49122/overlay`
   - **Width:** `1920` (or matching your canvas base resolution width).
   - **Height:** `1080` (or matching your canvas base resolution height).
   - **Custom frame rate:** Checked, set to `60` FPS.
   - **Control audio via OBS:** Optional (Overlay generates sound directly in the browser source).
   - **Shutdown source when not visible:** **UNCHECKED** *(Crucial: checking this disconnects the WebSocket when switching scenes)*.
   - **Refresh browser when scene becomes active:** **UNCHECKED**.
7. Click **OK**.
8. Return to Yeet and click **Test Throw** in the top toolbar to confirm projectiles spawn and impact your targets!

---

## 3. Throwable Items & Groups Reference

Yeet includes a rich inventory of built-in throwable projectiles. Each item possesses unique aerodynamic, restitution, mass, rotational, visual, and acoustic properties. Items are organized into **Groups** for batch filtering, themed redeems, and random mix throws.

### Complete Preset Items Catalog

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

### Item Groups & Thematic Categorization

Item groups allow streamers to organize projectiles into functional categories. Throws can target entire groups, combine multiple groups, or selectively exclude groups.

| Group Name | Included Preset Items | Suggested Use Cases & Stream Themes |
| :--- | :--- | :--- |
| `food` | `tomato`, `pie` | Slapstick food fights, cooking streams, chat pun punishments, comedy redeems |
| `construction` | `brick` | High-tier bits/donations, heavy boss attacks, sub raid barrages, maximum impact |
| `toys` | `rubber_duck` | Playful viewer greetings, follower milestones, cartoon bounce fun |
| `summer` | `beachball`, `water_balloon` | Pool party streams, beach themes, low-gravity floating barrages |
| `cute` | `heart` | Sub gifts, cheer love, appreciation redeems, cozy stream moments |
| `default` | *(Fallback group)* | Custom items created without an explicit group tag |

---

### Item Physical & Audio Attributes

Each projectile item is governed by the following parameters:

- **`id`** *(string)*: Unique identifier used in REST API calls (e.g. `brick`, `rubber_duck`).
- **`name`** *(string)*: Human-readable display label shown in logs, collision statistics, and GUI.
- **`group`** *(string)*: Category tag used for group filtering and exclusions (e.g. `summer`, `food`).
- **`image_url`** *(string)*: Relative or absolute URL served by Yeet (e.g. `/assets/items/beachball.svg`, or a local custom image). Supports PNG, WebP, GIF, and SVG formats.
- **`scale`** *(float, `0.02` – `0.35`)*: Normalized projectile size relative to stream canvas width. `0.08` represents 8% of canvas width.
- **`mass`** *(float, `0.1` – `10.0`)*: Physical mass in the Matter.js physics engine. Higher mass projectiles resist deflection upon impact and transfer heavy kinetic momentum.
- **`bounciness`** *(float, `0.0` – `1.0`)*: Kinetic restitution. `0.0` absorbs all velocity on impact (dead thud), whereas `0.92` produces dramatic trampoline-like ricochets.
- **`rotational_speed`** *(float, `0.0` – `5.0`)*: Torque multiplier applied at spawn time to produce spin during trajectory flight.
- **`gravity_scale`** *(float, `0.0` – `3.0`)*: Multiplier on world gravity. `1.0` equals normal Earth gravity; `< 1.0` produces floaty balloon-like motion; `> 1.0` makes heavy items plummet rapidly.
- **`lifetime`** *(float, `2.0` – `60.0` seconds)*: Duration before an item fades out and is purged from memory.
- **`sound_effect`** *(string)*: Procedural synthesizer preset (`squish`, `bonk`, `thud`, `pop`, `clang`) or custom URL/file path (`/assets/sounds/my_sound.wav`).
- **`sound_volume`** *(float, `0.0` – `1.0`)*: Impact playback volume multiplier.
- **`pitch_randomness`** *(float, `0.0` – `0.5`)*: Dynamic pitch variance applied on each impact to prevent acoustic fatigue.

---

### Adding Custom Items & Groups

You can add custom throwable items with your own graphics and sounds:

#### Via the Qt6 Desktop Application:
1. Open the **Items Inventory** tab.
2. Click **Add New Item…**.
3. Select an image file (SVG, PNG, WebP, or GIF).
4. Enter an **Item ID**, **Display Name**, and **Group Tag** (e.g. `spooky`, `pokemon`, `vip`).
5. Adjust mass, bounciness, gravity scale, and assign an impact sound.
6. Click **Save**. The item immediately syncs to OBS overlays and becomes available through the REST API!

#### Via Configuration File (`~/.config/yeet/config.json`):
```json
"items": {
  "anvil": {
    "id": "anvil",
    "name": "Heavy Iron Anvil",
    "image_url": "/assets/items/anvil.png",
    "group": "construction",
    "scale": 0.12,
    "mass": 5.0,
    "bounciness": 0.1,
    "rotational_speed": 0.4,
    "gravity_scale": 1.8,
    "lifetime": 8.0,
    "sound_effect": "clang",
    "sound_volume": 1.0,
    "pitch_randomness": 0.1
  }
}
```

---

## 4. Collision Targets & Boundary Shapes

Collision targets represent the physical obstacles in your OBS scene where thrown projectiles collide—such as your VTuber model's head and body, a webcam frame, a chat box, or stream props.

### Target Shape Geometries

1. **Capsule / Pill (`capsule`):**
   - Ideal for VTuber torsos, arms, and necks.
   - Defined by center `(x, y)`, `width`, `height`, and `rotation`.
2. **Circle / Ellipse (`circle`):**
   - Optimized for VTuber heads, mascots, badges, or circular webcam masks.
   - Defined by center `(x, y)`, `radius`, and `rotation`.
3. **Rectangle / Box (`box`):**
   - Perfect for rectangular webcams, chat boxes, game capture frames, or sponsor banners.
   - Defined by center `(x, y)`, `width`, `height`, and `rotation`.
4. **Custom Polygon Convex Hull (`polygon`):**
   - Designed for intricate avatar silhouettes, hats, wings, or asymmetrical props.
   - Double-click anywhere on the canvas to insert vertices; drag vertices to reshape; delete vertices via right-click or delete key.

### Normalized Relative Coordinates

All spatial coordinates in Yeet are **resolution-independent** and normalized between `0.0` and `1.0`:
- `(0.0, 0.0)` is the top-left corner of the stream canvas.
- `(0.5, 0.5)` is the exact center.
- `(1.0, 1.0)` is the bottom-right corner.

This guarantees that collision targets remain perfectly aligned whether your canvas is 1080p, 1440p, 4K, or vertical (9:16) for TikTok/Shorts!

### Interactive Qt6 Coordinate Mapper

The **Target Setup** tab features an interactive Qt6 canvas:
- **Move Target:** Click and drag inside any target to reposition.
- **Resize Target:** Drag corner handles to scale width and height.
- **Rotate Target:** Drag the top rotation handle to orient the target in 360 degrees.
- **Load Backdrop Image:** Click **Load Backdrop…** to load a screenshot of your stream layout or VTuber avatar directly onto the canvas for pixel-perfect collider alignment.

---

## 5. Physics Engine & Trajectories

Yeet embeds **Matter.js**, a 2D rigid-body physics engine executed inside the OBS browser source canvas.

### Spawn Trajectories

| Direction Key | Description & Behavior |
| :--- | :--- |
| `aimed` *(Default)* | Calculates an exact ballistic trajectory aimed directly at the primary target's center. Adjusts launch angle and force dynamically to compensate for world gravity and distance. |
| `random` | Randomly chooses an offscreen screen edge (left, right, or top) and launches toward the playfield. |
| `left` | Spawns along the left screen border with rightward velocity. |
| `right` | Spawns along the right screen border with leftward velocity. |
| `top` | Spawns above the canvas and launches downward. |
| `bottom` | Spawns below the canvas and launches upward into the playfield. |
| `rain` | Spawns across random horizontal positions above the top edge and drops with natural world gravity. |
| `spray` | Point-source cone spray originating from a fixed coordinate (`spawn_point`) at an adjustable angle (`spray_angle`). |

### Ballistics & Gravity Compensation

When `spawn_direction: "aimed"` is selected, Yeet solves the ballistic trajectory equation:
$$\theta = \arctan\left(\frac{v^2 \pm \sqrt{v^4 - g(g x^2 + 2 y v^2)}}{g x}\right)$$

This ensures that items with different masses and gravity scales (such as heavy bricks vs. floaty beach balls) hit the target center consistently.

---

## 6. Web Audio Synthesis Engine

Yeet features an embedded polyphonic Web Audio API sound engine that generates sound natively inside the OBS browser source.

### Procedural Audio Presets

| Sound Preset | Acoustic Characteristics | Implementation Model |
| :--- | :--- | :--- |
| `squish` | Wet, juicy splat | Fast exponential triangle wave downward frequency sweep ($380\,\text{Hz} \to 70\,\text{Hz}$) layered with low-pass filtered white noise burst. |
| `bonk` | Cartoon rubber comedy bonk | Triangle wave sweep ($480\,\text{Hz} \to 140\,\text{Hz}$) with mid-range resonance and snappy envelope. |
| `thud` | Deep, dull heavy punch | Low-frequency sine wave sweep ($160\,\text{Hz} \to 35\,\text{Hz}$) with high gain and rapid decay. |
| `pop` | Crisp, airy bubble pop | Upward chirped sine wave ($650\,\text{Hz} \to 1100\,\text{Hz}$) dropping to $150\,\text{Hz}$. |
| `clang` | Resonant metallic chime | Dual detuned sawtooth and square wave oscillators ($820\,\text{Hz} + 1240\,\text{Hz}$) feeding a high-Q bandpass filter. |

### Dynamic Limiter & Debounce System

To protect viewers' ears during massive 50-item barrages:
1. **Dynamic Compressor Node:** A master `DynamicsCompressorNode` (`threshold: -14dB`, `knee: 30`, `ratio: 12:1`, `attack: 0.003s`) limits sudden volume spikes and eliminates digital clipping.
2. **Sound Debounce Limiter:** Configurable `sound_debounce_ms` (default: `50ms`) sets a minimum interval between impact sounds so rapid simultaneous hits don't cause cacophony.
3. **Pitch Randomization:** Every collision dynamically varies pitch by $\pm \text{pitch\_randomness}$ to maintain acoustic variety.

---

## 7. Local REST API Reference

The local server listens on `http://127.0.0.1:49122` by default. All endpoints support **CORS** (`Access-Control-Allow-Origin: *`) for browser scripts and webhooks.

### 1. Triggering Throws (`POST` & `GET /api/v1/throw`)

Spawns one or more throwable projectiles. Accepts both JSON request bodies and URL query parameters.

- **URL:** `http://127.0.0.1:49122/api/v1/throw`
- **Methods:** `POST`, `GET`
- **Headers:** `Content-Type: application/json` *(for POST)*

#### Parameters:

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `item` | `string` | `"random"` | Item ID (`"brick"`, `"tomato"`, etc.), `"random"`, or `"random_mix"` / `"mix"`. |
| `items` | `string` / `list` | `null` | Candidate items for random mix: `"all"` or comma-separated list (`"tomato,pie,brick"`). |
| `group` / `item_group` | `string` / `list` | `null` | Filter pool by group name (`"summer"`, `"food"`, `"toys"`, `"construction"`, `"cute"`). |
| `item_exclude` / `group_exclude` / `exclude` | `string` / `list` | `null` | Exclude specific item IDs, names, or groups (e.g. `"winter,food"`). |
| `amount` | `integer` | `1` | Number of projectiles to spawn (`1` to `100`). |
| `spawn_direction` / `direction` | `string` | Configured | `"aimed"`, `"left"`, `"right"`, `"top"`, `"bottom"`, `"random"`, `"rain"`, `"spray"`. |
| `force` | `float` | `1.0` | Velocity multiplier (`0.1` to `5.0`). |
| `spread` | `float` | `15.0` | Launch angle spread in degrees. |

#### Example 1: Standard Single Item Throw (POST JSON)
```bash
curl -X POST http://127.0.0.1:49122/api/v1/throw \
  -H "Content-Type: application/json" \
  -d '{
    "item": "brick",
    "amount": 3,
    "spawn_direction": "aimed",
    "force": 1.2
  }'
```

#### Example 2: Chat Bot / Bookmarklet URL (GET Query String)
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=beachball&amount=5&spawn_direction=rain&force=1.5"
```

#### Response (Success `200 OK`):
```json
{
  "status": "ok",
  "message": "Spawned 3 items (Red Brick)",
  "mode": "single",
  "pool": ["brick"],
  "item": "brick",
  "items": ["brick", "brick", "brick"],
  "amount": 3,
  "spawn_direction": "aimed",
  "force": 1.2,
  "spread": 15.0
}
```

---

### 2. Random Mix, Group Filtering & Exclusions

In `random_mix` mode, each individual projectile in a barrage is selected independently at random from a resolved candidate pool.

#### Example 3: Throw 6 items from the `summer` group only
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&group=summer&amount=6"
```

#### Example 4: Throw all items EXCEPT the `construction` group (no bricks)
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&group_exclude=construction&amount=8"
```

#### Example 5: Throw all items excluding multiple groups (`food` and `construction`)
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=all&item_exclude=food,construction&amount=10"
```

#### Example 6: Custom candidate pool of specific items
```bash
curl "http://127.0.0.1:49122/api/v1/throw?item=random_mix&items=tomato,rubber_duck,heart&amount=5"
```

---

### 3. Direct Collision Trigger (`GET` & `POST /api/v1/collision`)

Simulates an **immediate impact** directly on a target collider without waiting for projectile flight time. Plays the collision sound with pitch variance, spawns an impact particle burst, and registers in collision statistics. Ideal for channel point redeems like `!slap` or `!bonk`.

- **URL:** `http://127.0.0.1:49122/api/v1/collision`
- **Parameters:**
  - `target` / `target_id`: Target name or ID (e.g. `"VTuber Head"`, `"target_vtuber_body"`). Defaults to primary target.
  - `item`: Item ID or name to simulate (e.g. `"pie"`, `"brick"`).
  - `sound`: Sound effect override (`"squish"`, `"bonk"`, `"thud"`, `"pop"`, `"clang"`).
  - `volume`: Playback volume multiplier (`0.0` to `1.0`).

```bash
# Direct slap with Cream Pie
curl "http://127.0.0.1:49122/api/v1/collision?target=VTuber+Head&item=pie&sound=squish"
```

#### Response:
```json
{
  "status": "ok",
  "message": "Collision triggered on VTuber Head with Cream Pie",
  "target": "target_vtuber_head",
  "target_name": "VTuber Head",
  "item": "pie",
  "item_name": "Cream Pie",
  "sound": "squish",
  "total_collisions": 42
}
```

---

### 4. Collision Statistics & Counters (`GET /api/v1/collisions`)

Returns cumulative collision counts, breakdowns by target and item, and recent collision logs. Ideal for stream leaderboard overlays or chat commands like `!hits`.

```bash
curl http://127.0.0.1:49122/api/v1/collisions
```

#### Response:
```json
{
  "status": "ok",
  "total_collisions": 128,
  "by_target": {
    "VTuber Head": 74,
    "VTuber Torso": 54
  },
  "by_item": {
    "tomato": 45,
    "brick": 30,
    "rubber_duck": 53
  },
  "recent": [
    {
      "id": 128,
      "target_id": "target_vtuber_head",
      "target_name": "VTuber Head",
      "item_id": "tomato",
      "item_name": "Ripe Tomato",
      "source": "physics",
      "timestamp": 1727518492.12
    }
  ]
}
```

---

### 5. Reset Collision Statistics (`POST` & `GET /api/v1/collisions/reset`)

Clears all collision counters and recent collision logs to zero.

```bash
curl -X POST http://127.0.0.1:49122/api/v1/collisions/reset
```

---

### 6. List Throwable Items (`GET /api/v1/items`)

Returns all configured items and their physical/audio parameters. Supports optional `?group=<name>` filtering.

```bash
# List all items
curl http://127.0.0.1:49122/api/v1/items

# List only summer items
curl "http://127.0.0.1:49122/api/v1/items?group=summer"
```

---

### 7. Manage Targets (`GET` & `POST /api/v1/targets`)

Retrieve or dynamically update the collision boundary target list.

```bash
# Retrieve targets
curl http://127.0.0.1:49122/api/v1/targets

# Update targets via POST JSON
curl -X POST http://127.0.0.1:49122/api/v1/targets \
  -H "Content-Type: application/json" \
  -d '{
    "targets": [
      {
        "id": "target_vtuber_head",
        "name": "VTuber Head",
        "type": "circle",
        "x": 0.5,
        "y": 0.3,
        "radius": 0.12,
        "bounciness": 0.75
      }
    ]
  }'
```

---

### 8. Clear Active Projectiles (`POST` & `GET /api/v1/clear`)

Immediately despawns all active rigid bodies from all connected OBS browser sources.

```bash
curl -X POST http://127.0.0.1:49122/api/v1/clear
```

---

### 9. Daemon Health & Status (`GET /api/v1/status`)

Returns daemon uptime, connected OBS overlay count, target count, and port.

```bash
curl http://127.0.0.1:49122/api/v1/status
```

#### Response:
```json
{
  "status": "running",
  "uptime_seconds": 3612.45,
  "connected_overlays": 1,
  "active_targets": 2,
  "total_items": 7,
  "total_collisions": 128,
  "host": "127.0.0.1",
  "port": 49122
}
```

---

### 10. Client Config Payload (`GET /api/v1/config`)

Returns full client configuration (targets, items inventory, and world physics settings).

```bash
curl http://127.0.0.1:49122/api/v1/config
```

---

### 11. Webhook Configuration & Testing (`GET` & `POST /api/v1/webhooks`)

Read or update outbound webhook settings, or fire a test webhook trigger.

```bash
# Read settings
curl http://127.0.0.1:49122/api/v1/webhooks

# Test First Hit trigger
curl "http://127.0.0.1:49122/api/v1/webhooks/test?event=first_hit"

# Test Last Hit trigger
curl "http://127.0.0.1:49122/api/v1/webhooks/test?event=last_hit"
```

---

## 8. Collision Webhooks & Barrage Engine

Yeet features an intelligent **barrage settling engine** that triggers external webhooks without spamming your network during heavy projectile barrages.

### First Hit vs. Last Hit Lifecycle

```
Projectile Thrown ──▶ Impact 1 (First Hit!) ──▶ Webhook: First Hit Dispatched
                            │
                      Impact 2 (Intermediate)
                            │   (Debounce active: no webhook spam)
                      Impact 3 (Intermediate)
                            │
                      Silence for Settling Delay (e.g. 2.0s)
                            │
                            ▼
                      Barrage Settled! ───────▶ Webhook: Last Hit Dispatched
```

- **First Hit URL:** Fired **immediately** upon the very first impact of a throw (e.g. switch VTuber avatar expression to `Shocked` or flash studio lights red).
- **Barrage Debounce:** Intermediate impacts occurring while items continue hitting the avatar will *not* flood external services.
- **Last Hit URL:** Fired once the barrage ends and no new collisions occur for the duration of the **Settling Delay** (default: `2.0` seconds). Perfect for restoring a neutral expression or ambient lighting.

### Dynamic URL Interpolation Placeholders

Both GET and POST URLs support dynamic string replacement:

- `{target}`: URL-encoded target name (e.g. `VTuber+Head`).
- `{item}`: URL-encoded item name (e.g. `Red+Brick`).
- `{hits}`: Total accumulated hits during this barrage (e.g. `7`).
- `{event}`: `"first_hit"` or `"last_hit"`.

### External Software Integration Recipes

#### 1. VTube Studio (Hotkey / Expression Switching)
Trigger hotkeys in VTube Studio via its local API:
- **First Hit URL (POST):**  
  `http://127.0.0.1:8001/vts/hotkey?id=Expression_Dizzy`
- **Last Hit URL (POST):**  
  `http://127.0.0.1:8001/vts/hotkey?id=Expression_Neutral`

#### 2. VNyan / Warudo (WebSockets / HTTP Triggers)
- **First Hit URL (GET):**  
  `http://127.0.0.1:8000/vnyan?trigger=hit&target={target}&item={item}`
- **Last Hit URL (GET):**  
  `http://127.0.0.1:8000/vnyan?trigger=hit_settled&hits={hits}`

#### 3. Lumia Stream / Home Assistant (RGB Smart Lights)
- **First Hit URL (GET):**  
  `http://127.0.0.1:39231/api/rgb?color=red&flash=true`
- **Last Hit URL (GET):**  
  `http://127.0.0.1:39231/api/rgb?color=purple&flash=false`

---

## 9. WebSocket Protocol Reference (`/ws`)

OBS Browser Sources connect to `ws://127.0.0.1:49122/ws`.

### Server-to-Client Messages

1. **`init`**: Sent immediately upon WebSocket connection. Contains full config payload.
2. **`throw`**: Instructs the overlay to instantiate and launch projectiles.
   ```json
   {
     "type": "throw",
     "mode": "single",
     "item": "brick",
     "item_data": { ... },
     "items": ["brick"],
     "amount": 1,
     "spawn_direction": "aimed",
     "force": 1.0,
     "spread": 15.0
   }
   ```
3. **`collision`**: Triggers immediate simulated impact and particle burst.
4. **`clear`**: Removes all active rigid bodies.
5. **`config_update`**: Real-time broadcast when physics parameters or items are edited in the GUI.
6. **`targets_updated`**: Real-time broadcast when target boundaries are resized or moved.

### Client-to-Server Messages

1. **`ping`**: Client heartbeat. Server replies with `{"type": "pong"}`.
2. **`collision_event`**: Fired by Matter.js upon genuine physical collision.
   ```json
   {
     "type": "collision_event",
     "target_id": "target_vtuber_head",
     "target_name": "VTuber Head",
     "item_id": "tomato",
     "item_name": "Ripe Tomato"
   }
   ```

---

## 10. Stream Automation & Chat Bot Recipes

### Streamer.bot

#### Triggering a Throw via Sub-Action
1. In Streamer.bot, add a Sub-Action: **Network** ➔ **Fetch URL**.
2. Set **URL**:  
   `http://127.0.0.1:49122/api/v1/throw?item=tomato&amount=3&spawn_direction=aimed`
3. Set **Method**: `GET`.
4. Trigger on Channel Point Redeems, Cheer bits, or Chat Commands (`!yeet`).

#### C# Execute Code Sub-Action
```csharp
using System;
using System.Net.Http;

public class CPHInline
{
    private static readonly HttpClient client = new HttpClient();

    public bool Execute()
    {
        string url = "http://127.0.0.1:49122/api/v1/throw?item=random_mix&group=summer&amount=5";
        client.GetAsync(url);
        return true;
    }
}
```

---

### SAMMI & MixItUp

- **Action:** Web Request / HTTP Request
- **Method:** `POST`
- **URL:** `http://127.0.0.1:49122/api/v1/throw`
- **Headers:** `Content-Type: application/json`
- **Body:**
  ```json
  {
    "item": "random_mix",
    "items": "all",
    "item_exclude": "construction",
    "amount": 4
  }
  ```

---

### Twitch Channel Points

Link custom channel rewards directly to throws:
- **"Tomato Throw" (100 pts):** `GET /api/v1/throw?item=tomato&amount=1&spawn_direction=aimed`
- **"Slap with Cream Pie" (250 pts):** `GET /api/v1/collision?target=VTuber+Head&item=pie&sound=squish`
- **"Brick Barrage" (1,000 pts):** `GET /api/v1/throw?item=brick&amount=5&spawn_direction=rain&force=1.5`
- **"Beach Party Barrage" (500 pts):** `GET /api/v1/throw?item=random_mix&group=summer&amount=6`

---

### Nightbot / Cloudbot Chat Commands

Add chat commands using `$(urlfetch)`:
```
!throw -> $(urlfetch http://127.0.0.1:49122/api/v1/throw?item=random&amount=2)
!slap  -> $(urlfetch http://127.0.0.1:49122/api/v1/collision?item=pie)
!hits  -> Total avatar hits: $(urlfetch http://127.0.0.1:49122/api/v1/collisions)
```

---

## 11. Configuration File Reference (`config.json`)

Yeet stores its settings in `~/.config/yeet/config.json`. Below is an annotated complete example:

```json
{
  "targets": [
    {
      "id": "target_vtuber_body",
      "name": "VTuber Torso",
      "type": "capsule",
      "x": 0.50,
      "y": 0.65,
      "width": 0.22,
      "height": 0.40,
      "radius": 0.1,
      "rotation": 0.0,
      "points": [],
      "bounciness": 0.6,
      "friction": 0.15
    },
    {
      "id": "target_vtuber_head",
      "name": "VTuber Head",
      "type": "circle",
      "x": 0.50,
      "y": 0.35,
      "width": 0.2,
      "height": 0.2,
      "radius": 0.12,
      "rotation": 0.0,
      "points": [],
      "bounciness": 0.75,
      "friction": 0.1
    }
  ],
  "items": {
    "tomato": {
      "id": "tomato",
      "name": "Ripe Tomato",
      "image_url": "/assets/items/tomato.svg",
      "group": "food",
      "scale": 0.08,
      "mass": 0.8,
      "bounciness": 0.4,
      "rotational_speed": 1.5,
      "gravity_scale": 1.0,
      "lifetime": 8.0,
      "sound_effect": "squish",
      "sound_volume": 0.9,
      "pitch_randomness": 0.2
    }
  },
  "physics": {
    "gravity": [0.0, 1.0],
    "default_spawn_direction": "aimed",
    "default_force": 1.0,
    "default_spread": 15.0,
    "spawn_point": [0.0, 0.5],
    "spray_angle": 0.0,
    "sound_debounce_ms": 50,
    "max_active_items": 120,
    "debug_boundaries": false
  },
  "server": {
    "host": "127.0.0.1",
    "port": 49122
  },
  "webhooks": {
    "enabled": false,
    "first_hit_url": "",
    "first_hit_method": "GET",
    "last_hit_url": "",
    "last_hit_method": "GET",
    "settling_delay": 2.0
  }
}
```

---

## 12. Compilation & Installation

### Arch Linux / AUR
```bash
makepkg -si
```

### Manual Build with Meson
```bash
meson setup build --prefix=/usr
meson compile -C build
meson test -C build
sudo meson install -C build
```

### Running from Source Directly
```bash
./bin/yeet
```
