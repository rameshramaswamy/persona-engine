# Copy this file to persona-engine-core/src/api/middleware.py

from starlette.types import ASGIApp, Scope, Receive, Send
from starlette.websockets import WebSocket
import json

# Import the Mesh (assuming it's installed or in path)
# from persona_safety_mesh.src.manager import SafetyMesh

class SafetyMiddleware:
    def __init__(self, app: ASGIApp, safety_mesh):
        self.app = app
        self.mesh = safety_mesh

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            # WebSockets are tricky to intercept in middleware without reading the stream
            # Usually, we inject the safety check inside the route handler (Layer 2)
            # For HTTP requests:
            pass
        
        await self.app(scope, receive, send)

# BETTER APPROACH: Dependency Injection in Routes
# See Step 4 below