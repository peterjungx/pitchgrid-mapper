"""
Web API for controlling the application and serving the UI.

Provides REST endpoints and WebSocket for real-time updates.
"""

import logging
from typing import Optional

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from .app import PGIsomapApp
from .config import settings
from .layouts import LayoutConfig, LayoutType

logger = logging.getLogger(__name__)


class ConnectControllerRequest(BaseModel):
    """Request to connect to a controller."""
    device_name: str


class LayoutConfigUpdate(BaseModel):
    """Layout configuration update."""
    layout_type: LayoutType
    root_x: int = 0
    root_y: int = 0
    skew_x: int = 0
    skew_y: int = 0
    rotation: int = 0
    move_x: int = 0
    move_y: int = 0


class WebAPI:
    """Web API server."""

    def __init__(self, app: PGIsomapApp):
        self.app = app
        self.fastapi = FastAPI(title="PG Isomap API", version=settings.version)

        # Set reference back to app so it can broadcast updates
        self.app.web_api = self

        # CORS middleware
        self.fastapi.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # In production, restrict this
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # WebSocket connections
        self.active_connections: list[WebSocket] = []

        # Event loop reference (set when FastAPI starts)
        self.event_loop = None

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register API routes."""

        @self.fastapi.get("/api/status")
        async def get_status():
            """Get current application status."""
            return self.app.get_status()

        @self.fastapi.get("/api/controllers")
        async def get_controllers():
            """Get list of available controllers."""
            return {
                'controllers': self.app.controller_manager.get_all_device_names(),
                'connected': self.app.current_controller.device_name if self.app.current_controller else None
            }

        @self.fastapi.post("/api/controllers/connect")
        async def connect_controller(request: ConnectControllerRequest):
            """Connect to a controller."""
            success = self.app.connect_to_controller(request.device_name)
            return {'success': success}

        @self.fastapi.post("/api/controllers/disconnect")
        async def disconnect_controller():
            """Disconnect from current controller."""
            self.app.disconnect_controller()
            return {'success': True}

        @self.fastapi.post("/api/controllers/switch")
        async def switch_controller(request: ConnectControllerRequest):
            """
            Switch to a controller configuration without requiring MIDI connection.

            This loads the controller's pad layout and geometry, but doesn't
            establish a MIDI connection. Useful for Computer Keyboard and for
            visualizing controllers that aren't physically connected.
            """
            config = self.app.controller_manager.get_config(request.device_name)
            if not config:
                return {'success': False, 'error': f'Controller config not found: {request.device_name}'}

            # Disconnect from any existing MIDI controller
            self.app.midi_handler.disconnect_controller()

            # Load the configuration
            self.app.current_controller = config

            # Reset layout calculator to default when changing controllers
            self.app.current_layout_calculator = None

            # Recalculate layout with fresh calculator
            self.app._recalculate_layout()

            logger.info(f"Switched to controller configuration: {request.device_name}")
            return {'success': True}

        @self.fastapi.get("/api/layout")
        async def get_layout():
            """Get current layout configuration."""
            return self.app.current_layout_config.dict()

        @self.fastapi.post("/api/layout")
        async def update_layout(config: LayoutConfigUpdate):
            """Update layout configuration."""
            layout_config = LayoutConfig(**config.dict())
            self.app.update_layout_config(layout_config)

            # Notify WebSocket clients
            await self._broadcast({
                'type': 'layout_update',
                'config': config.dict()
            })

            return {'success': True}

        @self.fastapi.post("/api/trigger_note")
        async def trigger_note(request: dict):
            """Trigger a MIDI note (for clicking pads or keyboard input)."""
            logical_x = request.get('x')
            logical_y = request.get('y')
            velocity = request.get('velocity', 100)

            if logical_x is None or logical_y is None:
                return {'success': False, 'error': 'Missing x or y coordinate'}

            # Lookup the mapped note
            coord = (logical_x, logical_y)
            if coord in self.app.midi_handler.note_mapping:
                note = self.app.midi_handler.note_mapping[coord]
                # Send note-on then note-off after a short duration
                # This is a simplified version - in real implementation,
                # we'd need proper note tracking
                logger.info(f"Triggered note {note} from pad ({logical_x}, {logical_y})")
                return {'success': True, 'note': note}

            return {'success': False, 'error': 'Pad not mapped to a note'}

        @self.fastapi.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            """WebSocket endpoint for real-time updates."""
            import asyncio

            # Store event loop reference on first WebSocket connection
            if self.event_loop is None:
                self.event_loop = asyncio.get_event_loop()

            await websocket.accept()
            self.active_connections.append(websocket)

            try:
                # Send initial state
                await websocket.send_json({
                    'type': 'init',
                    'status': self.app.get_status()
                })

                # Keep connection alive and receive messages
                while True:
                    data = await websocket.receive_text()
                    logger.debug(f"Received WebSocket message: {data}")

                    # Parse and handle client messages
                    try:
                        import json
                        message = json.loads(data)
                        message_type = message.get('type')

                        if message_type == 'apply_transformation':
                            # Handle transformation request
                            transformation = message.get('transformation')
                            if transformation:
                                success = self.app.apply_transformation(transformation)
                                if success:
                                    # Broadcast updated status to all clients
                                    await self._broadcast({
                                        'type': 'status_update',
                                        'status': self.app.get_status()
                                    })
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in WebSocket message: {data}")
                    except Exception as e:
                        logger.error(f"Error handling WebSocket message: {e}")

            except WebSocketDisconnect:
                self.active_connections.remove(websocket)
                logger.info("WebSocket client disconnected")

        # Serve frontend static files if available
        if settings.frontend_dist_dir and settings.frontend_dist_dir.exists():
            @self.fastapi.get("/")
            async def serve_frontend():
                """Serve frontend index.html."""
                return FileResponse(settings.frontend_dist_dir / "index.html")

            # Mount static assets after defining routes
            self.fastapi.mount(
                "/assets",
                StaticFiles(directory=settings.frontend_dist_dir / "assets"),
                name="assets"
            )

    async def _broadcast(self, message: dict):
        """Broadcast message to all connected WebSocket clients."""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to WebSocket: {e}")
                disconnected.append(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.active_connections.remove(connection)

    def broadcast_status_update(self):
        """
        Broadcast current status to all WebSocket clients.

        This is a synchronous wrapper that schedules the broadcast
        to be executed in the event loop from any thread.
        """
        import asyncio

        if not self.active_connections or self.event_loop is None:
            return

        message = {
            'type': 'status_update',
            'status': self.app.get_status()
        }

        # Schedule the broadcast in the event loop
        async def send_to_all():
            disconnected = []
            for connection in self.active_connections[:]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting to WebSocket: {e}")
                    disconnected.append(connection)

            # Remove disconnected clients
            for connection in disconnected:
                if connection in self.active_connections:
                    self.active_connections.remove(connection)

        # Use run_coroutine_threadsafe to schedule from another thread
        try:
            asyncio.run_coroutine_threadsafe(send_to_all(), self.event_loop)
        except Exception as e:
            logger.error(f"Error scheduling WebSocket broadcast: {e}")
