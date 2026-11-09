"""
Yeet - Embedded HTTP REST & WebSocket Server
App ID: gay.geeks.Yeet
"""

import os
import time
import json
import random
import logging
import asyncio
import threading
import urllib.parse
from typing import Set, Dict, Any, Optional, Callable, List, Tuple
from collections import deque
import aiohttp
from aiohttp import web, WSMsgType

from .config import ConfigManager
from .models import ThrowableItem

logger = logging.getLogger("yeet.server")

class ServerDaemon:
    def __init__(self, config_manager: ConfigManager, base_dir: str = None, on_throw_event: Optional[Callable[[Dict[str, Any]], None]] = None, on_collision_event: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.config_manager = config_manager
        self.on_throw_event = on_throw_event
        self.on_collision_event = on_collision_event
        self.start_time = time.time()
        self.connected_ws: Set[web.WebSocketResponse] = set()

        # Collision Event Statistics & History
        self.total_collisions: int = 0
        self.collisions_by_target: Dict[str, int] = {}
        self.collisions_by_item: Dict[str, int] = {}
        self.recent_collisions: deque = deque(maxlen=50)

        # Outbound Webhook & Barrage First/Last Hit State
        self._barrage_active: bool = False
        self._barrage_hits: int = 0
        self._barrage_first_target: str = ""
        self._barrage_last_target: str = ""
        self._barrage_last_item: str = ""
        self._barrage_timer_task: Optional[asyncio.Task] = None
        self.http_client: Optional[aiohttp.ClientSession] = None

        # Locate assets and overlay directories
        if not base_dir:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        self.base_dir = base_dir
        self.overlay_dir = os.path.join(base_dir, "overlay")
        self.assets_dir = os.path.join(base_dir, "assets")

        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.runner: Optional[web.AppRunner] = None
        self.site: Optional[web.TCPSite] = None
        self.thread: Optional[threading.Thread] = None
        self._is_running = False

    @property
    def is_running(self) -> bool:
        return self._is_running

    def get_connected_count(self) -> int:
        return len(self.connected_ws)

    def get_uptime_seconds(self) -> float:
        return time.time() - self.start_time

    # --- HTTP Route Handlers ---
    async def handle_index(self, request: web.Request) -> web.Response:
        raise web.HTTPFound("/overlay/index.html")

    async def handle_docs(self, request: web.Request) -> web.Response:
        raise web.HTTPFound("/overlay/docs.html")

    async def handle_cors_preflight(self, request: web.Request) -> web.Response:
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
        return web.Response(status=204, headers=headers)

    def record_collision(self, target_id: str, target_name: str, item_id: str, item_name: str, source: str = "physics"):
        self.total_collisions += 1
        self.collisions_by_target[target_name] = self.collisions_by_target.get(target_name, 0) + 1
        self.collisions_by_item[item_id] = self.collisions_by_item.get(item_id, 0) + 1
        collision_entry = {
            "id": self.total_collisions,
            "target_id": target_id,
            "target_name": target_name,
            "item_id": item_id,
            "item_name": item_name,
            "source": source,
            "timestamp": time.time(),
        }
        self.recent_collisions.append(collision_entry)

        # Trigger first/last hit barrage tracking
        if self.loop and self.loop.is_running():
            try:
                running_loop = asyncio.get_running_loop()
            except RuntimeError:
                running_loop = None

            if running_loop == self.loop:
                self.loop.create_task(self._handle_barrage_hit(target_name, item_name))
            else:
                asyncio.run_coroutine_threadsafe(self._handle_barrage_hit(target_name, item_name), self.loop)

        if self.on_collision_event:
            try:
                self.on_collision_event(collision_entry)
            except Exception as e:
                logger.error(f"Error in on_collision_event callback: {e}")

    async def _dispatch_webhook(self, event_type: str, target_name: str, item_name: str, hits: int):
        if not self._is_running:
            return
        cfg = self.config_manager.webhooks
        if not cfg.enabled:
            return

        if event_type == "first_hit":
            url_template = cfg.first_hit_url
            method = cfg.first_hit_method or "GET"
        else:
            url_template = cfg.last_hit_url
            method = cfg.last_hit_method or "GET"

        if not url_template or not url_template.strip():
            return

        # String placeholder substitution
        url = url_template.replace("{target}", urllib.parse.quote_plus(target_name))
        url = url.replace("{item}", urllib.parse.quote_plus(item_name))
        url = url.replace("{hits}", str(hits))
        url = url.replace("{event}", event_type)

        logger.info(f"Dispatching {event_type} webhook to {url} (method: {method})")

        payload = {
            "event": event_type,
            "target_name": target_name,
            "item_name": item_name,
            "barrage_hits": hits,
            "timestamp": time.time()
        }

        try:
            if self.http_client and self.http_client.closed:
                return
            session = self.http_client or aiohttp.ClientSession()
            close_session = (session != self.http_client)
            try:
                if method.upper() == "POST":
                    async with session.post(url, json=payload, timeout=4.0) as resp:
                        logger.info(f"Webhook {event_type} POST {url} returned status {resp.status}")
                else:
                    async with session.get(url, timeout=4.0) as resp:
                        logger.info(f"Webhook {event_type} GET {url} returned status {resp.status}")
            finally:
                if close_session:
                    await session.close()
        except Exception as e:
            logger.warning(f"Failed to dispatch {event_type} webhook to {url}: {e}")

    async def _handle_barrage_hit(self, target_name: str, item_name: str):
        settling_delay = self.config_manager.webhooks.settling_delay or 2.0

        if not self._barrage_active:
            # FIRST HIT OF BARRAGE
            self._barrage_active = True
            self._barrage_hits = 1
            self._barrage_first_target = target_name
            self._barrage_last_target = target_name
            self._barrage_last_item = item_name

            await self._dispatch_webhook("first_hit", target_name, item_name, self._barrage_hits)
        else:
            # Continuing barrage
            self._barrage_hits += 1
            self._barrage_last_target = target_name
            self._barrage_last_item = item_name

        # Cancel previous settling countdown if running
        if self._barrage_timer_task and not self._barrage_timer_task.done():
            self._barrage_timer_task.cancel()

        async def _settling_worker():
            try:
                await asyncio.sleep(settling_delay)
                # LAST HIT - Barrage settled!
                hits = self._barrage_hits
                tgt = self._barrage_last_target
                it = self._barrage_last_item
                self._barrage_active = False
                self._barrage_hits = 0

                await self._dispatch_webhook("last_hit", tgt, it, hits)
            except asyncio.CancelledError:
                pass

        self._barrage_timer_task = asyncio.create_task(_settling_worker())

    def _schedule_simulated_throw_hits(self, items):
        if not items:
            return
        if not isinstance(items, list):
            items = [items]

        target = self.config_manager.targets[0] if self.config_manager.targets else None
        target_id = target.id if target else "target"
        target_name = target.name if target else "VTuber Head"

        # Staggered simulation hits after brief flight delay (0.35s)
        base_delay = 0.35
        hits_count = max(1, min(len(items), 8))

        def _fire_hit(tgt_id, tgt_nm, it_id, it_nm):
            self.record_collision(
                target_id=tgt_id,
                target_name=tgt_nm,
                item_id=it_id,
                item_name=it_nm,
                source="simulated"
            )

        if self.loop and self.loop.is_running():
            for i in range(hits_count):
                it = items[i]
                delay = base_delay + (i * 0.12)
                self.loop.call_later(delay, _fire_hit, target_id, target_name, it.id, it.name)

    def resolve_items_for_throw(
        self,
        item_key: Optional[str] = None,
        raw_items: Optional[List[str]] = None,
        raw_groups: Optional[List[str]] = None,
        raw_excludes: Optional[List[str]] = None,
        amount: int = 1,
    ) -> Tuple[List[ThrowableItem], bool, List[str]]:
        """
        Resolves the projectile items to spawn.
        Supports specific items, random, and random_mix with items/group filters and exclusions.
        Returns: (selected_items, is_random_mix, candidate_pool_ids)
        """
        all_items = list(self.config_manager.items.values())
        if not all_items:
            return [], False, []

        amount = max(1, min(100, amount))

        # Determine if random_mix mode is requested
        is_mix = False
        if item_key:
            ik = item_key.strip().lower()
            if ik in ["random_mix", "mix", "all"]:
                is_mix = True
        if raw_items:
            is_mix = True
        if raw_groups:
            is_mix = True
        if raw_excludes:
            is_mix = True

        # Build candidate item pool
        if raw_items:
            # Check if "all" keyword is present in items
            if any(x.lower() == "all" for x in raw_items):
                pool = list(all_items)
            else:
                pool = []
                for query_val in raw_items:
                    qv = query_val.strip().lower()
                    matched = False
                    for it in all_items:
                        if it.id.lower() == qv or it.name.lower() == qv:
                            if it not in pool:
                                pool.append(it)
                            matched = True
                    # If not matched by ID/name, check if it matches an item group
                    if not matched:
                        for it in all_items:
                            if it.group.lower() == qv:
                                if it not in pool:
                                    pool.append(it)
        elif item_key and item_key.strip().lower() == "all":
            pool = list(all_items)
        else:
            pool = list(all_items)

        # Filter by group(s) if provided
        if raw_groups:
            group_set = {g.strip().lower() for g in raw_groups if g.strip()}
            if group_set:
                if not raw_items or any(x.lower() == "all" for x in raw_items):
                    pool = [it for it in pool if it.group.lower() in group_set]
                else:
                    # Include any items matching groups in addition to explicit items
                    for it in all_items:
                        if it.group.lower() in group_set and it not in pool:
                            pool.append(it)

        # Apply exclusions (item ID, name, or group)
        if raw_excludes:
            exclude_set = {x.strip().lower() for x in raw_excludes if x.strip()}
            if exclude_set:
                pool = [
                    it for it in pool
                    if it.id.lower() not in exclude_set
                    and it.name.lower() not in exclude_set
                    and it.group.lower() not in exclude_set
                ]

        if is_mix:
            if not pool:
                return [], True, []
            selected_items = [random.choice(pool) for _ in range(amount)]
            return selected_items, True, [it.id for it in pool]

        # Standard non-mix selection
        if not item_key or item_key.strip().lower() == "random":
            single_item = random.choice(all_items)
        else:
            single_item = None
            target_key = item_key.strip().lower()
            for it in all_items:
                if it.id.lower() == target_key or it.name.lower() == target_key:
                    single_item = it
                    break
            if not single_item:
                single_item = random.choice(all_items)

        return [single_item] * amount, False, [single_item.id]

    async def handle_status(self, request: web.Request) -> web.Response:
        data = {
            "status": "running",
            "uptime_seconds": round(self.get_uptime_seconds(), 2),
            "connected_overlays": len(self.connected_ws),
            "active_targets": len(self.config_manager.targets),
            "total_items": len(self.config_manager.items),
            "total_collisions": self.total_collisions,
            "host": self.config_manager.server.host,
            "port": self.config_manager.server.port,
        }
        return web.json_response(data, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_get_items(self, request: web.Request) -> web.Response:
        fmt = request.query.get("format", "").strip().lower()
        if fmt in ["csv", "ids", "text", "plain", "list"]:
            return await self.handle_get_item_ids(request)

        group_filter = request.query.get("group")
        items_list = [item.to_dict() for item in self.config_manager.items.values()]
        if group_filter:
            gf = group_filter.strip().lower()
            items_list = [it for it in items_list if it.get("group", "").lower() == gf]
        return web.json_response({"items": items_list}, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_get_item_ids(self, request: web.Request) -> web.Response:
        """Returns a comma-separated list of all throwable item IDs (or JSON if requested)."""
        group_filter = request.query.get("group")
        items = list(self.config_manager.items.values())
        if group_filter:
            gf = group_filter.strip().lower()
            items = [it for it in items if getattr(it, "group", "").lower() == gf]

        item_ids = [it.id for it in items]

        # Determine separator: ?sep=, or ?separator=, or ?space=false
        sep = request.query.get("sep", request.query.get("separator"))
        if sep is None:
            sep = "," if request.query.get("space", "true").lower() in ["false", "0", "no"] else ", "

        fmt = request.query.get("format", "").strip().lower()
        if fmt == "json":
            return web.json_response({
                "ids": item_ids,
                "csv": sep.join(item_ids),
                "count": len(item_ids)
            }, headers={"Access-Control-Allow-Origin": "*"})

        return web.Response(
            text=sep.join(item_ids),
            content_type="text/plain",
            charset="utf-8",
            headers={"Access-Control-Allow-Origin": "*"}
        )

    async def handle_get_targets(self, request: web.Request) -> web.Response:
        targets_list = [t.to_dict() for t in self.config_manager.targets]
        return web.json_response({"targets": targets_list}, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_post_targets(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            from .models import Target
            targets_data = body.get("targets", [])
            new_targets = [Target.from_dict(t) for t in targets_data]
            if new_targets:
                self.config_manager.targets = new_targets
                self.config_manager.save()
                await self.broadcast({"type": "targets_updated", "targets": [t.to_dict() for t in new_targets]})
            return web.json_response({"status": "ok", "targets_count": len(new_targets)}, headers={"Access-Control-Allow-Origin": "*"})
        except Exception as e:
            return web.json_response({"error": str(e)}, status=400, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_get_config(self, request: web.Request) -> web.Response:
        return web.json_response(self.config_manager.to_client_dict(), headers={"Access-Control-Allow-Origin": "*"})

    async def handle_throw(self, request: web.Request) -> web.Response:
        # Support parameters from either URL query string (?item=...&amount=...) or JSON body
        query = request.query
        body = {}
        if request.can_read_body:
            try:
                body = await request.json()
            except Exception:
                body = {}

        # item parameter
        item_key = query.get("item", body.get("item"))

        # Amount parsing
        amount_val = query.get("amount", body.get("amount", 1))
        try:
            amount = max(1, min(100, int(amount_val)))
        except (ValueError, TypeError):
            amount = 1

        # Spawn Direction (accepts spawn_direction or direction)
        spawn_direction = query.get(
            "spawn_direction",
            query.get(
                "direction",
                body.get(
                    "spawn_direction",
                    body.get("direction", self.config_manager.physics.default_spawn_direction)
                )
            )
        )

        # Force multiplier
        force_val = query.get("force", body.get("force", self.config_manager.physics.default_force))
        try:
            force = float(force_val)
        except (ValueError, TypeError):
            force = self.config_manager.physics.default_force

        # Spread angle
        spread_val = query.get("spread", body.get("spread", self.config_manager.physics.default_spread))
        try:
            spread = float(spread_val)
        except (ValueError, TypeError):
            spread = self.config_manager.physics.default_spread

        # Parse items list / filter
        raw_items = []
        if "items" in query:
            for val in query.getall("items"):
                for part in val.split(","):
                    p = part.strip()
                    if p:
                        raw_items.append(p)
        elif "items" in body:
            b_items = body.get("items")
            if isinstance(b_items, list):
                raw_items = [str(x).strip() for x in b_items if str(x).strip()]
            elif isinstance(b_items, str):
                raw_items = [x.strip() for x in b_items.split(",") if x.strip()]

        # Parse group filter (accepts group, item_group, groups, item_groups)
        raw_groups = []
        for g_key in ["group", "item_group", "groups", "item_groups"]:
            if g_key in query:
                for val in query.getall(g_key):
                    for part in val.split(","):
                        p = part.strip()
                        if p:
                            raw_groups.append(p)
            elif g_key in body:
                b_g = body.get(g_key)
                if isinstance(b_g, list):
                    raw_groups.extend([str(x).strip() for x in b_g if str(x).strip()])
                elif isinstance(b_g, str):
                    raw_groups.extend([x.strip() for x in b_g.split(",") if x.strip()])

        # Parse exclusion filters (accepts item_exclude, group_exclude, exclude, items_exclude, exclude_group, exclude_item, excludes)
        raw_excludes = []
        for ex_key in ["item_exclude", "group_exclude", "exclude", "items_exclude", "exclude_group", "exclude_item", "excludes"]:
            if ex_key in query:
                for val in query.getall(ex_key):
                    for part in val.split(","):
                        p = part.strip()
                        if p:
                            raw_excludes.append(p)
            elif ex_key in body:
                b_ex = body.get(ex_key)
                if isinstance(b_ex, list):
                    raw_excludes.extend([str(x).strip() for x in b_ex if str(x).strip()])
                elif isinstance(b_ex, str):
                    raw_excludes.extend([x.strip() for x in b_ex.split(",") if x.strip()])

        selected_items, is_random_mix, pool_ids = self.resolve_items_for_throw(
            item_key=item_key,
            raw_items=raw_items,
            raw_groups=raw_groups,
            raw_excludes=raw_excludes,
            amount=amount
        )

        if not selected_items:
            return web.json_response({
                "status": "error",
                "message": f"No throwable items matched filter criteria (item={item_key}, items={raw_items}, group={raw_groups}, exclude={raw_excludes})"
            }, status=400, headers={"Access-Control-Allow-Origin": "*"})

        first_item = selected_items[0]
        event_payload = {
            "type": "throw",
            "mode": "random_mix" if is_random_mix else "single",
            "item": first_item.id,
            "item_data": first_item.to_dict(),
            "items": [it.id for it in selected_items],
            "items_data": [it.to_dict() for it in selected_items],
            "amount": amount,
            "spawn_direction": spawn_direction,
            "force": force,
            "spread": spread,
        }
        await self.broadcast(event_payload)

        # Fallback simulation if no active OBS overlays are connected (e.g. headless/desktop testing)
        if len(self.connected_ws) == 0:
            logger.info("No active OBS overlays connected; simulating throw impact for barrage/webhook triggers")
            self._schedule_simulated_throw_hits(selected_items)

        # Notify GTK application callback if registered
        if self.on_throw_event:
            try:
                self.on_throw_event(event_payload)
            except Exception as e:
                logger.error(f"Error in on_throw_event callback: {e}")

        return web.json_response({
            "status": "ok",
            "message": f"Spawned {amount} items ({'random_mix' if is_random_mix else first_item.name})",
            "mode": "random_mix" if is_random_mix else "single",
            "pool": pool_ids if is_random_mix else [first_item.id],
            "item": first_item.id,
            "items": [it.id for it in selected_items],
            "amount": amount,
            "spawn_direction": spawn_direction,
            "force": force,
            "spread": spread,
        }, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_clear(self, request: web.Request) -> web.Response:
        await self.broadcast({"type": "clear"})
        return web.json_response({"status": "ok", "message": "Cleared all items"}, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_collision(self, request: web.Request) -> web.Response:
        """Trigger an instant collision event on a target via GET or POST."""
        query = request.query
        body = {}
        if request.can_read_body:
            try:
                body = await request.json()
            except Exception:
                body = {}

        target_key = query.get("target", query.get("target_id", body.get("target", body.get("target_id"))))
        item_key = query.get("item", body.get("item"))
        sound = query.get("sound", body.get("sound"))
        volume_val = query.get("volume", body.get("volume"))

        # Resolve target (match ID or name, fallback to primary target)
        target = None
        if target_key:
            for t in self.config_manager.targets:
                if t.id.lower() == target_key.lower() or t.name.lower() == target_key.lower():
                    target = t
                    break
        if not target and self.config_manager.targets:
            target = self.config_manager.targets[0]

        # Resolve item (match ID or name, fallback to first item or random)
        item = None
        if item_key:
            for it in self.config_manager.items.values():
                if it.id.lower() == item_key.lower() or it.name.lower() == item_key.lower():
                    item = it
                    break
        if not item and self.config_manager.items:
            item = list(self.config_manager.items.values())[0]

        target_id = target.id if target else "target"
        target_name = target.name if target else "Target"
        item_id = item.id if item else "item"
        item_name = item.name if item else "Item"
        sound_effect = sound or (item.sound_effect if item else "bonk")

        try:
            volume = float(volume_val) if volume_val is not None else (item.sound_volume if item else 0.85)
        except (ValueError, TypeError):
            volume = 0.85

        pitch_rand = item.pitch_randomness if item else 0.25

        # Record collision statistic
        self.record_collision(target_id, target_name, item_id, item_name, source="api")

        # Broadcast direct collision impact to OBS overlays
        event_payload = {
            "type": "collision",
            "target_id": target_id,
            "target_name": target_name,
            "item_id": item_id,
            "item_name": item_name,
            "item_data": item.to_dict() if item else None,
            "sound": sound_effect,
            "volume": volume,
            "pitch_randomness": pitch_rand,
        }
        await self.broadcast(event_payload)

        return web.json_response({
            "status": "ok",
            "message": f"Collision triggered on {target_name} with {item_name}",
            "target": target_id,
            "target_name": target_name,
            "item": item_id,
            "item_name": item_name,
            "sound": sound_effect,
            "total_collisions": self.total_collisions,
        }, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_get_collisions(self, request: web.Request) -> web.Response:
        """Query collision statistics or trigger collision if parameters provided."""
        # If trigger parameters are supplied in GET /api/v1/collisions, treat as trigger
        if "item" in request.query or "target" in request.query or request.query.get("trigger") == "true":
            return await self.handle_collision(request)

        data = {
            "status": "ok",
            "total_collisions": self.total_collisions,
            "by_target": dict(self.collisions_by_target),
            "by_item": dict(self.collisions_by_item),
            "recent": list(self.recent_collisions)
        }
        return web.json_response(data, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_reset_collisions(self, request: web.Request) -> web.Response:
        """Reset collision counter and history."""
        self.total_collisions = 0
        self.collisions_by_target.clear()
        self.collisions_by_item.clear()
        self.recent_collisions.clear()
        return web.json_response({"status": "ok", "message": "Collision statistics reset to 0"}, headers={"Access-Control-Allow-Origin": "*"})

    # --- WebSocket Handler ---
    async def handle_ws(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse(heartbeat=25.0)
        await ws.prepare(request)

        self.connected_ws.add(ws)
        logger.info(f"OBS Overlay connected via WebSocket. Active overlays: {len(self.connected_ws)}")

        # Send initial config payload upon connection
        init_payload = {
            "type": "init",
            "config": self.config_manager.to_client_dict()
        }
        await ws.send_json(init_payload)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    try:
                        data = json.loads(msg.data)
                        msg_type = data.get("type")
                        if msg_type == "ping":
                            await ws.send_json({"type": "pong"})
                        elif msg_type == "collision_event":
                            self.record_collision(
                                target_id=data.get("target_id", "target"),
                                target_name=data.get("target_name", "Target"),
                                item_id=data.get("item_id", "unknown"),
                                item_name=data.get("item_name", "Item"),
                                source="physics"
                            )
                    except Exception as e:
                        logger.warning(f"Invalid message from WS client: {e}")
                elif msg.type == WSMsgType.ERROR:
                    logger.warning(f"WS client error: {ws.exception()}")
        finally:
            self.connected_ws.discard(ws)
            logger.info(f"OBS Overlay disconnected. Active overlays: {len(self.connected_ws)}")

        return ws

    # --- Broadcast Helpers ---
    async def broadcast(self, message: Dict[str, Any]):
        if not self.connected_ws:
            return
        dead_ws = set()
        for ws in self.connected_ws:
            try:
                await ws.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send to WS client: {e}")
                dead_ws.add(ws)
        for ws in dead_ws:
            self.connected_ws.discard(ws)

    def threadsafe_broadcast(self, message: Dict[str, Any]):
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(self.broadcast(message), self.loop)

    def threadsafe_throw(
        self,
        item_id: str = "random",
        amount: int = 1,
        spawn_direction: str = "random",
        force: float = 1.0,
        spread: float = 15.0,
        items: Optional[List[str]] = None,
        group: Optional[str] = None,
        exclude: Optional[List[str]] = None,
    ):
        raw_items = items or []
        raw_groups = [group] if group else []
        raw_excludes = exclude or []

        selected_items, is_random_mix, pool_ids = self.resolve_items_for_throw(
            item_key=item_id,
            raw_items=raw_items,
            raw_groups=raw_groups,
            raw_excludes=raw_excludes,
            amount=amount
        )
        if not selected_items:
            logger.warning(f"No items available to throw for filter: item={item_id}")
            return

        first_item = selected_items[0]
        payload = {
            "type": "throw",
            "mode": "random_mix" if is_random_mix else "single",
            "item": first_item.id,
            "item_data": first_item.to_dict(),
            "items": [it.id for it in selected_items],
            "items_data": [it.to_dict() for it in selected_items],
            "amount": amount,
            "spawn_direction": spawn_direction,
            "force": force,
            "spread": spread,
        }
        self.threadsafe_broadcast(payload)
        if self.on_throw_event:
            self.on_throw_event(payload)

        # Fallback simulation if no active OBS overlays are connected (e.g. desktop app testing)
        if len(self.connected_ws) == 0:
            logger.info("No active OBS overlays connected; simulating throw impact for barrage/webhook triggers")
            self._schedule_simulated_throw_hits(selected_items)

    def threadsafe_clear(self):
        self.threadsafe_broadcast({"type": "clear"})

    def threadsafe_update_config(self):
        self.threadsafe_broadcast({
            "type": "config_update",
            "config": self.config_manager.to_client_dict()
        })

    async def handle_get_webhooks(self, request: web.Request) -> web.Response:
        return web.json_response({
            "status": "ok",
            "webhooks": self.config_manager.webhooks.to_dict()
        }, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_post_webhooks(self, request: web.Request) -> web.Response:
        try:
            body = await request.json()
            from .models import WebhookConfig
            self.config_manager.webhooks = WebhookConfig.from_dict(body)
            self.config_manager.save()
            return web.json_response({
                "status": "ok",
                "webhooks": self.config_manager.webhooks.to_dict()
            }, headers={"Access-Control-Allow-Origin": "*"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_test_webhook(self, request: web.Request) -> web.Response:
        query = request.query
        event_type = query.get("event", query.get("type", "first_hit"))
        if event_type in ["first", "1"]:
            event_type = "first_hit"
        elif event_type in ["last", "end"]:
            event_type = "last_hit"

        target_name = self.config_manager.targets[0].name if self.config_manager.targets else "VTuber Head"
        item_name = "Beach Ball"
        await self._dispatch_webhook(event_type, target_name, item_name, hits=1)

        return web.json_response({
            "status": "ok",
            "message": f"Test {event_type} webhook dispatched",
            "event": event_type,
            "webhooks_enabled": self.config_manager.webhooks.enabled,
        }, headers={"Access-Control-Allow-Origin": "*"})

    # --- Server Lifecycle & Daemon Thread ---
    def _create_app(self) -> web.Application:
        app = web.Application()

        # REST API Routes (supports POST with JSON/Query and GET with Query)
        app.router.add_post("/api/v1/throw", self.handle_throw)
        app.router.add_get("/api/v1/throw", self.handle_throw)
        app.router.add_post("/api/v1/clear", self.handle_clear)
        app.router.add_get("/api/v1/clear", self.handle_clear)
        # Collision API Routes (supports GET and POST for direct hits and stats)
        app.router.add_get("/api/v1/collision", self.handle_collision)
        app.router.add_post("/api/v1/collision", self.handle_collision)
        app.router.add_get("/api/v1/collisions", self.handle_get_collisions)
        app.router.add_post("/api/v1/collisions", self.handle_collision)
        app.router.add_get("/api/v1/collisions/reset", self.handle_reset_collisions)
        app.router.add_post("/api/v1/collisions/reset", self.handle_reset_collisions)

        # Webhook Configuration & Testing Routes
        app.router.add_get("/api/v1/webhooks", self.handle_get_webhooks)
        app.router.add_post("/api/v1/webhooks", self.handle_post_webhooks)
        app.router.add_get("/api/v1/webhooks/test", self.handle_test_webhook)
        app.router.add_post("/api/v1/webhooks/test", self.handle_test_webhook)

        app.router.add_get("/api/v1/items", self.handle_get_items)
        app.router.add_get("/api/v1/items/ids", self.handle_get_item_ids)
        app.router.add_get("/api/v1/items/csv", self.handle_get_item_ids)
        app.router.add_get("/api/v1/items/list", self.handle_get_item_ids)
        app.router.add_get("/items/ids", self.handle_get_item_ids)
        app.router.add_get("/api/v1/targets", self.handle_get_targets)
        app.router.add_post("/api/v1/targets", self.handle_post_targets)
        app.router.add_get("/api/v1/status", self.handle_status)
        app.router.add_get("/api/v1/config", self.handle_get_config)

        # CORS preflight options
        app.router.add_route("OPTIONS", "/api/v1/{tail:.*}", self.handle_cors_preflight)

        # WebSocket Route
        app.router.add_get("/ws", self.handle_ws)

        # Static Overlay & Assets Routes
        app.router.add_get("/", self.handle_index)
        app.router.add_get("/docs", self.handle_docs)
        app.router.add_get("/docs.html", self.handle_docs)
        app.router.add_get("/documentation", self.handle_docs)
        app.router.add_get("/documentation.html", self.handle_docs)
        if os.path.exists(self.overlay_dir):
            app.router.add_static("/overlay", self.overlay_dir, show_index=True)
        if os.path.exists(self.assets_dir):
            app.router.add_static("/assets", self.assets_dir, show_index=True)

        return app

    def _run_server_loop(self):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)

        app = self._create_app()
        self.runner = web.AppRunner(app)
        self.loop.run_until_complete(self.runner.setup())

        host = self.config_manager.server.host
        port = self.config_manager.server.port
        self.site = web.TCPSite(self.runner, host, port)
        self.loop.run_until_complete(self.site.start())

        async def _create_http_client():
            return aiohttp.ClientSession()

        self.http_client = self.loop.run_until_complete(_create_http_client())

        logger.info(f"Yeet server daemon running at http://{host}:{port}/")
        self._is_running = True

        try:
            self.loop.run_forever()
        finally:
            self._is_running = False
            if self.http_client:
                self.loop.run_until_complete(self.http_client.close())
            self.loop.run_until_complete(self.runner.cleanup())
            self.loop.close()
            logger.info("Yeet server daemon stopped.")

    def start(self):
        if self._is_running:
            return
        self.thread = threading.Thread(target=self._run_server_loop, daemon=True, name="YeetServerThread")
        self.thread.start()

    def stop(self):
        if not self._is_running or not self.loop:
            return
        if self._barrage_timer_task and not self._barrage_timer_task.done():
            self.loop.call_soon_threadsafe(self._barrage_timer_task.cancel)
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self._is_running = False
