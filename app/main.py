"""
FastAPI application for Google Photos Downloader
"""
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.api.routes import router
    from app.api.websockets import ConnectionManager
    from app.core.config import ConfigManager
except ImportError:
    from api.routes import router
    from api.websockets import ConnectionManager
    from core.config import ConfigManager

# Global instances
config = ConfigManager()
connection_manager = ConnectionManager()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    print("🚀 Starting Google Photos Downloader Web App...")
    
    # Verify static files directory exists
    if not static_path.exists():
        print(f"⚠️  Warning: Static files directory not found at {static_path}")
        print("Creating static directory...")
        static_path.mkdir(parents=True, exist_ok=True)
    
    # Verify configuration can be loaded
    try:
        config.load_config()
        print("✅ Configuration loaded successfully")
    except Exception as e:
        print(f"⚠️  Warning: Configuration loading issue: {e}")
    
    yield
    # Shutdown
    print("🛑 Shutting down Google Photos Downloader Web App...")


# Create FastAPI app
app = FastAPI(
    title="Google Photos Downloader",
    description="Web-based Google Photos downloader with real-time progress tracking",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files - Using pathlib for cross-platform compatibility
static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Serve the main HTML page."""
    html_path = static_path / "index.html"
    
    try:
        with open(html_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(
            content=f"<h1>Error: index.html not found</h1><p>Expected at: {html_path}</p>",
            status_code=404
        )
    except Exception as e:
        return HTMLResponse(
            content=f"<h1>Error loading page</h1><p>{str(e)}</p>",
            status_code=500
        )


@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """WebSocket endpoint for real-time progress updates."""
    await connection_manager.connect(websocket, session_id)
    try:
        while True:
            # Keep connection alive and handle any messages
            data = await websocket.receive_text()
            # Echo back for heartbeat
            await websocket.send_text(f"Heartbeat: {data}")
    except WebSocketDisconnect:
        connection_manager.disconnect(websocket, session_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        connection_manager.disconnect(websocket, session_id)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "message": "Google Photos Downloader is running"}


if __name__ == "__main__":
    import uvicorn
    import sys
    
    try:
        print("🌐 Starting server on http://0.0.0.0:8000")
        print("💻 Access the app at http://localhost:8000")
        print("⏹️  Press Ctrl+C to stop")
        
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        print("💡 Try running with: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000")
        sys.exit(1)