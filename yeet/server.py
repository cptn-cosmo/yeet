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
from typing import Set, Dict, Any, Optional, Callable
from aiohttp import web, WSMsgType

from .config import ConfigManager
from .models import ThrowableItem

logger = logging.getLogger("yeet.server")

class ServerDaemon:
    def __init__(self, config_manager: ConfigManager, base_dir: str = None, on_throw_event: Optional[Callable[[Dict[str, Any]], None]] = None):
        self.config_manager = config_manager
        self.on_throw_event = on_throw_event
        self.start_time = time.time()
        self.connected_ws: Set[web.WebSocketResponse] = set()

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

    async def handle_cors_preflight(self, request: web.Request) -> web.Response:
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
        return web.Response(status=204, headers=headers)

    async def handle_status(self, request: web.Request) -> web.Response:
        data = {
            "status": "running",
            "uptime_seconds": round(self.get_uptime_seconds(), 2),
            "connected_overlays": len(self.connected_ws),
            "active_targets": len(self.config_manager.targets),
            "total_items": len(self.config_manager.items),
            "host": self.config_manager.server.host,
            "port": self.config_manager.server.port,
        }
        return web.json_response(data, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_get_items(self, request: web.Request) -> web.Response:
        items_list = [item.to_dict() for item in self.config_manager.items.values()]
        return web.json_response({"items": items_list}, headers={"Access-Control-Allow-Origin": "*"})

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

        # Query parameters take precedence if provided, falling back to JSON body
        item_key = query.get("item", body.get("item"))

        # Amount parsing
        amount_val = query.get("amount", body.get("amount", 1))
        try:
            amount = int(amount_val)
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

        # Item selection: random if omitted, or pick specified
        available_items = list(self.config_manager.items.values())
        if not available_items:
            return web.json_response({"status": "error", "message": "No throwable items configured"}, status=400, headers={"Access-Control-Allow-Origin": "*"})

        selected_item: Optional[ThrowableItem] = None
        if not item_key or item_key == "random":
            selected_item = random.choice(available_items)
        else:
            if item_key in self.config_manager.items:
                selected_item = self.config_manager.items[item_key]
            else:
                # Case-insensitive match on ID or Name
                for it in available_items:
                    if it.id.lower() == item_key.lower() or it.name.lower() == item_key.lower():
                        selected_item = it
                        break
                if not selected_item:
                    selected_item = random.choice(available_items)

        # Broadcast throw command to all connected OBS overlay instances
        event_payload = {
            "type": "throw",
            "item": selected_item.id,
            "item_data": selected_item.to_dict(),
            "amount": max(1, min(100, amount)),
            "spawn_direction": spawn_direction,
            "force": force,
            "spread": spread,
        }
        await self.broadcast(event_payload)

        # Notify GTK application callback if registered
        if self.on_throw_event:
            try:
                self.on_throw_event(event_payload)
            except Exception as e:
                logger.error(f"Error in on_throw_event callback: {e}")

        return web.json_response({
            "status": "ok",
            "message": f"Spawned {amount} of {selected_item.name}",
            "item": selected_item.id,
            "amount": amount,
            "spawn_direction": spawn_direction,
            "force": force,
            "spread": spread,
        }, headers={"Access-Control-Allow-Origin": "*"})

    async def handle_clear(self, request: web.Request) -> web.Response:
        await self.broadcast({"type": "clear"})
        return web.json_response({"status": "ok", "message": "Cleared all items"}, headers={"Access-Control-Allow-Origin": "*"})

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
                        if data.get("type") == "ping":
                            await ws.send_json({"type": "pong"})
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

    def threadsafe_throw(self, item_id: str, amount: int = 1, spawn_direction: str = "random", force: float = 1.0, spread: float = 15.0):
        item = self.config_manager.items.get(item_id)
        if not item and self.config_manager.items:
            item = list(self.config_manager.items.values())[0]
        if not item:
            return

        payload = {
            "type": "throw",
            "item": item.id,
            "item_data": item.to_dict(),
            "amount": amount,
            "spawn_direction": spawn_direction,
            "force": force,
            "spread": spread,
        }
        self.threadsafe_broadcast(payload)
        if self.on_throw_event:
            self.on_throw_event(payload)

    def threadsafe_clear(self):
        self.threadsafe_broadcast({"type": "clear"})

    def threadsafe_update_config(self):
        self.threadsafe_broadcast({
            "type": "config_update",
            "config": self.config_manager.to_client_dict()
        })

    # --- Server Lifecycle & Daemon Thread ---
    def _create_app(self) -> web.Application:
        app = web.Application()

        # REST API Routes (supports POST with JSON/Query and GET with Query)
        app.router.add_post("/api/v1/throw", self.handle_throw)
        app.router.add_get("/api/v1/throw", self.handle_throw)
        app.router.add_post("/api/v1/clear", self.handle_clear)
        app.router.add_get("/api/v1/clear", self.handle_clear)
        app.router.add_get("/api/v1/items", self.handle_get_items)
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

        logger.info(f"Yeet server daemon running at http://{host}:{port}/")
        self._is_running = True

        try:
            self.loop.run_forever()
        finally:
            self._is_running = False
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
        self.loop.call_soon_threadsafe(self.loop.stop)
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2.0)
        self._is_running = False
