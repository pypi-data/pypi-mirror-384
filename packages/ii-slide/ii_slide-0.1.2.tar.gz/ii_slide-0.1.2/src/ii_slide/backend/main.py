"""
Main entry point for ii-slide backend server
"""
import uvicorn
import argparse
from ii_slide.backend.app import create_app


def main():
    """Main function to start the server"""
    parser = argparse.ArgumentParser(description="ii-slide backend server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", default=8000, type=int, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--log-level", default="info", help="Log level")

    args = parser.parse_args()

    app = create_app()

    print(f"""
🚀 Starting ii-slide backend server...

📍 Server will be available at:
   - Local: http://localhost:{args.port}
   - Network: http://{args.host}:{args.port}

📡 WebSocket endpoint: ws://{args.host}:{args.port}/ws

🔗 API Documentation:
   - Swagger UI: http://{args.host}:{args.port}/docs
   - ReDoc: http://{args.host}:{args.port}/redoc

🤖 AI endpoints start with: /api/ai/
🖼️  Frontend endpoints start with: /api/presentation/
🔄 Sync endpoints start with: /api/sync/
""")

    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level=args.log_level
    )


if __name__ == "__main__":
    main()