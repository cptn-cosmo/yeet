/**
 * Yeet - OBS HTML5 Physics Overlay Engine
 * App ID: gay.geeks.Yeet
 * 
 * Powered by Matter.js and Web Audio API
 */

(function () {
  'use strict';

  // --- Global State ---
  let canvas, ctx;
  let engine, world;
  let ws = null;
  let wsReconnectTimer = null;
  let width = window.innerWidth;
  let height = window.innerHeight;

  // Configuration (received from server)
  let config = {
    targets: [],
    items: {},
    physics: {
      gravity: [0.0, 1.0],
      default_force: 1.0,
      sound_debounce_ms: 50,
      max_active_items: 120,
      debug_boundaries: false
    }
  };

  // Image & Audio Caches
  const imageCache = new Map();
  const audioBufferCache = new Map();

  // Active Throwables & Particles Tracking
  const activeThrowables = [];
  const activeParticles = [];
  let targetBodies = [];

  // Web Audio Context & Dynamic Limiter
  let audioCtx = null;
  let masterCompressor = null;
  let masterGain = null;
  let lastGlobalSoundTime = 0;

  function initAudio() {
    if (audioCtx) return;
    try {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioCtx = new AudioContextClass();

      // Master Dynamics Compressor: Prevents audio clipping during barrages
      masterCompressor = audioCtx.createDynamicsCompressor();
      masterCompressor.threshold.setValueAtTime(-14, audioCtx.currentTime);
      masterCompressor.knee.setValueAtTime(30, audioCtx.currentTime);
      masterCompressor.ratio.setValueAtTime(12, audioCtx.currentTime);
      masterCompressor.attack.setValueAtTime(0.003, audioCtx.currentTime);
      masterCompressor.release.setValueAtTime(0.25, audioCtx.currentTime);

      masterGain = audioCtx.createGain();
      masterGain.gain.setValueAtTime(0.85, audioCtx.currentTime);

      masterCompressor.connect(masterGain);
      masterGain.connect(audioCtx.destination);
    } catch (e) {
      console.warn('[Yeet Audio] Failed to initialize AudioContext:', e);
    }
  }

  // Ensure AudioContext is resumed on user gesture or first incoming event
  function resumeAudio() {
    if (audioCtx && audioCtx.state === 'suspended') {
      audioCtx.resume();
    }
  }

  // --- Sound Synthesizer & Audio Player ---
  function playCollisionSound(soundKey, volume = 0.8, pitchRandomness = 0.2) {
    if (!audioCtx) initAudio();
    resumeAudio();
    if (!audioCtx) return;

    const now = performance.now();
    const minDebounce = config.physics.sound_debounce_ms || 40;
    if (now - lastGlobalSoundTime < minDebounce) {
      return; // Debounce limiter
    }
    lastGlobalSoundTime = now;

    // Pitch variation multiplier (e.g. 0.85 to 1.15)
    const pitchFactor = 1.0 + (Math.random() - 0.5) * 2 * pitchRandomness;
    const clampedVolume = Math.max(0.0, Math.min(1.0, volume));

    // Check if custom audio URL
    if (soundKey && (soundKey.startsWith('http') || soundKey.startsWith('/') || soundKey.endsWith('.wav') || soundKey.endsWith('.mp3') || soundKey.endsWith('.ogg'))) {
      playSampleSound(soundKey, clampedVolume, pitchFactor);
    } else {
      synthesizeProceduralSound(soundKey || 'bonk', clampedVolume, pitchFactor);
    }
  }

  function playSampleSound(url, volume, pitchFactor) {
    if (audioBufferCache.has(url)) {
      const buffer = audioBufferCache.get(url);
      if (buffer) {
        const source = audioCtx.createBufferSource();
        source.buffer = buffer;
        source.playbackRate.value = pitchFactor;

        const gainNode = audioCtx.createGain();
        gainNode.gain.setValueAtTime(volume, audioCtx.currentTime);

        source.connect(gainNode);
        gainNode.connect(masterCompressor);
        source.start(0);
      }
      return;
    }

    // Fetch and decode sample
    fetch(url)
      .then(res => res.arrayBuffer())
      .then(arrayBuffer => audioCtx.decodeAudioData(arrayBuffer))
      .then(decodedBuffer => {
        audioBufferCache.set(url, decodedBuffer);
        playSampleSound(url, volume, pitchFactor);
      })
      .catch(err => {
        console.warn('[Yeet Audio] Failed to load sample:', url, err);
        // Fallback to procedural bonk
        synthesizeProceduralSound('bonk', volume, pitchFactor);
      });
  }

  function synthesizeProceduralSound(type, volume, pitchFactor) {
    const t0 = audioCtx.currentTime;
    const gainNode = audioCtx.createGain();
    gainNode.connect(masterCompressor);

    switch (type) {
      case 'squish': {
        // Juicy wet splat for tomatoes, water balloons, pies
        const osc = audioCtx.createOscillator();
        osc.type = 'triangle';
        const startFreq = 380 * pitchFactor;
        osc.frequency.setValueAtTime(startFreq, t0);
        osc.frequency.exponentialRampToValueAtTime(70 * pitchFactor, t0 + 0.12);

        gainNode.gain.setValueAtTime(volume * 0.9, t0);
        gainNode.gain.exponentialRampToValueAtTime(0.001, t0 + 0.14);

        // Noise burst overlay for wet impact texture
        const bufferSize = audioCtx.sampleRate * 0.08;
        const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
        const output = noiseBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
          output[i] = Math.random() * 2 - 1;
        }
        const whiteNoise = audioCtx.createBufferSource();
        whiteNoise.buffer = noiseBuffer;

        const noiseFilter = audioCtx.createBiquadFilter();
        noiseFilter.type = 'lowpass';
        noiseFilter.frequency.setValueAtTime(1200 * pitchFactor, t0);

        const noiseGain = audioCtx.createGain();
        noiseGain.gain.setValueAtTime(volume * 0.45, t0);
        noiseGain.gain.exponentialRampToValueAtTime(0.001, t0 + 0.08);

        whiteNoise.connect(noiseFilter);
        noiseFilter.connect(noiseGain);
        noiseGain.connect(masterCompressor);

        osc.connect(gainNode);
        osc.start(t0);
        osc.stop(t0 + 0.15);
        whiteNoise.start(t0);
        whiteNoise.stop(t0 + 0.09);
        break;
      }

      case 'thud': {
        // Heavy dull punch for bricks, anvils, weights
        const osc = audioCtx.createOscillator();
        osc.type = 'sine';
        const baseFreq = 160 * pitchFactor;
        osc.frequency.setValueAtTime(baseFreq, t0);
        osc.frequency.exponentialRampToValueAtTime(35 * pitchFactor, t0 + 0.18);

        gainNode.gain.setValueAtTime(volume * 1.0, t0);
        gainNode.gain.exponentialRampToValueAtTime(0.001, t0 + 0.2);

        osc.connect(gainNode);
        osc.start(t0);
        osc.stop(t0 + 0.22);
        break;
      }

      case 'pop': {
        // Crisp bubble pop
        const osc = audioCtx.createOscillator();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(650 * pitchFactor, t0);
        osc.frequency.exponentialRampToValueAtTime(1100 * pitchFactor, t0 + 0.03);
        osc.frequency.exponentialRampToValueAtTime(150 * pitchFactor, t0 + 0.08);

        gainNode.gain.setValueAtTime(volume * 0.75, t0);
        gainNode.gain.exponentialRampToValueAtTime(0.001, t0 + 0.09);

        osc.connect(gainNode);
        osc.start(t0);
        osc.stop(t0 + 0.1);
        break;
      }

      case 'clang': {
        // Metallic resonant strike
        const osc1 = audioCtx.createOscillator();
        const osc2 = audioCtx.createOscillator();
        osc1.type = 'sawtooth';
        osc2.type = 'square';
        osc1.frequency.setValueAtTime(820 * pitchFactor, t0);
        osc2.frequency.setValueAtTime(1240 * pitchFactor, t0);

        gainNode.gain.setValueAtTime(volume * 0.6, t0);
        gainNode.gain.exponentialRampToValueAtTime(0.001, t0 + 0.3);

        const filter = audioCtx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(1000 * pitchFactor, t0);
        filter.Q.setValueAtTime(3.0, t0);

        osc1.connect(filter);
        osc2.connect(filter);
        filter.connect(gainNode);

        osc1.start(t0);
        osc2.start(t0);
        osc1.stop(t0 + 0.32);
        osc2.stop(t0 + 0.32);
        break;
      }

      case 'bonk':
      default: {
        // Cheerful cartoon bonk
        const osc = audioCtx.createOscillator();
        osc.type = 'triangle';
        const startFreq = 480 * pitchFactor;
        osc.frequency.setValueAtTime(startFreq, t0);
        osc.frequency.exponentialRampToValueAtTime(180 * pitchFactor, t0 + 0.1);

        gainNode.gain.setValueAtTime(volume * 0.85, t0);
        gainNode.gain.exponentialRampToValueAtTime(0.001, t0 + 0.12);

        osc.connect(gainNode);
        osc.start(t0);
        osc.stop(t0 + 0.13);
        break;
      }
    }
  }

  // --- Image Loader & Cache ---
  function getCachedImage(src) {
    if (!src) return null;
    if (imageCache.has(src)) {
      return imageCache.get(src);
    }
    const img = new Image();
    img.src = src;
    imageCache.set(src, img);
    return img;
  }

  // Preload items from config
  function preloadAssets() {
    if (!config.items) return;
    Object.values(config.items).forEach(item => {
      if (item.image_url) getCachedImage(item.image_url);
    });
  }

  // --- Physics Simulation (Matter.js) ---
  function initPhysics() {
    const Engine = Matter.Engine;
    const World = Matter.World;
    const Events = Matter.Events;

    engine = Engine.create({
      enableSleeping: false
    });
    world = engine.world;

    // Apply configured world gravity
    updateGravity();

    // Collision Detection Listener
    Events.on(engine, 'collisionStart', function (event) {
      const pairs = event.pairs;
      for (let i = 0; i < pairs.length; i++) {
        const pair = pairs[i];
        let targetBody = null;
        let throwableBody = null;

        const bodyA = pair.bodyA.parent || pair.bodyA;
        const bodyB = pair.bodyB.parent || pair.bodyB;

        if (bodyA.label === 'target' && bodyB.label === 'throwable') {
          targetBody = bodyA;
          throwableBody = bodyB;
        } else if (bodyB.label === 'target' && bodyA.label === 'throwable') {
          targetBody = bodyB;
          throwableBody = bodyA;
        } else if (pair.bodyA.label === 'target' && pair.bodyB.label === 'throwable') {
          targetBody = pair.bodyA;
          throwableBody = pair.bodyB;
        } else if (pair.bodyB.label === 'target' && pair.bodyA.label === 'throwable') {
          targetBody = pair.bodyB;
          throwableBody = pair.bodyA;
        }

        if (targetBody && throwableBody) {
          const data = throwableBody.yeetData || (throwableBody.parent && throwableBody.parent.yeetData);
          if (data && data.item) {
            const now = performance.now();
            if (now - (data.lastHitTime || 0) > 60) {
              data.lastHitTime = now;
              data.hitCount = (data.hitCount || 0) + 1;

              // Trigger collision audio effect
              playCollisionSound(
                data.item.sound_effect,
                data.item.sound_volume ?? 0.8,
                data.item.pitch_randomness ?? 0.2
              );

              // Trigger visual impact burst
              spawnImpactBurst(throwableBody.position.x, throwableBody.position.y);

              // Target metadata
              const yeetTarget = targetBody.yeetTarget ||
                                 (targetBody.parent && targetBody.parent.yeetTarget) ||
                                 (config.targets && config.targets[0]);

              // Notify daemon server via WebSocket
              if (ws && ws.readyState === WebSocket.OPEN) {
                try {
                  ws.send(JSON.stringify({
                    type: 'collision_event',
                    target_id: yeetTarget ? yeetTarget.id : 'target',
                    target_name: yeetTarget ? yeetTarget.name : 'Target',
                    item_id: data.item.id,
                    item_name: data.item.name,
                    timestamp: Date.now()
                  }));
                } catch (e) {
                  console.error('[Yeet Overlay] Error sending collision_event:', e);
                }
              }
            }
          }
        }
      }
    });

    // Rebuild static target bodies
    rebuildTargets();
  }

  function updateGravity() {
    if (!engine) return;
    const grav = config.physics.gravity || [0.0, 1.0];
    engine.gravity.x = grav[0];
    engine.gravity.y = grav[1];
    engine.gravity.scale = 0.001;
  }

  // Rebuild static targets from normalized coordinates (0.0 to 1.0)
  function rebuildTargets() {
    if (!world) return;
    const World = Matter.World;
    const Bodies = Matter.Bodies;
    const Body = Matter.Body;

    // Remove existing target bodies
    targetBodies.forEach(b => World.remove(world, b));
    targetBodies = [];

    const targets = config.targets || [];
    targets.forEach(tgt => {
      let body = null;
      const bounciness = tgt.bounciness ?? 0.6;
      const friction = tgt.friction ?? 0.1;

      switch (tgt.type) {
        case 'box': {
          const cx = (tgt.x ?? 0.5) * width;
          const cy = (tgt.y ?? 0.5) * height;
          const w = (tgt.width ?? 0.2) * width;
          const h = (tgt.height ?? 0.3) * height;
          const angle = ((tgt.rotation ?? 0) * Math.PI) / 180;

          body = Bodies.rectangle(cx, cy, w, h, {
            isStatic: true,
            angle: angle,
            restitution: bounciness,
            friction: friction,
            label: 'target'
          });
          break;
        }

        case 'circle': {
          const cx = (tgt.x ?? 0.5) * width;
          const cy = (tgt.y ?? 0.5) * height;
          const r = (tgt.radius ?? 0.1) * Math.min(width, height);

          body = Bodies.circle(cx, cy, r, {
            isStatic: true,
            restitution: bounciness,
            friction: friction,
            label: 'target'
          });
          break;
        }

        case 'capsule': {
          // VTuber Pill / Capsule (torso & head)
          const cx = (tgt.x ?? 0.5) * width;
          const cy = (tgt.y ?? 0.5) * height;
          const w = (tgt.width ?? 0.18) * width;
          const h = (tgt.height ?? 0.35) * height;
          const radius = Math.min(w, h) / 2;

          // Chamfered / rounded rectangle creates an ideal pill collider
          body = Bodies.rectangle(cx, cy, w, h, {
            isStatic: true,
            chamfer: { radius: radius },
            restitution: bounciness,
            friction: friction,
            label: 'target'
          });
          break;
        }

        case 'polygon': {
          const points = tgt.points || [];
          if (points.length >= 3) {
            const scaledVertices = points.map(pt => ({
              x: pt[0] * width,
              y: pt[1] * height
            }));
            
            // Calculate center of vertices
            let sumX = 0, sumY = 0;
            scaledVertices.forEach(p => { sumX += p.x; sumY += p.y; });
            const cx = sumX / scaledVertices.length;
            const cy = sumY / scaledVertices.length;

            body = Bodies.fromVertices(cx, cy, [scaledVertices], {
              isStatic: true,
              restitution: bounciness,
              friction: friction,
              label: 'target'
            });
          }
          break;
        }
      }

      if (body) {
        body.yeetTarget = tgt;
        World.add(world, body);
        targetBodies.push(body);
      }
    });
  }

  // --- Spawning System ---
  function getPrimaryTargetCenter() {
    const targets = config.targets || [];
    if (targets.length > 0) {
      const t = targets[0];
      return {
        x: (t.x ?? 0.5) * width,
        y: (t.y ?? 0.5) * height
      };
    }
    return { x: width * 0.5, y: height * 0.5 };
  }

  function spawnItem(itemData, spawnDirection, forceMultiplier = 1.0, spreadAngle = 15.0) {
    if (!world || !engine) return;
    const Bodies = Matter.Bodies;
    const Body = Matter.Body;
    const World = Matter.World;

    // Enforce max active item limit
    const maxItems = config.physics.max_active_items || 120;
    while (activeThrowables.length >= maxItems) {
      const oldest = activeThrowables.shift();
      World.remove(world, oldest);
    }

    const targetPos = getPrimaryTargetCenter();
    let spawnX = 0;
    let spawnY = 0;
    let baseAngle = 0;
    let baseSpeed = 22.0 * (forceMultiplier || 1.0);

    const gravY = (config.physics && config.physics.gravity) ? (config.physics.gravity[1] ?? 1.0) : 1.0;
    const gravX = (config.physics && config.physics.gravity) ? (config.physics.gravity[0] ?? 0.0) : 0.0;
    const itemGrav = itemData.gravity_scale ?? 1.0;
    // Effective acceleration per frame in Matter.js (engine.gravity.scale = 0.001)
    const effAy = 0.24 * gravY * itemGrav;
    const effAx = 0.24 * gravX * itemGrav;

    const dir = (spawnDirection || 'random').toLowerCase();
    let chosenDir = dir;
    if (dir === 'random') {
      const options = ['left', 'right', 'top', 'bottom', 'aimed'];
      chosenDir = options[Math.floor(Math.random() * options.length)];
    }

    let isBallistic = false;

    switch (chosenDir) {
      case 'left':
        spawnX = -50;
        spawnY = targetPos.y + (Math.random() - 0.5) * (height * 0.25);
        isBallistic = true;
        break;

      case 'right':
        spawnX = width + 50;
        spawnY = targetPos.y + (Math.random() - 0.5) * (height * 0.25);
        isBallistic = true;
        break;

      case 'top':
        spawnX = targetPos.x + (Math.random() - 0.5) * (width * 0.3);
        spawnY = -50;
        isBallistic = true;
        break;

      case 'bottom':
        spawnX = targetPos.x + (Math.random() - 0.5) * (width * 0.3);
        spawnY = height + 50;
        isBallistic = true;
        break;

      case 'aimed': {
        const edge = Math.floor(Math.random() * 4);
        if (edge === 0) { spawnX = -50; spawnY = Math.random() * height; }
        else if (edge === 1) { spawnX = width + 50; spawnY = Math.random() * height; }
        else if (edge === 2) { spawnX = Math.random() * width; spawnY = -50; }
        else { spawnX = Math.random() * width; spawnY = height + 50; }
        isBallistic = true;
        break;
      }

      case 'rain': {
        const targetW = (config.targets && config.targets[0] && config.targets[0].width)
          ? config.targets[0].width * width
          : (width * 0.2);
        spawnX = targetPos.x + (Math.random() - 0.5) * (targetW * 1.2);
        spawnY = -40;
        baseAngle = Math.PI / 2; // Directly downward
        baseSpeed = 12.0 * (forceMultiplier || 1.0);
        break;
      }

      case 'spray': {
        const pt = config.physics.spawn_point || [0.0, 0.5];
        spawnX = pt[0] * width;
        spawnY = pt[1] * height;
        baseAngle = ((config.physics.spray_angle ?? 0) * Math.PI) / 180;
        break;
      }
    }

    if (isBallistic) {
      const dx = targetPos.x - spawnX;
      const dy = targetPos.y - spawnY;
      const dist = Math.hypot(dx, dy);
      const estTime = Math.max(1, dist / baseSpeed);
      const aimX = targetPos.x - 0.5 * effAx * estTime * estTime;
      const aimY = targetPos.y - 0.5 * effAy * estTime * estTime;
      baseAngle = Math.atan2(aimY - spawnY, aimX - spawnX);
    }

    // Apply angular variance (spread)
    const spreadRad = ((spreadAngle ?? 15.0) * Math.PI) / 180;
    const finalAngle = baseAngle + (Math.random() - 0.5) * spreadRad;

    const vx = Math.cos(finalAngle) * baseSpeed;
    const vy = Math.sin(finalAngle) * baseSpeed;

    // Item physical dimensions
    const scale = itemData.scale ?? 0.08;
    const radius = Math.max(12, (scale * Math.min(width, height)) / 2);
    const mass = itemData.mass ?? 1.0;
    const bounciness = itemData.bounciness ?? 0.65;
    const gravScale = itemData.gravity_scale ?? 1.0;

    // Create throwable physics body
    const body = Bodies.circle(spawnX, spawnY, radius, {
      restitution: bounciness,
      friction: 0.1,
      frictionAir: 0.005,
      density: 0.001 * mass,
      label: 'throwable'
    });

    Body.setVelocity(body, { x: vx, y: vy });

    // Initial angular velocity (spin)
    const spinRate = (itemData.rotational_speed ?? 1.0) * (Math.random() - 0.5) * 0.35;
    Body.setAngularVelocity(body, spinRate);

    // Yeet custom body metadata
    body.yeetData = {
      item: itemData,
      spawnTime: performance.now(),
      lifetimeMs: (itemData.lifetime ?? 8.0) * 1000,
      radius: radius,
      scale: scale,
      gravityScale: gravScale,
      image: getCachedImage(itemData.image_url)
    };

    World.add(world, body);
    activeThrowables.push(body);
  }

  function clearAllItems() {
    if (!world) return;
    const World = Matter.World;
    activeThrowables.forEach(b => World.remove(world, b));
    activeThrowables.length = 0;
  }

  function spawnImpactBurst(x, y) {
    const colors = ['#f6d32d', '#ff7800', '#e01b24', '#ffffff', '#62a0ea'];
    const count = 12;
    for (let i = 0; i < count; i++) {
      const angle = (Math.PI * 2 * i) / count + (Math.random() - 0.5) * 0.5;
      const speed = 2.5 + Math.random() * 4.5;
      activeParticles.push({
        x: x,
        y: y,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        size: 2.5 + Math.random() * 3.5,
        alpha: 1.0,
        color: colors[Math.floor(Math.random() * colors.length)]
      });
    }
  }

  // --- Rendering Loop ---
  function render() {
    requestAnimationFrame(render);

    if (!engine || !ctx) return;

    // Step physics engine
    Matter.Engine.update(engine, 1000 / 60);

    ctx.clearRect(0, 0, width, height);

    const now = performance.now();

    // 1. Draw Target Boundaries (if debug mode enabled)
    if (config.physics.debug_boundaries) {
      ctx.save();
      targetBodies.forEach(b => {
        ctx.strokeStyle = '#3584e4';
        ctx.fillStyle = 'rgba(53, 132, 228, 0.15)';
        ctx.lineWidth = 2;
        ctx.setLineDash([6, 4]);

        ctx.beginPath();
        const verts = b.vertices;
        if (verts && verts.length > 0) {
          ctx.moveTo(verts[0].x, verts[0].y);
          for (let i = 1; i < verts.length; i++) {
            ctx.lineTo(verts[i].x, verts[i].y);
          }
          ctx.closePath();
          ctx.fill();
          ctx.stroke();
        }

        // Target center reticle
        ctx.setLineDash([]);
        ctx.strokeStyle = '#62a0ea';
        ctx.fillStyle = '#62a0ea';
        ctx.beginPath();
        ctx.arc(b.position.x, b.position.y, 4, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    }

    // 2. Draw Active Throwables
    for (let i = activeThrowables.length - 1; i >= 0; i--) {
      const body = activeThrowables[i];
      const data = body.yeetData;
      const elapsed = now - data.spawnTime;

      // Handle lifetime expiration & smooth fade-out
      const remaining = data.lifetimeMs - elapsed;
      if (remaining <= 0) {
        Matter.World.remove(world, body);
        activeThrowables.splice(i, 1);
        continue;
      }

      // Smooth 1-second alpha fade-out
      let alpha = 1.0;
      if (remaining < 1000) {
        alpha = Math.max(0, remaining / 1000);
      }

      // Apply custom gravity scale if different from world
      if (data.gravityScale !== 1.0) {
        const extraGravY = (data.gravityScale - 1.0) * 0.001 * body.mass;
        Matter.Body.applyForce(body, body.position, { x: 0, y: extraGravY });
      }

      ctx.save();
      ctx.globalAlpha = alpha;
      ctx.translate(body.position.x, body.position.y);
      ctx.rotate(body.angle);

      const diameter = data.radius * 2;
      const img = data.image;

      if (img && img.complete && img.naturalWidth > 0) {
        ctx.drawImage(img, -data.radius, -data.radius, diameter, diameter);
      } else {
        // Fallback placeholder circle if image still loading
        ctx.fillStyle = '#e01b24';
        ctx.beginPath();
        ctx.arc(0, 0, data.radius, 0, Math.PI * 2);
        ctx.fill();
      }

      ctx.restore();
    }

    // 3. Draw Impact Burst Particles
    for (let i = activeParticles.length - 1; i >= 0; i--) {
      const p = activeParticles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vx *= 0.93;
      p.vy *= 0.93;
      p.alpha -= 0.035;

      if (p.alpha <= 0) {
        activeParticles.splice(i, 1);
        continue;
      }

      ctx.save();
      ctx.globalAlpha = p.alpha;
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    }
  }

  // --- WebSocket Connection & Real-Time Sync ---
  function updateStatus(text, stateClass) {
    const el = document.getElementById('status-indicator');
    if (!el) return;
    el.textContent = text;
    el.className = 'visible ' + stateClass;

    if (stateClass === 'connected') {
      setTimeout(() => {
        el.className = 'connected'; // Fades out
      }, 2500);
    }
  }

  function connectWebSocket() {
    if (wsReconnectTimer) {
      clearTimeout(wsReconnectTimer);
      wsReconnectTimer = null;
    }

    const proto = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const host = window.location.host || '127.0.0.1:49122';
    const wsUrl = `${proto}//${host}/ws`;

    console.log('[Yeet Overlay] Connecting to WebSocket:', wsUrl);
    updateStatus('Connecting...', 'disconnected');

    try {
      ws = new WebSocket(wsUrl);

      ws.onopen = function () {
        console.log('[Yeet Overlay] WebSocket Connected');
        updateStatus('Yeet Connected', 'connected');
      };

      ws.onmessage = function (event) {
        try {
          const msg = JSON.parse(event.data);
          handleWebSocketMessage(msg);
        } catch (e) {
          console.error('[Yeet Overlay] Error parsing message:', e);
        }
      };

      ws.onclose = function () {
        console.warn('[Yeet Overlay] WebSocket Disconnected. Retrying in 2s...');
        updateStatus('Disconnected', 'disconnected');
        ws = null;
        wsReconnectTimer = setTimeout(connectWebSocket, 2000);
      };

      ws.onerror = function (err) {
        console.error('[Yeet Overlay] WebSocket Error:', err);
        ws.close();
      };
    } catch (e) {
      console.error('[Yeet Overlay] WebSocket Exception:', e);
      wsReconnectTimer = setTimeout(connectWebSocket, 2000);
    }
  }

  function handleWebSocketMessage(msg) {
    switch (msg.type) {
      case 'init':
      case 'config_update':
        if (msg.config) {
          config = msg.config;
          updateGravity();
          rebuildTargets();
          preloadAssets();
        }
        break;

      case 'targets_updated':
        if (msg.targets) {
          config.targets = msg.targets;
          rebuildTargets();
        }
        break;

      case 'throw': {
        const item = (typeof msg.item === 'object' && msg.item !== null ? msg.item : null) ||
                     msg.item_data ||
                     (config.items && config.items[msg.item]) ||
                     (config.items && Object.values(config.items)[0]);
        if (!item) {
          console.warn('[Yeet Overlay] Unknown item for throw:', msg.item);
          return;
        }

        const count = Math.max(1, Math.min(50, msg.amount || 1));
        const direction = msg.spawn_direction || config.physics.default_spawn_direction || 'random';
        const force = msg.force ?? config.physics.default_force ?? 1.0;
        const spread = msg.spread ?? config.physics.default_spread ?? 15.0;

        for (let i = 0; i < count; i++) {
          // Slight staggered spawn delay for barrages
          setTimeout(() => {
            spawnItem(item, direction, force, spread);
          }, i * 35);
        }
        break;
      }

      case 'collision': {
        // Direct collision event triggered via REST API (e.g. GET /api/v1/collision)
        let targetBody = null;
        if (msg.target_id) {
          targetBody = targetBodies.find(b => b.yeetTarget && (
            b.yeetTarget.id === msg.target_id ||
            (b.yeetTarget.name && b.yeetTarget.name.toLowerCase() === msg.target_id.toLowerCase())
          ));
        }
        if (!targetBody && targetBodies.length > 0) {
          targetBody = targetBodies[0];
        }

        const sound = msg.sound || (msg.item_data && msg.item_data.sound_effect) || 'bonk';
        const volume = msg.volume ?? (msg.item_data && msg.item_data.sound_volume) ?? 0.85;
        const pitchRand = msg.pitch_randomness ?? (msg.item_data && msg.item_data.pitch_randomness) ?? 0.25;

        playCollisionSound(sound, volume, pitchRand);

        if (targetBody) {
          spawnImpactBurst(targetBody.position.x, targetBody.position.y);
        }
        break;
      }

      case 'clear':
        clearAllItems();
        break;

      default:
        console.log('[Yeet Overlay] Unhandled message:', msg);
        break;
    }
  }

  // --- Resize & Initialization ---
  function onResize() {
    width = window.innerWidth;
    height = window.innerHeight;
    if (canvas) {
      canvas.width = width;
      canvas.height = height;
    }
    rebuildTargets();
  }

  function init() {
    canvas = document.getElementById('overlay-canvas');
    ctx = canvas.getContext('2d');

    onResize();
    window.addEventListener('resize', onResize);
    window.addEventListener('click', resumeAudio);
    window.addEventListener('keydown', resumeAudio);

    initAudio();
    initPhysics();
    connectWebSocket();
    requestAnimationFrame(render);
  }

  // Auto-run on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
